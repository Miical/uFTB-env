from utils import *

import random

def rand_bits(bits_num):
    return random.randint(0, 2**bits_num - 1)

class FTBSlot:
    def __init__(self):
        self.valid = 0
        self.offset = 0
        self.lower = 0
        self.tarStart = 0
        self.sharing = 0

    @classmethod
    def from_rand(cls):
        return cls(offset=rand_bits(4), lower=rand_bits(12),
                   tarStart=rand_bits(12), sharing=rand_bits(1), valid=rand_bits(1))

    def __str__(self):
        return f"FTBSlot(valid={self.valid}, offset={self.offset}, lower={self.lower}, tarStart={self.tarStart}, sharing={self.sharing})"


class FTBEntry:
    def __init__(self):
        self.valid = 0
        self.brSlot = FTBSlot()
        self.tailSlot = FTBSlot()
        self.pftAddr = 0
        self.carry = 0
        self.isCall = False
        self.isRet = False
        self.isJalr = False
        self.last_may_be_rvi_call = False
        self.always_taken = [0, 0]

    def add_cond_branch_inst(self, start_pc, inst_pc, is_taken, target_addr):
        if self.brSlot.valid and self.tailSlot.valid:
            return False

        slot = FTBSlot()
        slot.valid = True
        slot.offset = get_part_addr(inst_pc - start_pc)
        slot.lower = get_lower_addr(inst_pc, 12)
        slot.tarStart = get_target_stat(start_pc >> 12, target_addr >> 12)

        if self.brSlot.valid:
            self.tailSlot = slot
            self.tailSlot.sharing = True
            self.always_taken[1] = is_taken
        else:
            self.brSlot = slot
            self.always_taken[0] = is_taken

        return True

    def add_jmp_inst(self, start_pc, inst_pc, target_addr, inst_len, is_call, is_ret, is_jalr):
        if self.tailSlot.valid:
            return False

        self.tailSlot.valid = True
        self.tailSlot.offset = get_part_addr(inst_pc - start_pc)
        self.tailSlot.lower = get_lower_addr(inst_pc, 20)
        self.tailSlot.tarStart = get_target_stat(start_pc >> 20, target_addr >> 20)
        self.tailSlot.sharing = False

        self.isCall = is_call
        self.isRet = is_ret
        self.isJalr = is_jalr
        self.last_may_be_rvi_call = is_call and inst_len == 4

        return True

    def get_fallthrough_addr(self, pc):
        return get_full_addr(pc, self.pftAddr, self.carry)

    def __dict__(self):
        return {
            "brSlots_0_offset": self.brSlot.offset,
            "brSlots_0_lower": self.brSlot.lower,
            "brSlots_0_tarStat": self.brSlot.tarStart,
            "brSlots_0_valid": self.brSlot.valid,
            "tailSlot_offset": self.tailSlot.offset,
            "tailSlot_lower": self.tailSlot.lower,
            "tailSlot_tarStat": self.tailSlot.tarStart,
            "tailSlot_sharing": self.tailSlot.sharing,
            "tailSlot_valid": self.tailSlot.valid,
            "pftAddr": self.pftAddr,
            "carry": self.carry,
            "isCall": self.isCall,
            "isRet": self.isRet,
            "isJalr": self.isJalr,
            "last_may_be_rvi_call": self.last_may_be_rvi_call,
            "always_taken_0": self.always_taken[0],
            "always_taken_1": self.always_taken[1]
        }

    @classmethod
    def from_dict(self, d):
        entry = FTBEntry()
        entry.brSlot.offset = d["brSlots_0_offset"]
        entry.brSlot.lower = d["brSlots_0_lower"]
        entry.brSlot.tarStart = d["brSlots_0_tarStat"]
        entry.brSlot.valid = d["brSlots_0_valid"]
        entry.tailSlot.offset = d["tailSlot_offset"]
        entry.tailSlot.lower = d["tailSlot_lower"]
        entry.tailSlot.tarStart = d["tailSlot_tarStat"]
        entry.tailSlot.sharing = d["tailSlot_sharing"]
        entry.tailSlot.valid = d["tailSlot_valid"]
        entry.pftAddr = d["pftAddr"]
        entry.carry = d["carry"]
        entry.isCall = d["isCall"]
        entry.isRet = d["isRet"]
        entry.isJalr = d["isJalr"]
        entry.last_may_be_rvi_call = d["last_may_be_rvi_call"]
        entry.always_taken[0] = d["always_taken_0"]
        entry.always_taken[1] = d["always_taken_1"]
        return entry

    def __str__(self):
        return f"FTBEntry(\n\tvalid={self.valid},\n\tbrSlot={self.brSlot},\n\ttailSlot={self.tailSlot},\n\tpftAddr={self.pftAddr},\n\tcarry={self.carry},\n\tisCall={self.isCall},\n\tisRet={self.isRet},\n\tisJalr={self.isJalr},\n\tlast_may_be_rvi_call={self.last_may_be_rvi_call},\n\talways_taken={self.always_taken})"
