document.getElementById("clickButton").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "clickVcRecordButton" }, (response) => {
    if (response) {
      console.log(response.response);
    } else {
      console.error('Error handling response for clickVcRecordButton');
    }
  });
});

document.getElementById("extractTextButton").addEventListener("click", () => {
  const conversationNumber = document.getElementById("conversationNumberInput").value;
  chrome.runtime.sendMessage({ action: "extractSectionText", conversationNumber: conversationNumber }, (response) => {
    if (response) {
      console.log(response.response);
    } else {
      console.error('Error handling response for extractSectionText');
    }
  });
});

document.getElementById("extractFlexTextButton").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "extractFlexText" }, (response) => {
    if (response) {
      console.log(response.response);
    } else {
      console.error('Error handling response for extractFlexText');
    }
  });
});

document.getElementById("generate_protocol").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "generate_protocol" }, (response) => {
    if (response) {
      console.log(response.response);
    } else {
      console.error('Error handling response for generating protocols');
    }
  });
});