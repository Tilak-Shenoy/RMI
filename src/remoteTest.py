from threading import Lock, Condition, Event
from typing import Callable, Tuple, Optional
import socket
import random
import unittest
import threading
from remote import newService

class RemoteObjectError(Exception):
    """Custom exception for remote object errors"""
    pass

class SimpleInterface:
    """
    Simple interface for a remote service
    
    Attributes:
        method: A method that takes an integer value and a boolean flag,
               returns an integer and a string, and may raise RemoteObjectError
        rendezvous: A method for coordinating concurrent calls
    """
    
    def __init__(self, method, rendezvous):
        self.method = method
        self.rendezvous = rendezvous

class SimpleObject:
    """
    Service object implementing the SimpleInterface methods
    
    Attributes:
        _mu: A thread lock for synchronization
        _wake: Flag set by first call, then wait until second call
        _wg: WaitGroup for synchronizing two threads
    """
    
    def __init__(self):
        self._mu = Lock()
        self._wake = False
        self._wg = threading.Event()  # Using Event as a WaitGroup equivalent
        
    def method(self, value, return_error):
        """
        Test method for sending arguments, return values, and errors.
        
        Args:
            value: An integer value
            return_error: Boolean indicating if an error should be returned
            
        Returns:
            Tuple containing modified value and error string
        """
        with self._mu:
            if return_error:
                return -value, f"Error for value {value}"
            return value, ""
        
    def rendezvous(self):
        """
        Method used to coordinate concurrent calls to the same service.
        First call sets the wake flag, second call waits for it.
        """
        with self._mu:
            if not self._wake:
                self._wake = True
                self._wg.set()  # Signal waiting threads
            else:
                self._wg.wait()  # Wait until wake is set

    def wake(self):
        """
        Method to wake waiting threads
        """
        self._wg.set()
    
class RemoteObjectError(Exception):
    """Custom exception for remote object errors"""
    pass


class BadInterface:
    """Test interface that should be rejected by Stub and Service"""
    
    @staticmethod
    def method(value, return_error):
        """Test method that doesn't return a RemoteObjectError"""
        pass


class BadObject:
    """Service object implementing the BadInterface methods"""
    
    def method(self, value, return_error):
        """Service implementation of the method in BadInterface"""
        if return_error:
            err = "This is an error."
            return -value, err
        return value, ""


class MismatchInterface:
    """Mismatched interface to test error handling at stub"""
    
    @staticmethod
    def method(x, y):
        """Mismatched method with (int, int) instead of (int, bool) parameters"""
        pass
    
    @staticmethod
    def rendezvous():
        """Mismatched return type (int, RemoteObjectError) instead of RemoteObjectError"""
        pass
    
    @staticmethod
    def extra_method():
        """Extra method not included in SimpleService interface"""
        pass


class MismatchInterface2:
    """Another mismatched interface to test error handling at stub"""
    
    @staticmethod
    def method(x, flag, y):
        """Mismatched method with (int, bool, int) instead of (int, bool) parameters"""
        pass
    
    @staticmethod
    def rendezvous():
        """Mismatched method signature"""
        pass


def probe(port):
    """
    Helper function for testing whether listening socket is active
    
    Args:
        port: The port number to check
        
    Returns:
        bool: True if the port is active, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except (socket.error, OSError):
        return False


def test_checkpoint_service_interface():
    """
    Test function to verify service interface validation
    """
    class TestServiceInterface(unittest.TestCase):
        def test_service_validation(self):
            # Choose a large-ish random port number for testing
            port = random.randint(7000, 17000)
            
            # Should raise an error due to non-remote interface definition and instance
            with self.assertRaises(Exception):
                newService(BadInterface, BadObject(), port, False, False)
            
            # Should raise an error due to None interface
            with self.assertRaises(Exception):
                newService(None, SimpleObject(), port, False, False)
            
            # Should raise an error due to None instance
            with self.assertRaises(Exception):
                newService(SimpleInterface, None, port, False, False)
            
            # Should work correctly with no error
            try:
                service = newService(SimpleInterface, SimpleObject(), port, False, False)
                self.assertIsNotNone(service)
            except Exception as e:
                self.fail("newService failed with proper service interface and instance: %s" % str(e))
    
    # Run the tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServiceInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

# Add this to run the test when the file is executed directly
if __name__ == "__main__":
    test_checkpoint_service_interface()
