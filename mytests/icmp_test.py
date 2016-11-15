import cases

def create_scenario():
    s = cases.init()
    cases.icmp_test(s)
    return s

scenario = create_scenario()
