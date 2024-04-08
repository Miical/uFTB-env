from config import *

def get_part_addr(pc):
    return (pc >> INST_OFFSET_BITS) & ((1 << PREDICT_WIDTH_OFFSET_BITS) - 1)

def get_lower_addr(pc, bits):
    return pc & ((1 << bits) - 1)

def get_part_addr_carry(pc, pftaddr):
    return ((pftaddr - pc) >> (INST_OFFSET_BITS + PREDICT_WIDTH_OFFSET_BITS)) & 1

def get_target_stat(pc_higher, target_higher):
    if target_higher < pc_higher:
        return TAR_UDF
    elif target_higher > pc_higher:
        return TAR_OVF
    else:
        return TAR_FIT
