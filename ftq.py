from mlvp.triggers import *
from bundle import *
from config import *
from utils import *
from executor import Executor
from ftb import *
from random import random


class FTQEntry:
    def __init__(self):
        self.pc = None
        self.ftb = None
        self.full_pred = None


class FTQ:
    def __init__(self):
        self.executor = Executor(reset_vector=RESET_VECTOR)

        self.entries = [FTQEntry() for i in range(32)]
        self.bpu_ptr = 0
        self.exec_ptr = 0


        self.update_queue = []
        self.redirect_queue = []

    def get_entry(self, ptr):
        return self.entries[ptr % 32]

    def exec_one_ftq_entry(self):
        if self.exec_ptr >= self.bpu_ptr:
            return None

        entry = self.get_entry(self.exec_ptr)
        current_pc = self.executor.current_inst()[0]
        self.exec_ptr += 1

        # Prediction Block Hit
        if entry.full_pred["hit"] and entry.pc == current_pc:
            print("Hit")

            # Execute the prediction block
            all_branches, redirect_addr, br_taken_mask = self.execute_this_pred_block(entry.pc, entry.full_pred)
            if redirect_addr is None:
                print("Predicition is correct")
            # TODO update ftb entry
            # new_ftb_entry = self.update_ftb_entry_from_branches(entry.ftb, all_branches, br_taken_mask)
            if redirect_addr is not None:
                self.redirect_queue.append((redirect_addr))

        # Prediction Block Miss
        else:
            if entry.pc != current_pc:
                print("Target Error %s right: %s" % (hex(entry.pc), hex(current_pc)))

            # Create a new FTB entry and update & redirect
            new_ftb_entry, br_taken_mask = self.generate_new_ftb_entry(current_pc)
            self.update_queue.append((current_pc, new_ftb_entry, br_taken_mask))
            self.redirect_queue.append((self.executor.current_inst()[0]))

    def generate_update_request(self, update_queue_item):
        pc, new_ftb_entry, br_taken_mask = update_queue_item[0], update_queue_item[1], update_queue_item[2]
        update_request = {}

        update_request["valid"] = True
        update_request["bits_pc"] = pc
        update_request["ftb_entry"] = new_ftb_entry.__dict__()
        update_request["bits_br_taken_mask_0"] = 0 if len(br_taken_mask) == 0 else br_taken_mask[0]
        update_request["bits_br_taken_mask_1"] = 0 if len(br_taken_mask) < 2 else br_taken_mask[1]

        print("[FTQ] Update Request: %s" % hex(pc))
        return update_request

    def generate_redirect_request(self, cfi_target):
        redirect_request = {}
        redirect_request["cfiUpdate"] = {}
        redirect_request["cfiUpdate"]["target"] = cfi_target

        return redirect_request

    def update_ftb_entry_from_branches(self, ftb_entry, branches, br_taken_mask):
        # TODO
        return ftb_entry

    def execute_this_pred_block(self, pc, full_pred):
        end_pc = full_pred["fallThroughAddr"]
        cfi_addr = get_cfi_addr_from_full_pred_dict(pc, full_pred)

        all_branches = []
        br_taken_mask = []
        redirect_addr = None
        print(hex(pc), hex(end_pc))
        while pc < end_pc:
            _, inst_len, branch = self.executor.current_inst()
            self.executor.next_inst()
            if branch is not None:
                br_taken_mask.append(branch["taken"])
                all_branches.append(branch)
            pc += inst_len

            pred_cfi_valid = cfi_addr is not None and pc == cfi_addr
            exec_cfi_valid = branch is not None and branch["taken"]

            if pred_cfi_valid and exec_cfi_valid:
                break
            elif pred_cfi_valid and not exec_cfi_valid:
                redirect_addr = pc
                break
            elif not pred_cfi_valid and exec_cfi_valid:
                # redirect_addr = pc
                redirect_addr = branch["target"]
                break

        return all_branches, redirect_addr, br_taken_mask

    def generate_new_ftb_entry(self, pc):
        br_taken_mask = []
        ftb_entry = FTBEntry()

        fallthrough_addr = pc
        while fallthrough_addr < pc + PREDICT_WIDTH_BYTES:
            _, inst_len, branch = self.executor.current_inst()

            if branch is not None:
                if Executor.is_cond_branch_inst(branch):
                    success = ftb_entry.add_cond_branch_inst(pc, branch["pc"], branch["taken"], branch["target"])
                    br_taken_mask.append(branch["taken"])

                    if not success:
                        break
                    else:
                        self.executor.next_inst()
                        fallthrough_addr += inst_len
                        if branch["taken"]:
                            break
                else:
                    ftb_entry.add_jmp_inst(pc,
                                           branch["pc"],
                                           branch["target"],
                                           inst_len,
                                           Executor.is_call_inst(branch),
                                           Executor.is_ret_inst(branch),
                                           Executor.is_jalr_inst(branch),
                                           Executor.is_jal_inst(branch))
                    fallthrough_addr += 2
                    self.executor.next_inst()
                    break
            else:
                fallthrough_addr += inst_len
                self.executor.next_inst()

        ftb_entry.valid = True
        ftb_entry.pftAddr = get_part_addr(fallthrough_addr)
        ftb_entry.carry = get_part_addr_carry(pc, ftb_entry.pftAddr)

        return ftb_entry, br_taken_mask

    def update_entries(self, bpu_out):
        if bpu_out["s1"]["valid"]:
            print("[FTQ] Add Entry (pc: %s)" % hex(bpu_out["s1"]["pc_3"]))
            entry = self.get_entry(self.bpu_ptr)
            entry.full_pred = bpu_out["s1"]["full_pred"]
            entry.pc = bpu_out["s1"]["pc_3"]
            entry.ftb = None
            self.bpu_ptr += 1


    def update(self, bpu_out):
        self.update_entries(bpu_out)
        self.exec_one_ftq_entry()

        update_request, redirect_request = None, None
        if self.update_queue:
            update_request = self.generate_update_request(self.update_queue.pop(0))

        if self.redirect_queue:
            cfi_target = self.redirect_queue.pop(0)
            redirect_request = self.generate_redirect_request(cfi_target)
            print("[FTQ] Redirect Request: (target: %s)" % hex(cfi_target))

        return (update_request, redirect_request)


if __name__ == "__main__":
    parser = Executor()
    for _ in range (100):
        print(parser.current_inst())
        parser.next_inst()

