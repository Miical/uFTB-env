from ftb import *

class uFTBWay:
    def __init__(self):
        self.valid = 0
        self.tag = 0
        self.ftb_entry = FTBEntry()

    @staticmethod
    def get_tag(pc):
        return pc >> INST_OFFSET_BITS & ((1 << UFTB_TAG_SIZE) - 1)

import math

class PLRU:
    def __init__(self, ways_num):
        self.ways_num = ways_num
        self.bits_layer_num = math.ceil(math.log2(ways_num))
        self.bits = [[0 for _ in range(2 ** layer)] for layer in range(self.bits_layer_num)]

    def update(self, way):
        pos = 0
        for i in range(self.bits_layer_num):
            self.bits[i][pos] = 0 if way & (1 << (self.bits_layer_num - i - 1)) else 1
            pos = pos * 2 + (0 if self.bits[i][pos] else 1)

    def get_lru_way(self):
        pos = 0
        for i in range(self.bits_layer_num):
            pos = pos * 2 + self.bits[i][pos]
        return pos

class TwoBitsCounter:
    def __init__(self):
        self.counter = 0

    def update(self, taken):
        if taken:
            self.counter = min(self.counter + 1, 3)
        else:
            self.counter = max(self.counter - 1, 0)

    def get_prediction(self):
        return 1 if self.counter > 1 else 0

class uFTBModel:
    def __init__(self):
        self.replacer = PLRU(UFTB_WAYS_NUM)
        self.ftb_ways = [uFTBWay() for _ in range(UFTB_WAYS_NUM)]
        self.counters = [[TwoBitsCounter(), TwoBitsCounter()] for _ in range(UFTB_WAYS_NUM)]
        self.update_queue = []
        self.replacer_update_queue = []
        self.replacer_update_queue2 = []

    def find_hit_way(self, pc):
        tag = uFTBWay.get_tag(pc)
        for i in range(UFTB_WAYS_NUM):
            if self.ftb_ways[i].valid and self.ftb_ways[i].tag == tag:
                return i
        return None

    def print_all_ftb_ways(self):
        for i in range(UFTB_WAYS_NUM):
            print(f"way {i}: valid: {self.ftb_ways[i].valid}, tag: {hex(self.ftb_ways[i].tag << 1)}")

    def generate_output(self, s1_fire, s1_pc):
        # print(self.replacer_update_queue)
        # print(self.replacer_update_queue2)
        # print(self.update_queue)
        # self.print_all_ftb_ways()

        # Process replacer update
        new_replacer_update_queue = []
        for i in range(len(self.replacer_update_queue)):
            if self.replacer_update_queue[i][1] == 0:
                self.replacer.update(self.replacer_update_queue[i][0])
                print(f"!                                                    way {self.replacer_update_queue[i][0]} is updated")
            else:
                new_replacer_update_queue.append((self.replacer_update_queue[i][0], self.replacer_update_queue[i][1] - 1))
        self.replacer_update_queue = new_replacer_update_queue

        new_replacer_update_queue2 = []
        for i in range(len(self.replacer_update_queue2)):
            if self.replacer_update_queue2[i][1] == 0:
                self.replacer.update(self.replacer_update_queue2[i][0])
                print(f"!                                                    way {self.replacer_update_queue2[i][0]} is updated")
            else:
                new_replacer_update_queue2.append((self.replacer_update_queue2[i][0], self.replacer_update_queue2[i][1] - 1))
        self.replacer_update_queue2 = new_replacer_update_queue2
        print(f"replacer: {self.replacer.get_lru_way()}")

        # process update request
        new_update_queue = []
        for i in range(len(self.update_queue)):
            if self.update_queue[i][1] == 0:
                self.update_all(self.update_queue[i][0], self.update_queue[i][2])
            else:
                selected_way = self.update_queue[i][2]
                if self.update_queue[i][1] == 2:
                    selected_way = self.find_hit_way(self.update_queue[i][0]['bits_pc'])
                    for j in range(len(self.update_queue)):
                        if self.update_queue[j][1] == 1:
                            if uFTBWay.get_tag(self.update_queue[i][0]['bits_pc']) == uFTBWay.get_tag(self.update_queue[j][0]['bits_pc']):
                                if selected_way is None or self.update_queue[j][2] < selected_way:
                                    selected_way = self.update_queue[j][2]
                                    break
                    print(f"Hit selected way is {selected_way}")
                elif self.update_queue[i][1] == 1:
                    if selected_way is None:
                        selected_way = self.replacer.get_lru_way()
                        print(f"victim way is {selected_way}, tag: {hex(self.ftb_ways[selected_way].tag << 1)}, valid: {self.ftb_ways[selected_way].valid}")
                    self.replacer_update_queue2.insert(0, (selected_way, 0))
                    print(f"Append way {selected_way}")
                new_update_queue.append((self.update_queue[i][0], self.update_queue[i][1] - 1, selected_way))
        self.update_queue = new_update_queue

        if not s1_fire:
            return None

        hit_way = self.find_hit_way(s1_pc)
        # print({ "hit_way": hit_way, "hit": 1 if hit_way is not None else 0})
        if hit_way is None:
            return None
        print(f"RM Hit at {hit_way}")

        self.replacer_update_queue.append((hit_way, 1))

        ftb_entry = self.ftb_ways[hit_way].ftb_entry
        br_taken_mask = [self.counters[hit_way][0].get_prediction(), self.counters[hit_way][1].get_prediction()]
        return ftb_entry, br_taken_mask, hit_way

    def get_update_way(self, pc):
        hit_way = self.find_hit_way(pc)
        if hit_way is not None:
            return hit_way
        else:
            victim_way = self.replacer.get_lru_way()
            print(f"victim way is {victim_way}, tag: {hex(self.ftb_ways[victim_way].tag << 1)}, valid: {self.ftb_ways[victim_way].valid}")
            return self.replacer.get_lru_way()

    def update_ftb_ways(self, update_request, selected_way):
        if not update_request["valid"]:
            return

        print(f"ftb entry {hex(update_request['bits_pc'])} is put into way {selected_way}")
        self.ftb_ways[selected_way].valid = 1
        self.ftb_ways[selected_way].tag = uFTBWay.get_tag(update_request["bits_pc"])
        self.ftb_ways[selected_way].ftb_entry = FTBEntry.from_dict(update_request["ftb_entry"])

    def update_counters(self, update_request, selected_way):
        if not update_request["valid"]:
            return

        need_to_update = [False, False]
        if update_request["ftb_entry"]["brSlots_0_valid"] and not update_request["ftb_entry"]["always_taken_0"]:
            need_to_update[0] = True
        if update_request["ftb_entry"]["tailSlot_valid"] and not update_request["ftb_entry"]["always_taken_1"] \
                                                         and update_request["ftb_entry"]["tailSlot_sharing"]:
            need_to_update[1] = True

        if need_to_update[0]:
            self.counters[selected_way][0].update(update_request["bits_br_taken_mask_0"])
        if need_to_update[1]:
            self.counters[selected_way][1].update(update_request["bits_br_taken_mask_1"])

    def update_all(self, update_request, selected_way):
        # self.replacer_update_queue.append((self.get_update_way(update_request['bits_pc']), 0))
        # self.replacer.update(self.get_update_way(update_request['bits_pc']))
        self.update_ftb_ways(update_request, selected_way)
        self.update_counters(update_request, selected_way)

    def update(self, update_request):
        # self.update_all(update_request)
        self.update_queue.append((update_request, 2, None))
