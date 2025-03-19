import { getHrTimestamp } from './utils';

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

  console.log('[Content] - ' + getHrTimestamp() + ' Creating modal overlay');

  // Create the overlay covering the entire page
  const modalOverlay = document.createElement('div');
  modalOverlay.id = 'dangerModalOverlay';
  modalOverlay.style.position = 'fixed';
  modalOverlay.style.top = '0';
  modalOverlay.style.left = '0';
  modalOverlay.style.width = '100%';
  modalOverlay.style.height = '100%';
  modalOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
  modalOverlay.style.zIndex = '2147483647';
  // Shift modal content to the right side
  modalOverlay.style.display = 'flex';
  modalOverlay.style.justifyContent = 'flex-end';
  modalOverlay.style.alignItems = 'center';
  modalOverlay.style.fontFamily = 'Roboto, sans-serif';

  // Create the modal container shifted to the right
  const modalContainer = document.createElement('div');
  modalContainer.id = 'dangerModalContainer';
  modalContainer.style.position = 'relative';
  modalOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.75)';
  modalContainer.style.padding = '20px';
  modalContainer.style.borderRadius = '5px';
  modalContainer.style.textAlign = 'center';
  modalContainer.style.width = '30vw';
  modalContainer.style.marginRight = '20px';

  // Create the warning message
  const message = document.createElement('p');
  message.textContent =
    'WARNING: This page may be dangerous. Please consider leaving.';
  message.style.color = 'white';
  message.style.backgroundColor = 'rgba(255, 0, 0)';
  message.style.padding = '10px';
  message.style.borderRadius = '5px';
  message.style.fontWeight = 'bold';
  document.body.appendChild(message);

  modalContainer.appendChild(message);
  console.log('[Content] - ' + getHrTimestamp() + ' Warning message added');

  // Create a container for the action buttons
  const buttonsContainer = document.createElement('div');
  buttonsContainer.style.display = 'flex';
  buttonsContainer.style.flexDirection = 'column';
  buttonsContainer.style.gap = '20px';
  buttonsContainer.style.marginTop = '20px';

  // "Ignore Warning" button – closes the modal
  const ignoreButton = document.createElement('button');
  ignoreButton.textContent = 'Ignore Warning';
  ignoreButton.style.backgroundColor = 'transparent';
  ignoreButton.style.color = 'white';
  ignoreButton.style.fontWeight = 'bold';
  ignoreButton.style.padding = '10px';
  ignoreButton.style.border = '2px solid white';
  ignoreButton.style.borderRadius = '5px';
  ignoreButton.style.cursor = 'pointer';
  ignoreButton.addEventListener('click', () => {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' Ignore Warning button clicked, removing modal overlay',
    );
    chrome.runtime.sendMessage({ type: 'resumeScans' });
    modalOverlay.remove();
  });

  // "Return to Safety" button – navigates to Google
  const returnButton = document.createElement('button');
  returnButton.textContent = 'Return to Safety';
  returnButton.style.backgroundColor = 'transparent';
  returnButton.style.color = 'white';
  returnButton.style.fontWeight = 'bold';
  returnButton.style.padding = '10px';
  returnButton.style.border = '2px solid white';
  returnButton.style.borderRadius = '5px';
  returnButton.style.cursor = 'pointer';
  returnButton.addEventListener('click', () => {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' Return to Safety button clicked, navigating to https://google.com',
    );
    chrome.runtime.sendMessage({ type: 'resumeScans' });
    window.location.href = 'https://google.com';
  });

  // "Not Malicious" button – manually overrides malicious page classification
  const notMalButton = document.createElement('button');
  notMalButton.textContent = 'Not Malicious';
  notMalButton.style.backgroundColor = 'transparent';
  notMalButton.style.color = 'white';
  notMalButton.style.fontWeight = 'bold';
  notMalButton.style.padding = '10px';
  notMalButton.style.border = '2px solid white';
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
    chrome.runtime.sendMessage({ type: 'resumeScans' });
    modalOverlay.remove();
  });

  buttonsContainer.appendChild(ignoreButton);
  buttonsContainer.appendChild(returnButton);
  buttonsContainer.appendChild(notMalButton);

  // Insert buttons container into modal container
  modalContainer.appendChild(buttonsContainer);

  // **New Code: Retrieve and display the screenshot**
  // Create an image element to hold the screenshot.
  const screenshotImg = document.createElement('img');
  screenshotImg.style.width = '30vw';
  screenshotImg.style.display = 'block';
  screenshotImg.style.margin = '10px auto';

  // Retrieve the screenshot data URL from storage and, if valid, set it as the source.
  chrome.storage.local.get('dataUrl', (result) => {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' dataUrl retrieved from local storage: ',
      result.dataUrl,
    );
    if (result.dataUrl && result.dataUrl !== 'NA') {
      screenshotImg.src = result.dataUrl;
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

  modalOverlay.appendChild(modalContainer);

  // Append the modal overlay to the document body
  document.body.appendChild(modalOverlay);
  console.log(
    '[Content] - ' +
      getHrTimestamp() +
      ' Modal overlay appended to document.body',
  );

  // Create the close button in the top right-hand corner of the page
  const closeButton = document.createElement('button');
  closeButton.textContent = 'X';
  closeButton.style.color = 'white';
  closeButton.style.position = 'fixed';
  closeButton.style.top = '10px';
  closeButton.style.right = '10px';
  closeButton.style.backgroundColor = 'red';
  closeButton.style.fontSize = '16px';
  closeButton.style.cursor = 'pointer';
  closeButton.addEventListener('click', () => {
    console.log(
      '[Content] - ' +
        getHrTimestamp() +
        ' Close button clicked, removing modal overlay',
    );
    chrome.runtime.sendMessage({ type: 'resumeScans' });
    modalOverlay.remove();
  });
  // Append the close button directly to the overlay so it stays in the top right corner.
  modalOverlay.appendChild(closeButton);
}

// If the DOM is already loaded, run immediately; otherwise, wait for it.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', showDangerModal);
} else {
  showDangerModal();
}
