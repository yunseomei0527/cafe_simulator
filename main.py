# 파일 임포트
import generator
import waiting
import order
import welcome

# pypdevs 임포트
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
from pypdevs.simulator import DEVSException
from pypdevs.DEVS import AtomicDEVS
from pypdevs.DEVS import CoupledDEVS
from pypdevs.simulator import Simulator
import random

top = Welcome("RestaurantSystem", max2=2, max4=2)

sim = Simulator(top)
sim.setClassicDEVS()
sim.setVerbose()
sim.setTerminationTime(50)
sim.simulate()