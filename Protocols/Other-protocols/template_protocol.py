"""
Name: template_protocol.py
Description: This is the template protocol
Tags: template
Command Environment: None
Inputs: None
Outputs: None
Subprotocols: None
Location: Protocols/Other-protocols/template_protocol.py
"""

import time
import os
import zmq
import threading
import json
import sys
import random
import hashlib


LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(os.path.abspath(__file__)).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass


pipe = None

# active_requests = {messageID: message}
active_requests = {}
# request_responses = {messageID: response_message}
request_responses = {}
# active_subprotocols = {subprotocolID: subprotocol_path}
active_subprotocols = {}
# global_variables = {variable_name: variable_value}
global_variables = {}

# SUBPROCESS_INFO = {subprotocolID: {subprotocol_path, mother_protocolID, main_protocolID, process, pipe, loaded, thread, other_info: {}}}
SUBPROCESS_INFO = {}
IDENTITYID = None
MAIN_PROTOCOLID = None
MOTHER_PROTOCOLID = None


#%% Functions
def set_up_communication():
    """This function sets up the communication with the main process."""
    global pipe

    context = zmq.Context()
    pipe = context.socket(zmq.PAIR)
    ipc_path = IDENTITYID.replace("subprocess_", "").replace(".py", "") + ".ipc"
    pipe.connect(f"ipc://{ipc_path}")

    finish_loading = {
        "response": "Protocol loaded",
        "input": None,
        "sender": IDENTITYID,
        "receiver": "MAIN-communication/MAIN_COMMUNICATION.py",
        "messageID": IDENTITYID + f"_{generate_ID()}",
    }
    send_request_message(finish_loading, wait_for_response=False)

    while True:
        try:
            message_str = pipe.recv_string().replace("'", '"')
            message = json.loads(message_str)

            log(f"Received message from main: {message}")
            handle_main_message(message)
        except zmq.ZMQError as e:
            log(f"Error in communication with main: {e}")
            break

def log(message, file_path=LOG_FILE_PATH):
    """This function logs messages to a log file."""
    with open(file_path, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def clear_log(file_path):
    """This function clears the content of a log file."""
    with open(file_path, "w") as log_file:
        log_file.write("")  # Clear the file content

def generate_ID():
    BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def base62_encode(num):
        """Convert a number to Base-62 string."""
        if num == 0:
            return BASE62_ALPHABET[0]

        base62 = []
        while num:
            num, rem = divmod(num, 62)
            base62.append(BASE62_ALPHABET[rem])

        return ''.join(reversed(base62))

    # Get current timestamp (milliseconds)
    timestamp = int(time.time() * 1000)  # e.g., 1700101234567

    # Convert timestamp to Base-62
    timestamp_base62 = base62_encode(timestamp)

    # Generate a random 3-character Base-62 string
    rand_str = ''.join(random.choices(BASE62_ALPHABET, k=3))

    # Compute a short hash checksum (Base-62)
    hash_input = f"{timestamp_base62}{rand_str}".encode()
    checksum = hashlib.md5(hash_input).digest()  # Generate MD5 hash
    hash_int = int.from_bytes(checksum, "big")  # Convert bytes to int
    hash_base62 = base62_encode(hash_int)[:2]  # Take first 2 characters

    return f"{timestamp_base62}{rand_str}{hash_base62}"

def send_request_message(message, wait_for_response=True):
    """This function sends a request message to the main process, and waits for a response.
    
    Args:
        message (dict): The message to send.
    Ouput:
        message (dict): The response message."""
    global active_requests

    json_message = json.dumps(message)
    if pipe:
        pipe.send_string(str(json_message))
        log(f"Message sent to MAIN_COMMUNICATION: {str(json_message)}")
    else:
        log("Pipe is not open, message not sent.")

    active_requests[message.get('messageID')] = message

    # Wait for response
    def waiting_for_response():
        while message.get('messageID') in active_requests:
            time.sleep(1)
        request_response = request_responses[message.get('messageID')]
        request_responses.pop(message.get('messageID'))
        return request_response

    if wait_for_response:
        return waiting_for_response()
    else:
        response_thread = threading.Thread(target=waiting_for_response, daemon=True)
        response_thread.start()
        response_thread.join()

def send_output(output):
    """Send the output to the main protocol that activated this protocol.
    
    Args:
        output (dict): The output of the protocol.
    """
    response_message = {
        "response": IDENTITYID + " response",
        "input": output,
        "sender": IDENTITYID,
        "receiver": MOTHER_PROTOCOLID,
        "messageID": IDENTITYID + f"_{generate_ID()}",
    }
    send_request_message(response_message, wait_for_response=False)

def handle_main_message(message):
    global active_requests

    log(f"Handling message from main: {message}")
    
    if message.get('request'):
        handle_requests(message)

    elif message.get('response'):
        active_requests.pop(message.get('messageID'))
        request_responses[message.get('messageID')] = message

        if message.get('response') == "Protocol activated":
            active_subprotocols[message.get('messageID')] = message.get('sender')
            
        elif message.get('response') == "Protocol deactivated":
            active_subprotocols.pop(message.get('messageID'))
    return

class Subprotocol():
    def __init__(self, subprotocol_type, subprotocol_path, subprotocolID=None, tab_name=None):
        self.subprotocol_type = subprotocol_type
        
        if subprotocol_type == "Python file":
            self.subprotocol_path = subprotocol_path
            self.subprotocolID = subprotocolID
        elif subprotocol_type == "Google extension function":
            self.tab_url = subprotocol_path
            self.tabID = subprotocolID
            self.tab_name = tab_name

    def activate_subprotocol(self):
        """
        This function active a subprotocol, returning the subprotocol ID.
        
        Args:
            subprotocol_path (str): The path of the subprotocol to activate.
            input (dict): The input for the subprotocol.
        """
        global active_subprotocols

        if not self.subprotocolID:
            if self.subprotocol_type == "Python file":
                message = {
                    "request": "activate_subprotocol",
                    "input": {"script_path": self.subprotocol_path, "subprotocolID": self.subprotocol_path + f"_{int(time.time())}"},
                    "sender": IDENTITYID,
                    "receiver": "MAIN-communication/MAIN_COMMUNICATION.py",
                    "messageID": IDENTITYID + f"_{generate_ID()}",
                }
                send_request_message(message, wait_for_response=True)
                self.subprotocolID = message.get('input').get('subprotocolID')
                active_subprotocols[self.subprotocolID] = self.subprotocol_path
                return self.subprotocolID


            elif self.subprotocol_type == "Google extension function":
                message = {
                    "request": "open_new_tab",
                    "input": {"tab_url": self.tab_url, "tab_name": "tab/" + self.tab_url + f"_{int(time.time())}"},
                    "sender": IDENTITYID,
                    "receiver": "Google Jarvis/background.js",
                    "messageID": IDENTITYID + f"_{generate_ID()}",
                }
                request_response = send_request_message(message, wait_for_response=True)
                self.tabID = request_response.get('input').get('tab_id')
                self.tab_name = message.get('input').get('tab_name')
                active_subprotocols[self.tabID] = self.tab_name
                return self.tabID

    def deactivate_subprotocol(self):
        """
        This function deactivates a subprotocol.
        
        Args:
            messageID (str): The request ID of the subprotocol to deactivate.
        """
        global active_subprotocols

        if self.subprotocolID:
            if self.subprotocol_type == "Python file":
                active_subprotocols.pop(self.subprotocolID)
                deactivate_message = {
                    "request": "deactivate_subprotocol",
                    "input": {"subprotocolID": self.subprotocolID},
                    "sender": IDENTITYID,
                    "receiver": "MAIN-communication/MAIN_COMMUNICATION.py",
                    "messageID": IDENTITYID + f"_{generate_ID()}",
                }
                send_request_message(deactivate_message, wait_for_response=True)

            elif self.subprotocol_type == "Google extension function":
                active_subprotocols.pop(self.tabID)
                deactivate_message = {
                    "request": "close_tab",
                    "input": {"tabID": self.tabID},
                    "sender": IDENTITYID,
                    "receiver": "Google Jarvis/background.js",
                    "messageID": IDENTITYID + f"_{generate_ID()}",
                }
                send_request_message(deactivate_message, wait_for_response=True)
    
    def execute_subprotocol(self, input):
        """Execute a subprocess with the given input.
        
        Args:
            subprotocolID (str): The subprotocol ID.
            input (dict): The input for the subprocess.
        Output:
            message (dict): The response message.
        """
        if self.subprotocol_type == "Python file":
            if not self.subprotocolID:
                self.activate_subprotocol()
                
            execute_message = {
                "request": "start",
                "input": input,
                "sender": IDENTITYID,
                "receiver": self.subprotocolID,
                "messageID": IDENTITYID + f"_{generate_ID()}"
            }

            request_response = send_request_message(execute_message, wait_for_response=True)
            self.deactivate_subprotocol()
            return request_response
        
        elif self.subprotocol_type == "Google extension function":
            execute_message = {
                "request": self.subprotocol_action,
                "input": input,
                "sender": IDENTITYID,
                "receiver": self.tabID,
                "messageID": IDENTITYID + f"_{generate_ID()}",
            }

            request_response = send_request_message(execute_message, wait_for_response=True)
            return request_response



#%% PROTOCOL MODIFICATION BELOW

def handle_requests(message):
    global global_variables
    if message.get('request') == "start":
        log("Message for main process to start")
        output = main(message.get('input'))   
        send_output(output)

    else:
        log(f"Warning: Unkown request {message.get('request')}")
 
def main(input):
    # Type 1 - Single output protocol E.x:
    input_a = input.get('input_a')
    input_b = input.get('input_b')
    input_c = input.get('input_c')

    def do_something(input_a, input_b, input_c):
        # Single subprotocol
        templete_subprotocol = Subprotocol("Python file", "Protocols/Other-protocols/template_subprotocol.py")
        output_1 = templete_subprotocol.execute_subprotocol({"input_a": input_a, "input_b": input_b})

        # Continous subprotocol that runs in the background
        templete_subprotocol = Subprotocol("Python file", "Protocols/Other-protocols/template_subprotocol.py")
        templete_subprotocol.start_subprotocol({"input_a": input_a, "input_b": input_b})
        templete_subprotocol.deactivate_subprotocol() # Deactivate the subprotocol at some other point

        # Subprotocol that has a function in Google extension
        templete_subprotocol = Subprotocol("Google extension function", "https://www.google.com", "Tab_Protocols.search_google")
        output_2 = templete_subprotocol.execute_subprotocol({"input_a": input_a, "input_b": input_b})

        output = output_1 + input_c
        return output

    output = do_something(input_a, input_b, input_c)
    send_output(output)



#%% PROTOCOL MODIFICATION ABOVE

def read_subprotocol_info():
    """Read the subprotocol info from the main process."""
    subprocess_info = sys.stdin.readline().strip()
    subprocess_info = json.loads(subprocess_info)
    log(f"Subprocess info: {subprocess_info}")
    return subprocess_info

def initialize_constants():
    """Initialize the constants for the protocol."""
    global SUBPROCESS_INFO, IDENTITYID, MAIN_PROTOCOLID, MOTHER_PROTOCOLID
    
    # SUBPROCESS_INFO = {subprotocolID: {subprotocol_path, mother_protocolID, main_protocolID, process, pipe, loaded, thread, other_info: {}}}
    SUBPROCESS_INFO = read_subprotocol_info()
    IDENTITYID = list(SUBPROCESS_INFO.keys())[0]
    MAIN_PROTOCOLID = SUBPROCESS_INFO.get(IDENTITYID).get('main_protocolID')
    MOTHER_PROTOCOLID = SUBPROCESS_INFO.get(IDENTITYID).get('mother_protocolID')

if __name__ == "__main__":
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Template Protocol started")

    initialize_constants()

    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=set_up_communication, daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)