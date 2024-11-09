import time
from pynput import keyboard
import os

# Variables to track recording state and file choice
is_recording = False
start_time = None
recording_key = None
key_log = []
log_file = "./Protocols/Key-press-protocols/key_log.txt"  # Default log file

def on_press(key):
    global is_recording, start_time, key_log, log_file, recording_key

    # Toggle recording with 'esc' or 'command'
    if key == keyboard.Key.esc or key == keyboard.Key.cmd:
        if not is_recording:
            # Start recording and set the appropriate log file
            is_recording = True
            start_time = time.time()
            recording_key = key  # Track which key initiated the recording
            log_file = (
                "./Protocols/Key-press-protocols/key_log.txt"
                if key == keyboard.Key.esc
                else "./Protocols/Key-press-protocols/key_log_2.txt"
            )
            print(f"Recording started... (Saving to {log_file})")
        elif key == recording_key:
            # Stop recording only if the same key is pressed again
            is_recording = False
            print(f"Recording stopped... (Saved to {log_file})")
            return False  # Stop listener to end recording

    elif is_recording:
        # Record key and relative timestamp
        timestamp = time.time() - start_time
        try:
            key_log.append((str(key.char), timestamp))
        except AttributeError:
            key_log.append((str(key), timestamp))  # Handle special keys

def main():
    os.makedirs("./Protocols/Key-press-protocols/", exist_ok=True)
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    # Write log to selected file after recording stops
    with open(log_file, "w") as f:
        for key, timestamp in key_log:
            f.write(f"{key} - {timestamp:.4f} seconds\n")
    print(f"Key log saved to {log_file}")

if __name__ == "__main__":
    main()

