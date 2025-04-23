// src/background.js

////// INITIALIZATION

// Imports
import blockhash from 'blockhash-core';
import { parse } from 'tldts';
import { getHrTimestamp } from './utils';

// Global settings
const mainExtDownloadDir = 'pp_ext';
const HASH_GRID_SIZE = 8;
const HAMMING_DIST_THOLD = 5;
const SCAN_INTERVAL = 5 * 1000;
const SAVE_INTERVAL = 2 * 60 * 1000;

function logMessage(message) {
  chrome.storage.local.get(
    ['mainToggleState', 'performanceToggleState'],
    (result) => {
      if (result.performanceToggleState) {
        let timestampedMessage = `[${new Date().toISOString()}] - ${message}`;
        logs.push(timestampedMessage);

        // Update storage with the full logs array.
        chrome.storage.local.set({ logs }, () => {
          if (chrome.runtime.lastError) {
            console.error('Error updating logs:', chrome.runtime.lastError);
          }
        });
        console.log(timestampedMessage);
      }
    },
  );
}

function saveLogsToFile() {
  chrome.storage.local.get({ logs: [] }, (result) => {
    let logText = result.logs.join('\n');
    // Create a data URL from the log text
    let url = 'data:text/plain;charset=utf-8,' + encodeURIComponent(logText);

    chrome.downloads.download({
      url: url,
      filename: `${mainExtDownloadDir}/${sessionStartTimeHr}/logs/performance_${getHrTimestamp()}.txt`,
      saveAs: false,
    });

    // Clear logs after saving (optional)
    logs = [];
    chrome.storage.local.set({ logs: [] });
  });
}

// Tranco list init
function loadTrancoIntoMemory(filePath = './tranco_100k.csv') {
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

    // Fetch and read the CSV file
    fetch(chrome.runtime.getURL(filePath))
      .then((response) => response.blob())
      .then((blob) => reader.readAsText(blob))
      .catch((error) => reject(`Fetch Error: ${error}`));
  });
}

// Ensuring offscreen document is avaliable
async function ensureOffscreen() {
  if (!chrome.offscreen) {
    console.warn(
      'chrome.offscreen API is not available. Offscreen inference will not work!',
    );
    return false;
  }
  try {
    const hasDocument = await chrome.offscreen.hasDocument();
    if (!hasDocument) {
      await chrome.offscreen.createDocument({
        url: 'offscreen.html',
        reasons: ['WORKERS'],
        justification: 'Needed to run ONNX inference',
      });
      console.log(
        '[Background] - ' + getHrTimestamp() + ' - Offscreen document created.',
      );
    } else {
      console.log(
        '[Background] - ' +
          getHrTimestamp() +
          ' - Offscreen document already exists.',
      );
    }
    return true;
  } catch (err) {
    console.error(
      '[Background] - ' +
        getHrTimestamp() +
        ' - Error ensuring offscreen document:',
      err,
    );
    return false;
  }
}

// Global variables
let sessionStartTime = Date.now();
let sessionStartTimeHr = getHrTimestamp();
let scanStartTime = 0;
let pureAllInfStartTime = 0;
let scanIntId = null;
let scanId = null;
let ssDataUrlRaw = null;
let currentDomain = null;
let offscreenPort = null;
let trancoSet = new Set();
let logs = [];
let currentUserAgent = 'default';
let isScanning = false;

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
  infFlag: null,
};

function getFromStorage(keys) {
  return new Promise((resolve) => {
    chrome.storage.local.get(keys, resolve);
  });
}

function setToStorage(data) {
  return new Promise((resolve) => {
    chrome.storage.local.set(data, resolve);
  });
}

// Store the values in chrome.storage.local
chrome.storage.local.set(initLocalData, () => {
  console.log(
    '[Background] - ' + getHrTimestamp() + ' - Local storage initialized',
  );
});

// Add UA update listener
chrome.runtime.onInstalled.addListener(() => {
  updateUserAgentRule();
});

function updateUserAgentRule() {
  const ruleId = 1;

  chrome.declarativeNetRequest.updateDynamicRules(
    {
      removeRuleIds: [ruleId],
      addRules:
        currentUserAgent === 'default'
          ? []
          : [
              {
                id: ruleId,
                priority: 1,
                action: {
                  type: 'modifyHeaders',
                  requestHeaders: [
                    {
                      header: 'User-Agent',
                      operation: 'set',
                      value: currentUserAgent,
                    },
                  ],
                },
                condition: {
                  urlFilter: '|http*://*',
                  resourceTypes: ['main_frame'],
                },
              },
            ],
    },
    () => {
      if (chrome.runtime.lastError) {
        console.error('Failed to update UA rule:', chrome.runtime.lastError);
      } else {
        console.log('Updated UA rule:', currentUserAgent);
      }
    },
  );
}

// Listen for changes to UA
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.selectedUserAgentString) {
    currentUserAgent = changes.selectedUserAgentString.newValue || 'default';
    updateUserAgentRule();
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
    chrome.storage.local.set({ backgroundInitialized: true });
    let initBackgroundTotalTime = Date.now() - initBackgroundStartTime;
    console.log(
      `[Background] - ${getHrTimestamp()} - Backgroung initialized in ${initBackgroundTotalTime} ms`,
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
chrome.runtime.onConnect.addListener((port) => {
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
        chrome.storage.local.set({ totalTime: case23TotalTime });

        console.log(
          `[Background] - ${getHrTimestamp()} - Case 2 or 3 (phash = null | phash > thold) scan completed in ${case23TotalTime} ms.`,
        );
        logMessage(
          `[Background] - case 2 or 3 total time: ${case23TotalTime} ms`,
        );

        const infData = {
          resizedDataUrl: message.data.resizedDataUrl, // For the screenshot <img>
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

        chrome.storage.local.set(infData, () => {
          console.log(
            '[Background] - ' +
              getHrTimestamp() +
              ' - Local storage updated with infResponse',
          );
        });

        chrome.storage.local.set({ infFlag: `complete` });
      }
      // Offscreen init feedback
      if (message.type === 'offscreenInit') {
        chrome.storage.local.set({ offscreenInitialized: true });
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

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'resetExtension') {
    chrome.storage.local.clear(() => {
      chrome.runtime.reload();
    });
    console.log('[Background] - ' + getHrTimestamp() + ' - Extension reset.');
  }
});

////// MAIN CODE FUNCTIONS

async function saveScreenshot(dataUrl, baseDir, filename) {
  chrome.storage.local.get(
    ['mainToggleState', 'ssToggleState'],
    async (data) => {
      if (data.mainToggleState && data.ssToggleState) {
        fetch(dataUrl)
          .then((res) => res.blob())
          .then((blob) => {
            const reader = new FileReader();
            reader.onloadend = function () {
              const dataUrlResult = reader.result;
              const fullPath = `${baseDir}/${filename}.png`;
              chrome.downloads.download(
                {
                  url: dataUrlResult,
                  filename: fullPath, // Specifies the directory inside Downloads
                  saveAs: false, // Automatically saves without prompt
                },
                (downloadId) => {
                  if (chrome.runtime.lastError) {
                    console.error('Download error:', chrome.runtime.lastError);
                  } else {
                    console.log(
                      `[Background] - ${getHrTimestamp()} - Screenshot saved as: ${fullPath}`,
                    );
                  }
                },
              );
            };
            reader.readAsDataURL(blob);
          })
          .catch((error) => console.error('Error saving screenshot:', error));
      }
    },
  );
}

async function showBrowserNotification() {
  return new Promise((resolve, reject) => {
    console.log(
      '[Background]  - ' +
        getHrTimestamp() +
        ' -  Showing browser notification',
    );

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || tabs.length === 0) {
        console.warn('[Background]  -  No active tab found');
        return reject('No active tab found');
      }

      const tab = tabs[0];
      chrome.windows.get(tab.windowId, { populate: false }, (win) => {
        if (!win) {
          console.warn('[Background] - No window found for active tab');
          return reject('No window found for active tab');
        }

        const popupWidth = Math.floor(win.width * 0.5);
        const popupHeight = Math.floor(win.height * 0.5);
        const top = win.top + Math.floor((win.height - popupHeight) / 2);
        const left = win.left + Math.floor((win.width - popupWidth) / 2);

        chrome.windows.create(
          {
            url: chrome.runtime.getURL('notification.html'),
            type: 'popup',
            width: popupWidth,
            height: popupHeight,
            top,
            left,
            focused: true,
          },
          (newWindow) => {
            if (chrome.runtime.lastError) {
              console.error(
                '[Background] - Failed to create popup:',
                chrome.runtime.lastError,
              );
              return reject(chrome.runtime.lastError);
            }

            console.log(
              `[Background] - ${getHrTimestamp()} -  Popup window created with ID: ${
                newWindow.id
              }`,
            );

            if (scanIntId) {
              clearInterval(scanIntId);
              scanIntId = null;
              console.log(
                '[Background]  - ' + getHrTimestamp() + ' -  Scanning paused.',
              );
            }

            let actionTaken = false;

            // Listener for message from popup
            const listener = (message, sender, sendResponse) => {
              if (message.type === 'userActionComplete') {
                console.log(
                  `[Background] - ${getHrTimestamp()}- Received userActionComplete message: ${
                    message.result
                  }`,
                );
                actionTaken = true;

                chrome.windows.remove(newWindow.id, () => {
                  if (chrome.runtime.lastError) {
                    console.warn(
                      '[Background] - Could not close popup window:',
                      chrome.runtime.lastError,
                    );
                  } else {
                    console.log(
                      `[Background] - ${getHrTimestamp()} - Popup window with ID ${
                        newWindow.id
                      } closed.`,
                    );
                  }
                });

                if (message.result === 'Return to Safety') {
                  chrome.tabs.query(
                    { active: true, currentWindow: true },
                    (tabs) => {
                      chrome.tabs.update(tabs[0].id, {
                        url: 'https://google.com',
                      });
                    },
                  );
                }

                console.log(
                  '[Background] - ' +
                    getHrTimestamp() +
                    ' - Resuming scan interval upon user interaction with popup',
                );
                runScans();

                chrome.runtime.onMessage.removeListener(listener);
                chrome.windows.onRemoved.removeListener(closedListener);
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

                chrome.runtime.onMessage.removeListener(listener);
                chrome.windows.onRemoved.removeListener(closedListener);

                console.log(
                  '[Background] - ' +
                    getHrTimestamp() +
                    ' - Resuming scan interval after manual close',
                );
                runScans();

                resolve('Closed Without Action');
              }
            };

            chrome.runtime.onMessage.addListener(listener);
            chrome.windows.onRemoved.addListener(closedListener);
          },
        );
      });
    });
  });
}

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'local') {
    if (
      changes.classification &&
      changes.classification.newValue.split('_')[0] === 'malicious'
    ) {
      (async () => {
        let result = await showBrowserNotification();

        console.log(
          `[Background] - ${getHrTimestamp()} - User action received: ${result}. `,
        );

        chrome.storage.local.get(
          ['phash', 'classification', 'currentDomain'],
          (result) => {
            saveScreenshot(
              ssDataUrlRaw,
              `${mainExtDownloadDir}/${sessionStartTimeHr}/${
                result.classification.split('_')[0]
              }`,
              `${currentDomain}_${result.phash}_${getHrTimestamp()}`,
            );
          },
        );
      })();

      return;
    }
    if (
      changes.classification &&
      changes.classification.newValue.split('_')[0] === 'benign'
    ) {
      (async () => {
        chrome.storage.local.get(
          ['phash', 'classification', 'currentDomain'],
          (result) => {
            saveScreenshot(
              ssDataUrlRaw,
              `${mainExtDownloadDir}/${sessionStartTimeHr}/${
                result.classification.split('_')[0]
              }`,
              `${currentDomain}_${result.phash}_${getHrTimestamp()}`,
            );
          },
        );
      })();

      return;
    }
  }
});

function captureScreenshot() {
  console.log(
    '[Background] - ' +
      getHrTimestamp() +
      ' - Attempting to capture screenshot...',
  );

  return new Promise((resolve, reject) => {
    chrome.tabs.captureVisibleTab(null, { format: 'png' }, (dataUrl) => {
      if (chrome.runtime.lastError || !dataUrl) {
        console.error(
          '[Background] Error capturing screenshot:',
          chrome.runtime.lastError,
        );
        reject(chrome.runtime.lastError);
        return;
      }

      console.log(
        '[Background] - ' + getHrTimestamp() + ' - Screenshot captured.',
      );
      resolve(dataUrl);
    });
  });
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
  return new Promise((resolve, reject) => {
    if (!offscreenPort) {
      console.warn(
        '[Background] - ' +
          getHrTimestamp() +
          ' - offscreen not connected to receive the screenshot.',
      );
      return reject(new Error('Offscreen port not connected'));
    }

    function listenForInfCompletion(changes, areaName) {
      if (areaName !== 'local') return;

      if (changes.infFlag && changes.infFlag.newValue === 'complete') {
        console.log(
          `[Background] - ${getHrTimestamp()} - Inference complete (via storage).`,
        );
        chrome.storage.onChanged.removeListener(listenForInfCompletion);
        resolve(true);
      }
    }
    chrome.storage.onChanged.addListener(listenForInfCompletion);

    // Set running flag
    chrome.storage.local.set({ infFlag: `running` });

    console.log(
      '[Background] - ' +
        getHrTimestamp() +
        ' - Sending raw screenshot data url to offscreen.',
    );
    offscreenPort.postMessage({ type: 'ssDataUrlRaw', data });
  });
}

function getCurrentTabDomain(callback) {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length === 0) {
      callback(null); // No active tab found
      return;
    }
    const url = new URL(tabs[0].url);
    const domain = parse(url.hostname).domain;
    callback(domain);
  });
}

async function startInference() {
  // Capturing screenshot
  const startTakeSsTime = Date.now();
  ssDataUrlRaw = await captureScreenshot();
  await setToStorage({ ssDataUrlRaw });
  const takeSsTime = Date.now() - startTakeSsTime;
  console.log(
    `[Background] - ${getHrTimestamp()} - Time to take screenshot: ${takeSsTime} ms`,
  );
  logMessage(`[Background] - screenshot capture time: ${takeSsTime} ms`);

  // Computing phash
  const phashStartTime = Date.now();
  const phashNew = await getImagePHash(ssDataUrlRaw);
  const phashTotalTime = Date.now() - phashStartTime;
  console.log(
    `[Background] - ${getHrTimestamp()} - Time to phash: ${phashTotalTime} ms`,
  );
  logMessage(`[Background] - phash computation time: ${phashTotalTime} ms`);

  // Selecting appropriate case
  const result = await getFromStorage(['phash', 'classification']);
  const phashCurrent = result.phash;

  console.log(
    `[Background] - ${getHrTimestamp()} - Retrieved phash value: ${phashCurrent}`,
  );

  if (phashCurrent === null || phashCurrent === 'NA') {
    // CASE 2 - No phash
    pureAllInfStartTime = Date.now();
    await sendSsDataToOffscreen(ssDataUrlRaw);
    await setToStorage({ phash: phashNew, hammingDistance: null });
  } else {
    const hammingDistance = getHammingDistance(phashCurrent, phashNew);

    if (hammingDistance >= HAMMING_DIST_THOLD) {
      // CASE 3 - HD > threshold
      pureAllInfStartTime = Date.now();
      await sendSsDataToOffscreen(ssDataUrlRaw);
      await setToStorage({ phash: phashNew, hammingDistance });
      console.log(
        `[Background] - ${getHrTimestamp()} - Updated local storage: Phash greater than threshold`,
      );
    } else {
      // CASE 4 - phash < threshold
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
      await setToStorage(case4Data);

      const { classification } = await getFromStorage([
        'phash',
        'classification',
      ]);
      saveScreenshot(
        ssDataUrlRaw,
        `${mainExtDownloadDir}/${sessionStartTimeHr}/${
          classification.split('_')[0]
        }`,
        `${currentDomain}_${phashNew}_${getHrTimestamp()}`,
      );
    }
  }
}

////// DRIVERS

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (changes.offscreenInitialized || changes.backgroundInitialized) {
    chrome.storage.local.get(
      ['offscreenInitialized', 'backgroundInitialized'],
      (result) => {
        if (result.offscreenInitialized && result.backgroundInitialized) {
          let initTotalTime = Date.now() - sessionStartTime;
          console.log(
            `[Background] - ${getHrTimestamp()} - Initialization completed in ${initTotalTime} ms`,
          );
          logMessage(
            `[Background] - initialization completion time: ${initTotalTime} ms`,
          );
          runScans();
        }
      },
    );
    return;
  }
});

function getCurrentTabDomainPromise() {
  return new Promise((resolve) => {
    getCurrentTabDomain((domain) => {
      resolve(domain);
    });
  });
}

async function runSingleScan() {
  const { mainToggleState, ssToggleState } = await chrome.storage.local.get([
    'mainToggleState',
    'ssToggleState',
  ]);

  if (!mainToggleState) {
    console.log(`[Background] - ${getHrTimestamp()} - Toggle is OFF.`);
    return;
  }

  console.log(`[Background] - ${getHrTimestamp()} - Toggle is ON.`);

  scanStartTime = Date.now();

  const domain = await getCurrentTabDomainPromise(); // use a promise version
  currentDomain = domain;

  if (trancoSet.has(domain)) {
    console.log(
      `[Background] - ${getHrTimestamp()} - Domain in Tranco set: ${domain}`,
    );

    const case1TotalTime = Date.now() - scanStartTime;

    const case1Data = {
      resizedDataUrl: 'NA',
      classification: `benign_${getHrTimestamp()}`,
      method: `Tranco whitelist - ${domain}`,
      infTime: 'NA',
      ocrText: 'NA',
      ocrTime: 'NA',
      phash: 'NA',
      hammingDistance: 'NA',
      totalTime: case1TotalTime,
    };

    await chrome.storage.local.set(case1Data);

    console.log(
      `[Background] - ${getHrTimestamp()} - Case 1 scan complete in ${case1TotalTime} ms`,
    );
    logMessage(`[Background] - case 1 total time: ${case1TotalTime} ms`);

    if (ssToggleState) {
      const screenshot = await captureScreenshot();
      saveScreenshot(
        screenshot,
        `${mainExtDownloadDir}/${sessionStartTimeHr}/benign`,
        `${domain}_wl_${getHrTimestamp()}`,
      );
    }
  } else {
    console.log(
      `[Background] - ${getHrTimestamp()} - Domain NOT in Tranco set.`,
    );
    await startInference();
  }
}

function runScans() {
  if (scanIntId) {
    console.log(
      '[Background] - ' +
        getHrTimestamp() +
        ' - Scan interval already running. Skipping start.',
    );
    return; // Already scanning
  }
  scanIntId = setInterval(async () => {
    if (isScanning) {
      console.log(
        '[Background] - ' +
          getHrTimestamp() +
          ' - Previous scan still running, skipping this cycle.',
      );
      return;
    }
    scanStartTime = Date.now();
    isScanning = true;
    scanId = crypto.randomUUID();

    try {
      console.log(
        `[Background] - ${getHrTimestamp()} - SCAN ${scanId} CYCLE STARTED!`,
      );
      await runSingleScan();
    } catch (err) {
      console.error('runSingleScan error:', err);
    } finally {
      isScanning = false;
      console.log(
        `[Background] - ${getHrTimestamp()} - SCAN ${scanId} CYCLE COMPLETE!`,
      );
    }
  }, SCAN_INTERVAL);
}

// Performance logging
setInterval(() => {
  chrome.storage.local.get(
    ['mainToggleState', 'performanceToggleState'],
    (data) => {
      if (data.performanceToggleState) {
        saveLogsToFile();
      }
    },
  );
}, SAVE_INTERVAL);
