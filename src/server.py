import remote, calcInterface

class CalculatorObject:
    def __init__(self, mu, wg, wake, total, val):
        self.mu = mu
        self.wg = wg
        self.wake = wake
        self.total = total
        self.val = val

    def start_calculator_service(self, port):
        calc_obj = CalculatorObject(self.mu, self.wg, self.wake, self.total, self.val)
        srvc, err = remote.newService(calcInterface(), calc_obj, port, False, False)

        if err:
            print("Error in new_service: %s", err)
        
        if srvc is None:
            print("new_service returned nil service")
        
        err = srvc.start()
        if err:
            print("Error in Service.start(): %s", err)

        