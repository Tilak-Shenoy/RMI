from typing import Callable, Tuple
from remote import RemoteObjectError

class CalculatorInterface:
    def __init__(self):
        self.add: Callable[[float, float], Tuple[float, RemoteObjectError]] = None
        self.subtract: Callable[[float, float], Tuple[float, RemoteObjectError]] = None
        self.multiply: Callable[[float, float], Tuple[float, RemoteObjectError]] = None
        self.divide: Callable[[float, float], Tuple[float, str, RemoteObjectError]] = None
        self.usage: Callable[[], Tuple[float, RemoteObjectError]] = None
        self.rendezvous: Callable[[], RemoteObjectError] = None