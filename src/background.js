// src/background.js

////// INITIALIZATION

// Imports
import blockhash from 'blockhash-core';
import { parse } from 'tldts';
import { getHrTimestamp } from './utils';

// Global settings
const mainExtDownloadDir = 'pp_ext';
const HASH_GRID_SIZE = 8;
const HAMMING_DIST_THOLD = 3;
const SCAN_INTERVAL = 5 * 1000;
const SAVE_INTERVAL = 30 * 1000;

// Global variables
let sessionStartTime = Date.now();
let sessionStartTimeHr = getHrTimestamp();
let scanStartTime = 0;
let pureAllInfStartTime = 0;
let scanId = null;
let ssDataUrlRaw = null;
let currentDomain = null;
let offscreenPort = null;
let trancoSet = new Set();
let logs = [];
let currentUserAgent = 'default';
let offscreenWindowId = null;

async function logMessage(message) {
  try {
    const result = await browser.storage.local.get([
      'mainToggleState',
      'performanceToggleState',
    ]);

    if (result.performanceToggleState) {
      const timestampedMessage = `[${new Date().toISOString()}] - ${message}`;
      logs.push(timestampedMessage);

      await browser.storage.local.set({ logs });
      // console.log(timestampedMessage);
    }
  } catch (error) {
    console.error('Error updating logs:', error);
  }
}

async function saveLogsToFile() {
  try {
    const result = await browser.storage.local.get({ logs: [] });
    const logText = result.logs.join('\n');

    // Create a Blob and object URL (Firefox-compatible)
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    await browser.downloads.download({
      url: url,
      filename: `${mainExtDownloadDir}/${sessionStartTimeHr}/logs/performance_${getHrTimestamp()}.txt`,
      saveAs: false,
      conflictAction: 'uniquify',
    });

    // Clean up the object URL after download
    setTimeout(() => URL.revokeObjectURL(url), 2000);

    // Clear logs after saving
    logs = [];
    await browser.storage.local.set({ logs: [] });
  } catch (error) {
    console.error('Error saving logs to file:', error);
  }
}

async function loadTrancoIntoMemory(filePath = './tranco_100k.csv') {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = function (event) {
      const startProcessing = Date.now();
      const text = event.target.result;
      const lines = text.split('\n');

      trancoSet.clear(); // Ensure we start fresh

      for (let line of lines) {
        let values = line.split(',').map((value) => value.trim());

        if (values.length > 1 && values[1] !== '') {
          // Store only the domain names
          trancoSet.add(values[1]);
        }
      }

      const processingTime = Date.now() - startProcessing;
      console.log(
        `[Background] - ${getHrTimestamp()} - Time to process CSV into Set: ${processingTime} ms`,
      );

      console.log(
        '[Background] - ' +
          getHrTimestamp() +
          ' - First 5 entries in Tranco Set:',
        [...trancoSet].slice(0, 5),
      );

      resolve(trancoSet.size); // Resolve with size of Set
    };

    reader.onerror = () => reject('Error reading the file.');

    fetch(browser.runtime.getURL(filePath))
      .then((response) => response.blob())
      .then((blob) => reader.readAsText(blob))
      .catch((error) => reject(`Fetch Error: ${error}`));
  });
}

async function ensureOffscreen() {
  try {
    // Check if we've already created the offscreen window
    if (offscreenWindowId) {
      // Optionally verify it's still open/valid
      const allWindows = await browser.windows.getAll();
      const existingWindow = allWindows.find((w) => w.id === offscreenWindowId);
      if (existingWindow) {
        console.log(
          '[Background] - Offscreen window already exists:',
          existingWindow.id,
        );
        return true;
      } else {
        // If not found, reset
        offscreenWindowId = null;
      }
    }

    // Create a minimized popup window that loads offscreen.html
    const newWindow = await browser.windows.create({
      url: browser.runtime.getURL('offscreen.html'),
      type: 'popup',
      focused: false,
      state: 'minimized',
    });

    offscreenWindowId = newWindow.id;

    console.log('[Background] - Created offscreen window:', offscreenWindowId);
    return true;
  } catch (err) {
    console.error('[Background] - Error creating offscreen window:', err);
    return false;
  }
}

// Make sure if user closers offscreen page that is it recreated
browser.windows.onRemoved.addListener(async (closedWindowId) => {
  if (closedWindowId === offscreenWindowId) {
    console.log(
      '[Background] - The offscreen (minimized) window was closed by the user.',
    );
    offscreenWindowId = null;

    ensureOffscreen()
      .then(() => console.log('[Background] - Offscreen window re-created.'))
      .catch((err) =>
        console.error(
          '[Background] - Error re-creating offscreen window:',
          err,
        ),
      );
  }
});

// Local storage variables
const initLocalData = {
  dataUrl: null,
  mainToggleState: false,
  ssToggleState: false,
  performanceToggleState: true,
  backgroundInitialized: false,
  offscreenInitialized: false,
  resizedDataUrl: null,
  classification: null,
  method: null,
  infTime: null,
  ocrText: null,
  ocrTime: null,
  totalTime: null,
  phash: null,
  hammingDistance: null,
};

// Store the values in chrome.storage.local
browser.storage.local.set(initLocalData);
console.log(
  '[Background] - ' + getHrTimestamp() + ' - Local storage initialized',
);

// Set UA from storage on startup
browser.storage.local.get(['selectedUserAgentString']).then((result) => {
  currentUserAgent = result.selectedUserAgentString || 'default';
});

// Update User-Agent header for outgoing requests
function modifyUserAgentHeader(details) {
  if (currentUserAgent === 'default') {
    return {}; // No modification
  }

  let headers = details.requestHeaders.filter(
    (header) => header.name.toLowerCase() !== 'user-agent',
  );

  headers.push({
    name: 'User-Agent',
    value: currentUserAgent,
  });

  return { requestHeaders: headers };
}

// Register listener
browser.webRequest.onBeforeSendHeaders.addListener(
  modifyUserAgentHeader,
  { urls: ['<all_urls>'], types: ['main_frame'] },
  ['blocking', 'requestHeaders'],
);

// Update User-Agent string when storage changes
browser.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.selectedUserAgentString) {
    currentUserAgent = changes.selectedUserAgentString.newValue || 'default';
    console.log('Updated currentUserAgent to:', currentUserAgent);
  }
});

// Initialization for background
async function initBackground() {
  try {
    let initBackgroundStartTime = Date.now();

    // Creating offscreen doc
    let offscreenCreateStartTime = Date.now();
    await ensureOffscreen();
    let offscreenCreateTotalTime = Date.now() - offscreenCreateStartTime;
    console.log(
      `[Background] - ${getHrTimestamp()} - Offscreen doc created in ${offscreenCreateTotalTime} ms`,
    );
    logMessage(
      `[Background] - offscreen doc creation time: ${offscreenCreateTotalTime} ms`,
    );

    // Load Tranco list at extension startup
    let loadTrancoStartTime = Date.now();
    let size = await loadTrancoIntoMemory();
    let loadTrancoTotalTime = Date.now() - loadTrancoStartTime;
    console.log(
      `[Background] - ${getHrTimestamp()} - Tranco List Loaded (${size} domains) in ${loadTrancoTotalTime} ms`,
    );
    logMessage(
      `[Background] - tranco list load time: ${loadTrancoTotalTime} ms`,
    );

    await browser.storage.local.set({ backgroundInitialized: true });

    let initBackgroundTotalTime = Date.now() - initBackgroundStartTime;
    console.log(
      `[Background] - ${getHrTimestamp()} - Background initialized in ${initBackgroundTotalTime} ms`,
    );
    logMessage(
      `[Background] - background init time: ${initBackgroundTotalTime} ms`,
    );
  } catch (error) {
    console.error(`[Background] - Error initializing background: ${error}`);
  }
}
initBackground();

// Setting up message passing ports for heavier and more frequent messaging
browser.runtime.onConnect.addListener((port) => {
  console.log(
    `[Background] - ${getHrTimestamp()} - Connected to: ${port.name}`,
  );

  if (port.name === 'offscreenPort') {
    offscreenPort = port;

    port.onMessage.addListener((message) => {
      if (message.type === 'infResponse') {
        console.log(
          '[Background] - ' + getHrTimestamp() + ' - Received infResponse',
        );

        let pureAllInfTotalTime = Date.now() - pureAllInfStartTime;
        console.log(
          `[Background] - ${getHrTimestamp()} - Pure all inference completed in ${pureAllInfTotalTime} ms.`,
        );
        logMessage(
          `[Background] - pure all inference time: ${pureAllInfTotalTime} ms`,
        );

        let case23TotalTime = Date.now() - scanStartTime;
        browser.storage.local.set({ totalTime: case23TotalTime });

        console.log(
          `[Background] - ${getHrTimestamp()} - Case 2 or 3 (phash = null | phash > thold) scan completed in ${case23TotalTime} ms.`,
        );
        logMessage(
          `[Background] - case 2 or 3 total time: ${case23TotalTime} ms`,
        );

        const infData = {
          resizedDataUrl: message.data.resizedDataUrl,
          classification: message.data.classification + '_' + Date.now(),
          method: 'Model inference',
          infTime: message.data.infTime,
          ocrText: message.data.ocrText,
          ocrTime: message.data.ocrTime,
        };

        console.log(
          `[Background] - ${getHrTimestamp()} - Pure ONNX inference time: ${
            message.data.infTime
          } ms.`,
        );
        logMessage(
          `[Background] - pure onnx inference time: ${message.data.infTime} ms`,
        );

        console.log(
          `[Background] - ${getHrTimestamp()} - Pure OCR inference time ${
            message.data.ocrTime
          } ms.`,
        );
        logMessage(
          `[Background] - pure ocr inference time: ${message.data.ocrTime} ms`,
        );

        browser.storage.local.set(infData).then(() => {
          console.log(
            '[Background] - ' +
              getHrTimestamp() +
              ' - Local storage updated with infResponse',
          );
        });
      }

      if (message.type === 'offscreenInit') {
        browser.storage.local.set({ offscreenInitialized: true });

        console.log(
          `[Background] - ${getHrTimestamp()} - ONNX worker created in ${
            message.data.onnxInitTime
          } ms`,
        );
        logMessage(
          `[Background] - onnx worker creation time: ${message.data.onnxInitTime} ms`,
        );

        console.log(
          `[Background] - ${getHrTimestamp()} - Tokenizer initialized in ${
            message.data.tokenizerInitTime
          } ms`,
        );
        logMessage(
          `[Background] - tokenizer initialization time: ${message.data.tokenizerInitTime} ms`,
        );

        console.log(
          `[Background] - ${getHrTimestamp()} - OCR initialized in ${
            message.data.ocrInitTime
          } ms`,
        );
        logMessage(
          `[Background] - ocr initialization time: ${message.data.ocrInitTime} ms`,
        );

        console.log(
          `[Background] - ${getHrTimestamp()} - Offscreen initialized in ${
            message.data.offscreenInitTime
          } ms`,
        );
        logMessage(
          `[Background] - offscreen initialization time: ${message.data.offscreenInitTime} ms`,
        );
      }
    });

    port.onDisconnect.addListener(() => {
      console.log(
        '[Background] - ' + getHrTimestamp() + ' - Popup disconnected.',
      );
      offscreenPort = null;
    });
  }
});

////// EXTENSION RELOAD LOGIC

browser.runtime.onMessage.addListener((message, sender) => {
  if (message.type === 'resetExtension') {
    browser.storage.local.clear().then(() => {
      browser.runtime.reload();
    });
    console.log('[Background] - ' + getHrTimestamp() + ' - Extension reset.');
  }
});

////// MAIN CODE FUNCTIONS

async function saveScreenshot(dataUrl, baseDir, filename) {
  try {
    const data = await browser.storage.local.get([
      'mainToggleState',
      'ssToggleState',
    ]);

    if (!data.mainToggleState || !data.ssToggleState) return;

    // Fetch and convert the data URL to a blob
    const response = await fetch(dataUrl);
    const blob = await response.blob();

    // Create a temporary object URL
    const objectUrl = URL.createObjectURL(blob);

    const fullPath = `${baseDir}/${filename}.png`;

    try {
      await browser.downloads.download({
        url: objectUrl,
        filename: fullPath,
        saveAs: false,
      });
      console.log(
        `[Background] - ${getHrTimestamp()} - Screenshot saved as: ${fullPath}`,
      );
    } catch (err) {
      console.error('Download error:', err);
    } finally {
      // Revoke the object URL to free memory
      setTimeout(() => URL.revokeObjectURL(objectUrl), 2000);
    }
  } catch (error) {
    console.error('Error saving screenshot:', error);
  }
}

async function showBrowserNotification() {
  return new Promise(async (resolve, reject) => {
    console.log(
      '[Background]  - ' +
        getHrTimestamp() +
        ' -  Showing browser notification',
    );

    try {
      const tabs = await browser.tabs.query({
        active: true,
        currentWindow: true,
      });

      if (!tabs || tabs.length === 0) {
        console.warn('[Background]  -  No active tab found');
        return reject('No active tab found');
      }

      const tab = tabs[0];
      const win = await browser.windows.get(tab.windowId, { populate: false });

      if (!win) {
        console.warn('[Background] - No window found for active tab');
        return reject('No window found for active tab');
      }

      const popupWidth = Math.floor(win.width * 0.5);
      const popupHeight = Math.floor(win.height * 0.5);
      const top = win.top + Math.floor((win.height - popupHeight) / 2);
      const left = win.left + Math.floor((win.width - popupWidth) / 2);

      const newWindow = await browser.windows.create({
        url: browser.runtime.getURL('notification.html'),
        type: 'popup',
        width: popupWidth,
        height: popupHeight,
        top,
        left,
        focused: true,
      });

      console.log(
        `[Background] - ${getHrTimestamp()} -  Popup window created with ID: ${
          newWindow.id
        }`,
      );

      if (scanId) {
        clearInterval(scanId);
        console.log(
          '[Background]  - ' + getHrTimestamp() + ' -  Scanning paused.',
        );
      }

      let actionTaken = false;

      // Listener for message from popup
      const listener = async (message, sender) => {
        if (message.type === 'userActionComplete') {
          console.log(
            `[Background] - ${getHrTimestamp()} - Received userActionComplete message: ${
              message.result
            }`,
          );
          actionTaken = true;

          try {
            await browser.windows.remove(newWindow.id);
            console.log(
              `[Background] - ${getHrTimestamp()} - Popup window with ID ${
                newWindow.id
              } closed.`,
            );
          } catch (err) {
            console.warn('[Background] - Could not close popup window:', err);
          }

          if (message.result === 'Return to Safety') {
            const tabs = await browser.tabs.query({
              active: true,
              currentWindow: true,
            });
            await browser.tabs.update(tabs[0].id, {
              url: 'https://google.com',
            });
          }

          console.log(
            '[Background] - ' +
              getHrTimestamp() +
              ' - Resuming scan interval upon user interaction with popup',
          );
          runScans();

          browser.runtime.onMessage.removeListener(listener);
          browser.windows.onRemoved.removeListener(closedListener);
          resolve(message.result);
        }
      };

      // Listener for manual popup closure (e.g., X button)
      const closedListener = (closedWindowId) => {
        if (closedWindowId === newWindow.id && !actionTaken) {
          console.log(
            '[Background]  - ' +
              getHrTimestamp() +
              ' -  Popup manually closed (likely via X button)',
          );

          browser.runtime.onMessage.removeListener(listener);
          browser.windows.onRemoved.removeListener(closedListener);

          console.log(
            '[Background] - ' +
              getHrTimestamp() +
              ' - Resuming scan interval after manual close',
          );
          runScans();

          resolve('Closed Without Action');
        }
      };

      browser.runtime.onMessage.addListener(listener);
      browser.windows.onRemoved.addListener(closedListener);
    } catch (err) {
      console.error('[Background] - Error showing browser notification:', err);
      reject(err);
    }
  });
}

browser.storage.onChanged.addListener(async (changes, areaName) => {
  if (areaName !== 'local') return;

  const classification = changes.classification?.newValue;
  if (!classification) return;

  const label = classification.split('_')[0];

  if (label === 'malicious') {
    try {
      const userAction = await showBrowserNotification();
      console.log(
        `[Background] - ${getHrTimestamp()} - User action received: ${userAction}.`,
      );
    } catch (err) {
      console.error(`[Background] - Error showing notification:`, err);
    }
  }

  if (label === 'malicious' || label === 'benign') {
    try {
      const { phash, classification, currentDomain } =
        await browser.storage.local.get([
          'phash',
          'classification',
          'currentDomain',
        ]);

      const screenshotPath = `${mainExtDownloadDir}/${sessionStartTimeHr}/${
        classification.split('_')[0]
      }`;
      const screenshotFilename = `${currentDomain}_${phash}_${getHrTimestamp()}`;

      saveScreenshot(ssDataUrlRaw, screenshotPath, screenshotFilename);
    } catch (err) {
      console.error(`[Background] - Error saving screenshot:`, err);
    }
  }
});

async function captureScreenshot() {
  console.log(
    '[Background] - ' +
      getHrTimestamp() +
      ' - Attempting to capture screenshot...',
  );

  try {
    const dataUrl = await browser.tabs.captureVisibleTab(null, {
      format: 'png',
    });

    if (!dataUrl) {
      throw new Error('No dataUrl returned from captureVisibleTab');
    }

    console.log(
      '[Background] - ' + getHrTimestamp() + ' - Screenshot captured.',
    );

    return dataUrl;
  } catch (err) {
    console.error('[Background] Error capturing screenshot:', err);
    throw err;
  }
}

function getHammingDistance(hash1, hash2) {
  let distance = 0;
  for (let i = 0; i < hash1.length; i++) {
    if (hash1[i] !== hash2[i]) {
      distance++;
    }
  }
  return distance;
}

async function getImagePHash(dataUrl) {
  try {
    // Fetch the image as a blob from the data URL.
    const response = await fetch(dataUrl);
    const blob = await response.blob();

    // Create an ImageBitmap from the blob.
    const bitmap = await createImageBitmap(blob);

    // Create an OffscreenCanvas with the dimensions of the bitmap.
    const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
    const ctx = canvas.getContext('2d');

    // Draw the bitmap onto the canvas.
    ctx.drawImage(bitmap, 0, 0, bitmap.width, bitmap.height);

    // Extract the image data from the canvas.
    const imageData = ctx.getImageData(0, 0, bitmap.width, bitmap.height);

    // Generate the perceptual hash.
    const hash = blockhash.bmvbhash(imageData, HASH_GRID_SIZE); // 8x8 hash grid

    return hash;
  } catch (error) {
    throw error;
  }
}

function sendSsDataToOffscreen(data) {
  // Send screenshot via open port if connected
  if (offscreenPort) {
    console.log(
      '[Background] - ' +
        getHrTimestamp() +
        ' - Sending raw screenshot data url to offscreen.',
    );
    offscreenPort.postMessage({ type: 'ssDataUrlRaw', data: data });
  } else {
    console.warn(
      '[Background] - ' +
        getHrTimestamp() +
        ' - offscreen not connected to receive the screenshot.',
    );
  }
}

async function getCurrentTabDomain() {
  try {
    const tabs = await browser.tabs.query({
      active: true,
      currentWindow: true,
    });

    if (tabs.length === 0) {
      return null; // No active tab found
    }

    const url = new URL(tabs[0].url);
    const domain = parse(url.hostname).domain;
    return domain;
  } catch (err) {
    console.error('Error getting current tab domain:', err);
    return null;
  }
}

// Inference Init Function
async function startInference() {
  try {
    // Capturing screenshot
    let startTakeSsTime = Date.now();
    ssDataUrlRaw = await captureScreenshot();

    await browser.storage.local.set({ ssDataUrlRaw });

    let takeSsTime = Date.now() - startTakeSsTime;
    console.log(
      `[Background] - ${getHrTimestamp()} - Time to take screenshot: ${takeSsTime} ms`,
    );
    logMessage(`[Background] - screenshot capture time: ${takeSsTime} ms`);

    // Computing phash
    let phashStartTime = Date.now();
    let phashNew = await getImagePHash(ssDataUrlRaw);
    let phashTotalTime = Date.now() - phashStartTime;
    console.log(
      `[Background] - ${getHrTimestamp()} - Time to phash: ${phashTotalTime} ms`,
    );
    logMessage(`[Background] - phash computation time: ${phashTotalTime} ms`);

    // Selecting appropriate case
    const { phash: phashCurrent, classification } =
      await browser.storage.local.get(['phash', 'classification']);
    console.log(
      `[Background] - ${getHrTimestamp()} - Retrieved phash value: ${phashCurrent}`,
    );

    // CASE 2 - No phash -> inference
    if (phashCurrent === null || phashCurrent === 'NA') {
      pureAllInfStartTime = Date.now();
      sendSsDataToOffscreen(ssDataUrlRaw);
      await browser.storage.local.set({
        phash: phashNew,
        hammingDistance: null,
      });
      return;
    }

    // CASE 3 or 4
    const hammingDistance = getHammingDistance(phashCurrent, phashNew);

    if (hammingDistance >= HAMMING_DIST_THOLD) {
      // CASE 3 - Significant change -> inference
      pureAllInfStartTime = Date.now();
      sendSsDataToOffscreen(ssDataUrlRaw);
      await browser.storage.local.set({ phash: phashNew, hammingDistance });
      console.log(
        '[Background] - ' +
          getHrTimestamp() +
          ' - Updated local storage: Phash greater than threshold',
      );
    } else {
      // CASE 4 - Insignificant change -> reuse previous classification
      const case4TotalTime = Date.now() - scanStartTime;
      console.log(
        `[Background] - ${getHrTimestamp()} - Case 4 (phash < thold) scan complete in ${case4TotalTime} ms.`,
      );
      logMessage(`[Background] - case 4 total time: ${case4TotalTime} ms`);

      const case4Data = {
        resizedDataUrl: 'NA',
        method: 'Phash less than threshold',
        infTime: 'NA',
        ocrText: 'NA',
        ocrTime: 'NA',
        hammingDistance,
        totalTime: case4TotalTime,
      };

      await browser.storage.local.set(case4Data);
      console.log(
        '[Background] - ' +
          getHrTimestamp() +
          ' - Local storage updated: (Case 4) Phash less than threshold.',
      );

      const { phash, classification, currentDomain } =
        await browser.storage.local.get([
          'phash',
          'classification',
          'currentDomain',
        ]);

      saveScreenshot(
        ssDataUrlRaw,
        `${mainExtDownloadDir}/${sessionStartTimeHr}/${
          classification.split('_')[0]
        }`,
        `${currentDomain}_${phash}_${getHrTimestamp()}`,
      );
    }
  } catch (err) {
    console.error('[Background] - Error in startInference:', err);
  }
}

////// DRIVERS

browser.storage.onChanged.addListener(async (changes, areaName) => {
  if (areaName !== 'local') return;

  if (changes.offscreenInitialized || changes.backgroundInitialized) {
    try {
      const result = await browser.storage.local.get([
        'offscreenInitialized',
        'backgroundInitialized',
      ]);

      if (result.offscreenInitialized && result.backgroundInitialized) {
        const initTotalTime = Date.now() - sessionStartTime;
        console.log(
          `[Background] - ${getHrTimestamp()} - Initialization completed in ${initTotalTime} ms`,
        );
        logMessage(
          `[Background] - initialization completion time: ${initTotalTime} ms`,
        );
        runScans();
      }
    } catch (err) {
      console.error('[Background] - Error checking init state:', err);
    }
  }
});

async function runSingleScan() {
  try {
    const data = await browser.storage.local.get(['mainToggleState']);

    if (!data.mainToggleState) {
      console.log('[Background] - ' + getHrTimestamp() + ' - Toggle is OFF.');
      return;
    }

    console.log('[Background] - ' + getHrTimestamp() + ' - Toggle is ON.');
    scanStartTime = Date.now();

    currentDomain = await getCurrentTabDomain();
    await browser.storage.local.set({ currentDomain });

    if (!currentDomain) {
      console.warn('[Background] - Could not determine current domain.');
      return;
    }

    // CASE 1: Tranco whitelist
    if (trancoSet.has(currentDomain)) {
      console.log(
        `[Background] - ${getHrTimestamp()} - Domain in Tranco set: ${currentDomain}`,
      );

      const case1TotalTime = Date.now() - scanStartTime;
      const case1Data = {
        resizedDataUrl: 'NA',
        classification: `benign_${getHrTimestamp()}`,
        method: `Tranco whitelist - ${currentDomain}`,
        infTime: 'NA',
        ocrText: 'NA',
        ocrTime: 'NA',
        phash: 'NA',
        hammingDistance: 'NA',
        totalTime: case1TotalTime,
      };

      await browser.storage.local.set(case1Data);
      console.log(
        '[Background] - ' +
          getHrTimestamp() +
          ' - Local storage updated: (Case 1) Tranco whitelist.',
      );
      console.log(
        `[Background] - ${getHrTimestamp()} - Case 1 (whitelist) scan completed in ${case1TotalTime} ms`,
      );
      logMessage(`[Background] - case 1 total time: ${case1TotalTime} ms`);

      const { ssToggleState } = await browser.storage.local.get([
        'ssToggleState',
      ]);
      if (ssToggleState) {
        const screenshot = await captureScreenshot();
        saveScreenshot(
          screenshot,
          `${mainExtDownloadDir}/${sessionStartTimeHr}/benign`,
          `${currentDomain}_wl_${getHrTimestamp()}`,
        );
      }
    } else {
      console.log(
        '[Background] - ' + getHrTimestamp() + ' - Domain not in Tranco set.',
      );
      startInference();
    }
  } catch (err) {
    console.error('[Background] - Error during runSingleScan:', err);
  }
}

function runScans() {
  scanId = setInterval(() => {
    runSingleScan();
  }, SCAN_INTERVAL);
}

// Performance logging
setInterval(async () => {
  try {
    const data = await browser.storage.local.get([
      'mainToggleState',
      'performanceToggleState',
    ]);

    if (data.performanceToggleState) {
      saveLogsToFile();
    }
  } catch (err) {
    console.error('[Background] - Error during performance logging:', err);
  }
}, SAVE_INTERVAL);
