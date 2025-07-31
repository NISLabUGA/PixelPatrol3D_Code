import { getHrTimestamp } from './utils.js';

// Retrieve the screenshot from local storage and display it
const { ssDataUrlRaw } = await browser.storage.local.get('ssDataUrlRaw');
console.log('ssDataUrlRaw', ssDataUrlRaw);

const img = document.getElementById('screenshot');
if (ssDataUrlRaw && ssDataUrlRaw !== 'NA') {
  img.src = ssDataUrlRaw;
  img.style.display = 'block';
}

// Send user action back to background
async function sendUserAction(action) {
  await browser.runtime.sendMessage({
    type: 'userActionComplete',
    result: `${action}`,
  });
}

// Wire up the buttons
document.getElementById('return').addEventListener('click', async () => {
  console.log(
    `[Notification] - ${getHrTimestamp()} - Return to Safety button clicked, navigating to https://google.com`,
  );
  await sendUserAction('Return to Safety');
});

document.getElementById('ignore').addEventListener('click', async () => {
  console.log(
    `[Notification] - ${getHrTimestamp()} - Ignore Warning button clicked, continuing on page`,
  );
  await sendUserAction('Ignore Warning');
});

document.getElementById('override').addEventListener('click', async () => {
  console.log(
    `[Notification] - ${getHrTimestamp()} - Not Malicious button clicked, overriding alert`,
  );

  const { classification } = await browser.storage.local.get('classification');
  if (classification && classification.includes('_')) {
    const ts = classification.split('_')[1];
    await browser.storage.local.set({ classification: `fp_${ts}` });
  }

  await sendUserAction('Not Malicious');
});
