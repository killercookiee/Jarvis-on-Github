"""
Name: template_protocol.py
Description: This is the template protocol
Tags: template
Prerequisites: None
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


# Paths for communication and log files
IDENTITY_PATH = os.path.abspath(__file__)
LOG_FILE_PATH = os.path.join(os.path.dirname(IDENTITY_PATH), os.path.basename(IDENTITY_PATH).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass

pipe = None
active_requests = {}
active_subprotocols = {}
request_responses = {}
main_protocol = ""
main_protocol_requestID = ""

def set_up_communication():
    """This function sets up the communication with the main process."""
    global pipe

    context = zmq.Context()
    pipe = context.socket(zmq.PAIR)
    pipe.connect(f"ipc://{IDENTITY_PATH}.ipc")
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

def send_main_message(message):
    """This function sends a message to the main process."""
    json_message = json.dumps(message)
    if pipe:
        pipe.send_string(str(json_message))
        log(f"Message sent to MAIN_COMMUNICATION: {str(json_message)}")
    else:
        log("Pipe is not open, message not sent.")

def send_quit_message():
    """This function sends a quit message to the main process."""
    quit_message = {
        "action": "deactivate_subprocess",
        "input": {'script_path': IDENTITY_PATH},
        "sender": IDENTITY_PATH,
        "receiver": "MAIN-communication/MAIN_COMMUNICATION.py",
    }
    send_main_message(quit_message)

def activate_subprotocol(subprotocol_path, input):
    """
    This function sends a request message to the other protocols, waiting for a response.
    
    Args:
        subprotocol_path (str): The path of the subprotocol to activate.
        input (dict): The input for the subprotocol.
    """
    message = {
        "request": "start",
        "input": input,
        "sender": IDENTITY_PATH,
        "receiver": subprotocol_path,
        "requestID": IDENTITY_PATH + f"_{int(time.time())}",
    }
    
    global active_requests
    send_main_message(message)
    active_requests[message.get('requestID')] = message

    # Wait for response
    while message.get('requestID') in active_requests:
        time.sleep(1)
    request_response = request_responses[message.get('requestID')]
    request_responses.pop(message.get('requestID'))
    return request_response

def send_ouput(output):
    """Send the output to the main protocol that activated this protocol.
    
    Args:
        output (dict): The output of the protocol.
    """
    response_message = {
        "response": IDENTITY_PATH + " output",
        "input": output,
        "sender": IDENTITY_PATH,
        "receiver": main_protocol,
        "requestID": main_protocol_requestID,
    }
    send_main_message(response_message)


### PROTOCOL MODIFICATION BELOW

def handle_main_message(message):
    global main_protocol
    global main_protocol_requestID
    global active_requests

    log(f"Handling message from main: {message}")
    
    if message.get('request'):
        main_protocol = message.get('sender')
        main_protocol_requestID = message.get('requestID')

    elif message.get('response'):
        active_requests.pop(message.get('requestID'))
        request_responses[message.get('requestID')] = message

    if message.get('action') or message.get('request'):
        if message.get('action') == "start" or message.get('request') == "start":
            log("Message for main process to start")
            output = main(message.get('input'))   
            if message.get('request'):
                send_ouput(output)
            send_quit_message()
        elif message.get('action') == "stop" or message.get('request') == "stop":
            log(f"Message for main process to stop")
            send_quit_message()
    return
 
def main(input):
    # Type 1 - Single output protocol
    input_a = input.get('input_a')
    input_b = input.get('input_b')
    def do_something(input_a, input_b):
        output_a = None
    output_a = do_something(input_a, input_b)
    return output_a


    # Type 2 - Multiple output protocols
    while true or some_condition:
        input_a = input.get('input_a')
        input_b = input.get('input_b')
        def do_something(input_a, input_b):
            output_a = {"action": "output_a", "input": None}
        output_a = do_something(input_a, input_b)
        send_output(output_a)



### PROTOCOL MODIFICATION ABOVE



if __name__ == "__main__":
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Template Protocol started")

    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=set_up_communication, daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)