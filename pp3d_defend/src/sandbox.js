// src/sandbox.js

let sandboxStartTime = Date.now();

console.log('[Sandbox] - ' + getHrTimestamp() + ' - Sandbox document loaded.');

import { getHrTimestamp } from './utils';

(async () => {
  try {
    console.log(
      '[Sandbox] - ' +
        getHrTimestamp() +
        ' - Initializing Tesseract scheduler with dynamic grid workers',
    );
    const { createScheduler, createWorker } = Tesseract;

    // Specify how many rows and columns you want.
    const numRows = 4; // Desired number of rows.
    const numCols = 1; // Desired number of columns.
    const totalPieces = numRows * numCols;

    // Create a scheduler and initialize as many workers as pieces.
    const scheduler = createScheduler();
    for (let i = 0; i < totalPieces; i++) {
      const worker = await createWorker('eng');
      scheduler.addWorker(worker);
    }
    console.log(
      `[Sandbox] Scheduler - ${getHrTimestamp()} - initialized with ${totalPieces} workers.`,
    );

    window.parent.postMessage(
      { type: 'ocrInit', message: Date.now() - sandboxStartTime },
      '*',
    );

    // Helper function to crop the image.
    const cropImage = (dataUrl, rectangle) => {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.src = dataUrl;
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = rectangle.width;
          canvas.height = rectangle.height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(
            img,
            rectangle.left,
            rectangle.top,
            rectangle.width,
            rectangle.height,
            0,
            0,
            rectangle.width,
            rectangle.height,
          );
          resolve(canvas.toDataURL());
        };
        img.onerror = (err) => reject(err);
      });
    };

    // Listen for screenshot messages from the parent.
    window.addEventListener('message', async (event) => {
      const message = event.data;
      if (message.type === 'ssDataUrlRaw' && message.dataUrl) {
        console.log(
          '[Sandbox] - ' + getHrTimestamp() + ' - Received screenshot for OCR.',
        );

        let startTime = Date.now();

        // Create an image to determine its dimensions.
        const img = new Image();
        img.src = message.dataUrl;
        img.onload = async () => {
          const width = img.naturalWidth;
          const height = img.naturalHeight;
          console.log(
            '[Sandbox] - ' + getHrTimestamp() + ' - Image dimensions:',
            width,
            height,
          );

          // Calculate piece dimensions.
          const pieceWidth = Math.floor(width / numCols);
          const pieceHeight = Math.floor(height / numRows);

          // Create an array of jobs, each with its grid coordinates.
          let jobs = [];
          for (let row = 0; row < numRows; row++) {
            for (let col = 0; col < numCols; col++) {
              const left = col * pieceWidth;
              const top = row * pieceHeight;
              // Adjust width/height for the last column/row.
              const rectWidth = col === numCols - 1 ? width - left : pieceWidth;
              const rectHeight =
                row === numRows - 1 ? height - top : pieceHeight;
              jobs.push({
                row,
                col,
                rectangle: { left, top, width: rectWidth, height: rectHeight },
              });
            }
          }
          console.log(
            '[Sandbox] - ' + getHrTimestamp() + ' - Defined job rectangles:',
            jobs,
          );

          try {
            // Submit OCR jobs for each cropped piece.
            const jobPromises = jobs.map(async (job) => {
              // Crop the image to get the specific piece.
              const croppedDataUrl = await cropImage(
                message.dataUrl,
                job.rectangle,
              );
              // Submit the cropped image for OCR.
              return scheduler
                .addJob('recognize', croppedDataUrl)
                .then((result) => ({
                  row: job.row,
                  col: job.col,
                  text: result.data.text,
                }));
            });
            const results = await Promise.all(jobPromises);

            // Sort results by row then column.
            results.sort((a, b) => {
              if (a.row === b.row) {
                return a.col - b.col;
              }
              return a.row - b.row;
            });

            // Concatenate the text in row-major order.
            const combinedText = results.map((r) => r.text).join(' ');
            let endTime = Date.now();
            const ocrTime = endTime - startTime;
            console.log(
              '[Sandbox] - ' + getHrTimestamp() + ' - OCR completed for grid:',
              combinedText,
              'Time:',
              ocrTime,
              'ms',
            );

            window.parent.postMessage(
              {
                messageId: event.data.messageId, // Pass along the received messageId.
                response: { text: combinedText, ocrTime },
              },
              '*',
            );
          } catch (jobError) {
            console.error('[Sandbox] Error processing OCR jobs:', jobError);
            window.parent.postMessage(
              { type: 'ocrError', error: jobError.message },
              '*',
            );
          }
        };
        img.onerror = (err) => {
          console.error('[Sandbox] Error loading image for OCR:', err);
          window.parent.postMessage(
            { type: 'ocrError', error: err.message },
            '*',
          );
        };
      }
    });
  } catch (error) {
    console.error('[Sandbox] Error initializing scheduler or workers:', error);
  }
})();
