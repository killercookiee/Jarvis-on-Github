//// Change code below 

const Protocols = {
  ChatGPT_Protocols: {
    utilityProtocols: {
      async observeForElement(selector, timeout = 15000) {
        
        const element = document.querySelector(selector);
        if (element) {
            return element;  // Return immediately if element already exists
        } 

        // Proceed with MutationObserver if element is not initially found
        return new Promise((resolve, reject) => {
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
                reject(`Element with selector "${selector}" not found within ${timeout / 1000} seconds.`);
            }, timeout);
        });
      },

      async clickVcRecordButton() {
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
              button = await this.observeForElement(buttonSelector);
              button.click();
              console.log('Clicked vc-record-button after observing DOM changes');
              } catch (error) {
              console.error(`Error observing for button: ${error}`);
              }
          }
      },
      
      async observeForElementGone(selector, timeout = 60000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();

            const interval = setInterval(() => {
                const element = document.querySelector(selector);
                if (!element) {
                    clearInterval(interval);
                    resolve();
                } else if (Date.now() - startTime > timeout) {
                    clearInterval(interval);
                    reject(`Element with selector "${selector}" did not disappear within ${timeout / 1000} seconds.`);
                }
            }, 500); // Check every 500ms
        });
      },    

      extractGPTText(turnNumber) {
        const selector = `.w-full.text-token-text-primary[data-testid="conversation-turn-${turnNumber}"] p, 
                          .w-full.text-token-text-primary[data-testid="conversation-turn-${turnNumber}"] h3,
                          .w-full.text-token-text-primary[data-testid="conversation-turn-${turnNumber}"] code, 
                          .w-full.text-token-text-primary[data-testid="conversation-turn-${turnNumber}"] pre`;
        const textElements = document.querySelectorAll(selector);

        return Array.from(textElements).map(el => el.textContent.trim()).join("\n").trim();
      },

      async sendUserMessage(input_text) {
        try {
            // Wait for the #prompt-textarea container to load
            console.log("Sending message to ChatGPT:", input_text);
            const promptContainer = await this.observeForElement("#prompt-textarea.ProseMirror", 20000);
            
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
            const sendButton = await this.observeForElement('button[data-testid="send-button"]', 5000);

            for (let i = 0; i < 3; i++) {
              if (sendButton) {
                  sendButton.click();
                  await Protocols.ChatGPT_Protocols.utilityProtocols.observeForElementGone('button[data-testid="stop-button"]', 1000);
                  console.log("Message sent to ChatGPT.");
              } else {
                  console.error("Send button not found.");
              }
            }

        } catch (error) {
            console.error("Error in pasteAndSendMessage:", error);
        }
      },

      async observeGPTResponse() {
        console.log("Initializing observer for GPT responses");
    
        const conversationContainer = await Protocols.ChatGPT_Protocols.utilityProtocols.observeForElement('div[role="presentation"]', 15000);
    
        if (conversationContainer) {
          let lastTurnNumber = 0;
  
          return new Promise((resolve, reject) => { // Create a new promise
              const observer = new MutationObserver((mutationsList) => {
                mutationsList.forEach((mutation) => {
                    mutation.addedNodes.forEach(async (node) => {
                      if (node.tagName === 'ARTICLE' && node.getAttribute('data-testid')?.startsWith("conversation-turn-")) {
                          const turnNumber = parseInt(node.getAttribute('data-testid').split("-").pop(), 10);
                          console.log("Observed turn number:", turnNumber);

                          // Check for odd-numbered GPT response turn
                          if (turnNumber % 2 !== 0 && turnNumber > lastTurnNumber) {
                              lastTurnNumber = turnNumber;

                              // Wait until the stop button disappears, indicating GPT has finished generating
                              try {
                                  await Protocols.ChatGPT_Protocols.utilityProtocols.observeForElementGone('button[data-testid="stop-button"]', 60000);
                                  console.log("GPT response generation complete.");

                                  // Extract GPT response text
                                  const gptResponse = Protocols.ChatGPT_Protocols.utilityProtocols.extractGPTText(turnNumber);

                                  resolve(gptResponse); // Resolve with the response
                              } catch (error) {
                                  console.error("GPT did not finish within the timeout period:", error);
                                  reject(error); // Reject the promise if there's an error
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
        console.log("Initializing observer for user input text");
    
        // Wait for the conversation container to appear, using observerForElement
        const conversationContainer = await Protocols.ChatGPT_Protocols.utilityProtocols.observeForElement('div[role="presentation"]', 15000);

    
        // Check if the conversation container is found
        if (conversationContainer) {
            let lastTurnNumber = 0;
    
            const observer = new MutationObserver((mutationsList) => {
              mutationsList.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                  if (node.tagName === 'ARTICLE' && node.getAttribute('data-testid')?.startsWith("conversation-turn-")) {
                      const turnNumber = parseInt(node.getAttribute('data-testid').split("-").pop(), 10);
                      console.log("Observed turn number:", turnNumber);

                      // Check for even-numbered user message
                      if (turnNumber % 2 === 0 && turnNumber > lastTurnNumber) {
                        lastTurnNumber = turnNumber;

                        const lastUserMessage = node.querySelector('.whitespace-pre-wrap');
                        if (lastUserMessage) {
                          const commandText = lastUserMessage.textContent.trim();
                          console.log("Detected user input:", commandText);

                          // Send the detected message to Command GPT
                          this.sendToCommandGPT(commandText);
                        }
                      }
                    }
                  });
                });
            });
    
            // Begin observing the conversationContainer
            observer.observe(conversationContainer, { childList: true, subtree: true });
            console.log("Observer is active and watching for user messages.");
        } else {
            console.error("Conversation container not found within the timeout period.");
        }
      },

    },

    noiseProtocol: {
      handleStartNoise() {
          console.log("Start noise detected. Executing clickVcRecordButton...");
          Protocols.ChatGPT_Protocols.utilityProtocols.Action.clickVcRecordButton();
      },
      
      handleEndNoise() {
          console.log("End noise detected. Executing appropriate action...");
          Protocols.ChatGPT_Protocols.utilityProtocols.Action.clickVcRecordButton();
      },
    },

    ConversationGPTProtocol: {
      async initialize() {
        console.log("Initializing Conversation GPT Protocols...");
        const initialize_message = `
        You are Conversation GPT. Remember and use the strict response structure below:

        **"Analyze the user prompt and respond with the following strict structure:

        User Prompt: This is the prompt given by the user

        Is command: Indicate if the input represents a command (Yes or No).
        Further information needed: Indicate if further information is needed to execute the command (Yes or No).
        
        Command context: Provide the the complete context of what the user is trying to achieve, prerequisites (such as if it requires the user to be already logged into something), the scope of the command. 
        Command Description: Provide a description of the command, including its purpose, function, and any specific methods or actions needed for execution.
        Command Input: Identify and list any required input parameters or arguments for the command.
        Command Output: Identify and list the expected output or result of the command.
        Tags: Identify and list any relevant tags associated with the command (e.g., system control, database interaction, file management, etc.).
        Appropriate response: This is the response that you would normally give
        "**
        `;

        await Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(initialize_message);
        this.continuous_observerGPTResponse();
      },

      async continuous_observerGPTResponse() {
        console.log("Starting continuous observation of GPT responses");

        while (true) {
          try {
            const gptResponse = await Protocols.ChatGPT_Protocols.utilityProtocols.observeGPTResponse();
            await this.handleGPTResponse(gptResponse);

          } catch (error) {
            console.error("Error during GPT response observation:", error);
          }
        }
      },

      async handleGPTResponse(gptResponse) {
        if (gptResponse.includes("Is command: Yes") && gptResponse.includes("Further information needed: No")) {
          console.log("Detected command in GPT response:", gptResponse);
          const commandDetails = gptResponse.replace(/^Is command: (Yes|No)\s*/, "").replace(/^Further information needed: (Yes|No)\s*/, "");

          if (check_executable_command(commandDetails)) {
            this.sendToProblemSolver(commandDetails);
          }
        }
      },

      sendToProblemSolver(commandText) {
        const message_to_send = {
            'action': "send_text_to_chat",
            'input': {'Input text': commandText },
            'sender': "tab/Conversation GPT",
            'receiver': "tab/Problem Solver GPT"
        };

        console.log('Sending to Problem Solver GPT:', message_to_send);

        chrome.runtime.sendMessage(message_to_send)
      },
    },

    ProblemSolverGPTProtocol: {
      async initialize() {
        console.log("Initializing Problem Solver GPT Protocols...");
        const initialize_message =`
        You are Problem Solver GPT. Remember and use the strict response structure below:

        **"Analyze the following input and respond with the following structure:

        Execution steps: Provide a step-by-step guide on how to execute the input using the available protocols.
        Expected output: Describe the expected output, result, or workflow of the execution.
        "**`;

        await Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(initialize_message);
        this.continuous_observerGPTResponse();
      },

      async continuous_observerGPTResponse() {
        console.log("Starting continuous observation of GPT responses");

        while (true) {
          try {
            const gptResponse = await Protocols.ChatGPT_Protocols.utilityProtocols.observeGPTResponse();
            await this.handleGPTResponse(gptResponse);

          } catch (error) {
            console.error("Error during GPT response observation:", error);
          }
        }
      },

      async handleGPTResponse(gptResponse) {
        this.sendToProtocolGenerationGPT(gptResponse);
      },

      sendToProtocolGenerationGPT(commandText) {
        const message_to_send = {
            'action': "send_text_to_chat",
            'input': {'Input text': commandText },
            'sender': "tab/Problem Solver GPT",
            'receiver': "tab/Protocol Generation GPT"
        };

        console.log('Sending to Protocol Generation GPT:', message_to_send);

        chrome.runtime.sendMessage(message_to_send)
      },
    },

    ProtocolGenerationGPTProtocol: {
      async initialize() {
        console.log("Initializing Protocol Generation GPT Protocols...");
        const initialize_message = `
        You are Protocol Generation GPT. Remember the response architecture you will be using from now on below:

        **"Analyze the following input and respond with the following structure:

        Protocol steps: Provide a detailed step-by-step guide on how to execute the input using the available protocols.
        Protocol output: Describe the expected output, result, or workflow of the execution.
        "**`;

        await Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(initialize_message);
        this.continuous_observerGPTResponse();
      },

      async continuous_observerGPTResponse() {
        console.log("Starting continuous observation of GPT responses");

        while (true) {
          try {
            const gptResponse = await Protocols.ChatGPT_Protocols.utilityProtocols.observeGPTResponse();
            await this.handleGPTResponse(gptResponse);

          } catch (error) {
            console.error("Error during GPT response observation:", error);
          }
        }
      },

      async handleGPTResponse(gptResponse) {
        console.log("Detected response from Protocol Generation GPT:", gptResponse);
      },
    },
  },

  GeneralProtocols: {
    Protocol_analysisProtocols: {
      async map_protocols() {
      },

      async get_protocol_map() {
      },

      async check_command_is_executable(commandDetails) {
      },

      async get_related_protocols(commandDetails) {
      },
    },
  },
}


// Add to your existing action handlers
function handle_background_message(message) {
  console.log('Handling message:', message);

  if (message.receiver === "tab/Conversation GPT") {
    if (message.action === "initialize") {
      Protocols.ChatGPT_Protocols.ConversationGPTProtocol.initialize();
    }
  }

  else if (message.receiver === "tab/Problem Solver GPT") {
    if (message.action === 'initialize') {
      Protocols.ChatGPT_Protocols.ProblemSolverGPTProtocol.initialize();
    }
    
    else if (message.action === "send_text_to_chat") {
      let protocol_context = Protocols.GeneralProtocols.utilityProtocols.get_related_protocols();

      let input_text = 
      `
      '${message.input["Input text"]}'

      Related Protocols:
      '${protocol_context}'
      `;

      Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(input_text);
    }
  }

  else if (message.receiver === "tab/Protocol Generation GPT") {
    if (message.action === 'initialize') {
      Protocols.ChatGPT_Protocols.ProtocolGenerationGPTProtocol.initialize();
    }
    else if (message.action === "send_text_to_chat") {
      let input_text = `
      '${message.input["Input text"]}'`;

      Protocols.ChatGPT_Protocols.utilityProtocols.sendUserMessage(input_text);
    }
  }

  else {
    if (message.action === "clickVcRecordButton") {
      Protocols.ChatGPT_Protocols.utilityProtocols.clickVcRecordButton();
    } 
    else if (message.action === "extractSectionText") {
      Protocols.ChatGPT_Protocols.utilityProtocols.extractSectionText(message.input['conversationNumber']);
    } 
    else if (message.action === "extractFlexText") {
      Protocols.ChatGPT_Protocols.utilityProtocols.extractFlexText();
    } 
    else if (message.action === "start_noise") {
      Protocols.ChatGPT_Protocols.noiseProtocol.handleStartNoise();
    } 
    else if (message.action === "end_noise") {
      Protocols.ChatGPT_Protocols.noiseProtocol.handleEndNoise();
    }
  }
  return true
};


//// Change code above




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
    wait_until_loaded(() => {
      try {
        console.log('Problem is handle_background_message')
        handle_background_message(message);

        response_message = {
          'response': `${message.action} executed`,
          'input': {},
          'sender': `${message.receiver}`,
          'receiver': 'GitHub Jarvis/background.js'
        }

        console.log('Sending response message', response_message);
        sendResponse(response_message);
        


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