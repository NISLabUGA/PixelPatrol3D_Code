// src/offscreen.js

// Global Variables

let offscreenStartTime = Date.now();

const IMG_SIZE = { width: 1920, height: 1080 };
const IMG_PROC_SCALE_FACTOR = 0.5;
const IMG_OCR_SCALE_FACTOR = 0.5;
const MAX_TOKEN_LENGTH = 512;

console.log(
  '[Offscreen] - ' + getHrTimestamp() + ' - Offscreen document loaded.',
);

// Imports

import { AutoTokenizer } from '@xenova/transformers';
import { getHrTimestamp } from './utils';

document.addEventListener('DOMContentLoaded', async () => {
  const sandboxIframe = document.getElementById('sandboxIframe');
  if (!sandboxIframe) {
    console.error('[Offscreen] - sandboxIframe not found in DOM.');
    return;
  }

  // Open a long-lived offscreenPort to the background script.
  const offscreenPort = chrome.runtime.connect({ name: 'offscreenPort' });

  // Initialize the ONNX worker.
  let onnxWorker;
  let onnxWorkerStartTime = Date.now();
  let onnxWorkerTotalTime = null;
  try {
    onnxWorker = new Worker(chrome.runtime.getURL('onnx_worker.js'), {
      type: 'module',
    });
  } catch (err) {
    console.error('[Offscreen] Error instantiating ONNX worker:', err);
  }

  await new Promise((resolve) => {
    onnxWorker.onmessage = (event) => {
      if (event.data.type === 'onnxWorkInitialized') {
        resolve();
        onnxWorkerTotalTime = Date.now() - onnxWorkerStartTime;
        console.log(
          `[Offscreen] - ${getHrTimestamp()} - ONNX worker instantiated in ${onnxWorkerTotalTime} ms.`,
        );
      }
    };
  });

  // Initialize the tokenizer.
  let tokenizer;
  let tokenizerStartTime = Date.now();
  let tokenizerTotalTime = null;
  try {
    tokenizer = await AutoTokenizer.from_pretrained('bert_mini_tokenizer');
    tokenizerTotalTime = Date.now() - tokenizerStartTime;
    console.log(
      `[Offscreen] - ${getHrTimestamp()} - Tokenizer loaded in ${tokenizerTotalTime} ms.`,
    );
  } catch (err) {
    console.error('[Offscreen] Error loading tokenizer:', err);
  }

  let ocrTotalTime = null;
  const waitForOcrInit = new Promise((resolve) => {
    function handleOcrInit(event) {
      if (event.data.type === 'ocrInit') {
        ocrTotalTime = event.data.message;
        console.log(
          `[Offscreen] - ${getHrTimestamp()} - OCR initialized in ${ocrTotalTime} ms.`,
        );
        window.removeEventListener('message', handleOcrInit);
        resolve();
      }
    }
    window.addEventListener('message', handleOcrInit);
  });
  await waitForOcrInit;

  let offscreenInitTotalTime = Date.now() - offscreenStartTime;
  // Now that all initialization steps are complete, send the offscreenInit message.
  offscreenPort.postMessage({
    type: 'offscreenInit',
    data: {
      onnxInitTime: onnxWorkerTotalTime,
      tokenizerInitTime: tokenizerTotalTime,
      ocrInitTime: ocrTotalTime,
      offscreenInitTime: offscreenInitTotalTime,
    },
  });

  // Functions

  // Image resize function
  async function resizeImage(dataUrl, scaleFactor) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const newWidth = img.width * scaleFactor;
        const newHeight = img.height * scaleFactor;
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        canvas.width = newWidth;
        canvas.height = newHeight;
        ctx.drawImage(img, 0, 0, newWidth, newHeight);

        resolve(canvas.toDataURL('image/png'));
      };
      img.onerror = reject;
      img.src = dataUrl; // Set the image source
    });
  }

  // Process the screenshot image to create an image tensor.
  async function processImage(dataUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        console.log(
          '[Offscreen] - ' +
            getHrTimestamp() +
            ' - Image loaded for processing.',
        );
        const origWidth = img.naturalWidth;
        const origHeight = img.naturalHeight;
        const targetLongest = Math.max(IMG_SIZE.width, IMG_SIZE.height);
        const origLongest = Math.max(origWidth, origHeight);
        let intermediateWidth, intermediateHeight;
        if (origLongest > targetLongest) {
          const scaleDownFactor = targetLongest / origLongest;
          intermediateWidth = Math.round(origWidth * scaleDownFactor);
          intermediateHeight = Math.round(origHeight * scaleDownFactor);
        } else {
          intermediateWidth = origWidth;
          intermediateHeight = origHeight;
        }

        // Resize the image.
        const resizeCanvas = document.createElement('canvas');
        resizeCanvas.width = intermediateWidth;
        resizeCanvas.height = intermediateHeight;
        const resizeCtx = resizeCanvas.getContext('2d');
        resizeCtx.drawImage(img, 0, 0, intermediateWidth, intermediateHeight);

        // Pad the image.
        const paddedCanvas = document.createElement('canvas');
        paddedCanvas.width = IMG_SIZE.width;
        paddedCanvas.height = IMG_SIZE.height;
        const paddedCtx = paddedCanvas.getContext('2d');
        paddedCtx.fillStyle = 'black';
        paddedCtx.fillRect(0, 0, IMG_SIZE.width, IMG_SIZE.height);
        const padX = Math.floor((IMG_SIZE.width - intermediateWidth) / 2);
        const padY = Math.floor((IMG_SIZE.height - intermediateHeight) / 2);
        paddedCtx.drawImage(
          resizeCanvas,
          padX,
          padY,
          intermediateWidth,
          intermediateHeight,
        );

        // Scale the padded image.
        const finalWidth = Math.round(IMG_SIZE.width * IMG_PROC_SCALE_FACTOR);
        const finalHeight = Math.round(IMG_SIZE.height * IMG_PROC_SCALE_FACTOR);
        const finalCanvas = document.createElement('canvas');
        finalCanvas.width = finalWidth;
        finalCanvas.height = finalHeight;
        const finalCtx = finalCanvas.getContext('2d');
        finalCtx.drawImage(paddedCanvas, 0, 0, finalWidth, finalHeight);

        // Create the image tensor.
        const imageData = finalCtx.getImageData(0, 0, finalWidth, finalHeight);
        const { data } = imageData;
        const numPixels = finalWidth * finalHeight;
        const floatData = new Float32Array(numPixels * 3);
        let j = 0;
        for (let i = 0; i < data.length; i += 4) {
          floatData[j++] = data[i] / 255.0;
          floatData[j++] = data[i + 1] / 255.0;
          floatData[j++] = data[i + 2] / 255.0;
        }
        // Transpose from [H, W, 3] to [1, 3, W, H].
        const transposed = new Float32Array(3 * numPixels);
        for (let r = 0; r < finalHeight; r++) {
          for (let c = 0; c < finalWidth; c++) {
            for (let ch = 0; ch < 3; ch++) {
              const srcIndex = (r * finalWidth + c) * 3 + ch;
              const destIndex =
                ch * (finalWidth * finalHeight) + c * finalHeight + r;
              transposed[destIndex] = floatData[srcIndex];
            }
          }
        }
        const imageTensor = {
          data: transposed.buffer,
          dims: [1, 3, finalWidth, finalHeight],
        };
        resolve({ imageTensor, resizedDataUrl: finalCanvas.toDataURL() });
      };
      img.onerror = (err) => reject(err);
      img.src = dataUrl;
    });
  }

  async function runInference(ssDataUrlRaw) {
    if (!sandboxIframe || !sandboxIframe.contentWindow) {
      throw new Error('Sandbox iframe not available');
    }

    // Start processing the image and the iframe request at the same time
    const processImagePromise = processImage(ssDataUrlRaw);

    const ssDataUrlResized = await resizeImage(
      ssDataUrlRaw,
      IMG_OCR_SCALE_FACTOR,
    );
    // const ssDataUrlResized = structuredClone(ssDataUrlRaw);

    const ocrRequestPromise = new Promise((resolve, reject) => {
      const messageId = Math.random().toString(36).substring(7); // Unique ID for tracking responses

      function handleMessage(event) {
        if (event.source !== sandboxIframe.contentWindow) return; // Ensure message comes from the expected iframe
        if (!event.data || event.data.messageId !== messageId) return; // Ensure correct message response

        window.removeEventListener('message', handleMessage); // Cleanup event listener
        resolve(event.data.response); // Resolve the promise with iframe's response
      }

      window.addEventListener('message', handleMessage);

      sandboxIframe.contentWindow.postMessage(
        {
          type: 'ssDataUrlRaw',
          dataUrl: ssDataUrlResized,
          messageId,
        },
        '*',
      );
    });

    // Wait for both promises to resolve
    const [ssDataProcessed, ocrResponse] = await Promise.all([
      processImagePromise,
      ocrRequestPromise,
    ]);

    // Tokenize OCR text

    const startTokenTime = Date.now();
    const tokenized = await tokenizer(ocrResponse.text, {
      truncation: true,
      padding: 'max_length',
      max_length: MAX_TOKEN_LENGTH,
    });
    const endTokenTime = Date.now();
    const tokenTime = endTokenTime - startTokenTime;
    console.log(
      '[Offscreen] - ' +
        getHrTimestamp() +
        ' - Time to tokenize OCR text: ' +
        tokenTime +
        ' ms',
    );

    // Build payload using transferable buffers.
    const inputIdsBuffer = tokenized.input_ids.data.buffer; // Assumed to be an ArrayBuffer or use .buffer if needed
    const attentionMaskBuffer = tokenized.attention_mask.data.buffer; // Likewise

    // Build payload using transferable ArrayBuffers:
    const payload = {
      imageTensor: {
        data: ssDataProcessed.imageTensor.data,
        dims: ssDataProcessed.imageTensor.dims,
      },
      input_ids: inputIdsBuffer,
      attention_mask: attentionMaskBuffer,
    };

    // Send the payload to the ONNX worker and await its response.
    const inferenceResponse = await new Promise((resolve, reject) => {
      onnxWorker.onmessage = (event) => {
        resolve(event.data);
      };
      onnxWorker.onerror = (err) => {
        reject(err);
      };
      onnxWorker.postMessage(
        {
          type: 'runInference',
          payload: payload,
        },
        [ssDataProcessed.imageTensor.data, inputIdsBuffer, attentionMaskBuffer],
      );
    });

    console.log(
      '[Offscreen] - ' +
        getHrTimestamp() +
        ' - Inference result from ONNX worker:',
      inferenceResponse,
    );

    let resizedDataUrl = ssDataProcessed.resizedDataUrl;
    let classification = inferenceResponse.classification;
    let infTime = inferenceResponse.onnxInferenceTime;
    let ocrText = ocrResponse.text;
    let ocrTime = ocrResponse.ocrTime;

    let data = { resizedDataUrl, classification, infTime, ocrText, ocrTime };

    offscreenPort.postMessage({ type: 'infResponse', data });
  }

  // Listen for messages from background.js
  offscreenPort.onMessage.addListener((message) => {
    if (message.type === 'ssDataUrlRaw') {
      console.log(
        '[Offscreen] - ' + getHrTimestamp() + ' - Received screenshot.',
        message,
      );
      runInference(message.data);
    }
  });
});
