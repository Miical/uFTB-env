from mlvp.triggers import *
from bundle import *
from config import *
from utils import *
from executor import Executor
from ftb import *




class FTQEntry:
    def __init__(self):
        self.hit = None
        self.pc = None




class FTQ:
    def __init__(self, dut, update: UpdateBundle, bpu_out: BranchPredictionResp):
        self.dut = dut
        self.update = update
        self.bpu_out = bpu_out
        self.executor = Executor(reset_vector=RESET_VECTOR)

        self.entries = [FTQEntry() for i in range(32)]
        self.bpu_ptr = 0
        self.exec_ptr = 0

    def get_entry(self, ptr):
        return self.entries[ptr % 32]

    def exec_one_ftq_entry(self):
        if self.exec_ptr >= self.bpu_ptr:
            return None

        entry = self.get_entry(self.exec_ptr)
        if entry.hit:
            pass
        else:
            print("ftb_entry:", self.generate_new_ftb_entry(self.executor.current_inst()[0]))

    def generate_new_ftb_entry(self, pc):
        ftb_entry = FTBEntry()

        fallthrough_addr = pc
        while fallthrough_addr < pc + PREDICT_WIDTH_BYTES:
            _, inst_len, branch = self.executor.current_inst()

            if branch is not None:
                if Executor.is_cond_branch_inst(branch):
                    success = ftb_entry.add_cond_branch_inst(pc, branch["pc"], branch["taken"], branch["target"])

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
                                           Executor.is_jalr_inst(branch))
                    fallthrough_addr += 2
                    self.executor.next_inst()
                    break
            else:
                fallthrough_addr += inst_len
                self.executor.next_inst()

        ftb_entry.valid = True
        ftb_entry.pftAddr = get_part_addr(fallthrough_addr)
        ftb_entry.carry = get_part_addr_carry(pc, ftb_entry.pftAddr)

        return ftb_entry

    def update_entries(self):
        if self.bpu_out.s1_fire():
            print("s1 add entry")
            entry = self.get_entry(self.bpu_ptr)
            entry.hit = self.bpu_out.s1.ftb_entry_hit()
            entry.pc = self.bpu_out.s1.pc_1.value

            self.bpu_ptr += 1



    async def run(self):
        while True:
            self.update_entries()
            await ClockCycles(self.dut)

            self.exec_one_ftq_entry()


if __name__ == "__main__":
    parser = Executor()
    for _ in range (100):
        print(parser.current_inst())
        parser.next_inst()


