// Store tab IDs globally for use {"tab name": "tab id"}
let active_tabs = {};

// Message queue for commands
let commandQueue = [];

// Flag to indicate if we should temporarily override the keep_alive message
let overrideMessage = null; 
let overridePromiseResolve = null; // Store resolve function for external trigger

const Background_Protocols = {
  CommunicationProtocols: {
    async communicateWithMainHost(initialMessage) {
      // Name: communicateWithMainHost
      // Description: This function is used to communicate with the main native host
      // Prerequisites: The main native host must be setup
      // Inputs: initialMessage (object) - The initial message to send to the main native host
      // Outputs: None
      // Tags: Communication, Native Messaging, Message, Messaging, Main Host, Background, Send Message, Receive Message, Handle Message
      // Subprotocols: Background_Protocols.CommunicationProtocols.sendMainHostMessage, Background_Protocols.CommunicationProtocols.handleMainHost
      // Location: Background_Protocols.CommunicationProtocols.communicateWithMainHost

      let continueCommunication = true;
      let lastMessageWasOverride = false; // Track if the last message was an override

      while (continueCommunication) {
        try {
          // Log the current override and initial messages
          console.log('Current override message:', overrideMessage);
          console.log('Current initial message:', initialMessage);

          // If there is an override, use it; otherwise, use the keep_alive message
          const messageToSend = overrideMessage ? overrideMessage : initialMessage;
          console.log('Message to send:', messageToSend);

          // Track if this was an override message
          lastMessageWasOverride = Boolean(overrideMessage);

          const response = await this.sendMainHostMessage(messageToSend);
          console.log('Response from main native host:', response);

          // Handle the response using the new function
          continueCommunication = handleMainHost(response);

          // If an override message was sent and we receive a response, reset and resolve the promise
          if (lastMessageWasOverride) {
            console.log('Override message processed, resetting...');
            overrideMessage = null; // Revert to keep_alive
            if (overridePromiseResolve) {
              overridePromiseResolve();  // Resolve the promise to notify that override was processed
              overridePromiseResolve = null; // Reset after resolving
            }
            lastMessageWasOverride = false; // Reset the flag
          }

          // Prepare the next message to keep the communication alive
          if (continueCommunication && !overrideMessage) {
            console.log('Setting next message as keep_alive');
            initialMessage = { action: "keep_alive" };
          }

        } catch (error) {
          console.error('Error in communication loop:', error);
          continueCommunication = false;
        }
      }
    },

    async sendnextMainHostNMessage(altMessage) {
      // Name: sendnextMainHostNMessage
      // Description: This function is used to temporarily override the keep_alive message and send a custom message to the main native host
      // Prerequisites: The main native host must be setup
      // Inputs: altMessage (object) - The custom message to send to the main native host
      // Outputs: Promise - Resolves when the override message is processed
      // Tags: Communication, Native Messaging, Main Host, Background, Send Message, Override Message
      // Subprotocols: Background_Protocols.CommunicationProtocols.sendMainHostMessage
      // Location: Background_Protocols.CommunicationProtocols.sendnextMainHostNMessage

      console.log('Setting override message:', altMessage);
      overrideMessage = altMessage;

      // Return a promise that resolves when overrideMessage is reset to null
      return new Promise((resolve) => {
        console.log('Override message promise created');
        overridePromiseResolve = resolve; // Store resolve function for future use when message is processed
      });
    },

    async sendMainHostMessage(message) {
      // Name: sendMainHostMessage
      // Description: This function is used to send a message to the main native host
      // Prerequisites: The main native host must be setup
      // Inputs: message (object) - The message to send to the main native host
      // Outputs: Promise - Resolves with the response from the main native host
      // Tags: Communication, Native Messaging, Message, Messaging, Main Host, Background, Send Message
      // Subprotocols: None
      // Location: Background_Protocols.CommunicationProtocols.sendMainHostMessage

      return new Promise((resolve, reject) => {
          chrome.runtime.sendNativeMessage('com.jarvis.mainnativehost', message, (response) => {
              if (chrome.runtime.lastError) {
                  console.error('Error sending message to main native host:', chrome.runtime.lastError);
                  reject(chrome.runtime.lastError);
              } else {
                  console.log('Response from main native host:', response);
                  resolve(response);
              }
          });
      });
    },

    async sendResponseMessage(message) {
      // Name: sendResponseMessage
      // Description: This function is used to send a response message to the appropriate receiver
      // Prerequisites: The receiver must be known and accessible
      // Inputs: message (object) - The response message to send, sender (object)
      // Outputs: None
      // Tags: Communication, Response, Message, Messaging, Background, Send Message
      // Subprotocols: Background_Protocols.CommunicationProtocols.handleTabMessages
      // Location: Background_Protocols.CommunicationProtocols.sendResponseMessage


      if (message.receiver.startsWith('Protocols/')) {
        Background_Protocols.CommunicationProtocols.sendMainHostMessage(message);
      }
      else if (message.receiver.startsWith('tab/')) {
        Background_Protocols.CommunicationProtocols.sendMessageToSpecificTab(message);
      }
      else {
        console.log('Unhandled response message:', message);
      }
    },

    async sendMessageToSpecificTab(message, receiver = None) {
      // Name: sendMessageToSpecificTab
      // Description: This function is used to send a message to a specific tab
      // Prerequisites: The tab must be open and accessible
      // Inputs: message (object) - The message to send to the tab
      // Outputs: Promise - Resolves with the response from the tab
      // Tags: Communication, Tabs, Message, Messaging, Background, Send Message, Receive Message, Handle Message
      // Subprotocols: Background_Protocols.CommunicationProtocols.handleTabMessages
      // Location: Background_Protocols.CommunicationProtocols.sendMessageToSpecificTab

      if (receiver === None) {
        receiver = message.receiver
      }

      console.log(`Sending message to ${receiver}: ${message}`)
      let tabId = active_tabs[receiver]
      return new Promise((resolve, reject) => {
          chrome.tabs.sendMessage(tabId, message, (response) => {
              if (chrome.runtime.lastError) {
                  console.error(`Error sending message to tab ${tabId}:`, chrome.runtime.lastError.message);
                  reject(chrome.runtime.lastError);
              } else {
                  handleTabMessages(response);
                  resolve(response);
              }
          });
      });
    },
  },

  GoogleProtocols: {
    UtilityProtocols: {
      async openNewTab(new_tab_url, new_tab_name) {
        // Name: openNewTab
        // Description: This function is used to open a new tab with a specific URL and name
        // Prerequisites: None
        // Inputs: new_tab_url (string) - The URL to open in the new tab
        // Outputs: Promise - Resolves with the tab ID of the new tab
        // Tags: Tabs, Communication, Background, Open Tab, New Tab, URL, Tab ID
        // Subprotocols: None
        // Location: Background_Protocols.GoogleProtocols.UtilityProtocols.openNewTab

        if (new_tab_name in active_tabs) {
          console.log('Tab already exists:', new_tab_name);
          return active_tabs[new_tab_name];
        }

        return new Promise((resolve) => {
          chrome.tabs.create({ url: new_tab_url }, (tab) => {
            active_tabs[new_tab_name] = tab.id;


            // Listen for the tab to fully load
            chrome.tabs.onUpdated.addListener(function listener(tabId, changeInfo) {
              if (tabId === tab.id && changeInfo.status === 'complete') {
                console.log('Tab has fully loaded:', tabId);
                
                // Resolve the promise with the custom tab ID
                resolve(active_tabs[new_tab_name]);
                
                // Remove the listener after the tab has loaded
                chrome.tabs.onUpdated.removeListener(listener);
              }
            });
          });
        });
      },
    },
  }
}


// Function to handle the response from the main native host
function handleMessageForBackground(message, sender=None, sendResponse=None) {
  if (message.request === "get_tab_id") {
    const response_message = {
      'response': sender.tab.Id,
      'input': {"result": sender.tab.Id},
      'sender': 'Google Jarvis/background.js',
      'receiver': Object.keys(active_tabs).find(key => obj[key] === sender.tab.id)
    }
    console.log('Sending response message:', response_message);
    sendResponse(response_message);
  }
  
  else if (message.request === "get_tab_name") {
    const response_message = {
      'response': Object.keys(active_tabs).find(key => active_tabs[key] === sender.tab.id),
      'input': {"Request result": sender.tab.Id},
      'sender': 'Google Jarvis/background.js',
      'receiver': Object.keys(active_tabs).find(key => active_tabs[key] === sender.tab.id)
    }
    console.log('Sending response message:', response_message);
    sendResponse(response_message);
  }

  else if (message.request === 'open_new_tab' || message.action === 'open_new_tab') {
    Background_Protocols.GoogleProtocols.UtilityProtocols.openNewTab(message.input.url, message.input.name);
    
    if (message.request) {
      response_message = {
        'response': 'Opening new tab',
        'input': {'result': None},
        'sender': message.receiver,
        'receiver': message.sender,
        'requestID': message.requestID
      }
      Background_Protocols.CommunicationProtocols.sendResponseMessage(response_message);
    }
  }
  
  else {
    console.log('Unhandled action in message:', message.action);
  }
}

async function initializeGoogleExtension() {
  try {
    // Start opening the new tab (this will run asynchronously)
    await Background_Protocols.GoogleProtocols.UtilityProtocols.openNewTab('https://chatgpt.com/c/671e4bf1-5d20-8010-9f8b-91d7ee3149b2', 'tab/Problem Solver GPT');
    // await openNewTab('https://chatgpt.com/c/671e4c21-7ad8-8010-9ad2-619cc347dac3', 'tab/Protocol Generation GPT');
    await Background_Protocols.GoogleProtocols.UtilityProtocols.openNewTab('https://chatgpt.com/c/671b9513-5c58-8010-8a32-4715cd9ae3d7', 'tab/Conversation GPT');


    // Initial message to start the communication
    const initialMessage = {
      'action': 'activate',
      'input': {},
      'sender': 'Google Jarvis/background.js',
      'receiver': "/Users/killercookie/Jarvis/MAIN-communication/MAIN_COMMUNICATION.py"
    };
    // communicateWithMainHost(initialMessage);


    const initialize_conversation_message = {
      'action': 'initialize_observer',
      'input': {},
      'sender': 'Google Jarvis/background.js',
      'receiver': "tab/Conversation GPT"
    }
    Background_Protocols.CommunicationProtocols.sendMessageToSpecificTab(initialize_conversation_message)

    const initialize_problem_solver_message = {
      'action': 'initialize_observer',
      'input': {},
      'sender': 'Google Jarvis/background.js',
      'receiver': "tab/Problem Solver GPT"
    }
    Background_Protocols.CommunicationProtocols.sendMessageToSpecificTab(initialize_problem_solver_message)


  } catch (error) {
    console.error('Error in async operation:', error);
  }
}


// Change code above!








function handleMainHost(message) {
  console.log('Handling response from main native host:', message);

  if (message.receiver.startsWith('Protocols/')) {
    Background_Protocols.CommunicationProtocols.sendMainHostMessage(message);
  }

  else if (message.receiver.startsWith('tab/')) {
    if (message.receiver in active_tabs) {
      Background_Protocols.CommunicationProtocols.sendMessageToSpecificTab(message);
    }

    else {
      Background_Protocols.GoogleProtocols.UtilityProtocols.openNewTab(message.receiver, message.receiver);
      Background_Protocols.CommunicationProtocols.sendMessageToSpecificTab(message);
    }
  }

  else if (message.receiver === 'Google Jarvis/background.js') {
    handleMessageForBackground(message);
  }

  else {
    console.log('Message did not match any known receiver:', message.receiver);
  }
}

function handleTabMessages(message, sender, sendResponse) {
  console.log('Handling message from tab:', message);

  if (message.receiver.startsWith('Protocols/')) {
    Background_Protocols.CommunicationProtocols.sendMainHostMessage(message);
  }

  else if (message.receiver.startsWith('tab/')) {
    if (message.receiver in active_tabs) {
      Background_Protocols.CommunicationProtocols.sendMessageToSpecificTab(message);
    }
    else {
      Background_Protocols.GoogleProtocols.UtilityProtocols.openNewTab(message.receiver, message.receiver);
      Background_Protocols.CommunicationProtocols.sendMessageToSpecificTab(message);
    }
  }

  else if (message.receiver === 'Google Jarvis/background.js'){
    handleMessageForBackground(message, sender, sendResponse);
  }
  
  else {
    console.log('Unhandled tab message from sender:', message.sender);
  }

  return true;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Received message in background script:', message);

  // Check if the message originated from content.js, i.e tab
  if (message.sender && message.sender.startsWith("tab/")) {
    handleTabMessages(message, sender, sendResponse);
  }
  
  else {
  // Default message handling for other sources, like popup.js
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (chrome.runtime.lastError) {
      console.error('Error querying tabs:', chrome.runtime.lastError);
      sendResponse({ error: 'Error querying tabs' });
      return;
    }
    if (tabs.length === 0) {
      console.error('No active tab found');
      sendResponse({ error: 'No active tab found' });
      return;
    }

    tabs.forEach(tab => {
      chrome.tabs.sendMessage(tab.id, message, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Error sending message to content script:', chrome.runtime.lastError);
          sendResponse({ error: 'Error sending message to content script', details: chrome.runtime.lastError });
          return;
        }
        console.log('Response from content script:', response);
        sendResponse(response);
      });
    });
  });
  }
  return true; // Allows asynchronous response
});


// Example usage of the async functions
chrome.runtime.onInstalled.addListener(async () => {
  console.log('Extension installed');

  // Initialize the Google extension
  initializeGoogleExtension();
});