// src/popup.js

import { getHrTimestamp } from './utils';

document.addEventListener('DOMContentLoaded', () => {
  // Connecting for port messaging (if needed for other communication)
  const popupPort = chrome.runtime.connect({ name: 'popup' });

  console.log('[Popup] - ' + getHrTimestamp() + ' - Popup loaded.');
  const screenshotEl = document.getElementById('screenshot');
  const phashEl = document.getElementById('phash');
  const hammingDistanceEl = document.getElementById('hammingDistance');
  const ocrTextEl = document.getElementById('ocrText');
  const classificationEl = document.getElementById('classification');
  const methodEl = document.getElementById('method');
  const onnxInferenceTimeEl = document.getElementById('onnxInferenceTime');
  const totalTimeEl = document.getElementById('totalTime');
  const mainToggle = document.getElementById('mainToggle');
  const resetButton = document.getElementById('resetButton');
  const ocrTimeEl = document.getElementById('ocrTime');
  const ssLoggingToggle = document.getElementById('ssLoggingToggle');
  const performanceLoggingToggle = document.getElementById(
    'performanceLoggingToggle',
  );
  const userAgentSelect = document.getElementById('userAgentSelect');

  ////// User Agent Strings

  const USER_AGENT_STRINGS = {
    default: 'default',
    chrome_android_mobile:
      'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
    chrome_android_tablet:
      'Mozilla/5.0 (Linux; Android 4.3; Nexus 7 Build/JSS15Q) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    chrome_iphone:
      'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/134.0.0.0 Mobile/15E148 Safari/604.1',
    chrome_ipad:
      'Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/134.0.0.0 Mobile/15E148 Safari/604.1',
    chrome_chrome_os:
      'Mozilla/5.0 (X11; CrOS x86_64 10066.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    chrome_mac:
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    chrome_windows:
      'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    firefox_android_mobile:
      'Mozilla/5.0 (Android 4.4; Mobile; rv:70.0) Gecko/70.0 Firefox/70.0',
    firefox_android_tablet:
      'Mozilla/5.0 (Android 4.4; Tablet; rv:70.0) Gecko/70.0 Firefox/70.0',
    firefox_iphone:
      'Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0 Mobile/12F69 Safari/600.1.4',
    firefox_ipad:
      'Mozilla/5.0 (iPad; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) FxiOS/1.0 Mobile/12F69 Safari/600.1.4',
    firefox_mac:
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:70.0) Gecko/20100101 Firefox/70.0',
    firefox_windows:
      'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:70.0) Gecko/20100101 Firefox/70.0',
    edge_windows:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.100.0',
    edge_mac:
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/604.1 Edg/134.0.100.0',
    edge_iphone:
      'Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 EdgiOS/44.5.0.10 Mobile/15E148 Safari/604.1',
    edge_ipad:
      'Mozilla/5.0 (iPad; CPU OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 EdgiOS/44.5.2 Mobile/15E148 Safari/605.1.15',
    edge_android_mobile:
      'Mozilla/5.0 (Linux; Android 8.1.0; Pixel Build/OPM4.171019.021.D1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36 EdgA/42.0.0.2057',
    edge_android_tablet:
      'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 7 Build/MOB30X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 EdgA/42.0.0.2057',
    opera_mac:
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 OPR/65.0.3467.48',
    opera_windows:
      'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 OPR/65.0.3467.48',
    opera_android_mobile:
      'Opera/12.02 (Android 4.1; Linux; Opera Mobi/ADR-1111101157; U; en-US) Presto/2.9.201 Version/12.02',
    opera_iphone:
      'Opera/9.80 (iPhone; Opera Mini/8.0.0/34.2336; U; en) Presto/2.8.119 Version/11.10',
    safari_ipad:
      'Mozilla/5.0 (iPad; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
    safari_iphone:
      'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
    safari_mac:
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15',
  };

  ////// Main Toggle

  // Initialize the main toggle state
  chrome.storage.local.get('mainToggleState', (data) => {
    updateToggleButton(data.mainToggleState ?? false);
  });

  // Event listener for main toggle button
  mainToggle.addEventListener('click', () => {
    chrome.storage.local.get('mainToggleState', (data) => {
      const newState = !data.mainToggleState;
      chrome.storage.local.set({ mainToggleState: newState }, () => {
        updateToggleButton(newState);
        console.log(
          '[Popup] - ' + getHrTimestamp() + ' - Toggle state updated:',
          newState,
        );
      });
    });
  });

  // Update function for main toggle
  function updateToggleButton(isOn) {
    mainToggle.textContent = isOn ? 'ON' : 'OFF';
    mainToggle.classList.remove('on', 'off');
    mainToggle.classList.add(isOn ? 'on' : 'off');
    console.log(
      '[Popup] - ' + getHrTimestamp() + ' - Toggle button updated:',
      isOn,
    );
  }

  ////// Reset Button

  resetButton.addEventListener('click', () => {
    chrome.runtime.sendMessage({
      type: 'resetExtension',
    });
  });

  ////// SS Logging Toggle

  // Initialize the SS Logging state
  chrome.storage.local.get('ssToggleState', (data) => {
    updateSsLoggingToggle(data.ssToggleState ?? false);
  });

  // Event listener for SS Logging toggle button
  ssLoggingToggle.addEventListener('click', () => {
    chrome.storage.local.get('ssToggleState', (data) => {
      const newState = !data.ssToggleState;
      chrome.storage.local.set({ ssToggleState: newState }, () => {
        updateSsLoggingToggle(newState);
        console.log(
          '[Popup] - ' + getHrTimestamp() + ' - SS Logging state updated:',
          newState,
        );
      });
    });
  });

  // Update function for SS Logging toggle
  function updateSsLoggingToggle(isOn) {
    ssLoggingToggle.textContent = isOn ? 'ON' : 'OFF';
    ssLoggingToggle.classList.remove('on', 'off');
    ssLoggingToggle.classList.add(isOn ? 'on' : 'off');
    console.log(
      '[Popup] - ' + getHrTimestamp() + ' - SS Logging button updated:',
      isOn,
    );
  }

  ////// Performance Logging

  // Initialize the Performance Logging state
  chrome.storage.local.get('performanceToggleState', (data) => {
    updatePerformanceLoggingToggle(data.performanceToggleState ?? true);
  });

  // Event listener for Performance Logging toggle button
  performanceLoggingToggle.addEventListener('click', () => {
    chrome.storage.local.get('performanceToggleState', (data) => {
      const newState = !data.performanceToggleState;
      chrome.storage.local.set({ performanceToggleState: newState }, () => {
        updatePerformanceLoggingToggle(newState);
        console.log(
          '[Popup] - ' +
            getHrTimestamp() +
            ' - Performance Logging state updated:',
          newState,
        );
      });
    });
  });

  // Update function for performance Logging toggle
  function updatePerformanceLoggingToggle(isOn) {
    performanceLoggingToggle.textContent = isOn ? 'ON' : 'OFF';
    performanceLoggingToggle.classList.remove('on', 'off');
    performanceLoggingToggle.classList.add(isOn ? 'on' : 'off');
    console.log(
      '[Popup] - ' + getHrTimestamp() + ' - SS Logging button updated:',
      isOn,
    );
  }

  ////// User Agent Selection Dropdown

  // Populate user agent options
  for (const key in USER_AGENT_STRINGS) {
    const option = document.createElement('option');
    option.value = key;
    option.textContent = key.replace(/_/g, ' '); // Optional: make it more readable
    userAgentSelect.appendChild(option);
  }

  // Load saved user agent selection
  chrome.storage.local.get('selectedUserAgent', (data) => {
    if (data.selectedUserAgent) {
      userAgentSelect.value = data.selectedUserAgent;
    }
  });

  // Save selection on change
  userAgentSelect.addEventListener('change', () => {
    const selectedKey = userAgentSelect.value;
    const userAgent = USER_AGENT_STRINGS[selectedKey];

    chrome.storage.local.set({
      selectedUserAgent: selectedKey,
      selectedUserAgentString: userAgent,
    });

    console.log(
      '[Popup] - ' + getHrTimestamp() + ' - Selected user agent updated:',
      selectedKey,
      userAgent,
    );
  });

  ////// Populate Popup Info

  function formatTime(value) {
    return value !== null && value !== undefined && value !== 'NA'
      ? `${parseInt(value, 10)} ms`
      : 'NA';
  }

  function formatNonTime(value) {
    return value !== null && value !== undefined && value !== 'NA'
      ? value
      : 'NA';
  }

  // On load, read the local data and update the popup UI.
  chrome.storage.local.get(null, (localData) => {
    if (localData) {
      if (localData.resizedDataUrl) {
        screenshotEl.src = formatNonTime(localData.resizedDataUrl);
      }
      if (localData.phash) {
        phashEl.textContent = formatNonTime(localData.phash);
      }
      if (localData.hammingDistance) {
        hammingDistanceEl.textContent = formatNonTime(
          localData.hammingDistance,
        );
      }
      if (localData.ocrText) {
        ocrTextEl.textContent = formatNonTime(localData.ocrText);
      }
      if (localData.classification) {
        classificationEl.textContent = formatNonTime(localData.classification);
      }
      if (localData.method) {
        methodEl.textContent = formatNonTime(localData.method);
      }
      if (localData.ocrTime) {
        ocrTimeEl.textContent = formatTime(localData.ocrTime);
      }
      if (localData.infTime) {
        onnxInferenceTimeEl.textContent = formatTime(localData.infTime);
      }
      if (localData.totalTime) {
        totalTimeEl.textContent = formatTime(localData.totalTime);
      }
    }
  });

  // Listen for changes in local storage to update the UI in real-time.
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local') {
      if (changes.resizedDataUrl) {
        screenshotEl.src = formatNonTime(changes.resizedDataUrl.newValue);
      }
      if (changes.phash) {
        phashEl.textContent = formatNonTime(changes.phash.newValue);
      }
      if (changes.hammingDistance) {
        hammingDistanceEl.textContent = formatNonTime(
          changes.hammingDistance.newValue,
        );
      }
      if (changes.ocrText) {
        ocrTextEl.textContent = formatNonTime(changes.ocrText.newValue);
      }
      if (changes.classification) {
        classificationEl.textContent = formatNonTime(
          changes.classification.newValue,
        );
      }
      if (changes.method) {
        methodEl.textContent = formatNonTime(changes.method.newValue);
      }
      if (changes.ocrTime) {
        ocrTimeEl.textContent = formatTime(changes.ocrTime.newValue);
      }
      if (changes.infTime) {
        onnxInferenceTimeEl.textContent = formatTime(changes.infTime.newValue);
      }
      if (changes.totalTime) {
        totalTimeEl.textContent = formatTime(changes.totalTime.newValue);
      }
    }
  });
});
