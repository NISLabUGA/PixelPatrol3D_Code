# Pixel Patrol Browser Extention - Chrome

**The web threat detection extension!**

---

## Building the Extension

\*\* **Most people should skip to next section. Only really applies to those directly interesting build the extension form source.** \*\*

### 1. Ensure Node.js is Installed

- Check if Node.js and npm are installed by running:

  ```sh
  node -v
  npm -v
  ```

- if not installed, download and install from https://nodejs.org/en/download

### 2. Install Dependencies

- Install Webpack and Webpack CLI:

  ```sh
  npm install --save-dev webpack webpack-cli

  ```

- If using Babel for ES6+ support, also install:

  ```sh
  npm install --save-dev babel-loader @babel/core @babel/preset-env
  ```

### 3. Navigate to Project Folder

- Open terminal and run

  ```sh
  cd path/to/where/you/pulled/down/the/repo
  ```

### 4. Remove Previous Build (If exists) and Rebuild

- Run the following command:

  ```
  rm -rf dist && npx webpack --mode development
  ```

---

## Loading the Extension

#### 1. You will need a build directory to load into the browser. There are 2 main way to get this file:

1. Download the ZIP file associated with the latest release from the main GitHub page. Unzip the file. This folder is what needs to be loaded into the browser.

2. You can also build the extension from the source code by pulling down the repository and going through the steps in the previous section on building the extension. Once the extension is built, it will generate a dist directory. This is what you will load into the browser!

If you've never loaded an unpacked Chrome extension before, follow these steps:

#### 2. Enable Developer Mode in Chrome

1. Open **Google Chrome** or a Chome based variant.
2. In the address bar, type: "chrome://extensions" and press **Enter**.
3. In the top-right corner of the **Extensions** page, toggle on **Developer mode**.

#### 3. Load the Unpacked Extension

1. Click the **"Load unpacked"** button.
2. In the file picker, navigate to the folder containing your unpacked extension (the root directory with `manifest.json`).
3. Select the folder and click **Open**.

#### 4. Verify That the Extension Is Loaded

- The extension should now appear in the list of installed extensions.
- If the extension has an icon, it will also appear in the Chrome toolbar.
- If the extension needs permissions, click **"Allow"** when prompted.

#### 5. Troubleshooting

- **Extension not working:** Click **"Inspect views"** under the extension name to check for console errors.
- **Not appearing in toolbar:** Click the puzzle piece 🧩 (extensions icon) and pin it.

---

## Using the Extension

Once the extension is loaded in the browser you simply have to toggle the main button (largest button to the left under the popup title and description that reads "ON" or "OFF"). The extension will then scan as you browser at regular intervals to detect potential threats. If you have any issues or the extension hangs for whatever reason, try resetting the extension to default by clicking the "RESET" button to the right off the main toggle described above. This will reset the extension to the initial as if it was freshly loaded.

\*\* **NOTE** \*\* The extension has performance logging enabled by default to capture the initialization performance metrics. However, if you do not want this functionality you will need to manually disble it by toggling the associated button to off.

If the extension does find any potential threats, it will alert you by injecting a transparent overlay onto the webpage. This will keep you from moving forward in browsing to potentially harmful content until you interact with the overlay. There are 3 options:

1. `Ignore Warning` - this is the button to select if you want to accept the risk and continue browsing. Any logged screenshots will be marked as "malicious" and saved in the corresponding directory.

2. `X (Close Button)` - this button is essentially the same as Ignore Warning above. Just added for extra convience. Any logged screenshots will be marked as "malicious" and saved in the corresponding directory.

3. `Return to Safety` - this button will navigate you back to safety. For now it just take you back to google.com. Any logged screenshots will be marked as "malicious" and saved in the corresponding directory.

4. `Not Malicious` - this button means that the extension has made a mistake and the page should not have been flagged as malicous. This will change the screenshot designation to "fp" for false positive and will be saved in the corresponding directory.

### Logging

1. Performance Logging

   1. When toggled on this collects the time in ms associated with all major part of the application. It is meant to find potential bottlenecks and better understand usability and latency.

   1. Logs are collected and saved in bulk every 30 seconds

   1. Output path: `Downloads/pp_ext/<session_start_timestamp>/logs/`

1. SS (Screenshot) Logging

   1. When toggle on this collects webpage screenshots. This is mean to aid in collecting samples for model retraining and debugging.

   1. A screenshot is collected and saved every scan cycle which is normally 5 seconds.

   1. Output path: `Downloads/pp_ext/<session_start_timestamp>/{benign, fp, malicous}/`

      1. Depending on the classification the screenshot will be saved to the corresponding directory.

### Setting User Agent

If you wish to change your user agent to perhaps try to find new or different social engineering attack type and reduce the likelyhood of browser fingerprinting, that is an option. The extension uses your native user agent string. However, you can use the dropdown box to the right of "User Agent" to select from many common User Agent strings.
