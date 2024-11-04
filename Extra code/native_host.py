#!/usr/bin/env python3

import sys
import json
import struct
import traceback

def log(message):
    with open("/Users/killercookie/Main file/Own Code/Jarvis/Local Native Host/nativehost.log", "a") as log_file:
        log_file.write(message + "\n")

def read_message():
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
    response_str = json.dumps(response)
    response_bytes = response_str.encode('utf-8')
    response_length = struct.pack('I', len(response_bytes))
    sys.stdout.buffer.write(response_length)
    sys.stdout.buffer.write(response_bytes)
    sys.stdout.buffer.flush()

def action_test():
    log("Native host is online")
    return {"action": "test"}

def handle_actions(json_message):
    if json_message.get("action") == "test":
        return action_test()
    elif json_message.get("action") == "extractFlexText":
        return {"response": "extractFlexText"}
    else:
        return {"response": "Unknown action"}

if __name__ == "__main__":
    try:
        log("Native host started")
        while True:
            try:
                message = read_message()
                log(f"Message received: {message}")
                json_message = json.loads(message)
                log(f"JSON message: {json_message}")
                
                response = handle_actions(json_message)
                
                log(f"Response: {response}")
                send_message(response)
                
            except Exception as e:
                log(f"Exception in message handling: {str(e)}")
                log(traceback.format_exc())
                sys.exit(1)
    except Exception as e:
        log(f"Startup Exception: {str(e)}")
        log(traceback.format_exc())
        sys.exit(1)
