"""
Name: sound_activation.py
Description: This is the protocol to detect when a voice has been made then sends a message to the Google extension to press the mia voice button on the chatgpt tab
Prerequisites: Conversation GPT opened
Inputs: Sound from the microphone
Outputs: start_noise, end_noise to Conversation GPT
Tags: audio, voice, mia, chatgpt, google extension
Subprotocols: None
Location: Protocols/Audio-protocols/sound_activation.py


Author: Nguyen Ba Phi
Date: 2024-10-24
"""


import pyaudio
import numpy as np
import time
import os
import traceback
import zmq
import threading
import json

# Paths for communication and log files
LOCAL_FOLDER = "/Users/killercookie/Jarvis/"

IDENTITY_PATH = os.path.abspath(__file__)
LOG_FILE_PATH = os.path.join(os.path.dirname(IDENTITY_PATH), os.path.basename(IDENTITY_PATH).replace("_", "").replace(".py", ".log"))
# Create log file if not exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'a') as log_file:
        pass


MAIN_PATH = LOCAL_FOLDER + "MAIN-communication/MAIN_COMMUNICATION.py"


context = zmq.Context()
pipe = context.socket(zmq.PAIR)
pipe.connect(f"ipc://{IDENTITY_PATH}.ipc")

stop_event = threading.Event()

def log(message, file_path=LOG_FILE_PATH):
    """Utility function to log into log file."""
    with open(file_path, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def clear_log(file_path):
    """Utility function to clear the contents of a log file."""
    with open(file_path, "w") as log_file:
        log_file.write("")  # Clear the file content

def handle_main_communication(pipe):
    """Read the message from the pipe from MAIN_COMMUNICATION.py then process it"""
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
    """"Send message to MAIN_COMMUNICATION.py"""
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
        
    # Ensure the pipe is open and ready before sending
    if pipe:
        pipe.send_string(str(json_message))
        log(f"Message sent to MAIN_COMMUNICATION: {str(json_message)}")
    else:
        log("Pipe is not open, message not sent.")



### PROTOCOL MODIFICATION BELOW

def handle_main_message(message):
    """Process the message from MAIN_COMMUNICATION.py"""
    global stop_event
    log(f"Handling message from main: {message}")

    if message['action'] == "start":
        log("Message for sound_activation main process start")
        stop_event.clear()  # Reset the stop event
        main_thread = threading.Thread(target=main, daemon=True)
        main_thread.start()

    elif message.get('action') == "stop":
        log(f"Message for sound_activation main process stop")
        stop_event.set()  # Signal the thread to stop

    return
 
def main():
    """This is the main function"""
    # Constants
    CHUNK_SIZE = 2048  # Number of frames per buffer
    FORMAT = pyaudio.paInt16  # Audio format (16-bit)
    CHANNELS = 1  # Mono audio
    RATE = 22050  # Sample rate
    VOICE_THRESHOLD = 100  # RMS threshold for detecting voice
    NOISE_DURATION_THRESHOLD = 0.5  # Duration (in seconds) to confirm continuous voice
    END_NOISE_DELAY = 3.5  # Delay (in seconds) of continuous background noise to confirm speech has ended


    def calculate_rms(audio_data):
        audio_data = np.frombuffer(audio_data, dtype=np.int16)
        audio_data = audio_data.astype(np.int32)  # Use int32 to prevent overflow
        try:
            rms = np.sqrt(np.mean(np.square(audio_data)))

            if np.isnan(rms) or np.isinf(rms):
                log("Invalid RMS calculated, skipping this chunk.")
                return None

            return rms

        except Exception as e:
            log(f"Exception in RMS calculation: {e}")
            return None

    try:
        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        # Open a stream for reading audio input
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
        log("Audio stream opened, starting to listen for sounds...")

        noise_started = False
        continuous_voice_frames = 0
        continuous_background_frames = 0
        frame_duration = CHUNK_SIZE / RATE  # Calculate the duration of each frame

        while not stop_event.is_set():
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            rms = calculate_rms(data)
            if rms is None:
                continue

            log(f"RMS value: {rms}")

            if rms > VOICE_THRESHOLD:
                continuous_voice_frames += 1
                continuous_background_frames = 0  # Reset background counter
            else:
                # Background noise detected, count frames
                continuous_background_frames += 1

                # If voice was detected previously, confirm if it's ended
                if noise_started and continuous_background_frames * frame_duration >= END_NOISE_DELAY:
                    noise_started = False
                    log("Speech ended, writing '{action: end_noise}' message to communication file")
                    message_to_send = {
                        'action': 'end_noise',
                        'input': {},
                        'sender': IDENTITY_PATH,
                        'receiver': 'tab/Conversation GPT'
                    }
                    send_main_message(message_to_send)

                # Reset voice frames count
                continuous_voice_frames = 0

            # Check if continuous voice is detected
            if continuous_voice_frames * frame_duration >= NOISE_DURATION_THRESHOLD and not noise_started:
                noise_started = True
                log("Continuous voice detected, writing '{action: start_noise}' message to communication file")
                message_to_send = {
                    'action': 'start_noise',
                    'input': {},
                    'sender': IDENTITY_PATH,
                    'receiver': 'tab/Conversation GPT'
                }
                send_main_message(message_to_send)

            time.sleep(0.1)  # To reduce CPU usage

    except Exception as e:
        log(f"Error during audio detection: {e}")
        log(traceback.format_exc())

    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
            audio.terminate()
        log("Audio stream closed")



### PROTOCOL MODIFICATION ABOVE



if __name__ == "__main__":
    """Sets up the communication with MAIN_COMMUNICATION.py"""
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Sound activation script started")

    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=handle_main_communication, args=(pipe,), daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)