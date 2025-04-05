// src/content.js

import { getHrTimestamp } from './utils';

const MAX_Z = 2147483647;

// Track whether the user explicitly closed the modal (so we don't resurrect it).
let userClosedModal = false;

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

  const html = document.documentElement;
  html.style.zIndex = '0'; // Ensure it’s below your modal
  html.style.pointerEvents = 'auto'; // Prevent it from eating clicks

  // Create a <style> element for the overlay’s CSS so !important rules can override everything else.
  const styleTag = document.createElement('style');
  styleTag.textContent = `
    #dangerModalOverlay {
      position: fixed !important;
      pointer-events: auto !important; 
      top: 0 !important;
      left: 0 !important;
      width: 100% !important;
      height: 100% !important;
      background-color: rgba(0, 0, 0, 0.5) !important;
      z-index: ${MAX_Z} !important; /* Very high value */
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

  // Create the overlay covering the entire page
  const modalOverlay = document.createElement('div');
  modalOverlay.id = 'dangerModalOverlay';

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
    userClosedModal = true; // user explicitly closed
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
    userClosedModal = true; // user explicitly closed
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
    userClosedModal = true; // user explicitly closed
    chrome.storage.local.get(['classification'], (result) => {
      let ts = result.classification.split('_')[1];
      chrome.storage.local.set({ classification: `fp_${ts}` });
    });
    sendModalCompletionMessage('Not Malicious');
    modalOverlay.remove();
  });

  // Append buttons to the container
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
  document.documentElement.appendChild(modalOverlay);

  console.log(
    '[Content] - ' +
      getHrTimestamp() +
      ' Modal overlay appended to document.element',
  );

  // =======================================================================
  // PERIODICALLY RE-APPLY STYLES / RE-INJECT OVERLAY IF THE PAGE REMOVES IT
  // =======================================================================
  setInterval(() => {
    // If the user explicitly closed the modal, do nothing
    if (userClosedModal) {
      return;
    }

    // If the modal overlay was removed by the page, re-inject it
    const existingOverlay = document.getElementById('dangerModalOverlay');
    if (!existingOverlay) {
      document.documentElement.appendChild(modalOverlay);
    } else {
      // Re-apply essential styles
      existingOverlay.style.position = 'fixed';
      existingOverlay.style.pointerEvents = 'auto';
      existingOverlay.style.top = '0';
      existingOverlay.style.left = '0';
      existingOverlay.style.width = '100%';
      existingOverlay.style.height = '100%';
      existingOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
      existingOverlay.style.zIndex = `${MAX_Z}`;
      existingOverlay.style.display = 'flex';
      existingOverlay.style.justifyContent = 'flex-end';
      existingOverlay.style.alignItems = 'center';
      existingOverlay.style.fontFamily = 'Roboto, sans-serif';
    }

    [...document.documentElement.children].forEach((el) => {
      // Ignore <head> and your own overlay
      if (el.tagName === 'HEAD' || el.id === 'dangerModalOverlay') return;

      const z = window.getComputedStyle(el).zIndex;

      if (z && !isNaN(z) && parseInt(z) >= MAX_Z) {
        console.warn('[Extension] Removing high z-index element:', el);
        el.remove();
      }
    });
  }, 100);
}

// Run after DOM is ready if the document is still loading
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', showDangerModal);
} else {
  showDangerModal();
}
