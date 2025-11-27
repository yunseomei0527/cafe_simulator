from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
from pypdevs.simulator import DEVSException
from pypdevs.DEVS import AtomicDEVS
from pypdevs.DEVS import CoupledDEVS
from pypdevs.simulator import Simulator
import random

# ----------------------------------------------------------------------
# 2인석 대기열 atomic 모델
# ----------------------------------------------------------------------
class Waiting2AMState:
    def __init__(self, current="WAIT"):
        self.set(current)

    def set(self, value):
        self.__state = value
        return self.__state

    def get(self):
        return self.__state

    def __str__(self):
        return self.get()


class Waiting2AM(AtomicDEVS):
    def __init__(self, name, max2):
        super().__init__(name)

        # Input/Output Ports
        self.in_guest = self.addInPort("in_guest")      # (Hall, n)
        self.in_exit = self.addInPort("in_exit")        # exit2
        self.out_order = self.addOutPort("out_order")   # (Hall, n)

        # Parameters
        self.max2 = max2

        # Initial State
        self.state = Waiting2AMState("WAIT")
        self.m2 = 0
        self.queue = []
        self.current = None  # 현재 사용자 (ORDER 상태에서)

    def timeAdvance(self):
        state = self.state.get()
        if state == "WAIT":
            return INFINITY
        elif state == "ORDER":
            return 1
        else:
            raise DEVSException(f"Unknown state <{state}> in timeAdvance")

    def outputFnc(self):
        state = self.state.get()
        
        print(f"[Waiting] State: {state}, Current: {self.current}, Queue: {self.queue}, m2: {self.m2}")

        if state == "ORDER" and self.current:
            return {self.out_order: self.current}
        return {}

    def intTransition(self):
        state = self.state.get()

        if state == "ORDER":
            self.state = Waiting2AMState("WAIT")
            self.m2 += 1
            self.current = None

            return self.state

        elif state == "WAIT":

            # WAIT 상태에서는 내부 전이 없음
            return self.state

        else:
            raise DEVSException(f"Unknown state <{state}> in intTransition")

    def extTransition(self, inputs):
        state = self.state.get()

        # WAIT 상태
        if state == "WAIT":
            # 손님 도착
            if self.in_guest in inputs:
                guest = inputs[self.in_guest]
                # print(guest)
                self.queue.append(guest)

                if self.m2 < self.max2:
                    # 좌석 있음 → ORDER로 전이
                    self.current = self.queue.pop(0)
                    self.state = Waiting2AMState("ORDER")
                else:
                    # 좌석 없음 → WAIT 유지
                    self.state = Waiting2AMState("WAIT")

            # 퇴장 signal
            if self.in_exit in inputs:
                if len(self.queue) > 0:
                    # 대기열 있음 → ORDER로 전이
                    self.current = self.queue.pop(0)
                    self.m2 -= 1
                    self.state = Waiting2AMState("ORDER")
                else:
                    # 대기열 없음 → 좌석 수만 감소
                    self.m2 -= 1
                    self.state = Waiting2AMState("WAIT")

        # ORDER 상태
        elif state == "ORDER":
            if self.in_exit in inputs:
                # ORDER 중에 exit 도착 → 상태 유지, 좌석 수만 감소
                self.m2 -= 1
                self.state = Waiting2AMState("ORDER")

        else:
            raise DEVSException(f"Unknown state <{state}> in extTransition")

        return self.state


# ----------------------------------------------------------------------
# 4인석 대기열 atomic 모델
# ----------------------------------------------------------------------
class Waiting4AMState:
    def __init__(self, current="WAIT"):
        self.set(current)

    def set(self, value):
        self.__state = value
        return self.__state

    def get(self):
        return self.__state

    def __str__(self):
        return self.get()


class Waiting4AM(AtomicDEVS):
    def __init__(self, name, max4):
        super().__init__(name)

        # Input/Output Ports
        self.in_guest = self.addInPort("in_guest")      # (Hall, n)
        self.in_exit = self.addInPort("in_exit")        # exit4
        self.out_order = self.addOutPort("out_order")   # (Hall, n)

        # Parameters
        self.max4 = max4

        # Initial State
        self.state = Waiting4AMState("WAIT")
        self.m4 = 0
        self.queue = []
        self.current = None  # 현재 사용자 (ORDER 상태에서)

    def timeAdvance(self):
        state = self.state.get()
        if state == "WAIT":
            return INFINITY
        elif state == "ORDER":
            return 1
        else:
            raise DEVSException(f"Unknown state <{state}> in timeAdvance")

    def outputFnc(self):
        state = self.state.get()
        
        print(f"[Waiting] State: {state}, Current: {self.current}, Queue: {self.queue}, m2: {self.m2}")
        
        if state == "ORDER" and self.current:
            return {self.out_order: self.current}
        return {}

    def intTransition(self):
        state = self.state.get()
        if state == "ORDER":
            self.state = Waiting4AMState("WAIT")
            self.m4 += 1
            self.current = None
            return self.state
        elif state == "WAIT":
            return self.state
        else:
            raise DEVSException(f"Unknown state <{state}> in intTransition")

    def extTransition(self, inputs):
        state = self.state.get()

        # WAIT 상태
        if state == "WAIT":
            # 손님 도착
            if self.in_guest in inputs:
                guest = inputs[self.in_guest]
                self.queue.append(guest)

                if self.m4 < self.max4:
                    # 좌석 있음 → ORDER로 전이
                    self.current = self.queue.pop(0)
                    self.state = Waiting4AMState("ORDER")
                else:
                    # 좌석 없음 → WAIT 유지
                    self.state = Waiting4AMState("WAIT")

            # 퇴장 signal
            if self.in_exit in inputs:
                if len(self.queue) > 0:
                    # 대기열 있음 → ORDER로 전이
                    self.current = self.queue.pop(0)
                    self.m4 -= 1
                    self.state = Waiting4AMState("ORDER")
                else:
                    # 대기열 없음 → 좌석 수만 감소
                    self.m4 -= 1
                    self.state = Waiting4AMState("WAIT")

        # ORDER 상태
        elif state == "ORDER":
            if self.in_exit in inputs:
                # ORDER 중에 exit 도착 → 상태 유지, 좌석 수만 감소
                self.m4 -= 1
                self.state = Waiting4AMState("ORDER")

        else:
            raise DEVSException(f"Unknown state <{state}> in extTransition")

        return self.state


# ----------------------------------------------------------------------
# 좌석 대기열 coupled model
# ----------------------------------------------------------------------
# 최대 좌석 수 정의
max2 = 2
max4 = 2

class HallSeatQueueCM(CoupledDEVS):
    def __init__(self, name, max2, max4):
        super().__init__(name)

        # gen에서 들어오는 입력 포트
        self.in_hall12 = self.addInPort("in_hall12")
        self.in_hall34 = self.addInPort("in_hall34")
        self.in_takeout = self.addInPort("in_takeout")

        # 좌석에서 들어오는 입력포트
        self.in_exit2 = self.addInPort("in_exit2")
        self.in_exit4 = self.addInPort("in_exit4")

        self.out_order2 = self.addOutPort("out_order2")  # (Hall, n)
        self.out_order4 = self.addOutPort("out_order4")

        # Submodels
        self.waiting2 = Waiting2AM("waiting2", max2) #2인석 대기 atomic 모델
        self.waiting4 = Waiting4AM("waiting4", max4) #4인석 대기 atomic 모델

        self.addSubModel(self.waiting2)
        self.addSubModel(self.waiting4)

        # 좌석 모델과 연결
        self.connectPorts(self.in_exit2, self.waiting2.in_exit)
        self.connectPorts(self.in_exit4, self.waiting4.in_exit)

        #print(self.in_guest)
        self.connectPorts(
            self.in_hall12,
            self.waiting2.in_guest,
            lambda val: val if val[1] in [1, 2] else None
        )

        self.connectPorts(
            self.in_hall34,
            self.waiting4.in_guest,
            lambda val: val if val[1] in [3, 4] else None
        )
        
        self.connectPorts(self.waiting2.out_order, self.out_order2)
        self.connectPorts(self.waiting4.out_order, self.out_order4)