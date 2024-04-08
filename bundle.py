from mlvp.interface import Interface

class PipelineCtrlBundle(Interface):
    signals_list = ["s0_fire", "s1_fire", "s2_fire", "s3_fire",
                    "s1_ready", "s2_ready", "s3_ready",
                    "s2_redirect", "s3_redirect"]

class EnableCtrlBundle(Interface):
    signals_list = ["ubtb_enable", "btb_enable", "bim_enable", "tage_enable",
                    "sc_enable", "ras_enable", "loop_enable"]


class FTBEntryBundle(Interface):
    signals_list = ["brSlots_0_offset", "brSlots_0_lower", "brSlots_0_tarStat", "brSlots_0_valid",
                    "tailSlot_offset", "tailSlot_lower", "tailSlot_tarStat", "tailSlot_sharing", "tailSlot_valid",
                    "pftAddr", "carry", "isCall", "isRet", "isJalr", "last_may_be_rvi_call",
                     "always_taken_0", "always_taken_1"]

class UpdateBundle(Interface):
    signals_list = ["valid", "bits_pc"]

    sub_interfaces = [
        ("ftb_entry", lambda dut: FTBEntryBundle.from_prefix(dut, "bits_ftb_entry_"))
    ]

class FullBranchPredirectionBundle(Interface):
    signals_list = ["hit", "slot_valids_0", "slot_valids_1", "targets_0", "targets_1",
                    "offsets_0", "offsets_1", "fallThroughAddr", "fallThroughErr",
                    "is_jal", "is_jalr", "is_call", "is_ret", "is_br_sharing",
                    "last_may_be_rvi_call",
                    "br_taken_mask_0", "br_taken_mask_1",
                    "jalr_target"]

class BranchPredictionBundle(Interface):
    signals_list = ["pc_1", "valid", "hasRedirect", "ftq_idx"]
    sub_interfaces = [
        ("full_pred", lambda dut: FullBranchPredirectionBundle.from_regex(dut, r"full_pred_\d_(.*)"))
    ]


    def ftb_entry_hit(self):
        return self.full_pred.hit.value



class BranchPredictionResp(Interface):
    signals_list = ["last_stage_meta"]
    sub_interfaces = [
        ("s1", lambda dut: BranchPredictionBundle.from_prefix(dut, "s1_")),
        ("s2", lambda dut: BranchPredictionBundle.from_prefix(dut, "s2_")),
        ("s3", lambda dut: BranchPredictionBundle.from_prefix(dut, "s3_")),
        ("last_stage_ftb_entry", lambda dut: FTBEntryBundle.from_prefix(dut, "last_stage_ftb_entry_"))
    ]


    def s1_fire(self):
        return self.s1.valid.value
    def s2_fire(self):
        return self.s2.valid.value and self.s2.hasRedirect.value
    def s3_fire(self):
        return self.s3.valid.value and self.s3.hasRedirect.value







