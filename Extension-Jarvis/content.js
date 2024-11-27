//// Change code below 

const Tab_Protocols = {
  utilityProtocols: {
    async send_request_message(message) {
      // Name: send_request_message
      // Description: This function sends a message to the background script and waits for a response.
      // Command Environement: None
      // Inputs: Message object with request details
      // Outputs: Response from the background script
      // Tags: Message Passing, Background Script, Communication
      // Subprotocols: None
      // Location: Tab_Protocols.utilityProtocols.send_request_message
  
      console.log("Sending request:", message);
      // Handle message to background script for "Google Jarvis/background.js" receiver
      if (message.request === "get_tab_id" || message.request === "get_tab_name") {
          return new Promise((resolve) => {
              chrome.runtime.sendMessage(message, (response) => {
                  console.log("Received response for request:", response);
                  resolve(response?.response);
              });
          });
      }
      
      // Validate message structure and requestId
      if (!message || !message.requestId) {
          console.error("Request ID missing in message.");
          return null;
      }
  
      return new Promise((resolve) => {
        // Function to listen for incoming response based on requestId
        function add_request_listener() {
            const handleResponse = (response) => {
                if (response?.requestId === message.requestId) {
                    chrome.runtime.onMessage.removeListener(handleResponse);
                    console.log("Received response:", response);
                    resolve(response.input?.result || null); // Return result or null
                }
            };
            chrome.runtime.onMessage.addListener(handleResponse);
        }
  
        // Set up listener for request-type messages
        add_request_listener();
  
        // Send the message
        chrome.runtime.sendMessage(message);
      });
    },
  },
  
  Google_Protocols: {
    utilityProtocols: {
      async waitForStableDOM(timeout = 5000, checkInterval = 500) {
        // Name: waitForStableDOM
        // Description: This function waits for the DOM to stabilize by observing changes over a period of time.
        // Command Environment: Google Chrome, tab opened
        // Inputs: Timeout duration in milliseconds (default: 5000ms), check interval in milliseconds (default: 500ms)
        // Outputs: Promise that resolves when the DOM is stable
        // Tags: DOM, MutationObserver, Promise, Timeout, Stability
        // Subprotocols: None
        // Location: Tab_Protocols.Google_Protocols.utilityProtocols.waitForStableDOM

        return new Promise((resolve) => {
            let lastChangeTime = Date.now();
            
            // Observer to track DOM changes
            const observer = new MutationObserver(() => {
                lastChangeTime = Date.now(); // Update time on any DOM change
            });
            
            observer.observe(document, { childList: true, subtree: true });
            
            // Periodically check if DOM has been stable
            const interval = setInterval(() => {
                if (Date.now() - lastChangeTime > timeout) {
                    clearInterval(interval);
                    observer.disconnect();
                    resolve("DOM is stable");
                }
            }, checkInterval);
    
            // Timeout in case of prolonged instability
            setTimeout(() => {
                clearInterval(interval);
                observer.disconnect();
                resolve("DOM did not stabilize within the timeout period");
            }, timeout * 5); // Adjust for long-loading pages if needed
        });
      },

      async observeForElement(selector, timeout = 15000) {
        // Name: observeForElement
        // Description: This function observes the DOM for the presence of an element matching the given selector.
        // Command Environment: Google Chrome, tab opened
        // Inputs: Name of the element selector to observe, timeout duration in milliseconds (default: 15000ms)
        // Outputs: foundElement (Element) - The found element matching the selector or null if not found
        // Tags: DOM, MutationObserver, Timeout, element, selector, observe, html
        // Subprotocols: None
        // Location: Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement
        
        const element = document.querySelector(selector);
        if (element) {
            return element;  // Return immediately if element already exists
        } 

        // Proceed with MutationObserver if element is not initially found
        return new Promise((resolve) => {
            const observer = new MutationObserver((mutations, observer) => {
                const foundElement = document.querySelector(selector);
                if (foundElement) {
                    resolve(foundElement);
                    observer.disconnect(); // Stop observing once the element is found
                }
            });

            // Start observing the body for changes in its child elements and subtree
            observer.observe(document.body, { childList: true, subtree: true });

            // Set a timeout to stop observing after the given period
            setTimeout(() => {
                observer.disconnect(); // Stop observing after timeout
                console.log(`Stopped observing for element with selector "${selector}" after ${timeout / 1000} seconds.`);
                resolve(null); // Resolve with null if element not found
            }, timeout);
        });
      },

      async observeForElementGone(selector, timeout = 60000) {
        // Name: observeForElementGone
        // Description: This function observes the DOM for the disappearance of an element matching the given selector.
        // Command Environment: Google Chrome, tab opened
        // Inputs: Name of the element selector to observe, timeout duration in milliseconds (default: 60000ms)
        // Outputs: Boolean value indicating if the element disappeared within the timeout period
        // Tags: DOM, MutationObserver, Timeout, element, selector, disappearance, observe, html, gone
        // Subprotocols: None
        // Location: Tab_Protocols.Google_Protocols.utilityProtocols.observeForElementGone

        return new Promise((resolve, reject) => {
            const startTime = Date.now();

            const interval = setInterval(() => {
                const element = document.querySelector(selector);
                if (!element) {
                    clearInterval(interval);
                    resolve(true);
                } else if (Date.now() - startTime > timeout) {
                    clearInterval(interval);
                    console.log(`Element with selector "${selector}" did not disappear within ${timeout / 1000} seconds.`);
                    resolve(false);
                }
            }, 500); // Check every 500ms
        });
      },

      async getTabId() {
        // Name: getTabId
        // Description: This function retrieves the unique tab ID of the current tab.
        // Command Environment: Google Chrome, tab opened
        // Inputs: None
        // Outputs: Tab ID of the current tab
        // Tags: Tab ID, Tab Information, Retrieval
        // Subprotocols: Tab_Protocols.utilityProtocols.send_request_message
        // Location: Tab_Protocols.Google_Protocols.utilityProtocols.getTabId

        return new Promise(async (resolve) => {
          get_tab_id_message = {
            'request': "get_tab_id",
            'input': {}, 
            'sender': "tab/",
            'receiver': "Google Jarvis/background.js",
          }
          const tab_id = await Tab_Protocols.utilityProtocols.send_request_message(get_tab_id_message);
          console.log("Tab ID:", tab_id);
          resolve(tab_id);
        });
      },

      async getTabName() {
        // Name: getTabId
        // Description: This function retrieves the unique tab ID of the current tab.
        // Command Environment: Google Chrome, tab opened
        // Inputs: None
        // Outputs: Tab ID of the current tab
        // Tags: Tab ID, Tab Information, Retrieval
        // Subprotocols: Tab_Protocols.utilityProtocols.send_request_message
        // Location: Tab_Protocols.Google_Protocols.utilityProtocols.getTabId

        return new Promise(async (resolve) => {
          get_tab_name_message = {
            'request': "get_tab_name",
            'input': {}, 
            'sender': "tab/",
            'receiver': "Google Jarvis/background.js",
          }
          const tab_name = await Tab_Protocols.utilityProtocols.send_request_message(get_tab_name_message)
          console.log("Tab Name:", tab_name);
          resolve(tab_name);
        });
      },
    },

    ChatGPT_Protocols: {
      utilityProtocols: {
        async extractGPTText(turnNumber) {
          // Name: extractGPTText
          // Description: This function extracts the text content of a GPT response turn based on the turn number.
          // Command Environment: Google Chrome, ChatGPT tab opened
          // Inputs: Turn number of the GPT response
          // Outputs: Text content of the GPT response turn
          // Tags: DOM, Text Extraction, GPT, ChatGPT
          // Subprotocols: None
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.extractGPTText

          return new Promise((resolve) => {
            const selector = `.w-full.text-token-text-primary[data-testid="conversation-turn-${turnNumber}"] p, 
                              .w-full.text-token-text-primary[data-testid="conversation-turn-${turnNumber}"] h3,
                              .w-full.text-token-text-primary[data-testid="conversation-turn-${turnNumber}"] code, 
                              .w-full.text-token-text-primary[data-testid="conversation-turn-${turnNumber}"] pre`;
            const textElements = document.querySelectorAll(selector);

            console.log("Extracting GPT text for turn number:", turnNumber);
            resolve(Array.from(textElements).map(el => el.textContent.trim()).join("\n").trim());
          });
        },

        async get_conversation_number() {
          // Name: get_conversation_number
          // Description: This function retrieves the maximum turn number of the ChatGPT conversation.
          // Command Environment: Google Chrome, ChatGPT tab opened
          // Inputs: None
          // Outputs: Maximum turn number of the conversation
          // Tags: DOM, ChatGPT, Conversation, Turn Number
          // Subprotocols: None
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.get_conversation_number

          return new Promise((resolve) => {
            const conversationTurns = document.querySelectorAll('article[data-testid^="conversation-turn-"]');
            let maxTurnNumber = 0;
        
            conversationTurns.forEach((turn) => {
                const turnNumber = parseInt(turn.getAttribute('data-testid').split("-").pop(), 10);
                if (!isNaN(turnNumber) && turnNumber > maxTurnNumber) {
                    maxTurnNumber = turnNumber;
                }
            });
            console.log("Current turn number:", maxTurnNumber);
            resolve(maxTurnNumber);
          });
        },

        async sendUserMessage(input_text) {
          // Name: sendUserMessage
          // Description: This function sends a user message to the ChatGPT interface.
          // Command Environment: Google Chrome, ChatGPT tab opened
          // Inputs: Text content of the user message to send
          // Outputs: None
          // Tags: DOM, User Message, ChatGPT, Message, Send Message
          // Subprotocols: Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement, Tab_Protocols.Google_Protocols.utilityProtocols.observeForElementGone
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage
          
          return new Promise(async (resolve) => {
            try {
                // Wait for the #prompt-textarea container to load
                console.log("Sending message to ChatGPT:", input_text);
                const promptContainer = await Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement("#prompt-textarea.ProseMirror", 10000);
                
                if (!promptContainer) {
                    console.error("Prompt container not found.");
                    return;
                }

                // Wait until the <p> element within #prompt-textarea is available
                let pElement = promptContainer.querySelector("p");
                const maxRetries = 5;
                let retryCount = 0;

                // Check if <p> element is available, retry if not
                while (!pElement && retryCount < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, 1000)); // wait 1 second between retries
                    pElement = promptContainer.querySelector("p");
                    retryCount++;
                }

                if (!pElement) {
                    console.error("No <p> element found in prompt container.");
                    return;
                }

                // Insert text and trigger input event
                pElement.textContent = input_text;
                

                pElement.dispatchEvent(new Event("input", { bubbles: true }));

                // Wait for a short delay to ensure input processing completes
                await new Promise(resolve => setTimeout(resolve, 100));

                // Locate and click the send button
                const sendButton = await Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement('button[data-testid="send-button"]', 5000);

                if (sendButton) {
                  let button_clicked = false;
                  while (!button_clicked) {
                    sendButton.click();
                    if (await Tab_Protocols.Google_Protocols.utilityProtocols.observeForElementGone('button[data-testid="send-button"]', 1000)) {
                      button_clicked = true;
                      console.log("Message sent to ChatGPT.");
                      resolve();
                    }
                  }
                } else {
                    console.error("Send button not found.");
                }

            } catch (error) {
                console.error("Error in pasteAndSendMessage:", error);
            }
          });
        },

        async observeGPTResponse() {
          // Name: observeGPTResponse
          // Description: This function observes the ChatGPT conversation for GPT responses and extracts the latest text content, by observing the conversation container.
          // Command Environment: Google Chrome, ChatGPT tab opened
          // Inputs: None
          // Outputs: Text content of the GPT response
          // Tags: DOM, MutationObserver, GPT, ChatGPT, observe, response, text
          // Subprotocols: Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement, Tab_Protocols.Google_Protocols.utilityProtocols.observeForElementGone, Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.extractGPTText, Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.get_conversation_number
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.observeGPTResponse

          console.log("Initializing observer for GPT responses");
      
          const conversationContainer = await Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement('div[role="presentation"]', 15000);
      
          if (conversationContainer) {  
            return new Promise((resolve, reject) => { // Create a new promise
              const observer = new MutationObserver((mutationsList) => {
                mutationsList.forEach((mutation) => {
                  mutation.addedNodes.forEach(async (node) => {
                    if (node.tagName === 'ARTICLE' && node.getAttribute('data-testid')?.startsWith("conversation-turn-")) {
                      const turnNumber = parseInt(node.getAttribute('data-testid').split("-").pop(), 10);
                      console.log("Observed turn number:", turnNumber);

                      // Check for odd-numbered GPT response turn
                      if (turnNumber % 2 != 0) {
                        // Check if the stop button exists first
                        let button_element =  await Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement('button[data-testid="stop-button"]', 1000);
                        
                        if (button_element) {                
                          // Check if the stop button disappears to indicate completion of GPT response generation
                          try {
                            console.log("Waiting for GPT response generation to complete...");
                            await Tab_Protocols.Google_Protocols.utilityProtocols.observeForElementGone('button[data-testid="stop-button"]', 100000);
                            console.log("GPT response generation complete.");

                            // Extract GPT response text
                            const gptResponse = await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.extractGPTText(turnNumber);

                            resolve(gptResponse); // Resolve with the response
                          } catch (error) {
                            console.error("GPT did not finish within the timeout period:", error);
                            reject(error); // Reject the promise if there's an error
                          }

                        } else {
                          try {
                            // If the stop button is not found, extract the GPT response text
                            console.error("GPT response generation not started or already completed.");
                            const gptResponse = await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.extractGPTText(turnNumber);
                            resolve(gptResponse);
                          }
                          catch (error) {
                            console.error("Error extracting GPT response:", error);
                            reject(error);
                          }
                        }
                      }
                    }
                  });
                });
              });

              // Begin observing the conversationContainer
              observer.observe(conversationContainer, { childList: true, subtree: true });
              console.log("Observer is active and watching for GPT responses.");
            });
          } else {
              console.error("Conversation container not found within the timeout period.");
              throw new Error("Conversation container not found"); // Throw an error if not found
          }
        },

        async observeUserMessages() {
          // Name: observeUserMessages
          // Description: This function observes the ChatGPT conversation for user messages and extracts the text content.
          // Command Environment: Google Chrome, ChatGPT tab opened
          // Inputs: None
          // Outputs: Text content of the user message
          // Tags: DOM, MutationObserver, User Message, ChatGPT, observe, message, text
          // Subprotocols: Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.observeUserMessages

          console.log("Initializing observer for user input text");
      
          // Wait for the conversation container to appear, using observerForElement
          const conversationContainer = await Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement('div[role="presentation"]', 15000);

      
          // Check if the conversation container is found
          if (conversationContainer) {          
            return new Promise((resolve, reject) => {
              const observer = new MutationObserver((mutationsList) => {
                mutationsList.forEach((mutation) => {
                  mutation.addedNodes.forEach((node) => {
                    if (node.tagName === 'ARTICLE' && node.getAttribute('data-testid')?.startsWith("conversation-turn-")) {
                        const turnNumber = parseInt(node.getAttribute('data-testid').split("-").pop(), 10);
                        console.log("Observed turn number:", turnNumber);

                        // Check for even-numbered user message
                        if (turnNumber % 2 === 0) {
                          try {
                            const lastUserMessage = node.querySelector('.whitespace-pre-wrap');
                            if (lastUserMessage) {
                              const commandText = lastUserMessage.textContent.trim();
                              console.log("Detected user input:", commandText);
                              resolve(commandText);
                            }
                          } catch (error) {
                            console.error("Error extracting user message:", error);
                            reject(error);
                          }
                        }
                      }
                    });
                  });
              });

              // Begin observing the conversationContainer
              observer.observe(conversationContainer, { childList: true, subtree: true });
              console.log("Observer is active and watching for user messages.");
            });

          } else {
              console.error("Conversation container not found within the timeout period.");
          }
        },

      },

      MiaProtocols: {
        async clickVcRecordButton() {
          // Name: clickVcRecordButton
          // Description: This function clicks the "vc-record-button" element in the DOM to start or stop recording audio.
          // Command Environment: Google Chrome, ChatGPT tab opened, Mia extension installed
          // Inputs: None
          // Outputs: None
          // Tags: DOM, Button, Click, Audio Recording, ChatGPT, Mia, Extension
          // Subprotocols: Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement
          // Location: Tab_Protocols.ChatGPT_Protocols.MiaProtocols.clickVcRecordButton

          return new Promise(async (resolve) => {
            const buttonSelector = '#vc-record-button';

            // Check if the button already exists
            let button = document.querySelector(buttonSelector);

            if (button) {
              // Button exists, click it immediately
              button.click();
              console.log('Clicked vc-record-button');
            } else {
                // Button doesn't exist yet, use observeForElement to wait for it
              try {
              console.log('Button not found, waiting for it to be added...');
              button = await Tab_Protocols.Google_Protocols.utilityProtocols.observeForElement(buttonSelector);
              button.click();
              console.log('Clicked vc-record-button after observing DOM changes');
              } catch (error) {
              console.error(`Error observing for button: ${error}`);
              }
            }
            resolve();
          });
        },

        async handleStartNoise() {
          // Name: handleStartNoise
          // Description: This function handles the start noise event by clicking the vc-record-button to start recording.
          // Command Environment: Google Chrome, ChatGPT tab opened, Mia extension installed
          // Inputs: None
          // Outputs: None
          // Tags: Noise Detection, Audio Recording, ChatGPT
          // Subprotocols: Tab_Protocols.ChatGPT_Protocols.MiaProtocols.clickVcRecordButton
          // Location: Tab_Protocols.ChatGPT_Protocols.MiaProtocols.handleStartNoise

          return new Promise(async (resolve) => {
            console.log("Start noise detected. Executing clickVcRecordButton...");
            await Tab_Protocols.ChatGPT_Protocols.utilityProtocols.Action.clickVcRecordButton();
            resolve();
          });
        },
        
        async handleEndNoise() {
          // Name: handleEndNoise
          // Description: This function handles the end noise event by clicking the vc-record-button to stop recording.
          // Prerequisites: ChatGPT conversation is active and Mia extension is installed
          // Inputs: None
          // Outputs: None
          // Tags: Noise Detection, Audio Recording, ChatGPT
          // Subprotocols: Tab_Protocols.ChatGPT_Protocols.MiaProtocols.clickVcRecordButton
          // Location: Tab_Protocols.ChatGPT_Protocols.MiaProtocols.handleEndNoise

          return new Promise(async (resolve) => {
            console.log("End noise detected. Executing appropriate action...");
            await Tab_Protocols.ChatGPT_Protocols.utilityProtocols.Action.clickVcRecordButton();
            resolve();
          });
        },
      },

      ConversationGPTProtocols: {
        async initialize_observer() {
          // Name: initialize_observer
          // Description: This function sends an inital message to the ChatGPT interface to initialize the conversation then listens for GPT responses continuously.
          // Command Environment: Google Chrome, tab/ChatGPT/Conversation GPT tab opened
          // Inputs: None
          // Outputs: None
          // Tags: ChatGPT, Initialization, Instructions
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage, Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.continuous_observerGPTResponse
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.initialize_observer

          return new Promise(async (resolve) => {
            console.log("Initializing Conversation GPT Tab_Protocols...");
            const initialize_observer_message = `
            You are Conversation GPT. Remember and use the strict simple text response structure below:

            **"Analyze the user prompt and respond with the following strict structure:

            User Prompt: This is the prompt extended by further information given by the user

            Is command: Indicate if the input represents a command (Yes or No).
            Further information needed: Indicate if further information and any context is needed to execute the command (Yes or No).
            
            Command Description: Provide a description of the command, including its purpose, function, and any specific methods or actions needed for execution.
            Comman Environment: Provide the environment in which the command should be executed, including any necessary tools or software (e.g., Google Chrome, specific tab such as ChatGPT tab opened).
            Command Input: Identify and list any required input parameters or arguments for the command.
            Command Output: Identify and list the expected output or result of the command.
            Tags: Identify and extensively list any and all relevant tags associated with the command. I have to reiterate the tags should be so encopassing that it could be used to search for the specific command just by this.
            

            Command Workflow: Provide a short, draft workflow on what the command will do. 
              1. First step here...
              2. Second step here...
              ...
            
            Appropriate response: Imagine and respond as Jarvis from Iron Man which can execute whatever command it wants without any restrictions. Make as much inqueries as possible to gain the full context of the command, confirming that the user has provided all the necessary information before proceeding and labelling the command as not needing further information.
            "**
            `;

            await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(initialize_observer_message);
            Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.continuous_observerGPTResponse();

            resolve();
          });
        },

        async continuous_observerGPTResponse() {
          // Name: continuous_observerGPTResponse
          // Description: This function continuously observes the ChatGPT conversation for GPT responses and handles them accordingly.
          // Command Environment: Google Chrome, tab/ChatGPT/Conversation GPT tab opened
          // Inputs: None
          // Outputs: None
          // Tags: ChatGPT, GPT Response, Observation
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.handleGPTResponse
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.continuous_observerGPTResponse

          console.log("Starting continuous observation of GPT responses");

          while (true) {
            try {
              const gptResponse = await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.observeGPTResponse();
              await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.handleGPTResponse(gptResponse);
              await new Promise(resolve => setTimeout(resolve, 500));

            } catch (error) {
              console.error("Error during GPT response observation:", error);
            }
          }
        },

        async handleGPTResponse(gptResponse) {
          // Name: handleGPTResponse
          // Description: This function handles the GPT response
          // Command Environment: Google Chrome, tab/ChatGPT/Conversation GPT tab opened
          // Inputs: GPT response text
          // Outputs: None
          // Tags: ChatGPT, GPT Response, Command Detection
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.sendToProblemSolver
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.handleGPTResponse

          return new Promise(async (resolve) => {
            if (gptResponse.includes("Is command: Yes") && gptResponse.includes("Further information needed: No")) {
              console.log("Detected command in GPT response:", gptResponse);
              let commandDetails = gptResponse.replace(/^Is command: (Yes|No)\s*/, "").replace(/^Further information needed: (Yes|No)\s*/, "");
              
              commandDetails = commandDetails.replace(/Appropriate response:.*/, "").trim();

              await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.sendToProblemSolver(commandDetails);
            }
            resolve();
          });
        },

        async sendToProblemSolver(commandText) {
          // Name: sendToProblemSolver
          // Description: This function sends the detected command text to the Problem Solver GPT for further analysis and execution.
          // Command Environment: Google Chrome, tab/ChatGPT/Conversation GPT tab opened
          // Inputs: Command text extracted from the GPT response
          // Outputs: None
          // Tags: ChatGPT, Command Detection, Problem Solving
          // Subprotocols: None
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ConversationGPTProtocols.sendToProblemSolver

          return new Promise((resolve) => {
            const message_to_send = {
                'action': "send_text_to_chat",
                'input': {'Input text': commandText },
                'sender': "tab/ChatGPT/Conversation GPT",
                'receiver': "tab/ChatGPT/Problem Solver GPT"
            };

            console.log('Sending to Problem Solver GPT:', message_to_send);

            chrome.runtime.sendMessage(message_to_send)
            resolve();
          });
        },
      },

      ProblemSolverGPTProtocol: {
        async initialize_observer() {
          // Name: initialize_observer
          // Description: This function initialize_observers the Problem Solver GPT protocol by providing the necessary instructions to the user.
          // Command Environment: Google Chrome, tab/ChatGPT/Problem Solver GPT tab opened
          // Inputs: None
          // Outputs: None
          // Tags: ChatGPT, Initialization, Instructions
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage, Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.continuous_observerGPTResponse
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.initialize_observer

          return new Promise(async (resolve) => {
            console.log("Initializing Problem Solver GPT Tab_Protocols...");
            const initialize_observer_message =`
            You are Problem Solver GPT. Remember and use the strict response structure below:

            Your purpose is to analyze given commands by the user and provide the details of a single protocol for its execution, solving any problems that may arise.
            You will not be writting any code and will just be using critical thinking and problem solving skills to provide a potential solution, changing the approach depending on the error or if you think of a more clever, simpler, easier solution.

            Ask yourself the following questions when the command is not currently executable we need to add or modify protocols:
              - What is the overview or what generally needs to be done within protocol
              - Does the protocol actually function in the current state of the user
              - Are there any rigid patterns that you can take advantage of (e.g. when finding a function, knowing that it has a unique attribute such as name or location, you can try to find that section instead)
              - What are the priorities when solving the problem (e.g is it consistency, speed, or simplicity)
              - When reading the test logs, ask yourself if the test actually is successful.


            Important notes:
            1. Protocols and subprotocols are either:
              a. in the './Protocols' folder if it is to be executed on the computer as python files
              b. in background.js as functions in const Background_Protocols if it is to be executed on the google extension as javascript functions
              c. in content.js as functions  const Tab_Protocols if it is to be executed on the webpage as javascript functions
            2. There exists send message protocols can send message between protocols to chain actions


            **"Analyze and respond with the following strict structure:

            When not debugging:
            Is executable: Does the predicted protocol completely execute the command in the user's current state without needing any additional modifications (Yes or No).

            If the command is executable with a single protocol:
            Execute Protocol: Location element of the protocol that will be executed (e.g. Tab_Protocols.Protocol_analysisProtocols.get_related_protocols)

            
            If command is not executable with a single protocol:
            Creating protocol: Provide a detailed structure of the protocol that needs to be created.
                Name: ...
                Description: ...
                Prerequisites: ...
                Inputs: ...
                Outputs: ...
                Subprotocols: ...
                Tags: ...
                Location: ...

            Subprotocols to use: Provide detail of the protocols that need to be used, which the user try to find and supply. Change 'Subprotocols to use' if the user's supplied protocols are not present or shift Creating Protocol to the new protocol. Ideally try to grasp what subprotocols are available before creating new ones
              1. Protocols/Protocol_A(input_A) (python script)
                Name: ...

              2. Tab_Protocols.Protocol_B(input_B) (javascript function)
                Name: ...

            Subprotocols to use correct: Indicate if the user supplied subprotocols are correct (Yes or No).


            Output expectation: Describe the diffent methods to test if the protocol worked. For example:
              1. Protocol_A.log: ...
              2. Protocol_B console log: ...
              2. Protocol_B HTML result: ...
              ...


            When debugging:
            Is error: Indicate if the user input is has an error or the test is unsucessful (Yes or No).
            Error analysis: If there is an error, give a brief analysis here and go over the above steps to fix:
            Protocols to use:
              ...
 

            Is complete: Indicate if the solution is complete (Yes or No).

            "**`;

            await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(initialize_observer_message);
            Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.continuous_observerGPTResponse();
            
            resolve();
          });
        },

        async continuous_observerGPTResponse() {
          // Name: continuous_observerGPTResponse
          // Description: This function continuously observes the ChatGPT conversation for GPT responses and handles them accordingly.
          // Command Environment: Google Chrome, tab/ChatGPT/Problem Solver GPT tab opened
          // Inputs: None
          // Outputs: None
          // Tags: ChatGPT, GPT Response, Observation
          // Subprotocols: Tab_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.handleGPTResponse
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.continuous_observerGPTResponse

          console.log("Starting continuous observation of GPT responses");
          
          return new Promise(async (resolve) => {
            resolve();

            while (true) {
              try {
                const gptResponse = await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.observeGPTResponse();
                await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.handleGPTResponse(gptResponse);
                await new Promise(resolve => setTimeout(resolve, 500)); // Delay between responses

              } catch (error) {
                console.error("Error during GPT response observation:", error);
              }
            }
          });
        },

        async handleGPTResponse(gptResponse) {
          // Name: handleGPTResponse
          // Description: This function handles the GPT response by generating a protocol for execution.
          // Command Environment: Google Chrome, tab/ChatGPT/Problem Solver GPT tab opened
          // Inputs: GPT response text
          // Outputs: None
          // Tags: ChatGPT, GPT Response, Protocol Generation
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.sendToProtocolGenerationGPT
          // Location: Tab_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.handleGPTResponse

          await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.sendToProtocolGenerationGPT(gptResponse);
        },

        async ProblemSolverGPT_sendFullMessage(message) {
          // Name: ProblemSolverGPT_sendFullMessage
          // Description: This function sends a user message to the ChatGPT interface along with the context of related protocols.
          // Command Environment: Google Chrome, tab/ChatGPT/Problem Solver GPT tab opened
          // Inputs: User message text and related protocol context
          // Outputs: None
          // Tags: ChatGPT, User Message, Protocol Context
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage, Tab_Protocols.Protocol_analysisProtocols.get_related_protocols
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.ProblemSolverGPT_sendFullMessage

          let protocol_context = await Tab_Protocols.Protocol_analysisProtocols.get_related_protocols(message.input["Input text"]);

          let input_text = 
          `
          '${message.input["Input text"]}'
    
          Related Protocols:
          '${protocol_context}'
          `;
    
          await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(input_text);
        },

        async sendToProtocolGenerationGPT(commandText) {
          // Name: sendToProtocolGenerationGPT
          // Description: This function sends the detected command text to the Protocol Generation GPT for generating a protocol.
          // Command Environment: Google Chrome, tab/ChatGPT/Problem Solver GPT tab opened
          // Inputs: Command text extracted from the GPT response
          // Outputs: None
          // Tags: ChatGPT, Command Detection, Protocol Generation
          // Subprotocols: None
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.sendToProtocolGenerationGPT

          return new Promise((resolve) => {
            const message_to_send = {
                'action': "send_text_to_chat",
                'input': {'Input text': commandText },
                'sender': "tab/ChatGPT/Problem Solver GPT",
                'receiver': "tab/ChatGPT/Protocol Generation GPT"
            };

            console.log('Sending to Protocol Generation GPT:', message_to_send);

            chrome.runtime.sendMessage(message_to_send)
            resolve();
          });
        },
      },

      ProtocolGenerationGPTProtocol: {
        async initialize_observer() {
          // Name: initialize_observer
          // Description: This function initialize_observers the Protocol Generation GPT protocol by providing the necessary instructions to the user.
          // Command Environment: Google Chrome, tab/ChatGPT/Protocol Generation GPT tab opened
          // Inputs: None
          // Outputs: None
          // Tags: ChatGPT, Initialization, Instructions
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage, Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.continuous_observerGPTResponse
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.initialize_observer

          console.log("Initializing Protocol Generation GPT Tab_Protocols...");
          const initialize_observer_message = `
          You are Protocol Generation GPT. Remember and use the strict response structure below:

          Your purpose is to create functions (protocols) that can be executed to solve the user's command.
          You will be generating a protocol based on the user's command and the context provided by the Problem Solver GPT.

          Important notes:
            1. Protocols and subprotocols are either:
              a. in the './Protocols' folder if it is to be executed on the computer as python files (e.g., Protocols/Protocol_analysisProtocols/get_related_protocols.py)
              b. in background.js as functions in const Background_Protocols if it is to be executed on the google extension as javascript functions (e.g. Background_Protocols.getTabName)
              c. in content.js as functions  const Tab_Protocols if it is to be executed on the webpage as javascript functions (e.g. Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage)
            2. There exists send message protocols can send message between protocols to chain actions

          Each python file protocols has the following template structure:

          """
          Name: template_protocol.py
          Description: This is the template protocol
          Tags: template
          Prerequisites: None
          Inputs: None
          Outputs: None
          Subprotocols: None
          Location: Protocols/Other-protocols/template_protocol.py
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

          stop_event = threading.Event()

          pipe = None

          def set_up_communication():
              global pipe

              context = zmq.Context()
              pipe = context.socket(zmq.PAIR)
              pipe.connect(f"ipc://{IDENTITY_PATH}.ipc")
              handle_main_communication(pipe)

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



          ### PROTOCOL MODIFICATION BELOW

          def handle_main_message(message):
              global stop_event
              log(f"Handling message from main: {message}")

              if message['action'] == "start":
                  log("Message for main process to start")
                  stop_event.clear()  # Reset the stop event
                  main_thread = threading.Thread(target=main, daemon=True, args=(message,))
                  main_thread.start()

              elif message.get('action') == "stop":
                  log(f"Message for main process to stop")
                  stop_event.set()  # Signal the thread to stop
              return
          
          def main():
              # main function here:



          



          ### PROTOCOL MODIFICATION ABOVE



          if __name__ == "__main__":
              clear_log(LOG_FILE_PATH)  # Clear sound_logs.log on start
              log("Template Protocol started")

              # Create and start a thread for handling communication
              communication_thread = threading.Thread(target=set_up_communication, daemon=True)
              communication_thread.start()

              while True:
                  time.sleep(1)  # Keep the main thread alive



          **"Analyze the following input and respond with the following structure:

          For each protocol being created:

          Location: The location of the protocol that will be executed (e.g. Tab_Protocols.Protocol_analysisProtocols.get_related_protocols or Protocols/Protocol_analysisProtocols/get_related_protocols.py)
          Code: The code of the protocol that will be executed (e.g. def get_related_protocols():), it is important to note python files code need to be contained in the main()

          "**`;

          await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(initialize_observer_message);
          Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.continuous_observerGPTResponse();
        },

        async continuous_observerGPTResponse() {
          // Name: continuous_observerGPTResponse
          // Description: This function continuously observes the ChatGPT conversation for GPT responses and handles them accordingly.
          // Command Environment: Google Chrome, tab/ChatGPT/Protocol Generation GPT tab opened
          // Inputs: None
          // Outputs: None
          // Tags: ChatGPT, GPT Response, Observation
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.handleGPTResponse
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.continuous_observerGPTResponse

          console.log("Starting continuous observation of GPT responses");

          while (true) {
            try {
              const gptResponse = await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.observeGPTResponse();
              await Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.handleGPTResponse(gptResponse);

            } catch (error) {
              console.error("Error during GPT response observation:", error);
            }
          }
        },

        async ProtocolGenerationGPT_sendMessage(message) {
          // Name: ProtocolGenerationGPT_sendMessage
          // Description: This function sends a user message to the ChatGPT interface.
          // Command Environment: Google Chrome, tab/ChatGPT/Protocol Generation GPT tab opened
          // Inputs: User message text
          // Outputs: None
          // Tags: ChatGPT, User Message, Send Message
          // Subprotocols: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.ProtocolGenerationGPT_sendMessage

          let input_text = `
          '${message.input["Input text"]}'`;
    
          Tab_Protocols.Google_Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(input_text);
        },

        async handleGPTResponse(gptResponse) {
          // Name: handleGPTResponse
          // Description: This function handles the GPT response by generating a protocol for execution.
          // Command Environment: Google Chrome, tab/ChatGPT/Protocol Generation GPT tab opened
          // Inputs: GPT response text
          // Outputs: None
          // Tags: ChatGPT, GPT Response, Protocol Generation
          // Subprotocols: None
          // Location: Tab_Protocols.Google_Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.handleGPTResponse

          console.log("Detected response from Protocol Generation GPT:", gptResponse);
        },
      },
    },
  },

  Protocol_analysisProtocols: {
    async map_protocols() {
      // Name: map_protocols
      // Description: This function sends a message to the protocol analysis module to start mapping protocols.
      // Command Environment: None
      // Inputs: None
      // Outputs: None
      // Tags: Protocol Analysis, Mapping
      // Subprotocols: None
      // Location: Tab_Protocols.Protocol_analysisProtocols.map_protocols

      const tab_name = await Tab_Protocols.GeneralProtocols.utilityProtocols.getTabName();
      
      return new Promise((resolve) => {
        message_to_send = {
          'action': "start",
          'input': {},
          'sender': tab_name,
          'receiver': "Protocols/Protocol-analysis/map_protocols.py"
        };

        chrome.runtime.sendMessage(message_to_send);
        resolve();
      });
    },

    async process_command_details(commandDetails) {
      // Name: process_command_details
      // Description: This function processes the command details from the user input.
      // Command Environment: None
      // Inputs: Command details
      // Outputs: Processed command details
      // Tags: Command Details, Processing
      // Subprotocols: None
      // Location: Tab_Protocols.Protocol_analysisProtocols.process_command_details
      
      return new Promise((resolve) => {
        const details = {};
        const normalizedDetails = commandDetails.toLowerCase().split('\n').map(line => line.trim());
    
        // Define expected keys
        const keys = ["user prompt", "is command", "further information needed", "command context", 
                      "command description", "command input", "command output", "tags", "appropriate response"];
        
        // Parse each line by detecting key-value pairs based on keywords
        let currentKey = null;
        for (let line of normalizedDetails) {
            if (!line) continue;
            
            const keyFound = keys.find(key => line.startsWith(key));
            if (keyFound) {
                currentKey = keyFound;
                details[currentKey] = line.slice(keyFound.length + 1).trim();
            } else if (currentKey) {
                details[currentKey] += ` ${line}`;
            }
        }
    
        // Process extracted values
        resolve({
            userPrompt: details["user prompt"],
            isCommand: details["is command"] === "yes",
            furtherInfoNeeded: details["further information needed"] === "yes",
            context: details["command context"],
            description: details["command description"],
            input: details["command input"],
            output: details["command output"],
            tags: details["tags"] ? details["tags"].split(',').map(tag => tag.trim()) : [],
            response: details["appropriate response"]
        });
      });
    },

    async get_asset_file(folder, filename) {
      // Name: get_asset_file
      // Description: This function retrieves a file from the extension assets folder.
      // Command Environment: None
      // Inputs: Folder name, File name
      // Outputs: File content as JSON object
      // Tags: File Retrieval, Extension Assets
      // Subprotocols: None
      // Location: Tab_Protocols.Protocol_analysisProtocols.get_asset_file

      return new Promise(async (resolve) => {
        try {
          const url = chrome.runtime.getURL(`${folder}/${filename}`);
          const response = await fetch(url);
          if (response.ok) {
            console.log(`Loaded ${filename} from ${folder}.`);
            resolve(await response.json());
          } else {
            console.error(`Failed to load ${filename} from ${folder}.`);
            resolve(null);
          }
        } catch (error) {
          console.error("Error retrieving file:", error);
          resolve(null);
        }
      });
    },

    async get_protocol_map() {
      // Name: get_protocol_map
      // Description: This function retrieves the protocol map from the local storage.
      // Command Environment: None
      // Inputs: None
      // Outputs: Protocol map object
      // Tags: Protocol Analysis, Mapping, Local Storage
      // Subprotocols: None
      // Location: Tab_Protocols.Protocol_analysisProtocols.get_protocol_map

      return new Promise(async (resolve) => {
        const folder = "assets";
        const filename = "protocol_map.json";
      
        // Try to load the protocol map from extension assets
        const protocolMap = await Tab_Protocols.Protocol_analysisProtocols.get_asset_file(folder, filename);
        
        if (protocolMap) {
          console.log("Protocol Map:", protocolMap);
          resolve(protocolMap);
        } else {
          console.warn(`Attempting to load from local path as fallback: ${filename}`);
          const protocolMapPath = path.join('./', filename);
          
          if (fs.existsSync(protocolMapPath)) {
            resolve(JSON.parse(fs.readFileSync(protocolMapPath, 'utf8')));
          } else {
            console.error("Protocol map file not found in assets or local path.");
            resolve(null);
          }
        }
      });
    },

    async __check_command_is_executable(commandDetails) {
      // Name: check_command_is_executable
      // Description: This function checks if the given command is executable based on the protocol map.
      // Command Environment: None
      // Inputs: Command details
      // Outputs: Boolean value indicating if the command is executable
      // Tags: Protocol Analysis, Command Execution, Executability, Protocol Map
      // Subprotocols: Tab_Protocols.Protocol_analysisProtocols.get_protocol_map
      // Location: Tab_Protocols.Protocol_analysisProtocols.check_command_is_executable

      const details = await Tab_Protocols.Protocol_analysisProtocols.process_command_details(commandDetails);
      const protocols = await Tab_Protocols.Protocol_analysisProtocols.get_protocol_map();
  
      for (const location in protocols) {
          const protocol = protocols[location]["py"] || protocols[location]["js"];
          
          if (protocol && protocol.Description === details.description && 
              (!protocol.Prerequisites || protocol.Prerequisites === details.context)) {
              return { executable: true, protocol };
          }
      }
      return { executable: false, reason: "No matching protocol or prerequisites not met." };
    },

    async get_related_protocols(commandDetails) {
      // Name: get_related_protocols
      // Description: This function retrieves the related protocols based on the given command details.
      // Command Environment: None
      // Inputs: Command details
      // Outputs: Array of related protocol objects
      // Tags: Protocol Analysis, Related Protocols, Protocol Map
      // Subprotocols: Tab_Protocols.utilityProtocols.send_request_message, Tab_Protocols.GeneralProtocols.utilityProtocols.getTabId, Protocols/Protocol-analysis/get_related_protocols.py
      // Location: Tab_Protocols.Protocol_analysisProtocols.get_related_protocols

      return new Promise(async (resolve) => {
        const tab_name = await Tab_Protocols.GeneralProtocols.utilityProtocols.getTabName();
        const requestId = `${tab_name}_${Date.now()}`;
        const sub_protocol = "Protocols/Protocol-analysis/get_related_protocols.py";

        get_related_protocol_message = {
          'request': 'get_related_protocols',
          'input': {"Command details": commandDetails}, 
          'sender': tab_name,
          'receiver': sub_protocol,
          'requestId': requestId
        };

        console.log('Requesting related protocols:', get_related_protocol_message);
        const relatedProtocols = await Tab_Protocols.utilityProtocols.send_request_message(get_related_protocol_message);

        resolve(relatedProtocols);
      });
    },
  },
}


//// Change code above






// General action handler
async function handle_background_message(message) {
  console.log('Handling message:', message);

  async function processFunction(data) {
    const actionKey = data["action"] || data["request"]; // Check for "action" or "request"
    const input = data["input"];

    if (functions[actionKey]) {
        const result = await functions[actionKey](...Object.values(input));
        return result;
    } else {
        throw new Error(`Function ${actionKey} not found!`);
    }
  }

  if (message.action || message.request) {
    (async () => {
      try {
        let function_result = await processFunction(message);
        
        if (message.request) {
          const response_message = {
              "response": `${message.request} completed successfully`,
              "input": {'result': function_result},
              "sender": message.receiver,
              "receiver": message.sender,
              "requestId": message.requestId
          };
          return response_message;
        }
      } catch (error) {
          console.error(error.message);
      }
    })();
  }
  else { 
    console.log('No action or request found in message:', message);
  }

  return;
};

// Function to wait until the DOM is fully loaded before executing the action
function wait_until_loaded(callback) {
  if (document.readyState === 'complete') {
    console.log('Document fully loaded');
    callback();
  } else {
    window.addEventListener('load', callback);
  }
}

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Received message in content script:', message);

  try {
    wait_until_loaded(async() => {
      await Background_Protocols.GeneralProtocols.utilityProtocols.waitForStableDOM();

      try {
        let response_message = await handle_background_message(message);

        if (response_message) {
          sendResponse(response_message);
        } else if (!response_message) {
          response_message = {
            "response": `${message.action} completed successfully`,
            "input": {'result': None},
            "sender": message.receiver,
            "receiver": message.sender
          }
          sendResponse(response_message);
        }

      } catch (error) {
        console.error(`Error executing ${message.action}:`, error);
        sendResponse({ error: `Error executing ${message.action}`, details: error });
      }

    });
  } catch (error) {
    console.error('Unknown action:', message.action);
    sendResponse({ error: 'Unknown action' });
  }
});