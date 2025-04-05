// src/content.js

import { getHrTimestamp } from './utils';

function sendModalCompletionMessage(buttonType) {
  chrome.runtime.sendMessage({
    type: 'userActionComplete',
    result: `${buttonType} button was pressed`,
  });
  chrome.runtime.sendMessage({ type: 'resumeScans' });
}

function showDangerModal() {
  console.log('[Content] - ' + getHrTimestamp() + ' showDangerModal called');

  // Prevent multiple modals from being created
  if (document.getElementById('dangerModalOverlay')) {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' Danger modal already exists. Exiting showDangerModal.',
    );
    return;
  }

  console.log(
    '[Content] - ' + getHrTimestamp() + ' Creating style tag in <head>',
  );

  // 1. Create (or reuse) a <style> element in the <head> for the overlay’s CSS.
  //    This ensures we can use !important rules to override everything else.
  const styleTag = document.createElement('style');
  styleTag.textContent = `
    #dangerModalOverlay {
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      width: 100% !important;
      height: 100% !important;
      background-color: rgba(0, 0, 0, 0.5) !important;
      z-index: 2147483647 !important; /* Very high value */
      display: flex !important;
      justify-content: flex-end !important;
      align-items: center !important;
      font-family: Roboto, sans-serif !important;
    }

    #dangerModalContainer {
      position: relative !important;
      background-color: rgba(0, 0, 0, 0.75) !important;
      padding: 20px !important;
      border-radius: 5px !important;
      text-align: center !important;
      width: 30vw !important;
      max-width: 30vw !important;
      margin-right: 20px !important;
      border: 3px solid white !important;
      font-family: Roboto, sans-serif !important;
      font-weight: bold !important;
    }
  `;
  document.head.appendChild(styleTag);

  console.log('[Content] - ' + getHrTimestamp() + ' Creating modal overlay');

  // 2. Create the overlay covering the entire page
  const modalOverlay = document.createElement('div');
  modalOverlay.id = 'dangerModalOverlay';
  // We rely on the injected style's #dangerModalOverlay rules for positioning and z-index.

  // Create the modal container
  const modalContainer = document.createElement('div');
  modalContainer.id = 'dangerModalContainer';

  // Create a container for the warning and subtext
  const warningContainer = document.createElement('div');
  warningContainer.style.backgroundColor = 'rgba(255, 0, 0)';
  warningContainer.style.padding = '10px';
  warningContainer.style.borderRadius = '5px';
  warningContainer.style.color = 'white';
  warningContainer.style.marginBottom = '20px'; // optional spacing

  const message = document.createElement('p');
  message.textContent = '⚠️ WARNING: This page may be unsafe! ⚠️';
  message.style.margin = '0';
  message.style.fontSize = '1.1em';

  const subtext = document.createElement('p');
  subtext.textContent =
    'This site was flagged based on its content and behavior. Be cautious if you choose to proceed.';
  subtext.style.margin = '5px 0 0 0';
  subtext.style.fontSize = '0.85em';
  subtext.style.fontWeight = 'normal';

  warningContainer.appendChild(message);
  warningContainer.appendChild(subtext);
  modalContainer.appendChild(warningContainer);

  console.log('[Content] - ' + getHrTimestamp() + ' Warning message added');

  // Create a container for the action buttons
  const buttonsContainer = document.createElement('div');
  buttonsContainer.style.display = 'flex';
  buttonsContainer.style.flexDirection = 'column';
  buttonsContainer.style.gap = '20px';
  buttonsContainer.style.marginTop = '20px';

  // "Ignore Warning" button – closes the modal
  const ignoreButton = document.createElement('button');
  ignoreButton.textContent = 'Continue Anyway (Not Recommended)';
  ignoreButton.style.backgroundColor = 'transparent';
  ignoreButton.style.color = 'white';
  ignoreButton.style.fontWeight = 'bold';
  ignoreButton.style.padding = '10px';
  ignoreButton.style.border = '2px solid red';
  ignoreButton.style.borderRadius = '5px';
  ignoreButton.style.cursor = 'pointer';
  ignoreButton.addEventListener('click', () => {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' Ignore Warning button clicked, removing modal overlay',
    );
    sendModalCompletionMessage('Ignore Warning');
    modalOverlay.remove();
  });

  // "Return to Safety" button – navigates to Google
  const returnButton = document.createElement('button');
  returnButton.textContent = 'Leave Page Now (Recommended)';
  returnButton.style.backgroundColor = 'transparent';
  returnButton.style.color = 'white';
  returnButton.style.fontWeight = 'bold';
  returnButton.style.padding = '10px';
  returnButton.style.border = '2px solid green';
  returnButton.style.borderRadius = '5px';
  returnButton.style.cursor = 'pointer';
  returnButton.addEventListener('click', () => {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' Return to Safety button clicked, navigating to https://google.com',
    );
    sendModalCompletionMessage('Return to Safety');
    window.location.href = 'https://google.com';
  });

  // "Not Malicious" button – manually overrides malicious page classification
  const notMalButton = document.createElement('button');
  notMalButton.textContent = 'This Alert Is a Mistake';
  notMalButton.style.backgroundColor = 'transparent';
  notMalButton.style.color = 'white';
  notMalButton.style.fontWeight = 'bold';
  notMalButton.style.padding = '10px';
  notMalButton.style.border = '2px solid yellow';
  notMalButton.style.borderRadius = '5px';
  notMalButton.style.cursor = 'pointer';
  notMalButton.addEventListener('click', () => {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' Not malicious button clicked, changing classification to false positive ("fp")',
    );
    chrome.storage.local.get(['classification'], (result) => {
      let ts = result.classification.split('_')[1];
      chrome.storage.local.set({ classification: `fp_${ts}` });
    });
    sendModalCompletionMessage('Not Malicious');
    modalOverlay.remove();
  });

  buttonsContainer.appendChild(returnButton);
  buttonsContainer.appendChild(ignoreButton);
  buttonsContainer.appendChild(notMalButton);

  // Insert buttons container into modal container
  modalContainer.appendChild(buttonsContainer);

  // Insert screenshot if available
  const screenshotImg = document.createElement('img');
  screenshotImg.style.maxWidth = '100%';
  screenshotImg.style.height = 'auto';
  screenshotImg.style.display = 'block';
  screenshotImg.style.margin = '10px auto';

  chrome.storage.local.get('ssDataUrlRaw', (result) => {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' ssDataUrlRaw retrieved from local storage: ',
      result.ssDataUrlRaw,
    );
    if (result.ssDataUrlRaw && result.ssDataUrlRaw !== 'NA') {
      screenshotImg.src = result.ssDataUrlRaw;
      // Insert the screenshot image into the modal container above the buttons.
      modalContainer.insertBefore(screenshotImg, buttonsContainer);
    } else {
      console.warn(
        '[Content] - ' +
          getHrTimestamp() +
          ' No valid screenshot data found in local storage.',
      );
    }
  });

  // Add the container to the overlay and the overlay to the body
  modalOverlay.appendChild(modalContainer);
  document.body.appendChild(modalOverlay);

  console.log(
    '[Content] - ' +
      getHrTimestamp() +
      ' Modal overlay appended to document.body',
  );
}

// If the DOM is already loading, run after it's ready; otherwise, run now.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', showDangerModal);
} else {
  showDangerModal();
}
