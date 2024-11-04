"""
Name: map_protocols.py
Description: This creates the map file of all protocols in the system.
Prerequisites: None
Inputs: None
Outputs: protocol_mapping.json
Tags: protocol, mapping, json
Subprotocols: None
Location: Protocols/Protocol-analysis-protocols/map_protocols.py


Author: Nguyen Ba Phi
Date: 2024-11-4
"""


import time
import os
import traceback
import zmq
import threading
import json

import inspect
import re

# Paths for communication and log files
IDENTITY_PATH = os.path.abspath(__file__)
LOG_FILE_PATH = os.path.join(os.path.dirname(IDENTITY_PATH), os.path.basename(IDENTITY_PATH).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass


MAIN_PATH = "/Users/killercookie/Jarvis/MAIN-communication/MAIN_COMMUNICATION.py"


context = zmq.Context()
pipe = context.socket(zmq.PAIR)
pipe.connect(f"ipc://{IDENTITY_PATH}.ipc")

stop_event = threading.Event()

def log(message, file_path=LOG_FILE_PATH):
    with open(file_path, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def clear_log(file_path):
    with open(file_path, "w") as log_file:
        log_file.write("")  # Clear the file content

def handle_main_communication(pipe):
    while True:
        try:
            message_str = pipe.recv_string().replace("'", '"')
            message = json.loads(message_str)

            log(f"Received message from main: {message}")
            handle_main_message(message)
        except zmq.ZMQError as e:
            log(f"Error in communication with main: {e}")
            break

def send_main_message(message, input_data={}, sender=IDENTITY_PATH, receiver=MAIN_PATH):
    json_message = {
        'action': message.split(":")[1].strip().replace("'", ""),
        'input': input_data,
        'sender': sender,
        'receiver': receiver
    }
    json_message = json.dumps(json_message)
        
    # Ensure the pipe is open and ready before sending
    if pipe:
        pipe.send_string(str(json_message))
        log(f"Message sent to MAIN_COMMUNICATION: {str(json_message)}")
    else:
        log("Pipe is not open, message not sent.")



### PROTOCOL MODIFICATION BELOW

def handle_main_message(message):
    global stop_event
    log(f"Handling message from main: {message}")

    if message['action'] == "start":
        log("Message for main process to start")
        stop_event.clear()  # Reset the stop event
        main_thread = threading.Thread(target=main)
        main_thread.start()

    elif message.get('action') == "stop":
        log(f"Message for main process to stop")
        stop_event.set()  # Signal the thread to stop
    return
 
def main():
    try:
        while not stop_event.is_set():
            map_protocols()
            time.sleep(10)  # To reduce CPU usage

    except Exception as e:
        log(f"Error in template: {e}")
        log(traceback.format_exc())

    finally:
        log("Template Protocol stopped")



def map_protocols():
    protocol_map = {}

    # 1. Map Python protocols
    python_protocol_dir = "/Users/killercookie/Jarvis/Protocols"
    for filename in os.listdir(python_protocol_dir):
        if filename.endswith(".py"):
            file_path = os.path.join(python_protocol_dir, filename)
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract docstring
            docstring = inspect.getdoc(content)
            protocol_data = parse_protocol_docstring(docstring)
            protocol_map[filename] = protocol_data
    
    # 2. Map JavaScript protocols in `background.js`
    protocol_map.update(map_js_protocols("background.js", "const Protocols"))

    # 3. Map JavaScript protocols in `content.js`
    protocol_map.update(map_js_protocols("content.js", "const Protocols"))

    # Save to JSON file for easy access
    with open('protocol_mapping.json', 'w') as f:
        json.dump(protocol_map, f, indent=4)
    
    print("Protocol mapping completed and saved to protocol_mapping.json.")

def parse_protocol_docstring(docstring):
    # Assuming the docstring has specific headers like "Description:", "Prerequisites:", etc.
    protocol_data = {
        "Description": "",
        "Prerequisites": "",
        "Input": "",
        "Output": "",
        "Tags": [],
        "Subprotocols": [],
        "Location": ""
    }
    
    # Parse based on expected sections
    sections = re.split(r'\n\s*(?=\w+:)', docstring)
    for section in sections:
        key, *content = section.split(":", 1)
        protocol_data[key.strip()] = content[0].strip() if content else ""
    
    return protocol_data

def map_js_protocols(js_file, protocols_var):
    protocol_data = {}
    with open(js_file, 'r') as f:
        content = f.read()

    # Regex pattern to match each function and its preceding comment
    pattern = r"\/\*\*(.*?)\*\/\s*function\s+(\w+)\s*\("
    matches = re.findall(pattern, content, re.DOTALL)
    
    for comment, function_name in matches:
        protocol_data[function_name] = parse_js_protocol_comment(comment)
    
    return protocol_data

def parse_js_protocol_comment(comment):
    # Process comment block to extract structured information
    protocol_data = {
        "Description": "",
        "Prerequisites": "",
        "Input": "",
        "Output": "",
        "Tags": [],
        "Subprotocols": []
    }
    
    # Parse key-value pairs based on comment format
    sections = re.split(r'\n\s*(?=\w+:)', comment)
    for section in sections:
        key, *content = section.split(":", 1)
        protocol_data[key.strip()] = content[0].strip() if content else ""
    
    return protocol_data


### PROTOCOL MODIFICATION ABOVE



if __name__ == "__main__":
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Template Protocol started")

    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=handle_main_communication, args=(pipe,), daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)