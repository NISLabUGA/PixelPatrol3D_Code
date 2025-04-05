// utility to get human-readable timestamp if needed
import { getHrTimestamp } from './utils.js'; // adjust path if needed

// Retrieve the screenshot from local storage and display it if available
chrome.storage.local.get('ssDataUrlRaw', (result) => {
  const img = document.getElementById('screenshot');
  if (result.ssDataUrlRaw && result.ssDataUrlRaw !== 'NA') {
    img.src = result.ssDataUrlRaw;
    img.style.display = 'block';
  }
});

// Helper function to send the user action back to the background script
function sendUserAction(action) {
  chrome.runtime.sendMessage({
    type: 'userActionComplete',
    result: `${action}`,
  });
}

// Wire up the buttons
document.getElementById('return').addEventListener('click', () => {
  console.log(
    `[Notification] - ${getHrTimestamp()} - Return to Safety button clicked, navigating to https://google.com`,
  );
  sendUserAction('Return to Safety');
});

document.getElementById('ignore').addEventListener('click', () => {
  console.log(
    `[Notification] - ${getHrTimestamp()} - Ignore Warning button clicked, continuing on page`,
  );
  sendUserAction('Ignore Warning');
});

document.getElementById('override').addEventListener('click', () => {
  console.log(
    `[Notification] - ${getHrTimestamp()} - Not Malicious button clicked, overriding alert`,
  );
  chrome.storage.local.get('classification', (result) => {
    let ts = result.classification.split('_')[1];
    chrome.storage.local.set({ classification: `fp_${ts}` });
  });
  sendUserAction('Not Malicious');
});
