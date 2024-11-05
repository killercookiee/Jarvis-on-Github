import os
import json
import inspect
import re

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

