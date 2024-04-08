from BRTParser import BRTParser

class Executor:
    def __init__(self, filename="ready-to-run/microbench.bin", reset_vector=0x80000000):
        self.executor = BRTParser().fetch(filename)
        self.current_branch = next(self.executor)
        self.current_pc = reset_vector

    def exec_once(self):
        if (2 <= self.current_branch["pc"] - self.current_pc <= 4):
            self.current_pc = self.current_branch["pc"]
        elif (self.current_branch["pc"] == self.current_pc):
            self.current_pc = self.current_branch["target"] if self.current_branch["taken"] \
                else self.current_pc + Executor.branch_inst_len(self.current_branch)
            branch = self.current_branch
            self.current_branch = next(self.executor)

            return branch
        else:
            self.current_pc += Executor.random_inst_len(self.current_pc)


    @staticmethod
    def random_inst_len(pc):
        xor_ans = 0
        for i in range(8):
            xor_ans ^= (pc >> i) & 1
        return 2 if xor_ans else 4

    @staticmethod
    def is_compressed_inst(branch):
        type = branch["type"]
        return "C." in type

    @staticmethod
    def branch_inst_len(branch):
        return 2 if Executor.is_compressed_inst(branch) else 4

