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

import ast
import re
from collections import defaultdict


# Paths for communication and log files
IDENTITY_PATH = os.path.abspath(__file__)
LOG_FILE_PATH = os.path.join(os.path.dirname(IDENTITY_PATH), os.path.basename(IDENTITY_PATH).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass


MAIN_PATH = "/Users/killercookie/Jarvis-on-Github/MAIN-communication/MAIN_COMMUNICATION.py"


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
        main_thread = threading.Thread(target=main, daemon=True)
        main_thread.start()

    elif message.get('action') == "stop":
        log(f"Message for main process to stop")
        stop_event.set()  # Signal the thread to stop
    return
 
def main():
    def map_protocols():
        protocol_map = defaultdict(lambda: defaultdict(dict))
        log("Mapping protocols")

        # 1. Map Python Protocols
        python_dir = './Protocols'
        for root, _, files in os.walk(python_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        docstring = ast.get_docstring(ast.parse(f.read()))
                        if docstring:
                            protocol_info = parse_protocol_docstring(docstring)
                            add_to_map(protocol_map, protocol_info, separator='/')

        # 2. Map Background.js Protocols
        background_file = './Extension-Jarvis/background.js'
        protocol_map.update(map_js_protocols(background_file, 'Background_Protocols', separator='.'))

        # 3. Map Content.js Protocols
        content_file = './Extension-Jarvis/content.js'
        protocol_map.update(map_js_protocols(content_file, 'Tab_Protocols', separator='.'))

        # Save the protocol map as JSON
        output_path = './protocol_map.json'
        with open(output_path, 'w') as f:
            json.dump(protocol_map, f, indent=2)
        log(f"Protocol map saved to {output_path}")

    def parse_protocol_docstring(docstring):
        """Extract protocol details from a docstring with specified format."""
        fields = ["Name", "Description", "Prerequisites", "Inputs", "Outputs", "Tags", "Subprotocols", "Location"]
        protocol_info = {field: "" for field in fields}
        for line in docstring.splitlines():
            for field in fields:
                if line.startswith(f"{field}:"):
                    protocol_info[field] = line.split(f"{field}:")[1].strip()
        return protocol_info

    def map_js_protocols(filepath, protocol_const, separator='.'):
        """Parse protocols from JavaScript files using specified constants and location separator."""
        js_protocols = defaultdict(dict)
        with open(filepath, 'r') as f:
            content = f.read()

            # Pattern to find protocol functions within the specified constant's section
            pattern = re.compile(
                rf"{protocol_const}\s*=\s*{{(.*?)}};",
                re.DOTALL
            )
            match = pattern.search(content)
            if match:
                protocols_block = match.group(1)

                # Extract individual functions with inline comments
                func_pattern = re.compile(
                    r"async\s+(\w+)\s*\((.*?)\)\s*{\s*//\s*Name:\s*(.*?)\s*//\s*Description:\s*(.*?)\s*"
                    r"//\s*Prerequisites:\s*(.*?)\s*//\s*Inputs:\s*(.*?)\s*//\s*Outputs:\s*(.*?)\s*"
                    r"//\s*Tags:\s*(.*?)\s*//\s*Subprotocols:\s*(.*?)\s*//\s*Location:\s*(.*?)\n",
                    re.DOTALL
                )

                for func_match in func_pattern.finditer(protocols_block):
                    protocol_info = {
                        "Name": func_match.group(3).strip(),
                        "Description": func_match.group(4).strip(),
                        "Prerequisites": func_match.group(5).strip(),
                        "Inputs": func_match.group(6).strip(),
                        "Outputs": func_match.group(7).strip(),
                        "Tags": func_match.group(8).strip(),
                        "Subprotocols": func_match.group(9).strip(),
                        "Location": func_match.group(10).strip()
                    }
                    add_to_map(js_protocols, protocol_info, separator)

        return js_protocols

    def add_to_map(map_structure, protocol_info, separator='/'):
        """Insert protocol_info into map_structure based on its hierarchical Location."""
        location_keys = protocol_info["Location"].split(separator)
        current_level = map_structure
        for key in location_keys[:-1]:
            if key not in current_level:
                current_level[key] = {}
            current_level = current_level[key]
        current_level[location_keys[-1]] = protocol_info

    map_protocols()

        

### PROTOCOL MODIFICATION ABOVE



if __name__ == "__main__":
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Template Protocol started")

    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=handle_main_communication, args=(pipe,), daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)