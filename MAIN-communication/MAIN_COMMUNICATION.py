#%% Imports
import time
import os
import subprocess
import threading
import zmq
import json
import ast
import random
import hashlib

from assets.globalvariable import GlobalVariable


#%% Constants
PYTHON_INTERPRETER = "/usr/local/bin/python3"
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(os.path.abspath(__file__)).replace("_", "").replace(".py", ".log"))
open(LOG_FILE_PATH, 'a').close() # Create log file if not exist

def find_local_folder(folder_name="Jarvis-on-Github"):
    current_path = os.path.abspath(__file__)  # Absolute path of the current script
    current_dir = os.path.dirname(current_path)

    while True:
        if folder_name in os.listdir(current_dir):
            target_folder = os.path.join(current_dir, folder_name)
            if os.path.isdir(target_folder):
                return target_folder + os.sep  # Ensure it ends with a separator
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached the root
            break
        current_dir = parent_dir

    raise FileNotFoundError(f"Folder '{folder_name}' not found in the directory tree.")
LOCAL_FOLDER = find_local_folder()
EXTENSION_COMMS_LOG = LOCAL_FOLDER + "Communication-Folder/extension_comms.log"
COMPUTER_COMMS_LOG = LOCAL_FOLDER + "Communication-Folder/computer_comms.log"

MESSAGE_RATE = 10 # Rate at which messages are sent per seconds

#-- active_protocols = {subprotocolID: {subprotocol_path, mother_protocolID, main_protocolID, process, pipe, loaded, thread, other_info: {}}}
active_protocols = GlobalVariable({})
context = zmq.Context() # Initialize the ZMQ context


#%% Logs
def log(message, file_path=LOG_FILE_PATH):
    """Utility function to log into the log file"""    
    with open(file_path, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def clear_log(file_path):
    """Utility function to clear the contents of a log file"""
    with open(file_path, "w") as log_file:
        log_file.write("")  # Clear the file content
    log(f"Log file {file_path} cleared.")

def clear_all_logs():
    """Utility function to clear all logs it is connected to"""
    # Clear logs on start
    clear_log(LOG_FILE_PATH)
    clear_log(COMPUTER_COMMS_LOG)
    clear_log(EXTENSION_COMMS_LOG)
    log("All logs cleared.")



#%% Communications
def send_google_message(message):
    """Send message to the extension through the computer_comms.log file"""
    json_message = json.dumps(message)
    with open(COMPUTER_COMMS_LOG, "a") as log_file:
        log_file.write(f"{str(json_message)}\n")

    print(f"Sent to Google Jarvis: {str(json_message)}")

def initialize_google_message_receiver():
    """Continuously read new messages from the extension log file in real-time."""
    global MESSAGE_RATE
    last_position = 0  # Track last read position

    if not os.path.exists(EXTENSION_COMMS_LOG):
        log(f"Extension log file not found: {EXTENSION_COMMS_LOG}")
        return

    while True:
        try:
            with open(EXTENSION_COMMS_LOG, "r") as comm_file:
                comm_file.seek(last_position)  # Move to last known position

                for line in comm_file:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue

                    log(f"Processing: {line}")
                    try:
                        message = ast.literal_eval(line)
                        threading.Thread(
                            target=handle_message, 
                            args=(message,),
                            daemon=True
                        ).start()
                    except (SyntaxError, ValueError) as e:
                        log(f"Failed to parse: {line} | Error: {e}")

                # Update last known position
                last_position = comm_file.tell()

            # Sleep before retrying (allows new messages to be written)
            time.sleep(1 / MESSAGE_RATE)

            # Check if the file has been truncated (reset position if needed)
            if os.path.getsize(EXTENSION_COMMS_LOG) < last_position:
                last_position = 0  # Reset position if file is cleared

        except FileNotFoundError:
            log(f"File not found: {EXTENSION_COMMS_LOG}")
            time.sleep(1 / MESSAGE_RATE)  # Wait and retry
        except Exception as e:
            log(f"Error in message receiver: {e}")
            time.sleep(1 / MESSAGE_RATE)

def send_subprocess_message(message, subprotocolID):
    """Send a message to a subprocess via its pipe."""
    global active_protocols

    if not isinstance(message, dict):
        raise ValueError("Message must be a dictionary.")

    if subprotocolID in active_protocols:
        pipe = active_protocols[subprotocolID]['pipe']
        try:
            pipe.send_string(json.dumps(message))
            log(f"Sent to {subprotocolID}: {message}")
        except zmq.ZMQError as e:
            log(f"Error sending to {subprotocolID}: {e}")
    else:
        log(f"Subprocess {subprotocolID} not found.")




#%% Protocols
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

def generate_subprocessID(script_path):
    """Generates a unique subprotocol ID based on the script path."""
    return f"subprocess_{script_path}_{generate_ID()}"

def initialize_subprocess(script_path, subprotocolID, protocol_info=None):
    """Activates a subprocess using the file path."""
    global active_protocols

    def handle_subprocess_communication(pipe):
        """Handles messages received from the subprocess."""
        while True:
            try:
                message = json.loads(pipe.recv_string().replace("'", '"'))

                log(f"Received message from {subprotocolID}: {message}")
                handle_message(message)
            except zmq.ZMQError as e:
                log(f"Error in communication with {subprotocolID}: {e}")
                break

    def generate_ipc_path(subprotocolID):
        """Generates a unique pipe ID based on the subprotocol ID."""
        # SubprotocolID format: subprocess_{script_path}_{unique_ID}
        #-- 'subprocess_' prefix and remove '.py' when binding
        ipc_path = subprotocolID.replace("subprocess_", "").replace(".py", "") + ".ipc"
        return ipc_path

    def setup_pipe():
        """Sets up the pipe for communication with the subprocess."""
        # Create a communication pipe
        pipe = context.socket(zmq.PAIR)
        pipe.bind(f"ipc://{generate_ipc_path(subprotocolID)}")

        # Start the subprocess
        process = subprocess.Popen(
            [PYTHON_INTERPRETER, os.path.abspath(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True
        )
        protocol_info.update({
            'process': process,
            'pipe': pipe,
            'loaded': False,
            'comms_handler': None
        })
        active_protocols[subprotocolID] = {'subprocess_path': script_path, **protocol_info, "other_info": {}}
        log(f"Subprocess {script_path} started.")

        send_initial_message()

        # Start the communication thread
        communication_thread = threading.Thread(target=handle_subprocess_communication, args=(pipe,), daemon=True)
        communication_thread.start()
        active_protocols[subprotocolID]['comms_handler'] = communication_thread
        log(f"Communication thread for {subprotocolID} started.")
    
    def send_initial_message():
        # Send the subprocess information to the subprocess
        subprocess_info = json.dumps({subprotocolID: active_protocols[subprotocolID]}, default=lambda obj: str(obj)) + "\n"
        active_protocols[subprotocolID]['process'].stdin.write(subprocess_info)
        active_protocols[subprotocolID]['process'].stdin.flush()
        active_protocols[subprotocolID]['process'].stdin.close()
        log(f"Subprocess info sent to {subprotocolID}.")

    def wait_until_loaded():
        """Waits until the subprocess is loaded."""
        log(f"Waiting for {subprotocolID} to load...")
        while not active_protocols.get(subprotocolID).get('loaded'):
            time.sleep(1/MESSAGE_RATE)
        log(f"{subprotocolID} loaded.")

    # Start the setup pipe in a separate thread
    threading.Thread(target=setup_pipe, daemon=True).start()
    wait_until_loaded()

def deactivate_subprocess(subprotocolID):
    """Deactivates a subprotocol and its dependent subprotocols, starting from the given protocol."""
    global active_protocols

    # Find dependents based on mother_protocolID
    dependents = [
        key for key, value in active_protocols.items()
        if value['mother_protocolID'] == subprotocolID
    ]

    # Recursively deactivate dependents first
    for dependent_id in dependents:
        deactivate_subprocess(dependent_id)

    # Deactivate the main subprotocol
    if subprotocolID in active_protocols:
        #-- active_protocols = {subprotocolID: {subprotocol_path, mother_protocolID, main_protocolID, process, pipe, loaded, thread, other_info: {}}}
        subprocess_info = active_protocols[subprotocolID]
        script_path = subprocess_info['subprocess_path']
        process = subprocess_info['process']
        pipe = subprocess_info['pipe']
        communication_thread = subprocess_info['thread']
        other_info = subprocess_info['other_info']

        # Close the communication pipe
        try:
            pipe.close()
            log(f"Pipe for {script_path} closed.")
        except Exception as e:
            log(f"Error closing pipe for {script_path}: {type(e).__name__} - {e}")

        # Terminate the subprocess
        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=2)  # Ensure it exits properly
                log(f"{subprotocolID} terminated.")
            else:
                log(f"{subprotocolID} already stopped.")
        except subprocess.TimeoutExpired:
            process.kill()
            log(f"{subprotocolID} forcefully killed.")

        # Wait for the communication thread to exit
        if communication_thread and communication_thread.is_alive():
            try:
                communication_thread.join(timeout=2)  # Give it some time to clean up
                log(f"Communication thread for {script_path} stopped.")
            except Exception as e:
                log(f"Error stopping communication thread for {script_path}: {type(e).__name__} - {e}")

        # Remove the subprocess from the global list
        del active_protocols[subprotocolID]
        log(f"Subprotocol {script_path} successfully deactivated.")
    else:
        log(f"Subprotocol {subprotocolID} does not exist.")

def activate_subprocess(script_path, input, subprotocolID, mother_protocolID=None, main_protocolID=None):
    """Activates a protocol (main or subprotocol) with the given input and mother protocol ID"""
    # Activate the subprocess
    if main_protocolID is None:
        main_protocolID = "Main-communication/MAIN_COMMUNICATION.py"
    if mother_protocolID is None:
        mother_protocolID = "Main-communication/MAIN_COMMUNICATION.py"
    protocol_info = { 
        'mother_protocolID': mother_protocolID,
        'main_protocolID': subprotocolID if (mother_protocolID is None or mother_protocolID=='Main-communication/MAIN_COMMUNICATION.py') else active_protocols[mother_protocolID]['main_protocolID']
    }
    try:
        initialize_subprocess(script_path, subprotocolID, protocol_info)
    except Exception as e:
        log(f"Error activating {subprotocolID}: {e}")
    
    # Send the start message to the subprocess
    start_message = {
        "request": "start",
        "input": input,
        "sender": "Main-communication/MAIN_COMMUNICATION.py",
        "receiver": subprotocolID,
        "messageID": f"Main-communication/MAIN_COMMUNICATION.py_{generate_ID()}",
        "other_info": {}
    }
    try:
        send_subprocess_message(start_message, subprotocolID)
    except ValueError as e:
        log(f"Error sending start message to {subprotocolID}: {e}")

def handle_message_for_main(message, command_map=None):
    """Handles messages for MAIN_COMMUNICATION"""
    log(f"Handling message for MAIN_COMMUNICATION: {message}")
    # Action / Request
    if message.get('request') or message.get('action'):
        command = message.get('request') or message.get('action')
        response_message = {}

        # Default command map
        if command_map is None:
            command_map = {
                "initialize_subprocess": initialize_subprocess,
                "deactivate_subprocess": deactivate_subprocess,
                "activate_subprocess": activate_subprocess,
            }

        # Check if the command is recognized
        if command not in command_map:
            log(f"Warning: Unrecognized command {command}.")
            pass

        # Execute the command
        func = command_map[command]
        try:
            output = func(**message['input']) if message.get('input') else func()
            if output is not None:
                log("Output: " + str(output))
                response_message = {
                    "response": f"{message.get('messageID')} completed",
                    "input": output,
                    "sender": message.get('receiver'),
                    "receiver": message.get('sender'),
                    "messageID": message.get('messageID'),
                    "other_info": {}
                }
        except TypeError as e:
            log(f"Error executing {command}: {e}")

        # Respond
        if message.get('request'):
            if response_message == {}:
                send_response_message(message, default=True)
            else:
                send_response_message(response_message, default=False)
        
    # Response
    elif message.get('response'):
        if message.get('response') == "Protocol loaded":
            active_protocols[message.get('sender')]['loaded'] = True
            log(f"Subprocess {message.get('sender')} loaded.")

    # Error
    else:
        log(f"Warning: Message {message.get('request')} not recognized.")


#%% API sensitive
MESSAGE_HANDLERS = {
    "subprocess_": lambda msg: send_subprocess_message(msg, msg.get('receiver')),
    "Google Jarvis/background.js": send_google_message,
    "tab_": send_google_message,
    "MAIN-communication/MAIN_COMMUNICATION.py": handle_message_for_main,
}

def send_response_message(message, default=True):
    """Sends a response message to the appropriate receiver."""
    if default:
        message = {
            "response": f"{message.get('messageID')} completed",
            "input": None,
            "sender": message.get('receiver'),
            "receiver": message.get('sender'),
            "messageID": message.get('messageID'),
            "other_info": {}
        }
    
    # Determine the correct handler dynamically
    receiver = message.get('receiver', '')
    for prefix, handler in MESSAGE_HANDLERS.items():
        if receiver.startswith(prefix):
            handler(message)
            return

    log(f"Warning: Response message not sent to {receiver}: {message}")

def handle_message(message):
    """Handles all messages from subprocesses and the extension."""
    # Check if the message is empty
    if message == {}:
        return

    log(f"Handling message from {message.get('sender')}: {message}")
    
    # Determine the correct handler dynamically
    receiver = message.get('receiver', '')
    for prefix, handler in MESSAGE_HANDLERS.items():
        if receiver.startswith(prefix):
            handler(message)
            return

    log(f"Warning: Message not sent to {receiver}")



# %% Debug Tools
def debug_write_extension_comms(message):
    """Send message to MAIN_COMMUNICATION.py through the extension_comms.log file"""

    json_message = json.dumps(message)

    log(f"Writing into extension_comms: {str(json_message)}")

    with open(EXTENSION_COMMS_LOG, "a") as log_file:
        log_file.write(f"{str(json_message)}\n")



# %% Startup
def start_main_communication():
    """Starts up the MAIN_COMMUNICATION process"""
    
    # Clear logs on start
    clear_all_logs()
    log("MAIN_COMMUNICATION started")

    extension_comms_thread = threading.Thread(target=initialize_google_message_receiver, daemon=True)
    extension_comms_thread.start()

    message = {
        "action": "activate_subprocess",
        "input": {"script_path": "Protocols/Other-protocols/template_protocol.py", "input": {}, "subprotocolID": f"{generate_subprocessID('Protocols/Other-protocols/template_protocol.py')}"},
        "sender": "Main-communication/MAIN_COMMUNICATION.py",
        "receiver": "Main-communication/MAIN_COMMUNICATION.py",
        "messageID": f"Main-communication/MAIN_COMMUNICATION.py_{generate_ID()}",
        "other_info": {}
    }
    handle_message_for_main(message)
    time.sleep(10)
    log(active_protocols)



if __name__ == "__main__":
    """Sets up the communication with the extension"""
    try:
        start_main_communication()

        # Keep MAIN_COMMUNICATION running
        while True:
            time.sleep(1)

    except Exception as e:
        log(f"Error in MAIN_COMMUNICATION: {e}")

