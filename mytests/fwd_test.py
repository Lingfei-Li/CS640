import cases

def create_scenario():
    s = cases.init()
    cases.fwd_test(s)
    return s

scenario = create_scenario()
