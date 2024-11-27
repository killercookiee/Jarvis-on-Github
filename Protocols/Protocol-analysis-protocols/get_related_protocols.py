"""
Name: get_related_protocols.py
Description: Extract related protocols from a protocol map based on the command details.
Tags: Protocol, Analysis, Related, Map
Prerequisites: Protocol map JSON file
Inputs: Command details
Outputs: Related protocols
Subprotocols: None
Location: Protocols/Protocol-analysis-protocols/get_related_protocols.py
"""

import time
import os
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

pipe = None
requests_sent = {}
request_responses = {}

def set_up_communication():
    """This function sets up the communication with the main process."""
    global pipe

    context = zmq.Context()
    pipe = context.socket(zmq.PAIR)
    pipe.connect(f"ipc://{IDENTITY_PATH}.ipc")
    handle_main_communication(pipe)

def log(message, file_path=LOG_FILE_PATH):
    """This function logs messages to a log file."""
    with open(file_path, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def clear_log(file_path):
    """This function clears the content of a log file."""
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
    """This function sends a message to the main process."""
    json_message = json.dumps(message)
    if pipe:
        pipe.send_string(str(json_message))
        log(f"Message sent to MAIN_COMMUNICATION: {str(json_message)}")
    else:
        log("Pipe is not open, message not sent.")

def send_quit_message():
    """This function sends a quit message to the main process."""
    quit_message = {
        "action": "deactivate_subprocess",
        "input": {'script_path': IDENTITY_PATH},
        "sender": IDENTITY_PATH,
        "receiver": "MAIN-communication/MAIN_COMMUNICATION.py",
    }
    send_main_message(quit_message)

def send_request_message(message):
    """This function sends a request message to the other protocols, waiting for a response."""
    global requests_sent
    send_main_message(message)
    requests_sent[message.get('requestID')] = message
    return wait_for_response(message)

def wait_for_response(request_message):
    """This function waits for a response to a request message."""
    while request_message.get('requestID') in requests_sent:
        time.sleep(1)
    request_response = request_responses[request_message.get('requestID')]
    request_responses.pop(request_message.get('requestID'))
    return request_response


### PROTOCOL MODIFICATION BELOW

def handle_main_message(message):
    global requests_sent

    log(f"Handling message from main: {message}")

    if message.get('action'):
        if message.get('action') == "start":
            log("Message for main process to start")
            main_thread = threading.Thread(target=main, daemon=True, args=(message,))
            main_thread.start()

        elif message.get('action') == "stop":
            log(f"Message for main process to stop")
            send_quit_message()

        elif message.get('action') == "other_actions":
            # Handle other actions here
            return

    if message.get('response'):
        requests_sent.pop(message.get('requestID'))
        request_responses[message.get('requestID')] = message
            
    return
 

def main(message):
    import json
    import os
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    message = message[0]

    def load_protocols(file_path):
        """
        Load protocols from the given JSON file, traversing nested dictionaries to extract all protocols.
        """
        with open(file_path, 'r') as file:
            protocol_map = json.load(file)
        
        def extract_protocols(data):
            """
            Recursively extract protocols from nested dictionaries.
            """
            protocols = []
            for key, value in data.items():
                if isinstance(value, dict):
                    if "Name" in value and "Description" in value:  # A protocol entry
                        protocols.append(value)
                    else:  # A nested dictionary
                        protocols.extend(extract_protocols(value))
            return protocols

        return extract_protocols(protocol_map)

    def combine_protocol_fields(protocol):
        """
        Combine all relevant fields of a protocol into a single string for vectorization.
        """
        fields = [
            protocol.get("Name", ""),
            protocol.get("Description", ""),
            protocol.get("Inputs", ""),
            protocol.get("Outputs", ""),
            protocol.get("Tags", ""),
            protocol.get("Location", ""),
        ]
        # Join all fields with a separator for better readability during debugging
        return " | ".join(str(field) for field in fields if field)

    def find_similar_protocols(protocols, user_input, threshold=0.3):
        """
        Find protocols with a similarity score above the given threshold, ordered by descending similarity.
        """
        # Combine fields for all protocols
        protocol_texts = [combine_protocol_fields(protocol) for protocol in protocols]
        
        # Append the user input for comparison
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(protocol_texts + [user_input])
        similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
        
        # Filter protocols based on the threshold
        filtered_protocols = [
            (protocols[i], similarity_scores[i])
            for i, score in enumerate(similarity_scores) if score >= threshold
        ]
        
        # Sort filtered protocols by descending similarity
        filtered_protocols.sort(key=lambda x: x[1], reverse=True)
        return filtered_protocols

    # File path to the protocol JSON file
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
    protocol_map_path = os.path.join(script_dir, '../../protocol_map.json')

    # User input (replace this with the actual input)
    user_input = """
              
    """

    # Define similarity threshold
    similarity_threshold = 0.3

    # Load and process protocols
    protocols = load_protocols(protocol_map_path)
    similar_protocols = find_similar_protocols(protocols, user_input, threshold=similarity_threshold)

    # Print similar protocols
    if similar_protocols:
        log("Protocols similar to user input (ordered by similarity):")
        for protocol, score in similar_protocols:
            log(f"{protocol['Name']}: Similarity Score = {score:.2f}")
            log(f"Description: {protocol['Description']}")
            log(f"Prerequisites: {protocol.get('Prerequisites', 'N/A')}")
            log(f"Tags: {protocol.get('Tags', 'N/A')}")
            log()
    else:
        log("No protocols meet the similarity threshold.")

    response_to_send = {
        "response": "related_protocols",
        "input": {'Result': similar_protocols},
        "sender": IDENTITY_PATH,
        "receiver": message.get("sender"),
        "requestID": message.get("requestId")
    }

    send_main_message(response_to_send)

    send_quit_message()



### PROTOCOL MODIFICATION ABOVE



if __name__ == "__main__":
    clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
    log("Get Related protocol started")

    # Create and start a thread for handling communication
    communication_thread = threading.Thread(target=set_up_communication, daemon=True)
    communication_thread.start()

    while True:
        time.sleep(1)