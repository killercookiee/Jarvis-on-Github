#!/usr/bin/env python3

import sys
import json
import struct
import traceback
import os
import time
import ast

# Paths for communication and log files
LOCAL_FOLDER = "/Users/killercookie/Jarvis/"

IDENTITY_PATH = os.path.abspath(__file__)
LOG_FILE_PATH = os.path.join(os.path.dirname(IDENTITY_PATH), os.path.basename(IDENTITY_PATH).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass


COMPUTER_COMMS_LOG = LOCAL_FOLDER + "Communication-Folder/computer_comms.log"
EXTENSION_COMMS_LOG = LOCAL_FOLDER + "Communication-Folder/extension_comms.log"
LAST_POSITION_FILE = LOCAL_FOLDER + "Communication-Folder/last_position.log"


# Global variable to control monitoring
def log(message, file_path=LOG_FILE_PATH):
    """Utility function to log into log file"""
    with open(file_path, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def clear_log(file_path):
    """Utility function to clear the contents of a log file"""
    with open(file_path, "w") as log_file:
        log_file.write("")  # Clear the file content

def clear_all_logs():
    """Utility function to clear all logs it is connected to"""
    clear_log(COMPUTER_COMMS_LOG)
    clear_log(EXTENSION_COMMS_LOG)
    clear_log(LAST_POSITION_FILE)
    clear_log(LOG_FILE_PATH)
    log("All logs cleared on initialization.")

def read_message():
    """Read message received from the extension"""
    raw_length = sys.stdin.buffer.read(4)
    log(f"Raw length bytes: {raw_length}")
    if len(raw_length) != 4:
        log("Did not read 4 bytes for message length, exiting")
        sys.exit(0)

    message_length = struct.unpack('I', raw_length)[0]
    log(f"Message length: {message_length}")

    message_bytes = b""
    while len(message_bytes) < message_length:
        chunk = sys.stdin.buffer.read(message_length - len(message_bytes))
        if not chunk:
            log("No more data to read, exiting")
            sys.exit(0)
        message_bytes += chunk
        log(f"Read {len(chunk)} bytes, total read: {len(message_bytes)} bytes")

    log(f"Raw message bytes: {message_bytes}")
    return message_bytes.decode('utf-8')

def send_message(response):
    """Sends message back to the extension"""
    response_str = json.dumps(response)
    response_bytes = response_str.encode('utf-8')
    response_length = struct.pack('I', len(response_bytes))
    sys.stdout.buffer.write(response_length)
    sys.stdout.buffer.write(response_bytes)
    sys.stdout.buffer.flush()

def read_computer_comms():
    """Read the messages from MAIN_COMMUNICATION.py through the computer_comms.log file"""

    def get_last_position():
        """Gets the line last read from the last_position.log file"""
        if os.path.exists(LAST_POSITION_FILE):
            with open(LAST_POSITION_FILE, "r") as file:
                position = file.read().strip()
                return int(position) if position.isdigit() else 0
        return 0

    def save_last_position(position):
        """Saves the current position into log_position.log file"""
        with open(LAST_POSITION_FILE, "w") as file:
            file.write(str(position))

            
    last_position = get_last_position()
    if os.path.exists(COMPUTER_COMMS_LOG):
        while True:  # Continuous loop to keep monitoring
            log("Monitoring computer comms")
            with open(COMPUTER_COMMS_LOG, "r") as comm_file:
                comm_file.seek(last_position)
                new_lines = comm_file.readlines()
                if new_lines:
                    for line in new_lines:
                        log(f"New message from computer_comms.log: {line.strip()}")

                        # Attempt to parse the line as a dictionary
                        try:
                            message = ast.literal_eval(line.strip())
                        except (SyntaxError, ValueError) as e:
                            log(f"Failed to parse line: {line.strip()}. Error: {e}")
                            continue  # Skip this line if parsing fails

                        # Only send messages if the action is "start_noise" or "end_noise"
                        save_last_position(comm_file.tell())  # Save position after each action

                        return_message = {
                            "action": message.get('action'),
                            "input": message.get('input', {}),
                            "sender": message.get('sender'),
                            "receiver": "GitHub Jarvis/background.js"
                        }

                        return return_message
                    
                else:
                    time.sleep(100)
                    return {}

def write_extension_comms(message, input_data = {}, sender = IDENTITY_PATH, receiver = "/Users/killercookie/Jarvis/MAIN-communication/MAIN_COMMUNICATION.py"):
    """Send message to MAIN_COMMUNICATION.py through the extension_comms.log file"""
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

    log(f"Writing into extension_comms: {str(json_message)}")

    with open(EXTENSION_COMMS_LOG, "a") as log_file:
        log_file.write(f"{str(json_message)}\n")

def handle_extension_message(json_message):
    """Relays the messages between the extension and MAIN_COMMUNICATION.py"""

    if json_message.get("action") == "activate":
        log("Received activation message from Chrome extension")
        clear_all_logs()  # Clear the log before writing
        log("Sound native host activated")
        return {}
    
    elif json_message.get("action") == "keep_alive":
        log("Received keep_alive message from Chrome extension")
        return read_computer_comms()  # Keep sending new messages from the log
    
    else:
        log(f"Relaying message {json_message} from extension to main")
        write_extension_comms(json_message)
        return read_computer_comms()
        

if __name__ == "__main__":
    """Read message from extension and reponds with a message"""
    try:
        log("Sound native host started")
        while True:
            try:
                message = read_message()
                log(f"Message received: {message}")
                json_message = json.loads(message)
                log(f"JSON message: {json_message}")

                response = handle_extension_message(json_message)
                log(f"Response: {response}")
                send_message(response)

            except Exception as e:
                log(f"Exception in message handling: {e}")
                log(traceback.format_exc())
                sys.exit(1)
    except Exception as e:
        log(f"Startup Exception: {e}")
        log(traceback.format_exc())
        sys.exit(1)