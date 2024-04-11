from UT_FauFTB import *
import mlvp
from mlvp.reg import *
from mlvp.interface import *
from mlvp.triggers import *

from ftq import *
from bundle import *

uFTB = DUTFauFTB()
uFTB.init_clock("clock")



class BPUTop:
    def __init__(self, dut, dut_out: BranchPredictionResp, dut_update: UpdateBundle, pipeline_ctrl: PipelineCtrlBundle, enable_ctrl: EnableCtrlBundle):
        self.dut = dut

        self.dut_out = dut_out
        self.dut_update = dut_update
        self.pipeline_ctrl = pipeline_ctrl
        self.enable_ctrl = enable_ctrl

        enable_ctrl.ubtb_enable.value = 1

        self.s0_fire = 0
        self.s1_fire = 0
        self.s2_fire = 0
        self.s3_fire = 0

        self.s0_pc = 0
        self.s1_pc = 0
        self.s2_pc = 0
        self.s3_pc = 0

        self.ftq = FTQ()
        self.ftb_provider = FTBProvider()

    def pipeline_assign(self):
        self.pipeline_ctrl.s0_fire_0.value = self.s0_fire
        self.pipeline_ctrl.s0_fire_1.value = self.s0_fire
        self.pipeline_ctrl.s0_fire_2.value = self.s0_fire
        self.pipeline_ctrl.s0_fire_3.value = self.s0_fire

        self.pipeline_ctrl.s1_fire_0.value = self.s1_fire
        self.pipeline_ctrl.s1_fire_1.value = self.s1_fire
        self.pipeline_ctrl.s1_fire_2.value = self.s1_fire
        self.pipeline_ctrl.s1_fire_3.value = self.s1_fire

        self.pipeline_ctrl.s2_fire_0.value = self.s2_fire
        self.pipeline_ctrl.s2_fire_1.value = self.s2_fire
        self.pipeline_ctrl.s2_fire_2.value = self.s2_fire
        self.pipeline_ctrl.s2_fire_3.value = self.s2_fire

        self.pipeline_ctrl.s3_fire_0.value = self.s3_fire
        self.pipeline_ctrl.s3_fire_1.value = self.s3_fire
        self.pipeline_ctrl.s3_fire_2.value = self.s3_fire
        self.pipeline_ctrl.s3_fire_3.value = self.s3_fire

        self.dut.io_in_bits_s0_pc_0.value = self.s0_pc
        self.dut.io_in_bits_s0_pc_1.value = self.s0_pc
        self.dut.io_in_bits_s0_pc_2.value = self.s0_pc
        self.dut.io_in_bits_s0_pc_3.value = self.s0_pc


    def generate_bpu_output(self, dut_output):
        dut_output["s1"]["valid"] = self.s1_fire
        dut_output["s2"]["valid"] = self.s2_fire
        dut_output["s3"]["valid"] = self.s3_fire

        dut_output["s2"]["pc_3"] = self.s2_pc
        dut_output["s3"]["pc_3"] = self.s3_pc

        # Provide Basic FTB Prediction
        ftb_provider_stage_enable = (False, True, True)

        if self.s1_fire and ftb_provider_stage_enable[0]:
            ftb_entry = self.ftb_provider.provide_ftb_entry(self.s1_fire, self.s1_pc)
            if ftb_entry is not None:
                ftb_entry.put_to_full_pred_dict(self.s1_pc, dut_output["s1"]["full_pred"])
            else:
                set_all_none_item_to_zero(dut_output["s1"]["full_pred"])

        if self.s2_fire and ftb_provider_stage_enable[1]:
            ftb_entry = self.ftb_provider.provide_ftb_entry(self.s2_fire, self.s2_pc)
            if ftb_entry is not None:
                ftb_entry.put_to_full_pred_dict(self.s2_pc, dut_output["s2"]["full_pred"])
            else:
                set_all_none_item_to_zero(dut_output["s2"]["full_pred"])

        if self.s3_fire and ftb_provider_stage_enable[2]:
            ftb_entry = self.ftb_provider.provide_ftb_entry(self.s3_fire, self.s3_pc)
            if ftb_entry is not None:
                ftb_entry.put_to_full_pred_dict(self.s3_pc, dut_output["s3"]["full_pred"])
                dut_output["last_stage_ftb_entry"] = ftb_entry.__dict__()
            else:
                set_all_none_item_to_zero(dut_output["s3"]["full_pred"])
                dut_output["last_stage_ftb_entry"] = FTBEntry().__dict__()

        return dut_output


    async def run(self):
        self.dut.reset.value = 1
        await ClockCycles(self.dut, 10)
        self.dut.reset.value = 0
        await ClockCycles(self.dut, 10)

        while True:
            self.pipeline_assign()
            await ClockCycles(self.dut, 1)

            dut_output = self.dut_out.collect()
            bpu_output = self.generate_bpu_output(dut_output)

            npc_gen = RESET_VECTOR
            next_s0_fire = 1
            next_s1_fire = 1

            if self.s1_fire:
                 npc_gen = get_target_from_full_pred_dict(self.s1_pc, dut_output["s1"]["full_pred"])

            update_request, redirect_request = self.ftq.update(bpu_output)

            # Update Request
            if update_request:
                self.ftb_provider.update(update_request)
                self.dut_update.assign(update_request)
                self.dut_update.valid.value = 1
            else:
                self.dut_update.valid.value = 0

            # Redirect Request
            if redirect_request:
                next_s0_fire = 1
                next_s1_fire = 0
                npc_gen = redirect_request["cfiUpdate"]["target"]

            self.s3_fire = self.s2_fire
            self.s2_fire = self.s1_fire
            self.s1_fire = next_s1_fire
            self.s0_fire = next_s0_fire

            self.s3_pc = self.s2_pc
            self.s2_pc = self.s1_pc
            self.s1_pc = self.s0_pc
            self.s0_pc = npc_gen



async def uftb_test():
    uFTB_update = UpdateBundle.from_prefix(uFTB, "io_update_")
    uFTB_out = BranchPredictionResp.from_prefix(uFTB, "io_out_")
    pipeline_ctrl = PipelineCtrlBundle.from_prefix(uFTB, "io_")
    enable_ctrl = EnableCtrlBundle.from_prefix(uFTB, "io_ctrl_")

    mlvp.create_task(mlvp.start_clock(uFTB))
    mlvp.create_task(BPUTop(uFTB, uFTB_out, uFTB_update, pipeline_ctrl, enable_ctrl).run())

    await ClockCycles(uFTB, 2027)




if __name__ == "__main__":
    mlvp.run(uftb_test())
    uFTB.finalize()
