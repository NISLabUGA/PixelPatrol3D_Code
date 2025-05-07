# Pixel Patrol Browser Extention - Firefox Mobile (Android)

**The web threat detection extension!**

---

## Building the Extension

\*\* **Most people should skip to next section. Only really applies to those directly interesting build the extension form source.** \*\*

#### 1. Ensure Node.js is Installed

- Check if Node.js and npm are installed by running:

  ```sh
  node -v
  npm -v
  ```

- if not installed, download and install from https://nodejs.org/en/download

#### 2. Install Dependencies

- Install Webpack and Webpack CLI:

  ```sh
  npm install --save-dev webpack webpack-cli

  ```

- If using Babel for ES6+ support, also install:

  ```sh
  npm install --save-dev babel-loader @babel/core @babel/preset-env
  ```

#### 3. Navigate to Project Folder

- Open terminal and run

  ```sh
  cd path/to/where/you/pulled/down/the/repo
  ```

#### 4. Remove Previous Build (If exists) and Rebuild

- Run the following command:

  ```
  rm -rf dist && npx webpack --mode development
  ```

---

## Loading the Extension From Mozilla Add Ons

1. Open Firefox and navigate to the following url:

https://addons.mozilla.org/en-US/firefox/addon/pixel-patrol-mobile-public/

2. Select the `Add to Firefox` button

---

## Loading the Extension From Source on Firefox Mobile (Android)

This section outlines how to sideload the extension on Firefox Nightly for Android using USB debugging and `web-ext`.

#### Accessing Source Code

1. You will need a build directory to load into the browser. There are 2 main ways to get this:
   Download the ZIP file associated with the latest release from the main GitHub page. Unzip the file — this folder is what you'll load into Firefox.

2. Build from source: Pull down the repository and follow the steps in the previous section to build the extension. Once the build is complete, it will generate a dist directory. This is what you'll load into Firefox.

> ⚠️ This process is intended for **development and testing only**. Extensions sideloaded this way are not persistently installed — they will disappear after the app is restarted.

#### On Your Android Device

1. **Install Firefox Nightly** from the Google Play Store.
2. **Enable Developer Options:**
   - Open your device **Settings** → **About phone**
   - Tap **Build number** 7 times to enable Developer Mode.
3. **Disable Auto Blocker (optional but recommended):**
   - Go to **Settings** → **Security & privacy** → turn off **Auto Blocker**.
4. **Enable USB Debugging:**
   - Go to **Settings** → **System** → **Developer options** → turn on **USB debugging**.
5. **Enable Remote Debugging in Firefox:**
   - Open Firefox Nightly → Go to **Settings**
   - Enable **Remote debugging via USB**
   - (Optional) Enable **External download manager** for easier file handling

#### On Your Laptop

1. **Install the required tools:**
   ```bash
   sudo apt install android-platform-tools  # or brew install android-platform-tools on macOS
   npm install --global web-ext
   ```
2. **Enable ADB connection:**
   - Connect your phone to your laptop via USB
   - In a terminal, check connection:
     ```bash
     adb devices
     ```
     You should see your device listed.
3. **Run the extension on Firefox Android:**

   ```bash
   web-ext run -t firefox-android \
     --adb-device YOUR_DEVICE_ID \
     --firefox-apk org.mozilla.fenix
   ```

   Replace `YOUR_DEVICE_ID` with the actual ID shown from `adb devices` (e.g., `R5CY22R195N`).

4. **Wait for it to install and launch automatically** in Firefox Nightly on your phone.

#### Verifying the Extension

- Once the extension is loaded, it should appear in Firefox Nightly’s extension menu (three dots → **Add-ons**).
- You can test it just like on desktop — including browser actions, permissions, and content scripts.

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
