from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
from pypdevs.simulator import DEVSException
from pypdevs.DEVS import AtomicDEVS
from pypdevs.DEVS import CoupledDEVS
from pypdevs.simulator import Simulator
import random

import generator 
import waiting
import order
# ----------------------------------------------------------------------
# 카페 coupled 모델
# ----------------------------------------------------------------------
class Welcome(CoupledDEVS):
    def __init__(self, name, max2, max4):
        CoupledDEVS.__init__(self,name)

        # ----- Submodels -----
        self.gen = generator.GEN("GEN")
        self.hall = waiting.HallSeatQueueCM("Hall", max2, max4)
        self.orderworker = order.OrderWorkerCM("OrderWorker", max_worker=5 , make_time=5.0)

        self.addSubModel(self.gen)
        self.addSubModel(self.hall)
        self.addSubModel(self.orderworker)

        # ----- Port Connections -----
        # GEN → HallSeatQueueCM (손님 전달)
        #print(self.gen.outport)
        self.connectPorts(self.gen.out_hall12, self.hall.in_hall12)
        self.connectPorts(self.gen.out_hall34, self.hall.in_hall34)

        # GEN -> orderworkerCM
        self.connectPorts(self.gen.out_takeout, self.orderworker.in_takeout)

        # HallSeatQueueCM -> orderworkerCM
        self.connectPorts(self.hall.out_order2, self.orderworker.in_hall2)
        self.connectPorts(self.hall.out_order4, self.orderworker.in_hall4)