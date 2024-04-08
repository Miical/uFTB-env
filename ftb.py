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


    def send_to(self, ftb_bundle):
        ftb_bundle.brSlots_0_offset.value = self.brSlot.offset
        ftb_bundle.brSlots_0_lower.value = self.brSlot.lower
        ftb_bundle.brSlots_0_tarStat.value = self.brSlot.tarStart
        ftb_bundle.brSlots_0_valid.value = self.brSlot.valid
        ftb_bundle.tailSlot_offset.value = self.tailSlot.offset
        ftb_bundle.tailSlot_lower.value = self.tailSlot.lower
        ftb_bundle.tailSlot_tarStat.value = self.tailSlot.tarStart
        ftb_bundle.tailSlot_sharing.value = self.tailSlot.sharing
        ftb_bundle.tailSlot_valid.value = self.tailSlot.valid
        ftb_bundle.pftAddr.value = self.pftAddr
        ftb_bundle.carry.value = self.carry
        ftb_bundle.isCall.value = self.isCall
        ftb_bundle.isRet.value = self.isRet
        ftb_bundle.isJalr.value = self.isJalr
        ftb_bundle.last_may_be_rvi_call.value = self.last_may_be_rvi_call
        ftb_bundle.always_taken_0.value = self.always_taken[0]
        ftb_bundle.always_taken_1.value = self.always_taken[1]

    @classmethod
    def from_rand(cls):
        return cls(valid=rand_bits(1),
                   brSlot=FTBSlot.from_rand(),
                   tailSlot=FTBSlot.from_rand(),
                   pftAddr=rand_bits(4),
                   carry=rand_bits(1),
                   isCall=rand_bits(1),
                   isRet=rand_bits(1),
                   isJalr=rand_bits(1),
                   last_may_be_rvi_call=rand_bits(1),
                   always_taken=[rand_bits(1), rand_bits(1)])

    def __str__(self):
        return f"FTBEntry(\n\tvalid={self.valid},\n\tbrSlot={self.brSlot},\n\ttailSlot={self.tailSlot},\n\tpftAddr={self.pftAddr},\n\tcarry={self.carry},\n\tisCall={self.isCall},\n\tisRet={self.isRet},\n\tisJalr={self.isJalr},\n\tlast_may_be_rvi_call={self.last_may_be_rvi_call},\n\talways_taken={self.always_taken})"
