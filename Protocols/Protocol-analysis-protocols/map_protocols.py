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
import zmq
import threading
import json

import ast
from collections import defaultdict


# Paths for communication and log files
IDENTITY_PATH = os.path.abspath(__file__)
LOG_FILE_PATH = os.path.join(os.path.dirname(IDENTITY_PATH), os.path.basename(IDENTITY_PATH).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass

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

def send_main_message(message):
    json_message = json.dumps(message)
        
    # Ensure the pipe is open and ready before sending
    if pipe:
        pipe.send_string(str(json_message))
        log(f"Message sent to MAIN_COMMUNICATION: {str(json_message)}")
    else:
        log("Pipe is not open, message not sent.")

def send_quit_message():
    quit_message = {
        "action": "stop",
        "input": None,
        "sender": IDENTITY_PATH,
        "receiver": IDENTITY_PATH,
    }
    send_main_message(quit_message)



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
            f.write("")
            json.dump(protocol_map, f, indent=2)
        log(f"Protocol map saved to {output_path}")

        output_path_2 = './Extension-Jarvis/assets/protocol_map.json'
        with open(output_path_2, 'w') as f:
            f.write("")
            json.dump(protocol_map, f, indent=2)
        log(f"Protocol map saved to {output_path_2}")

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
        """Extract protocols by locating '// Location:' and processing preceding lines."""
        js_protocols = {}
        log(f"Opening file: {filepath}")

        with open(filepath, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if "// Location:" in line:
                # Extract the 7 lines above
                preceding_lines = lines[max(0, i - 7):i]
                preceding_lines = [l.strip() for l in preceding_lines]  # Remove leading/trailing spaces

                # Ensure the format matches
                expected_fields = ["// Name:", "// Description:", "// Prerequisites:", "// Inputs:", "// Outputs:", "// Tags:", "// Subprotocols:"]
                if all(field in " ".join(preceding_lines) for field in expected_fields):
                    # Extract field values
                    protocol_info = {
                        field.split(":")[0][3:]: next((l.split(":", 1)[-1].strip() for l in preceding_lines if l.startswith(field)), "")
                        for field in expected_fields
                    }
                    # Add Location
                    protocol_info["Location"] = line.split(":", 1)[-1].strip()

                    # Map by location
                    add_to_map(js_protocols, protocol_info, separator)
                    log(f"Extracted protocol: {protocol_info['Location']}")

        log(f"Completed mapping for {protocol_const}")
        return js_protocols

    def add_to_map(js_protocols, protocol_info, separator):
        """Helper function to add protocol info to the mapping."""
        location_parts = protocol_info["Location"].split(separator)
        current_level = js_protocols
        for part in location_parts[:-1]:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        current_level[location_parts[-1]] = protocol_info
        log(f"Added protocol to map: {protocol_info['Location']}")


    map_protocols()
    send_quit_message()

        

### PROTOCOL MODIFICATION ABOVE



if __name__ == "__main__":
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Template Protocol started")

    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=handle_main_communication, args=(pipe,), daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)