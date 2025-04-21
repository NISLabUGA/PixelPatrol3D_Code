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
const FLUSH_INTERVAL_MS = 2 * 60 * 1_000;
const SAVE_INTERVAL = FLUSH_INTERVAL_MS;

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
let currentUserAgent = 'default';
let offscreenTabId = null;
let lastAlertTabId = null;
let alertUITabId = null;
let perfBuffer = [];
let ssBuffer = [];

async function logMessage(message) {
  try {
    const { mainToggleState, performanceToggleState } =
      await browser.storage.local.get([
        'mainToggleState',
        'performanceToggleState',
      ]);

    if (performanceToggleState) {
      const ts = `[${new Date().toISOString()}] - ${message}`;
      perfBuffer.push(ts);
      // no more writes to browser.storage.local here
    }
  } catch (err) {
    console.error('Error updating logs:', err);
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
  // MOBILE: keep a hidden tab alive that hosts offscreen.html
  try {
    if (offscreenTabId) {
      await browser.tabs.get(offscreenTabId); // throws if closed
      return true;
    }
  } catch {
    offscreenTabId = null;
  }

  const tab = await browser.tabs.create({
    url: browser.runtime.getURL('offscreen.html'),
    active: false,
  });
  offscreenTabId = tab.id;
  console.log('[Background] - Created hidden offscreen tab:', offscreenTabId);
  return true;
}

// Make sure if user closers offscreen page that is it recreated
browser.tabs.onRemoved.addListener(async (tabId) => {
  if (tabId === offscreenTabId) {
    offscreenTabId = null;
    await ensureOffscreen();
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

browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'resetExtension') {
    browser.storage.local.clear().then(() => {
      browser.runtime.reload();
    });
    console.log('[Background] - ' + getHrTimestamp() + ' - Extension reset.');
  }
  if (message.type === 'downloadComplete' || message.type === 'dismiss') {
    perfBuffer = [];
    ssBuffer = [];
  }
  if (message.type === 'requestBuffers') {
    sendResponse({
      perfText: perfBuffer.join('\n'),
      screenshots: ssBuffer.map(({ name, dataUrl }) => ({ name, dataUrl })),
    });
    return true; // <== Important for async `sendResponse`
  }
});

////// HANDLE MALICIOUS NOTIFICATON BUTTON CLICKS

browser.runtime.onMessage.addListener((message, sender) => {
  if (message.type !== 'userActionComplete') return;

  const tabId = sender.tab?.id;
  switch (message.result) {
    case 'Return to Safety':
      if (lastAlertTabId != null) {
        // close the sketchy page
        browser.tabs.remove(lastAlertTabId);
        // open a brand‑new tab to Google
        browser.tabs.create({ url: 'https://google.com' });
      }
      if (tabId) browser.tabs.remove(tabId);
      console.log(
        `[Background] - ${getHrTimestamp()} - Received user action: ${
          message.result
        }`,
      );
      break;

    case 'Ignore Warning':
      if (lastAlertTabId != null) {
        browser.tabs.update(lastAlertTabId, { active: true });
      }
      if (tabId) browser.tabs.remove(tabId);
      console.log(
        `[Background] - ${getHrTimestamp()} - Received user action: ${
          message.result
        }`,
      );
      break;

    case 'Not Malicious':
      if (lastAlertTabId != null) {
        browser.tabs.update(lastAlertTabId, { active: true });
      }
      if (tabId) browser.tabs.remove(tabId);
      console.log(
        `[Background] - ${getHrTimestamp()} - Received user action: ${
          message.result
        }`,
      );
      break;
  }

  // clean up the UI‑tab tracker
  alertUITabId = null;
});

////// MAIN CODE FUNCTIONS

async function openDownloadCenter() {
  // Open the page only once per flush cycle
  const centerTab = await browser.tabs.create({
    url: browser.runtime.getURL('download_center.html'),
    active: true,
  });

  // Wait for the content script in download_center.html to request data
  function handleRequest(msg, sender) {
    if (msg.type !== 'requestBuffers') return;

    // Send blobs & names
    browser.tabs.sendMessage(sender.tab.id, {
      type: 'buffers',
      perfText: perfBuffer.join('\n'),
      screenshots: ssBuffer, // array of { name, blob }
    });

    // Clear listeners so we don't leak
    browser.runtime.onMessage.removeListener(handleRequest);
  }
  browser.runtime.onMessage.addListener(handleRequest);
}

async function saveScreenshot(dataUrl, baseDir, filename) {
  console.log('[Background] - ' + getHrTimestamp() + ' - saveScreenshot →', {
    baseDir,
    filename,
  });
  try {
    const { mainToggleState, ssToggleState } = await browser.storage.local.get([
      'mainToggleState',
      'ssToggleState',
    ]);

    if (!mainToggleState || !ssToggleState) return;

    ssBuffer.push({ name: `${baseDir}/${filename}.png`, dataUrl });
    console.log(
      `[Background] - ${getHrTimestamp()} - queued screenshot ${filename}.png`,
    );
  } catch (err) {
    console.error('Error queueing screenshot:', err);
  }
}

async function showBrowserNotification() {
  return new Promise((resolve) => {
    const id = `se_alert_${Date.now()}`;
    browser.notifications.create(id, {
      type: 'basic',
      title: 'Unsafe page detected!',
      message: 'Tap to view details.',
      priority: 2,
    });

    function clicked(nid) {
      if (nid !== id) return;
      browser.notifications.clear(id);

      // **focus the already‑open UI tab** (fallback to creating it)
      if (alertUITabId != null) {
        browser.tabs.update(alertUITabId, { active: true });
      } else {
        browser.tabs
          .create({
            url: browser.runtime.getURL('notification.html'),
          })
          .then((tab) => {
            alertUITabId = tab.id;
          });
      }

      cleanup('Clicked');
    }

    function closed(nid) {
      if (nid === id) cleanup('Dismissed');
    }

    function cleanup(result) {
      browser.notifications.onClicked.removeListener(clicked);
      browser.notifications.onClosed.removeListener(closed);
      resolve(result);
    }

    browser.notifications.onClicked.addListener(clicked);
    browser.notifications.onClosed.addListener(closed);
  });
}

async function injectAlertBanner(tabId) {
  try {
    await browser.tabs.executeScript(tabId, {
      file: 'alert_banner.js', // path is relative to extension root
      runAt: 'document_idle', // after the page finishes loading
    });
    console.log(`[Background] – Banner injected into tab ${tabId}`);
  } catch (err) {
    console.error('[Background] – Banner injection failed:', err);
  }
}

browser.storage.onChanged.addListener(async (changes, areaName) => {
  if (areaName !== 'local') return;

  const classification = changes.classification?.newValue;
  if (!classification) return;

  const label = classification.split('_')[0];

  if (label === 'malicious') {
    try {
      const [origin] = await browser.tabs.query({
        active: true,
        currentWindow: true,
      });
      if (origin) {
        lastAlertTabId = origin.id;
        // await injectAlertBanner(origin.id);
      }

      // **1) immediately open your full-screen alert UI**
      const uiTab = await browser.tabs.create({
        url: browser.runtime.getURL('notification.html'),
        active: true,
      });
      alertUITabId = uiTab.id;
      await showBrowserNotification();
    } catch (err) {
      console.error(`[Background] - Error showing notification:`, err);
    }
  }

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

setInterval(() => {
  if (perfBuffer.length === 0 && ssBuffer.length === 0) return;
  openDownloadCenter();
  // do NOT clear buffers yet – wait for user action
}, FLUSH_INTERVAL_MS);
