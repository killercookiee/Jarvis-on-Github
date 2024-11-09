import time
from pynput import keyboard
from pynput.keyboard import Controller, Key

# Initialize keyboard controller for simulating key presses
keyboard_controller = Controller()

# Variables to track replay state and file choice
start_replay = False
log_file = "key_log.txt"  # Default log file

def read_log_file(filename):
    actions = []
    with open(filename, "r") as f:
        for line in f:
            key, timestamp = line.strip().split(" - ")
            timestamp = float(timestamp.split()[0])  # Convert timestamp to float
            actions.append((key, timestamp))
    return actions

def replay_keys(actions):
    start_time = time.time()
    for key, timestamp in actions:
        while time.time() - start_time < timestamp:
            time.sleep(0.001)  # Small sleep to prevent busy waiting

        # Simulate special keys and normal characters
        if key.startswith("Key."):
            key_to_press = getattr(Key, key[4:], None)
            if key_to_press is None:
                print(f"Unknown special key: {key}")
                continue
        else:
            key_to_press = key.strip("'")

        # Press and release the key
        keyboard_controller.press(key_to_press)
        keyboard_controller.release(key_to_press)
        print(f"Pressed {key_to_press} at {timestamp:.4f} seconds")

    # Add a short delay to ensure the last press is processed
    time.sleep(0.1)

# Listener to detect 'esc' or 'command' to select the log file
def on_press(key):
    global start_replay, log_file
    if key == keyboard.Key.esc or key == keyboard.Key.cmd:
        log_file = "./Protocols/Key-press-protocols/key_log.txt" if key == keyboard.Key.esc else "./Protocols/Key-press-protocols/key_log_2.txt"
        start_replay = True
        print(f"Replay started... (Reading from {log_file})")
        return False  # Stop listener

def main():
    # Wait for 'esc' or 'command' to start replay
    print("Press 'Esc' to replay key_log.txt or 'Command' to replay key_log_2.txt...")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    # Read log file and replay keys
    if start_replay:
        actions = read_log_file(log_file)
        replay_keys(actions)
        print("Replay finished.")
        cleanup_controller()

def cleanup_controller():
    """Ensure the keyboard controller releases any resources before exiting."""
    # Add a short delay to make sure all keys are processed
    time.sleep(0.1)
    print("Controller cleanup completed.")

if __name__ == "__main__":
    main()
