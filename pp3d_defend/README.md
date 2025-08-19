# PP_Defend: Firefox Desktop Extension

**Real-time browser defense against web behavior manipulation attacks - Firefox Desktop version**

This is the Firefox desktop implementation of the PP_Defend browser extension. For complete project documentation, see the [main PP_Defend README](https://github.com/NISLabUGA/PixelPatrol3D_Code/blob/chrome/pp_defend/README.md) and [PixelPatrol3D project overview](https://github.com/NISLabUGA/PixelPatrol3D_Code/blob/chrome/README.md).

## 🔄 Key Differences from Chrome Version

This Firefox version implements the same core functionality as the Chrome extension but with Firefox-specific adaptations:

### Technical Differences

| Aspect                      | Chrome Version                | Firefox Version                       |
| --------------------------- | ----------------------------- | ------------------------------------- |
| **Manifest**                | Manifest V3                   | Manifest V2                           |
| **API Namespace**           | `chrome.*`                    | `browser.*` (WebExtensions API)       |
| **Background Script**       | Service Worker                | Persistent background script          |
| **Offscreen Processing**    | `chrome.offscreen` API        | Minimized popup window                |
| **User Agent Modification** | `declarativeNetRequest`       | `webRequest` API                      |
| **Installation**            | Persistent unpacked extension | Temporary add-on (reloads on restart) |

### Code Changes Summary

#### Manifest V2 Adaptations (`manifest.json`)

```json
{
  "manifest_version": 2,
  "background": {
    "scripts": ["background.js"],
    "persistent": true
  },
  "permissions": ["webRequest", "webRequestBlocking", "<all_urls>"]
}
```

#### Browser API Usage (`background.js`)

- All `chrome.*` calls replaced with `browser.*`
- Async/await pattern used throughout for better Firefox compatibility
- Promise-based storage and messaging APIs

#### Offscreen Implementation

```javascript
// Firefox: Uses minimized popup window instead of offscreen document
async function ensureOffscreen() {
  const newWindow = await browser.windows.create({
    url: browser.runtime.getURL("offscreen.html"),
    type: "popup",
    focused: false,
    state: "minimized",
  });
  offscreenWindowId = newWindow.id;
}
```

#### User Agent Modification

```javascript
// Firefox: Uses webRequest API instead of declarativeNetRequest
browser.webRequest.onBeforeSendHeaders.addListener(
  modifyUserAgentHeader,
  { urls: ["<all_urls>"], types: ["main_frame"] },
  ["blocking", "requestHeaders"]
);
```

## 🚀 Installation

### Option 1: Mozilla Add-ons (Recommended)

1. Visit: https://addons.mozilla.org/en-US/firefox/addon/pixel-patrol-desktop-public/
2. Click **"Add to Firefox"**
3. Grant required permissions

### Option 2: Development Installation

1. **Build Extension**

   ```bash
   cd pp3d_defend/
   npm install
   rm -rf dist && npx webpack --mode development
   ```

2. **Load in Firefox**
   - Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
   - Click **"Load Temporary Add-on…"**
   - Select `manifest.json` from the `dist/` folder

> ⚠️ **Note**: Temporary extensions are removed when Firefox restarts. You'll need to reload via `about:debugging` after each restart.

## 🔧 Firefox-Specific Features

### Enhanced Error Handling

- Improved async/await error handling for Firefox's Promise-based APIs
- Better memory management for object URLs and blob handling

### Window Management

- Automatic recreation of offscreen windows if closed by user
- Enhanced popup window positioning and sizing

### Download Handling

- Firefox-compatible blob URL creation and cleanup
- Proper object URL revocation to prevent memory leaks

## 🚨 Firefox-Specific Troubleshooting

### Extension Disappears After Restart

**Cause**: Firefox temporary extensions are not persistent
**Solution**: Reload via `about:debugging#/runtime/this-firefox`

### Offscreen Window Visible

**Cause**: Firefox doesn't have true offscreen documents
**Solution**: The minimized popup window is normal behavior - don't close it

### Permission Errors

**Cause**: Firefox has stricter permission handling
**Solution**: Ensure all permissions are granted during installation

### Performance Differences

**Expected**: Firefox version may have slightly different performance characteristics due to API differences

## 🛠️ Development Notes

### Testing Firefox-Specific Code

```bash
# Test in Firefox Developer Edition for better debugging
firefox-developer-edition --new-instance --profile /tmp/ff-test
```

### Debugging

- Use `about:debugging` for extension inspection
- Check Browser Console (`Ctrl+Shift+J`) for background script logs
- Use Web Console (`F12`) for content script debugging

### API Compatibility

- All WebExtensions APIs are Promise-based in Firefox
- Use `browser.*` namespace for cross-browser compatibility
- Handle Firefox-specific permission requirements

## 📞 Firefox-Specific Support

### Common Firefox Issues

1. **Extension not loading**: Check `about:debugging` for error messages
2. **API errors**: Verify all permissions are granted in manifest
3. **Performance issues**: Firefox may require different optimization approaches
4. **Window management**: Offscreen window behavior differs from Chrome

### Getting Help

- **Firefox Extension Documentation**: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions
- **Main Project Support**: See [main README](../README.md) for general support
- **Firefox-Specific Issues**: Report with "Firefox" label on GitHub

---

**Note**: This Firefox version maintains full feature parity with the Chrome extension while adapting to Firefox's extension architecture. The core detection model, scanning logic, and user interface remain identical.

For complete technical documentation, architecture details, and usage instructions, refer to the [main PP_Defend README](../pp_defend/README.md).
