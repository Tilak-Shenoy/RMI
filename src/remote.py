import socket
import threading
import time
import random
import json
import inspect
from typing import Callable

class LeakySocket:
    def __init__(self, conn, lossy, delayed):
        self.conn = conn
        self.lossy = lossy
        self.is_delayed = delayed
        self.ms_delay = 2
        self.us_delay = 0
        self.ms_timeout = 500
        self.us_timeout = 0
        self.loss_rate = 0.05
    
    # Send objects over the socket simulating the unreliable nature of the connection using delays and timeouts
    def send_object(self, data):
        if not data:
            return True, None
        
        if self.conn:
            # Simulate packet loss
            if self.lossy and random.random() < self.loss_rate:
                time.sleep(self.ms_timeout / 1000 + self.us_timeout / 1_000_000)
                return False, None
            
            # Simulate delay
            if self.is_delayed:
                time.sleep(self.ms_delay / 1000 + self.us_delay / 1_000_000)
            
            try:
                self.conn.sendall(data)
                return True, None
            except Exception as e:
                return False, f"SendObject Write error: {str(e)}"
            
        return False, "SendObject failed, nil socket"
    
    # Standard recieve function for the socket
    def recieve_object(self):
        if self.conn:
            try:
                data = self.conn.recv(4096)
                if not data:
                    return False, None
                
                return True, data
            
            except socket.timeout:
                return False, None
            except Exception as e:
                return False, f"RecieveObject Read error: {str(e)}"
            
        return False, "RecieveObject failed, nil socket"
    
    def setDelay(self, is_delayed, ms_delay, us_delay):
        self.is_delayed = is_delayed
        self.ms_delay = ms_delay
        self.us_delay = us_delay
    
    def setTimeout(self, ms_timeout, us_timeout):
        self.ms_timeout = ms_timeout
        self.us_timeout = us_timeout

    def setLossRate(self, loss_rate, lossy):
        self.lossy = lossy
        self.loss_rate = loss_rate

    def close(self):
        self.conn.close()
    

class Service:

    def __init__(self, ifc, sobj, port, lossy, delayed):
        self.running = False
        self.call_count = 0
        self.function_type = type(ifc)
        self.function_val = ifc
        self.object_val = sobj
        self.port = port
        self.lossy = lossy
        self.delayed = delayed
        self.listener = None
        self.mutex = threading.Lock()

    def start(self):
        self.mutex.Lock()
        if self.running:
            print("Service already running")
            return None

        try:
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener.bind(("", self.port))
            self.listener.listen(5)
            self.running = True
        except Exception as e:
            self.mutex.Unlock()
            print("Failed to start the listener")
            return e
        
        self.mutex.Unlock()
        threading.Thread(target=self._accept_connections, daemon=True).start()
        return None
    
    # have an infinite loop which keeps reading connections
    def _accept_connections(self):
        while self.running:
            try:
                conn, _ = self.listener.accept()
                threading.Thread(target=self._handle_connections, args=(conn,), daemon=True).start()
            except Exception as e:
                print(f"Listener accept error: {str(e)}")
                break

    # accept new connections from client callers until someone calls
	#  Stop on this Service, spawning a thread to handle each one
    def _handle_connections(self, conn):
        ls = LeakySocket(conn, self.lossy, self.delayed)
        try:
            input, err = ls.recieve_object()
            if err:
                print("Error reading byteString from leaky socket")
                return
            
            req = json.loads(input.decode())
            method_name = req.get("method")
            args = req.get("args", [])

            if not hasattr(self.object_val, method_name):
                print(f"Method {method_name} not found")
                return
            
            method = getattr(self.object_val, method_name)
            if not callable(method):
                print(f"{method_name} is not callable")
                return

        
            try:
                result = method(*args)
                response = {"Result": result, "Error": None}
            except Exception as e:
                response = {"Result": None, "Error": str(e)}

            ls.send_object(json.dumps(response).encode())

            self.mutex.Lock()
            self.call_count += 1
            self.mutex.Unlock()

        except Exception as e:
            print(f"Error handling connection: {str(e)}")
        finally:
            ls.close()

    def getCount(self):
        return self.call_count
    
    def isRunning(self):
        return self.running
    
    def stop(self):
        self.mutex.Lock()
        if not self.running:
            print("Service is not running")
            self.mutex.Unlock()
            return None
        
        self.running = False
        if self.listener:
            self.listener.close()
            self.listener = None
        
        self.mutex.Unlock()
        return None

class RemoteObjectError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.e = message

    def getError(self,):
        return self.e

class RequestMsg:
    def __init__(self, method: str, args: list):
        self.method = method
        self.args = args


class ReplyMsg:
    def __init__(self, success: bool, reply: list):
        self.success = success
        self.reply = reply
    
def validateIfc(ifc):
    # Check if the object is a class instance
    if not isinstance(ifc, object) or isinstance(ifc, (int, float, str, list, dict, tuple)):
        raise ValueError("First argument is not a class instance")
    
    # Iterate over all attributes of the object
    for name, attr in inspect.getmembers(ifc):
        # Check if the attribute is a callable (method)
        if callable(attr) and not name.startswith("__"):
            # Get the signature of the method
            signature = inspect.signature(attr)
            return_annotation = signature.return_annotation

            # Check if the return annotation includes RemoteObjectError
            if return_annotation is inspect.Signature.empty or RemoteObjectError not in getattr(return_annotation, '__args__', [return_annotation]):
                raise ValueError("The methods in the class do not return RemoteObjectError")
    return

def validateSobj(sobj):
    sobj_value = inspect.unwrap(sobj)

    if not isinstance(sobj_value, object) or not isinstance(sobj_value, (int, float, str, list, dict, tuple)):
        raise ValueError("Second argument is not a pointer to a struct")

    return None

def newService(ifc, sobj, port, lossy, delayed):
    if ifc is None or sobj is None:
        return None, ValueError("Service called with wrong interface & object values")
    
    err = validateIfc(ifc)
    if err:
        return None, err
    
    err = validateSobj(sobj)
    if err:
        return None, err

    # If the interface is a pointer to a struct with function declarations,
    # then reflect.TypeOf(ifc).Elem() is the reflected struct's Type
    # If sobj is a pointer to an object instance, then
    # reflect.ValueOf(sobj) is the reflected object's Value
    serviceInstance = Service(ifc, sobj, port, lossy, delayed)

    return serviceInstance, None







def stubFactory(ifc, address, lossy, delayed):
    if not ifc:
        raise TypeError("Interface must be a class type")
    
    err = validateIfc(ifc)
    if err:
        raise err
    
    # Get all methods from the interface
    methods = [name for name in dir(ifc) if callable(getattr(ifc, name)) and not name.startswith('_')]
    
    for method_name in methods:
        original_method = getattr(ifc, method_name)
        method_signature = inspect.signature(original_method)

        def create_dynamic_method(method_name, signature):
            def dynamic_method(self, *args, **kwargs):
                try:
                    # Create connection with server
                    host, port = address.split(':')
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((host, int(port)))
                    
                    ls = LeakySocket(conn, lossy, delayed)
                    
                    # Convert arguments to list
                    args_list = list(args)
                    
                    # Create request message
                    req = RequestMsg(
                        method=method_name,
                        args=args_list
                    )
                    
                    # Marshal the request
                    try:
                        msg = json.dumps(req.__dict__).encode('utf-8')
                    except Exception as e:
                        print(f"Error in marshalling the request: {e}")
                        return make_zero_return_values_with_error(signature)
                    
                     # Try sending the request until successful
                    while True:
                        success, error = ls.send_object(msg)
                        if not success:
                            print("Could not send msg successfully to server")
                        else:
                            break
                    
                     # Receive the response (blocking)
                    try:
                        result_bytes = ls.recv_object()
                        reply_dict = json.loads(result_bytes.decode('utf-8'))
                        reply = ReplyMsg(**reply_dict)
                    except Exception as e:
                        print(f"Error receiving/parsing response: {e}")
                        return make_zero_return_values_with_error(signature)
                    
                    # Process reply
                    if reply.reply is not None:
                        if not reply.success:
                            return make_zero_return_values_with_error(signature)
                        
                        # Return the reply values
                        if len(reply.reply) == 1:
                            return reply.reply[0]
                        else:
                            return tuple(reply.reply)
                    
                    return make_zero_return_values_with_error(signature)
                    
                except Exception as e:
                    print(f"Connection error: {e}")
                    return make_zero_return_values_with_error(signature)
                finally:
                    try:
                        conn.close()
                    except:
                        pass
            
            return dynamic_method
        # Set the dynamic method on the interface object
        setattr(ifc, method_name, create_dynamic_method(method_name, method_signature))
    
    return None

def make_zero_return_values_with_error(signature):
    zero_vals = []
    return_annotation = signature.return_annotation

    if return_annotation is inspect.Signature.empty:
        return zero_vals
    
    return_types = return_annotation.__args__

    for return_type in return_types:
        if return_type == RemoteObjectError or return_type is RemoteObjectError:
            zero_vals.append(RemoteObjectError("some remote object error"))
        else:
            zero_vals.append(None)

    return zero_vals
