from config import *

def get_part_addr(pc):
    return (pc >> INST_OFFSET_BITS) & ((1 << PREDICT_WIDTH_OFFSET_BITS) - 1)

def get_part_addr_carry(pc, pftaddr):
    return ((pftaddr - pc) >> (INST_OFFSET_BITS + PREDICT_WIDTH_OFFSET_BITS)) & 1

def get_full_addr(pc, part_addr, carry):
    return (pc & ~((1 << INST_OFFSET_BITS) - 1)) | (part_addr << INST_OFFSET_BITS) + (carry << (INST_OFFSET_BITS + PREDICT_WIDTH_OFFSET_BITS))



def get_lower_addr(pc, bits):
    return pc & ((1 << bits) - 1)

def get_target_stat(pc_higher, target_higher):
    if target_higher < pc_higher:
        return TAR_UDF
    elif target_higher > pc_higher:
        return TAR_OVF
    else:
        return TAR_FIT



def get_cfi_addr_from_full_pred_dict(pc, d):
    if not d["hit"]:
        return None
    elif d["slot_valids_0"] and d["br_taken_mask_0"]:
        return get_full_addr(pc, d["offsets_0"], 0)
    elif d["slot_valids_1"] and d["br_taken_mask_1"] and d["is_br_sharing"]:
        return get_full_addr(pc, d["offsets_1"], 0)
    elif d["slot_valids_1"] and not d["is_br_sharing"]:
        return get_full_addr(pc, d["offsets_1"], 0)
    else:
        return None

def get_target_from_full_pred_dict(pc, d):
    if not d["hit"]:
        return pc + PREDICT_WIDTH_BYTES
    elif d["slot_valids_0"] and d["br_taken_mask_0"]:
        return d["targets_0"]
    elif d["slot_valids_1"] and d["br_taken_mask_1"] and d["is_br_sharing"]:
        return d["targets_1"]
    elif d["slot_valids_1"] and not d["is_br_sharing"]:
        return d["jalr_target"]
    else:
        return d["fallThroughAddr"]
