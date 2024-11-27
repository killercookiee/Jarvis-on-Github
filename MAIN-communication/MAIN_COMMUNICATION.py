import time
import os
import subprocess
import threading
import zmq
import json
import ast
from pathlib import Path


PYTHON_INTERPRETER = "/usr/local/bin/python3"

IDENTITY_PATH = os.path.abspath(__file__)
LOG_FILE_PATH = os.path.join(os.path.dirname(IDENTITY_PATH), os.path.basename(IDENTITY_PATH).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass

def find_local_folder(folder_name="Jarvis-on-Github"):
    current_path = os.path.abspath(__file__)  # Absolute path of the current script
    current_dir = os.path.dirname(current_path)

    while True:
        if folder_name in os.listdir(current_dir):
            target_folder = os.path.join(current_dir, folder_name)
            if os.path.isdir(target_folder):
                return target_folder
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached the root
            break
        current_dir = parent_dir

    raise FileNotFoundError(f"Folder '{folder_name}' not found in the directory tree.")
LOCAL_FOLDER = find_local_folder()
EXTENSION_COMMS_LOG = LOCAL_FOLDER + "Communication-Folder/extension_comms.log"
COMPUTER_COMMS_LOG = LOCAL_FOLDER + "Communication-Folder/computer_comms.log"

message_rate = 5 # Rate at which messages are sent per seconds

subprocesses = {}
comms_last_position = 0

context = zmq.Context()


def log(message, file_path=LOG_FILE_PATH):
    """Utility function to clear the contents of a log file"""    
    with open(file_path, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def clear_log(file_path):
    """Utility function to clear the contents of a log file"""
    with open(file_path, "w") as log_file:
        log_file.write("")  # Clear the file content

def clear_all_logs():
    """Utility function to clear all logs it is connected to"""
    # Clear logs on start
    clear_log(LOG_FILE_PATH)
    clear_log(COMPUTER_COMMS_LOG)
    clear_log(EXTENSION_COMMS_LOG)
    log("All logs cleared on initialization.")

def send_google_message(message):
    """Send message to the extension through the computer_comms.log file"""

    json_message = json.dumps(message)

    with open(COMPUTER_COMMS_LOG, "a") as log_file:
        log_file.write(f"{str(json_message)}\n")

def read_extension_comms():
    """Read the messages from the extension through the extension_comms.log file"""

    global message_rate
    current_line = 0  # Track which line we should read next

    while True:  # Continuous loop to keep monitoring
        try:
            log("Monitoring extension comms")
            
            if os.path.exists(EXTENSION_COMMS_LOG):
                with open(EXTENSION_COMMS_LOG, "r") as comm_file:
                    # Read all lines
                    lines = comm_file.readlines()
                    
                    # Reset if file has been truncated or is empty
                    if len(lines) < current_line:
                        current_line = 0
                        log("File reset detected, starting from beginning")
                    
                    # If we have lines to process and we haven't reached the end
                    if lines and current_line < len(lines):
                        line = lines[current_line]
                        log(f"Processing line {current_line + 1}: {line.strip()}")
                        
                        try:
                            message = ast.literal_eval(line.strip())
                            
                            message_to_handle = {
                                "action": message.get('action'),
                                "input": message.get('input'),
                                "sender": message.get('sender'),
                                "receiver": message.get('receiver')
                            }
                            
                            # Start thread for handling message
                            handle_thread = threading.Thread(
                                target=handle_message,
                                args=(message_to_handle,),
                                daemon=True
                            )
                            handle_thread.start()
                            
                        except (SyntaxError, ValueError) as e:
                            log(f"Failed to parse line: {line.strip()}. Error: {e}")
                        except Exception as e:
                            log(f"Unexpected error processing line: {e}")
                        
                        # Move to next line regardless of whether processing succeeded
                        current_line += 1
            
            wait_time = 1 / message_rate
            time.sleep(wait_time)  # Check for new messages every second
            
        except Exception as e:
            log(f"Error in read_extension_comms: {e}")
            wait_time = 1 / message_rate
            time.sleep(wait_time)  # Wait before retrying

def send_message_subprocess(message):
    """Send a message to a subprocess."""
    global subprocesses

    requestID = message.get('requestID')

    # Check if the receiver exists in subprocess_events
    if requestID not in subprocesses:
        log(f"Subprocess {requestID} not found in events.")
        return

    # Ensure the message is a dictionary
    if not isinstance(message, dict):
        raise ValueError("Message must be a dictionary.")

    # Serialize the message to JSON format
    json_message_str = json.dumps(message)

    # Check if the subprocess exists
    if requestID in subprocesses:
        pipe = subprocesses[requestID]['pipe']

        try:
            # Send the message to the subprocess
            pipe.send_string(json_message_str)
            log(f"Sent message to {subprocesses[requestID]['subprocess_path']}: {json_message_str}")
        except zmq.ZMQError as e:
            log(f"Error sending message to {requestID}: {e}")
    else:
        log(f"Subprocess {subprocesses[requestID]['subprocess_path']} not found.")

def activate_subprocess(script_path, requestID):
    """Activates a subprocess using the file path."""
    global subprocesses

    # Convert the script path to an absolute path
    identity_path = os.path.abspath(script_path)

    # Create a new event for this subprocess
    pipe_ready_event = threading.Event()

    def handle_subprocess_communication(pipe):
        """Handles messages received from the subprocess."""
        while True:
            try:
                message_str = pipe.recv_string().replace("'", '"')
                message = json.loads(message_str)

                log(f"Received message from {identity_path}: {message}")
                handle_message(message)
            except zmq.ZMQError as e:
                log(f"Error in communication with {identity_path}: {e}")
                break

    def setup_pipe():
        """Sets up the pipe for communication with the subprocess."""
        # Create a communication pipe
        pipe = context.socket(zmq.PAIR)
        pipe.bind(f"ipc://{identity_path}.ipc")
        subprocesses[requestID] = {'subprocess_path': identity_path, 'process': subprocess.Popen([PYTHON_INTERPRETER, script_path]), 'pipe': pipe, 'thread': None, }
        log(f"{identity_path} subprocess started with pipe.")

        communication_thread = threading.Thread(target=handle_subprocess_communication, args=(pipe,), daemon=True)
        communication_thread.start()
        subprocesses[requestID]['thread'] = communication_thread

        pipe_ready_event.set()

    # Start the setup pipe in a separate thread
    threading.Thread(target=setup_pipe).start()

    # Wait for the pipe to be ready
    pipe_ready_event.wait()
    time.sleep(0.1)  # Wait for the subprocess to start

def deactivate_subprocess(script_path, requestID):
    """Deactivates a subprocess using the file path."""
    global subprocesses

    # Check if the subprocess exists
    if requestID in subprocesses:
        # Retrieve the subprocess and related components
        subprocess_info = subprocesses[requestID]
        process = subprocess_info['process']
        pipe = subprocess_info['pipe']
        communication_thread = subprocess_info['thread']

        # Close the communication pipe
        try:
            pipe.close()
            log(f"Pipe for {script_path} closed.")
        except Exception as e:
            log(f"Error closing pipe for {script_path}: {e}")

        # Terminate the subprocess
        if process.poll() is None:  # Check if the process is still running
            try:
                process.terminate()
                process.wait()  # Ensure process termination
                log(f"{script_path} subprocess terminated.")
            except Exception as e:
                log(f"Error terminating subprocess {script_path}: {e}")

        # Wait for the communication thread to exit
        if communication_thread and communication_thread.is_alive():
            try:
                communication_thread.join(timeout=2)  # Give it some time to clean up
                log(f"Communication thread for {script_path} stopped.")
            except Exception as e:
                log(f"Error stopping communication thread for {script_path}: {e}")

        # Remove the subprocess from the global list
        del subprocesses[requestID]
        log(f"Subprocess {script_path} successfully deactivated.")
    else:
        log(f"Subprocess {script_path} does not exist.")  

def send_response_message(message):
    """Sends a response message to the appropriate receiver."""
    if message.get('sender').startswith("Protocols/"):
        send_message_subprocess(message, message.get('receiver'))
    elif message.get('sender') == "Google Jarvis/background.js" or message.get('sender').startswith("tab/"):
        send_google_message(message)
    else:
        log(f"Warning: Response message not sent to {message.get('sender')}: {message}")

def handle_message(message):
    """Handles all the messages from the subprocess and the extension"""
    log(f"Handling message from {message.get('sender')}: {message}")

    if message.get('receiver').startswith("Protocols/"):
        if message.get('requestID') in subprocesses:
            send_message_subprocess(message)
        else:
            log(f"Warning: Subprocess {message.get('receiver')} not found.")

    elif message.get('receiver') == "Main-communication/MAIN_COMMUNICATION.py":
        handle_message_for_main(message)
            
    elif message.get('receiver') == "Google Jarvis/background.js" or message.get('receiver').startswith("tab/"):
        send_google_message(message)

    else:
        log(f"Warning: Message not sent to {message.get('receiver')}")
   

### SUBPROCESS MODIFICATION BELOW

# Function to handle all messages 

def handle_message_for_main(message):
    """Handles messages for MAIN_COMMUNICATION""" 
    if message.get('action') == "activate_subprocess" or message.get('request') == "activate_subprocess":
        activate_subprocess(message.get('input').get('script_path'), message.get('sender'))

        if message.get('request'):
            response_message = {
                "response": "Subprocess activated",
                "input": None,
                "sender": message.get('receiver'),
                "receiver": message.get('sender'),
                "requestID": message.get('requestID')
            }
            send_response_message(response_message)

    elif message.get('action') == "deactivate_subprocess" or message.get('request') == "deactivate_subprocess":
        deactivate_subprocess(message.get('input').get('script_path'), message.get('sender'))

        if message.get('request'):
            response_message = {
                "response": "Subprocess deactivated",
                "input": None,
                "sender": message.get('receiver'),
                "receiver": message.get('sender'),
                "requestID": message.get('requestID')
            }
            send_response_message(response_message)
    
    else:
        log(f"Warning: Action {message.get('action')} not recognized.")

def start_main_communication():
    """Starts up the MAIN_COMMUNICATION process"""
    
    # Clear logs on start
    clear_log(LOG_FILE_PATH)
    clear_log(COMPUTER_COMMS_LOG)
    log("MAIN_COMMUNICATION started")

    extension_comms_thread = threading.Thread(target=read_extension_comms, daemon=True)
    extension_comms_thread.start()
     
### SUBPROCESS MODIFICATION ABOVE




if __name__ == "__main__":
    """Sets up the communication with the extension"""
    try:
        start_main_communication()

        # Keep MAIN_COMMUNICATION running
        while True:
            time.sleep(1)

    except Exception as e:
        log(f"Error in MAIN_COMMUNICATION: {e}")
