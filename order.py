from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
from pypdevs.simulator import DEVSException
from pypdevs.DEVS import AtomicDEVS
from pypdevs.DEVS import CoupledDEVS
from pypdevs.simulator import Simulator
import random

# ----------------------------------------------------------------------
# 주문 대기열 atomic 모델
# ----------------------------------------------------------------------
# OrderAM
class OrderAMState:
    def __init__(self, current="FREE"):  # "FREE" or "SEND"
        self.set(current)

    def set(self, value):
        self.__state = value
        return self.__state

    def get(self):
        return self.__state

    # def __str__(self):
    #     return self.get()
    def __str__(self):
        q = getattr(self.parent, "queue", None)
        b = getattr(self.parent, "worker_busy", None)
        return f"[state={self.__state}, queue={q}, busy={b}]"


class OrderAM(AtomicDEVS):
    def __init__(self, name, max_worker):
        AtomicDEVS.__init__(self, name)
        self.max_worker = max_worker

        # 주문 대기열: (HT, n) ex) ("H2", 1), ("H4", 2), ("T", 1)
        self.queue = []

        # 현재 이 tick에 보낼 주문
        self.current_order = None          # (HT, n)
        self.target_worker = None          # 1 ~ max_worker
        self.state = OrderAMState("FREE")
        self.state.parent = self  

        # 각 worker의 busy 상태 관리 (True = 일하는 중)
        self.worker_busy = [False] * self.max_worker

        # 입력 포트
        self.in_hall2 = self.addInPort("in_hall2")      # ("H2", n) 형태로 보낸다고 가정
        self.in_hall4 = self.addInPort("in_hall4")      # ("H4", n)
        self.in_takeout = self.addInPort("in_takeout")  # ("T", n)

        # worker done 포트 / go 포트
        self.in_done = [self.addInPort(f"in_done{i}") for i in range(1, max_worker + 1)]
        self.out_go = [self.addOutPort(f"out_go{i}") for i in range(1, max_worker + 1)]

    # 내부 시간 진행
    def timeAdvance(self):
        state = self.state.get()
        if state == "SEND":
            # 바로 worker에게 내보내고 끝
            return 0.0
        elif state == "FREE":
            return INFINITY
        else:
            raise DEVSException(
                "unknown state <%s> in OrderAM timeAdvance" % state
            )

    # 내부 전이: SEND → FREE
    def intTransition(self):
        # SEND 단계에서 out_go로 보낸 후에는 다시 IDLE로
        self.current_order = None
        self.target_worker = None
        #self.state = OrderAMState("FREE")
        self.state.set("FREE") 
        return self.state

    # 외부 전이: 손님 도착 / worker done
    def extTransition(self, inputs):
        state = self.state.get()
        #print(inputs[self.in_hall2])


        # 1) 손님 도착 처리 (그냥 큐에 push)
        if self.in_hall2 in inputs:
            self.queue.append(inputs[self.in_hall2])   # 예: ("H2", n)
        if self.in_hall4 in inputs:
            self.queue.append(inputs[self.in_hall4])   # 예: ("H4", n)
        if self.in_takeout in inputs:
            self.queue.append(inputs[self.in_takeout]) # 예: ("T", n)

        # 2) worker done 처리 → 해당 worker를 free로
        for i, port in enumerate(self.in_done, start=1):
            if port in inputs:
                done_msg = inputs[port]   # ("done", worker_id) 라고 가정
                # 안전하게 체크
                if isinstance(done_msg, tuple) and done_msg[0] == "done":
                    self.worker_busy[i-1] = False

        # 3) FREE 상태이고, 대기열이 있고, free worker가 있으면 SEND 상태로 전환
        if state == "FREE" and self.queue:
            # 가장 번호가 작은 free worker 선택
            free_workers = [i+1 for i in range(self.max_worker) if not self.worker_busy[i]]

            if free_workers:  # free worker가 하나라도 있으면
                free_worker_idx = random.choice(free_workers)  # 랜덤 선택

                self.target_worker = free_worker_idx
                self.current_order = self.queue.pop(0)
                self.worker_busy[free_worker_idx - 1] = True
                self.state.set("SEND")

        return self.state

    # 출력 함수: SEND 상태일 때 한 번 out_go[target_worker]로 주문 내보냄
    def outputFnc(self):
        state = self.state.get()
        if state == "SEND" and self.current_order is not None and self.target_worker is not None:
            i = self.target_worker
            return {self.out_go[i - 1]: self.current_order}  # (HT, n)
        return {}

# ----------------------------------------------------------------------
# 직원 atomic 모델
# ----------------------------------------------------------------------
class WorkerAMState:
    def __init__(self, current="WAIT"):  # "WAIT" or "MAKE"
        self.set(current)

    def set(self, value):
        self.__state = value
        return self.__state

    def get(self):
        return self.__state

    def __str__(self):
        return self.get()


class WorkerAM(AtomicDEVS):
    def __init__(self, name, worker_id, make_time=1.0):
        AtomicDEVS.__init__(self, name)

        self.id = worker_id       # 1, 2, 3, ...
        self.make_time = make_time
        self.state = WorkerAMState("WAIT")
        

        self.ht = None            # "H2", "H4", "T"
        self.n = 0                # 주문 개수
        self.count = 0

        # 포트
        self.in_order = self.addInPort("in_order")       # (HT, n)
        self.out_done = self.addOutPort("out_done")      # ("done", worker_id)
        self.out_serving2 = self.addOutPort("out_serving2")  # ("serving", n)
        self.out_serving4 = self.addOutPort("out_serving4")
        self.out_takeout = self.addOutPort("out_takeout")  # ("takeout", n)

    def timeAdvance(self):
        state = self.state.get()
        if state == "MAKE":
            # 컵 수에 비례해서 시간 증가
            return self.make_time * self.n
        else:
            return INFINITY

    def intTransition(self):
        # MAKE → WAIT
        self.state = WorkerAMState("WAIT")
        self.ht = None
        self.n = 0
        return self.state

    def extTransition(self, inputs):
        state = self.state.get()

        # WAIT 상태에서만 주문을 받음
        if state == "WAIT" and self.in_order in inputs:
            self.ht, self.n = inputs[self.in_order]  # (HT, n)
            self.state = WorkerAMState("MAKE")
        elif state == "MAKE" and self.in_order in inputs:
            # MAKE 중에 들어오는 주문은 설계상 오면 안 됨
            raise DEVSException(
                "Worker %d: got new order while busy" % self.id
            )

        return self.state

    def outputFnc(self):
        state = self.state.get()
        if state == "MAKE":
            outputs = {}
            # OrderAM에게 완료 알림
            outputs[self.out_done] = ("done", self.id)
            self.count += self.n

            # 손님에게 결과 전달
            if self.ht in ("H2", "H4"):
                if self.n in [1,2]:
                    outputs[self.out_serving2] = ("serving2", self.n)

                if self.n in [3,4]:
                    outputs[self.out_serving4] = ("serving4", self.n)
            else:  # "T" (takeout)
                outputs[self.out_takeout] = ("takeout", self.n)

            return outputs

        return {}

# ----------------------------------------------------------------------
# 주문 coupled 모델
# ----------------------------------------------------------------------
class OrderWorkerCM(CoupledDEVS):
    def __init__(self, name, max_worker=3, make_time=5.0):
        CoupledDEVS.__init__(self, name)

        # External I/O
        self.in_hall2 = self.addInPort("in_hall2")
        self.in_hall4 = self.addInPort("in_hall4")
        self.in_takeout = self.addInPort("in_takeout")

        self.out_serving2 = self.addOutPort("out_serving2")
        self.out_serving4 = self.addOutPort("out_serving4")
        self.out_takeout = self.addOutPort("out_takeout")

        # Submodels
        self.order = self.addSubModel(OrderAM("order", max_worker=max_worker))

        self.workers = []
        for i in range(1, max_worker + 1):
            worker = self.addSubModel(WorkerAM(f"worker{i}", worker_id=i, make_time=make_time))
            self.workers.append(worker)

            # Order → Worker (IC)
            self.connectPorts(self.order.out_go[i - 1], worker.in_order)

            # Worker → Order (IC)
            self.connectPorts(worker.out_done, self.order.in_done[i - 1])

            # Worker → External (EOC)
            self.connectPorts(worker.out_serving2, self.out_serving2)
            self.connectPorts(worker.out_serving4, self.out_serving4)
            self.connectPorts(worker.out_takeout, self.out_takeout)


        #EIC: 외부 → OrderAM
        self.connectPorts(self.in_hall2, self.order.in_hall2)
        self.connectPorts(self.in_hall4, self.order.in_hall4)
        self.connectPorts(self.in_takeout, self.order.in_takeout)