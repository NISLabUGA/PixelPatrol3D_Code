const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });  // Keep browser open and visible
  const page = await browser.newPage();

  await page.goto('https://google.com');

  var x = 100
  var y = 100

  await page.evaluate((x, y) => {
    const dot = document.createElement('div');
    dot.style.position = 'absolute';
    dot.style.left = `${x + window.scrollX - 5}px`;
    dot.style.top = `${y + window.scrollY - 5}px`;
    dot.style.width = '10px';
    dot.style.height = '10px';
    dot.style.backgroundColor = 'red';
    dot.style.borderRadius = '50%';
    dot.style.zIndex = '9999';
    document.body.appendChild(dot);
    setTimeout(() => {
        dot.remove();
    }, 3000); // Removes the dot after 3 seconds
}, x, y);


// Simulate the mouse movement and click in Puppeteer
await page.mouse.move(x, y);
await page.waitForTimeout(100); // Optional delay for visibility
await page.mouse.down();
await page.waitForTimeout(100);
await page.mouse.up();



  // Keep the browser open for a while to see the result
  await page.waitForTimeout(10000);

  await browser.close();
})();
