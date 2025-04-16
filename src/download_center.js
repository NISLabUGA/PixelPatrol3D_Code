import JSZip from 'https://cdn.jsdelivr.net/npm/jszip@3.10.1/+esm';
import { getHrTimestamp } from './utils.js';

const portReady = new Promise((res) => {
  browser.runtime.sendMessage({ type: 'requestBuffers' });
  browser.runtime.onMessage.addListener(function handler(msg) {
    if (msg.type !== 'buffers') return;
    browser.runtime.onMessage.removeListener(handler);
    res(msg);
  });
});

const filesDiv = document.getElementById('files');
const zip = new JSZip();
let perfBlob;

function dataUrlToBlob(dataUrl) {
  const [header, base64] = dataUrl.split(',');
  const mimeMatch = header.match(/data:(.*);base64/);
  const mime = mimeMatch ? mimeMatch[1] : 'application/octet-stream';
  const binary = atob(base64);
  const array = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new Blob([array], { type: mime });
}

portReady.then(({ perfText, screenshots }) => {
  if (perfText && perfText.trim()) {
    perfBlob = new Blob([perfText], { type: 'text/plain' });
    const url = URL.createObjectURL(perfBlob);
    addLink('performance_logs.txt', url);
    zip.file('performance_logs.txt', perfText);
  }

  screenshots.forEach(({ name, dataUrl }) => {
    if (!dataUrl) {
      console.warn(`Skipping invalid screenshot: ${name} (dataUrl is null)`);
      return;
    }

    try {
      const blob = dataUrlToBlob(dataUrl);
      const url = URL.createObjectURL(blob);
      const filename = name.split('/').pop();

      addLink(filename, url);
      zip.file(filename, blob);
    } catch (e) {
      console.error('Error processing screenshot:', name, e);
    }
  });
});

function addLink(name, url) {
  const a = document.createElement('a');
  a.textContent = name;
  a.href = url;
  a.download = name;
  a.className = 'file';
  filesDiv.appendChild(a);
  filesDiv.appendChild(document.createElement('br'));
}

document.getElementById('dl').onclick = async () => {
  try {
    const blob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(blob);

    const timestamp = getHrTimestamp();
    const fullPath = `pp_ext/${timestamp}.zip`;

    const a = document.createElement('a');
    a.href = url;
    a.download = fullPath;
    a.click();

    browser.runtime.sendMessage({ type: 'downloadComplete' });
  } catch (e) {
    console.error('Error generating ZIP:', e);
  }
};

document.getElementById('dismiss').onclick = () => {
  browser.runtime.sendMessage({ type: 'dismiss' });
  window.close();
};
