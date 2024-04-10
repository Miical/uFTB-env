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

        self.s0_fire = RegInit(0)
        self.s1_fire = RegNext(self.s0_fire)
        self.s2_fire = RegNext(self.s1_fire)
        self.s3_fire = RegNext(self.s2_fire)

        self.s0_pc = RegInit(0)
        self.s1_pc = RegNext(self.s0_pc)
        self.s2_pc = RegNext(self.s1_pc)
        self.s3_pc = RegNext(self.s2_pc)

        self.ftq = FTQ()

    def pipeline_update(self):
        self.pipeline_ctrl.s0_fire_0.value = self.s0_fire.value
        self.pipeline_ctrl.s0_fire_1.value = self.s0_fire.value
        self.pipeline_ctrl.s0_fire_2.value = self.s0_fire.value
        self.pipeline_ctrl.s0_fire_3.value = self.s0_fire.value

        self.pipeline_ctrl.s1_fire_0.value = self.s1_fire.value
        self.pipeline_ctrl.s1_fire_1.value = self.s1_fire.value
        self.pipeline_ctrl.s1_fire_2.value = self.s1_fire.value
        self.pipeline_ctrl.s1_fire_3.value = self.s1_fire.value

        self.pipeline_ctrl.s2_fire_0.value = self.s2_fire.value
        self.pipeline_ctrl.s2_fire_1.value = self.s2_fire.value
        self.pipeline_ctrl.s2_fire_2.value = self.s2_fire.value
        self.pipeline_ctrl.s2_fire_3.value = self.s2_fire.value

        self.pipeline_ctrl.s3_fire_0.value = self.s3_fire.value
        self.pipeline_ctrl.s3_fire_1.value = self.s3_fire.value
        self.pipeline_ctrl.s3_fire_2.value = self.s3_fire.value
        self.pipeline_ctrl.s3_fire_3.value = self.s3_fire.value

        self.dut_out.s1.valid.value = self.s1_fire.value
        self.dut.io_in_bits_s0_pc_0.value = self.s0_pc.value
        self.dut.io_in_bits_s0_pc_1.value = self.s0_pc.value
        self.dut.io_in_bits_s0_pc_2.value = self.s0_pc.value
        self.dut.io_in_bits_s0_pc_3.value = self.s0_pc.value


    def generate_bpu_output(self, dut_output):
        dut_output["s1"]["valid"] = self.s1_fire
        dut_output["s2"]["valid"] = self.s2_fire
        dut_output["s3"]["valid"] = self.s3_fire

        return dut_output


    async def run(self):
        self.dut.reset.value = 1
        await ClockCycles(self.dut, 10)
        self.dut.reset.value = 0
        await ClockCycles(self.dut, 10)
        self.s0_fire.value = 1

        while True:
            dut_output = self.dut_out.collect()
            bpu_output = self.generate_bpu_output(dut_output)

            self.s0_pc.value = get_target_from_full_pred_dict(self.s0_pc.value, dut_output["s1"]["full_pred"])
            self.pipeline_update()

            update_request, redirect_request = self.ftq.update(bpu_output)

            # Update Request
            if update_request:
                self.dut_update.assign(update_request)
                self.dut_update.valid.value = 1
            else:
                self.dut_update.valid.value = 0

            # Redirect Request
            if redirect_request:
                self.s0_pc.value = redirect_request["cfiUpdate"]["target"]

            await ClockCycles(self.dut, 1)



async def uftb_test():
    uFTB_update = UpdateBundle.from_prefix(uFTB, "io_update_")
    uFTB_out = BranchPredictionResp.from_prefix(uFTB, "io_out_")
    pipeline_ctrl = PipelineCtrlBundle.from_prefix(uFTB, "io_")
    enable_ctrl = EnableCtrlBundle.from_prefix(uFTB, "io_ctrl_")

    mlvp.create_task(mlvp.start_clock(uFTB))
    mlvp.create_task(BPUTop(uFTB, uFTB_out, uFTB_update, pipeline_ctrl, enable_ctrl).run())

    await ClockCycles(uFTB, 500)




if __name__ == "__main__":
    mlvp.run(uftb_test())
    uFTB.finalize()
