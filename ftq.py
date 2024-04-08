from mlvp.triggers import *
from bundle import *
from Executor import Executor







class FTQEntry:
    def __init__(self):
        self.ftb = 0




class FTQ:
    def __init__(self, dut, update: UpdateBundle, bpu_out: BranchPredictionResp):
        self.dut = dut
        self.update = update
        self.bpu_out = bpu_out
        self.exec = Executor()

        self.bpu_ptr = 0
        self.exec_ptr = 0
        self.entries = [FTQEntry() for i in range(32)]

    def get_entry(self, ptr):
        return self.entries[ptr % 32]

    def exec_one_ftq_entry(self):
        if self.exec_ptr >= self.bpu_ptr:
            return None


    def update_entries(self):
        if self.bpu_out.s1_fire():
            print("s1 add entry")

        self.bpu_ptr = (self.bpu_ptr + 1) % 32


    async def run(self):
        while True:
            self.update_entries()
            await ClockCycles(self.dut)


if __name__ == "__main__":
    parser = Executor()





