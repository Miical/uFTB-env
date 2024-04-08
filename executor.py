from BRTParser import BRTParser

class Executor:
    def __init__(self, filename="ready-to-run/microbench.bin", reset_vector=0x80000000):
        self._executor = BRTParser().fetch(filename)
        self._current_branch = next(self._executor)
        self._current_pc = reset_vector

        self._last_exec_result = {
            "pc": 0,
            "inst_len": 0,
            "branch": 0
        }

        self._exec_once()

    def _exec_once(self):
        self._last_exec_result["pc"] = self._current_pc

        inst_len, branch = 0, None
        if (2 <= self._current_branch["pc"] - self._current_pc <= 4):
            inst_len = self._current_branch["pc"] - self._current_pc
            self._current_pc = self._current_branch["pc"]
        elif (self._current_branch["pc"] == self._current_pc):
            inst_len = Executor.branch_inst_len(self._current_branch)
            self._current_pc = self._current_branch["target"] if self._current_branch["taken"] \
                else self._current_pc + inst_len

            branch = self._current_branch
            self._current_branch = next(self._executor)
        else:
            inst_len = Executor.random_inst_len(self._current_pc)
            self._current_pc += Executor.random_inst_len(self._current_pc)

        self._last_exec_result["inst_len"] = inst_len
        self._last_exec_result["branch"] = branch

    def current_inst(self):
        return self._last_exec_result["pc"], self._last_exec_result["inst_len"], self._last_exec_result["branch"]

    def next_inst(self):
        self._exec_once()

    @staticmethod
    def random_inst_len(pc):
        xor_ans = 0
        for i in range(8):
            xor_ans ^= (pc >> i) & 1
        return 2 if xor_ans else 4

    @staticmethod
    def is_cond_branch_inst(branch):
        return branch["type"] == "*.CBR"

    @staticmethod
    def is_jump_inst(branch):
        return not Executor.is_cond_branch_inst(branch)

    @staticmethod
    def is_call_inst(branch):
        return ".CALL" in branch["type"]

    @staticmethod
    def is_ret_inst(branch):
        return ".RET" in branch["type"]

    @staticmethod
    def is_jalr_inst(branch):
        return ".JALR" in branch["type"] or ".JR" in branch["type"]

    @staticmethod
    def is_compressed_inst(branch):
        type = branch["type"]
        if "C." in type:
            return True
        elif Executor.is_cond_branch_inst(branch):
            return Executor.random_inst_len(branch["pc"]) == 2
        else:
            return False

    @staticmethod
    def branch_inst_len(branch):
        return 2 if Executor.is_compressed_inst(branch) else 4

