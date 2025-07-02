from calcInterface import CalculatorInterface
from server import CalculatorObject
from remote import RemoteObjectError

class calcObject(CalculatorInterface):
    def add(self, a, b):
        co = CalculatorObject()
        co.total = a+b
        
        co.mu.Lock()
        co.val+=1
        co.mu.Unlock()
        return co.total, None
    
    def subtract(self, a, b):
        co = CalculatorObject()
        co.total = a-b

        co.mu.Lock()
        co.val+=1
        co.mu.Unlock()
        return co.total, None
    
    def multiply(self, a, b):
        co = CalculatorObject()
        co.total = a*b
        
        co.mu.Lock()
        co.val+=1
        co.mu.Unlock()
        return co.total, None
    
    def divide(self, a,b):
        co = CalculatorObject()
        if b == 0:
            return None, "Division by zero is not allowed", None
        
        co.total = a/b
        
        co.mu.Lock()
        co.val+=1
        co.mu.Unlock()
        return co.total, None, None
    
    def usage(self):
        co = CalculatorObject()
        return co.val, None
    
    def rendezvous(self):
        with self.lock:
            if not self.wake:
                self.wake = True
                self.wg.wait()
            else:
                self.wg.set()
        return RemoteObjectError()