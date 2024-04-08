from UT_FauFTB import *
import mlvp
from mlvp.reg import *
from mlvp.wire import *
from mlvp.interface import *
from mlvp.triggers import *

from ftq import *
from bundle import *

uFTB = DUTFauFTB()
uFTB.init_clock("clock")



class BPUTop:
    def __init__(self, dut: DUTFauFTB, bpu_out: BranchPredictionResp):
        self.dut = dut
        self.bpu_out = bpu_out

        self.s0_fire = RegInit(0)
        self.s1_fire = RegNext(self.s0_fire)
        self.s2_fire = RegNext(self.s1_fire)
        self.s3_fire = RegNext(self.s2_fire)

        self.pipeline_ctrl = PipelineCtrlBundle.from_regex(uFTB, r"io_(.*)_.")
        self.enable_ctrl = EnableCtrlBundle.from_prefix(uFTB, "io_ctrl_")

    def pipeline_update(self):
        self.pipeline_ctrl.s0_fire.value = self.s0_fire.value
        self.pipeline_ctrl.s1_fire.value = self.s1_fire.value
        self.pipeline_ctrl.s2_fire.value = self.s2_fire.value
        self.pipeline_ctrl.s3_fire.value = self.s3_fire.value

        self.bpu_out.s1.valid.value = self.s1_fire.value


    async def run(self):
        self.dut.reset.value = 1
        await ClockCycles(self.dut, 10)
        self.dut.reset.value = 0
        await ClockCycles(self.dut, 10)
        self.s0_fire.value = 1

        while True:
            self.pipeline_update()
            await ClockCycles(self.dut, 1)






import random
def rand_bits(bits_num):
    return random.randint(0, 2**bits_num - 1)

class FTBSlot:
    def __init__(self, offset, lower, tarStart, sharing, valid):
        self.offset, self.lower, self.tarStart, self.sharing, self.valid = offset, lower, tarStart, sharing, valid

    @classmethod
    def from_rand(cls):
        return cls(offset=rand_bits(4), lower=rand_bits(12),
                   tarStart=rand_bits(12), sharing=rand_bits(1), valid=rand_bits(1))


class FTBEntry:
    def __init__(self, valid, brSlot, tailSlot, pftAddr, carry, isCall, isRet, isJalr, last_may_be_rvi_call, always_taken):
        self.valid, self.brSlot, self.tailSlot, self.pftAddr, self.carry, self.isCall, self.isRet, self.isJalr, self.last_may_be_rvi_call, self.always_taken = valid, brSlot, tailSlot, pftAddr, carry, isCall, isRet, isJalr, last_may_be_rvi_call, always_taken

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


async def uftb_test():
    uFTB_update = UpdateBundle.from_prefix(uFTB, "io_update_")
    uFTB_out = BranchPredictionResp.from_prefix(uFTB, "io_out_")

    print("bpu_out")
    #TODO interface problem
    bpu_out = BranchPredictionResp({
        "s1_valid": Wire(),
        "s2_valid": Wire(),
        "s3_valid": Wire(),
        "s2_hasRedirect": Wire(),
        "s3_hasRedirect": Wire(),
        "s1_full_pred_1_hit": Wire(),
    })
    print("bpu_out_end")


    mlvp.create_task(mlvp.start_clock(uFTB))
    mlvp.create_task(BPUTop(uFTB, bpu_out).run())
    mlvp.create_task(FTQ(uFTB, uFTB_update, bpu_out).run())

    await ClockCycles(uFTB, 10)

    uFTB.io_in_bits_s0_pc_0.value = 5
    # mlvp.delay_assign(uFTB.io_in_bits_s0_pc_1, 5)




    await ClockCycles(uFTB, 100)




if __name__ == "__main__":

    mlvp.run(uftb_test())

    uFTB.finalize()
