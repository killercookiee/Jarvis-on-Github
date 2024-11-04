"""
Name: template_protocol.py
Description: This is the template protocol
Tags: template
"""


import time
import os
import traceback
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
            send_main_message("'status': 'template protocol working'")
            time.sleep(10)  # To reduce CPU usage

    except Exception as e:
        log(f"Error in template: {e}")
        log(traceback.format_exc())

    finally:
        log("Template Protocol stopped")



### PROTOCOL MODIFICATION ABOVE



if __name__ == "__main__":
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Template Protocol started")

    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=handle_main_communication, args=(pipe,), daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)