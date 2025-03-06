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


LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(os.path.abspath(__file__)).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass


pipe = None

# active_requests = {requestID: message}
active_requests = {}
# request_responses = {requestID: response_message}
request_responses = {}
# active_subprotocols = {subprotocolID: subprotocol_path}
active_subprotocols = {}
# global_variables = {variable_name: variable_value}
global_variables = {}

# Identity of this protocol
identityID = ""
main_protocolID = ""

def set_up_communication():
    """This function sets up the communication with the main process."""
    global pipe

    context = zmq.Context()
    pipe = context.socket(zmq.PAIR)
    pipe.connect(f"ipc://{identityID}.ipc")

    finish_loading = {
        "response": "Protocol loaded",
        "input": None,
        "sender": identityID,
        "receiver": "MAIN-communication/MAIN_COMMUNICATION.py",
        "requestID": main_protocolID,
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

    active_requests[message.get('requestID')] = message

    # Wait for response
    def waiting_for_response():
        while message.get('requestID') in active_requests:
            time.sleep(1)
        request_response = request_responses[message.get('requestID')]
        request_responses.pop(message.get('requestID'))
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
        "response": identityID + " response",
        "input": output,
        "sender": identityID,
        "receiver": main_protocolID,
        "requestID": main_protocolID,
    }
    send_request_message(response_message, wait_for_response=False)

class Subprotocol():
    def __init__(self, subprotocol_type, subprotocol_path, subprotocol_action=None):
        self.subprotocol_type = subprotocol_type
        self.subprotocol_path = subprotocol_path
        self.subprotocol_action = subprotocol_action
        self.subprotocolID = None
        self.tabID = None

    def activate_subprotocol(self):
        """
        This function active a subprotocol, returning the subprotocol ID.
        
        Args:
            subprotocol_path (str): The path of the subprotocol to activate.
            input (dict): The input for the subprotocol.
        """
        if self.subprotocol_type == "Python file":
            message = {
                "request": "activate_subprotocol",
                "input": {"script_path": self.subprotocol_path, "subprotocolID": self.subprotocol_path + f"_{int(time.time())}"},
                "sender": identityID,
                "receiver": "MAIN-communication/MAIN_COMMUNICATION.py",
                "requestID": identityID + f"_{int(time.time())}",
            }
            self.subprotocolID = message.get('input').get('subprotocolID')
            active_subprotocols[self.subprotocolID] = self.subprotocol_path
            send_request_message(message, wait_for_response=False)
            return self.subprotocolID


        elif self.subprotocol_type == "Google extension function":
            message = {
                "request": "open_new_tab",
                "input": {"tab_url": self.subprotocol_path, "tabID": "tab/" + self.subprotocol_path + f"_{int(time.time())}"},
                "sender": identityID,
                "receiver": "Google Jarvis/background.js",
                "requestID": identityID + f"_{int(time.time())}",
            }
            request_response = send_request_message(message, wait_for_response=True)
            self.tabID = request_response.input.get('tab_id')
            active_subprotocols[self.tabID] = self.subprotocol_path
            return self.tabID

    def deactivate_subprotocol(self):
        """
        This function deactivates a subprotocol.
        
        Args:
            requestID (str): The request ID of the subprotocol to deactivate.
        """
        if self.subprotocol_type == "Python file":
            active_subprotocols.pop(self.subprotocolID)
            deactivate_message = {
                "request": "deactivate_subprotocol",
                "input": {"subprotocolID": self.subprotocolID},
                "sender": identityID,
                "receiver": "MAIN-communication/MAIN_COMMUNICATION.py",
                "requestID": identityID + f"_{int(time.time())}",
            }
            send_request_message(deactivate_message, wait_for_response=False)

        elif self.subprotocol_type == "Google extension function":
            active_subprotocols.pop(self.tabID)
            deactivate_message = {
                "request": "close_tab",
                "input": {"tabID": self.tabID},
                "sender": identityID,
                "receiver": "Google Jarvis/background.js",
                "requestID": identityID + f"_{int(time.time())}",
            }
            send_request_message(deactivate_message, wait_for_response=False)
    
    def start_subprotocol(self, input):
        """Start a subprocess with the given input.
        
        Args:
            subprotocolID (str): The subprotocol ID.
            input (dict): The input for the subprocess.
        Output:
            message (dict): The response message.
        """
        if not self.subprotocolID:
            self.activate_subprotocol()
            
        start_message = {
            "request": "start",
            "input": input,
            "sender": identityID,
            "receiver": self.subprotocolID,
            "requestID": identityID + f"_{int(time.time())}"
        }
        send_request_message(start_message, wait_for_response=False)
    
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
                "sender": identityID,
                "receiver": self.subprotocolID,
                "requestID": identityID + f"_{int(time.time())}"
            }

            request_response = send_request_message(execute_message, wait_for_response=True)
            self.deactivate_subprotocol()
            return request_response
        
        elif self.subprotocol_type == "Google extension function":
            execute_message = {
                "request": self.subprotocol_action,
                "input": input,
                "sender": identityID,
                "receiver": self.tabID,
                "requestID": identityID + f"_{int(time.time())}"
            }

            request_response = send_request_message(execute_message, wait_for_response=True)
            return request_response


def handle_main_message(message):
    global active_requests

    log(f"Handling message from main: {message}")
    
    if message.get('request'):
        handle_requests(message)

    elif message.get('response'):
        active_requests.pop(message.get('requestID'))
        request_responses[message.get('requestID')] = message

        if message.get('response') == "Protocol activated":
            active_subprotocols[message.get('requestID')] = message.get('sender')
            
        elif message.get('response') == "Protocol deactivated":
            active_subprotocols.pop(message.get('requestID'))
    return


### PROTOCOL MODIFICATION BELOW

def handle_requests(message):
    global global_variables
    if message.get('request') == "start":
        log("Message for main process to start")
        output = main(message.get('input'))   
        send_output(output)

    else:
        log(f"Warning: Unkown request {message.get('request')}")
 
def main(input):
    # Subprotocol that has a function in Google extension
    conversation_GPT = Subprotocol("Google extension function", "https://www.google.com", "Tab_Protocols.search_google")
    conversation_tab_id = conversation_GPT.activate_subprotocol({"input_a": input_a, "input_b": input_b})


    output = output_1 + input_c
    return output

    send_output(output)



### PROTOCOL MODIFICATION ABOVE



if __name__ == "__main__":
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Template Protocol started")

    identityID = sys.stdin.readline().strip()
    main_protocolID = sys.stdin.readline().strip()
    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=set_up_communication, daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)