import time
import os
import subprocess
import threading
import zmq
import json
import ast

LOCAL_FOLDER = "/Users/killercookie/Jarvis-on-Github/"
PYTHON_INTERPRETER = "/usr/local/bin/python3"

IDENTITY_PATH = os.path.abspath(__file__)
LOG_FILE_PATH = os.path.join(os.path.dirname(IDENTITY_PATH), os.path.basename(IDENTITY_PATH).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass


MAIN_NATIVE_HOST_PATH = LOCAL_FOLDER + "Native-hosts/main_native_host.py"
EXTENSION_COMMS_LOG = LOCAL_FOLDER + "Communication-Folder/extension_comms.log"
COMPUTER_COMMS_LOG = LOCAL_FOLDER + "Communication-Folder/computer_comms.log"


subprocesses = {}
subprocess_events = {}
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

def create_subprocess_paths(local_folder):
    """Connects the subprocess path and its name"""
    protocols_folder = os.path.join(local_folder, 'Protocols')
    subprocess_paths = {}

    # Walk through the Protocols folder and subfolders
    for root, dirs, files in os.walk(protocols_folder):
        for file in files:
            if file.endswith('.py'):
                # Get the script name in uppercase with _SUBPROCESS ending
                script_name = os.path.splitext(file)[0].upper() + "_SUBPROCESS"
                script_path = os.path.join(root, file)
                
                # Store the script path in the dictionary
                subprocess_paths[script_name] = script_path

    return subprocess_paths

def write_computer_comms(message, input_data = {}, sender = IDENTITY_PATH, receiver = MAIN_NATIVE_HOST_PATH):
    """Send message to the extension through the computer_comms.log file"""
    if isinstance(message, dict):
        # Case 1: Full JSON-like dictionary is provided
        json_message = message
    else:
        # Case 2: String-based message like "'action': 'end_noise'" or "'response': 'finished'"
        message = message.strip()
        key, value = message.split(":")
        key = key.strip().replace("'", "")
        value = value.strip().replace("'", "")

        # Handle all possible keys: 'action', 'response', 'message', 'status'
        if key in ["action", "response", "message", "status"]:
            json_message = {
                key: value,  # Dynamically use the correct key
                'input': input_data,
                'sender': sender,
                'receiver': receiver
            }
        else:
            raise ValueError(f"Unexpected key '{key}' in message. Supported keys are 'action', 'response', 'message', and 'status'.")

    json_message = json.dumps(json_message)

    with open(COMPUTER_COMMS_LOG, "a") as log_file:
        log_file.write(f"{str(json_message)}\n")

def read_extension_comms():
    """Read the messages from the extension through the extension_comms.log file"""

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
            
            time.sleep(1)  # Check for new messages every second
            
        except Exception as e:
            log(f"Error in read_extension_comms: {e}")
            time.sleep(1)  # Wait before retrying

def send_message_subprocess(message, input_data = {}, sender = IDENTITY_PATH, receiver = None):
    """Send message to a subprocess"""
    global subprocesses, subprocess_events
   
    # Wait for subprocess pipe to finish setting up
    subprocess_events[receiver].wait(timeout=5)
    
    # Handling the json Message
    if isinstance(message, dict):
        # Case 1: Full JSON-like dictionary is provided
        json_message = message
    else:
        # Case 2: String-based message like "'action': 'end_noise'" or "'response': 'finished'"
        message = message.strip()
        key, value = message.split(":")
        key = key.strip().replace("'", "")
        value = value.strip().replace("'", "")

        # Handle all possible keys: 'action', 'response', 'message', 'status'
        if key in ["action", "response", "message", "status"]:
            json_message = {
                key: value,  # Dynamically use the correct key
                'input': input_data,
                'sender': sender,
                'receiver': receiver
            }
        else:
            raise ValueError(f"Unexpected key '{key}' in message. Supported keys are 'action', 'response', 'message', and 'status'.")
        
    json_message = json.dumps(json_message)

    # Check if the subprocess exists
    if receiver in subprocesses:
        pipe = subprocesses[receiver]['pipe']

        try:
            # Send the message to the subprocess
            pipe.send_string(json_message)
            log(f"Sent message to {receiver}: {json_message}")
        except zmq.ZMQError as e:
            log(f"Error sending message to {receiver}: {e}")
    else:
        log(f"Subprocess {receiver} not found.")

def activate_subprocess(script_name, index=0):
    """Activates a subprocess using the file path"""
    global subprocesses, subprocess_events

    # Check if the subprocess is already running
    existing_subprocess = next((s for s in subprocesses if s.startswith(script_name)), None)
    if existing_subprocess:
        # Add an index number to differentiate this instance
        script_name = f"{script_name}_{index}"

    # Create a new event for this subprocess
    pipe_ready_event = threading.Event()
    subprocess_events[script_name] = pipe_ready_event

    def handle_subprocess_communication(pipe):
        """Handles messages received from the subprocess"""
        while True:
            try:
                message_str = pipe.recv_string().replace("'", '"')
                message = json.loads(message_str)

                log(f"Received message from {script_name}: {message}")
                handle_message(message)
            except zmq.ZMQError as e:
                log(f"Error in communication with {script_name}: {e}")
                break

    def setup_pipe():
        """Sets up the pipe for communication with the subprocess"""
        # Create a communication pipe
        pipe = context.socket(zmq.PAIR)
        pipe.bind(f"ipc://{script_name}.ipc")
        subprocesses[script_name] = {'process': subprocess.Popen([PYTHON_INTERPRETER, script_name]), 'pipe': pipe, 'thread': None}
        log(f"{script_name} subprocess started with pipe.")

        communication_thread = threading.Thread(target=handle_subprocess_communication, args=(pipe,), daemon=True)
        communication_thread.start()
        subprocesses[script_name]['thread'] = communication_thread

        pipe_ready_event.set()

    # Start the setup pipe in a separate thread
    threading.Thread(target=setup_pipe).start()

def deactivate_subprocess(script_name):
    global subprocesses, subprocess_events

    # Check if the subprocess exists
    if script_name in subprocesses:
        # Retrieve the subprocess and related components
        subprocess_info = subprocesses[script_name]
        process = subprocess_info['process']
        pipe = subprocess_info['pipe']
        communication_thread = subprocess_info['thread']

        # Close the communication pipe
        try:
            pipe.close()
            log(f"Pipe for {script_name} closed.")
        except Exception as e:
            log(f"Error closing pipe for {script_name}: {e}")

        # Terminate the subprocess
        if process.poll() is None:  # Check if the process is still running
            try:
                process.terminate()
                process.wait()  # Ensure process termination
                log(f"{script_name} subprocess terminated.")
            except Exception as e:
                log(f"Error terminating subprocess {script_name}: {e}")

        # Wait for the communication thread to exit
        if communication_thread and communication_thread.is_alive():
            try:
                communication_thread.join(timeout=2)  # Give it some time to clean up
                log(f"Communication thread for {script_name} stopped.")
            except Exception as e:
                log(f"Error stopping communication thread for {script_name}: {e}")

        # Remove the subprocess from the global list
        del subprocesses[script_name]
        del subprocess_events[script_name]
        log(f"Subprocess {script_name} successfully deactivated.")
    else:
        log(f"Subprocess {script_name} does not exist.")
    

### SUBPROCESS MODIFICATION BELOW
subprocess_paths = create_subprocess_paths(LOCAL_FOLDER)



# Function to handle messages specific to each subprocess
def handle_message(message):
    """Handles all the messages from the subprocess and the extension"""
    log(f"Handling message from {message.get('sender')}: {message}")

    # Handles message from subprocess
    if message.get('sender') == subprocess_paths['SOUND_ACTIVATION_SUBPROCESS']:
        if message['action'] == "start_noise":
            log(f"{message.get('sender')} reported noise started.")
            write_computer_comms(message)

        elif message.get('action') == "end_noise":
            log(f"{message.get('sender')} reported noise ended.")
            write_computer_comms(message)


    # Handles message from extension
    if message.get('sender') == "GitHub Jarvis/background.js":
        if message['action'] == "start_sound_activation":
            log(f"Generate protocol function activated")
            activate_subprocess(subprocess_paths['SOUND_ACTIVATION_SUBPROCESS'])
            send_message_subprocess(message="'action': 'start", receiver=subprocess_paths['SOUND_ACTIVATION_SUBPROCESS'])

        elif message['action'] == "stop_sound_activation":
            deactivate_subprocess(subprocess_paths['SOUND_ACTIVATION_SUBPROCESS'])


### SUBPROCESS MODIFICATION BELOW




if __name__ == "__main__":
    """Sets up the communication with the extension"""
    try:
        # Clear logs on start
        clear_log(LOG_FILE_PATH)
        clear_log(COMPUTER_COMMS_LOG)
        log("MAIN_COMMUNICATION started")

        extension_comms_thread = threading.Thread(target=read_extension_comms, daemon=True)
        extension_comms_thread.start()


        # Other processes that starts upon startup:
        log("starting MAP_PROTOCOLS_SUBPROCESS")
        activate_subprocess(subprocess_paths['MAP_PROTOCOLS_SUBPROCESS'])
        time.sleep(5)
        send_message_subprocess(message="'action': 'start", receiver=subprocess_paths['SOUND_ACTIVATION_SUBPROCESS'])

        # Keep MAIN_COMMUNICATION running
        while True:
            time.sleep(1)

    except Exception as e:
        log(f"Error in MAIN_COMMUNICATION: {e}")
