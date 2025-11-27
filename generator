class GENState:
    def __init__(self, current="out"):
        self.set(current)

    def set(self, value):
        self.__state = value
        return self.__state

    def get(self):
        return self.__state

    def __str__(self):
        return self.get()


class GEN(AtomicDEVS):
    def __init__(self, name='GEN', min_time=3, max_time=10):
        AtomicDEVS.__init__(self, name)
        self.name = name

        self.state = GENState("out")

        self.out_hall12 = self.addOutPort("out_hall12")
        self.out_hall34 = self.addOutPort("out_hall34")
        self.out_takeout = self.addOutPort("out_takeout")

        # 입장 시간 랜덤 범위
        self.min_time = min_time
        self.max_time = max_time


    def timeAdvance(self):
        state = self.state.get()

        if state == "out":
            # 입장 시간 랜덤 생성
            return random.uniform(self.min_time, self.max_time)

        else:
            raise DEVSException(
                "unknown state <%s> in GEN time advance transition function"
#                 % state
            )


    def intTransition(self):
        state = self.state.get()

        if state == "out":
            self.state = GENState("out")
            return self.state

        else:
            raise DEVSException(
                "unknown state <%s> in GEN internal transition function"
#                 % state
            )

    def outputFnc(self):
        # 랜덤으로 2인석 / 4인석 / 테이크아웃 선택
        pick = random.choice(["H2", "H4", "T"])

        if pick == "H2":
            n = random.choice([1, 2])
            return {self.out_hall12: ("H2", n)}
        elif pick == "H4":
            n = random.choice([3, 4])
            return {self.out_hall34: ("H4", n)}
        else:  # "T"
            n = random.choice([1, 2, 3, 4])
            return {self.out_takeout: ("T", n)}