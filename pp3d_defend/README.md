# PP_Defend: Firefox Mobile Extension

**Real-time browser defense against web behavior manipulation attacks - Firefox Mobile (Android) version**

This is the Firefox mobile implementation of the PP_Defend browser extension. For complete project documentation, see the [main PP_Defend README](https://github.com/NISLabUGA/PixelPatrol3D_Code/blob/chrome/pp_defend/README.md) and [PixelPatrol3D project overview](https://github.com/NISLabUGA/PixelPatrol3D_Code/blob/chrome/README.md).

## 🔄 Key Differences from Desktop Versions

This Firefox mobile version implements the same core functionality as the desktop extensions but with mobile-specific adaptations:

### Technical Differences

| Aspect                   | Desktop Versions                                          | Firefox Mobile Version                        |
| ------------------------ | --------------------------------------------------------- | --------------------------------------------- |
| **Offscreen Processing** | Minimized popup window (Firefox) / offscreen API (Chrome) | Hidden background tab                         |
| **Warning System**       | Popup windows                                             | Native notifications + full-screen alert tabs |
| **File Downloads**       | Direct browser downloads                                  | Download center with in-memory buffering      |
| **User Interface**       | Desktop-optimized popups                                  | Mobile-optimized touch interface              |
| **Installation**         | Temporary add-on                                          | Sideloading via `web-ext` and ADB             |
| **Performance**          | Desktop-class hardware                                    | Mobile-optimized for limited resources        |

### Mobile-Specific Code Changes

#### Offscreen Implementation (`background.js`)

```javascript
// Mobile: Uses hidden background tab instead of popup window
async function ensureOffscreen() {
  const tab = await browser.tabs.create({
    url: browser.runtime.getURL("offscreen.html"),
    active: false, // Hidden tab
  });
  offscreenTabId = tab.id;
}
```

#### Mobile-Optimized Warning System

```javascript
// Mobile: Native notifications + full-screen alert tabs
async function showBrowserNotification() {
  browser.notifications.create(id, {
    type: "basic",
    title: "Unsafe page detected!",
    message: "Tap to view details.",
    priority: 2,
  });

  // Open full-screen alert tab
  const uiTab = await browser.tabs.create({
    url: browser.runtime.getURL("notification.html"),
    active: true,
  });
}
```

#### Download Center System

```javascript
// Mobile: In-memory buffering with download center
let perfBuffer = [];
let ssBuffer = [];

async function openDownloadCenter() {
  const centerTab = await browser.tabs.create({
    url: browser.runtime.getURL("download_center.html"),
    active: true,
  });
}
```

### New Mobile-Specific Files

| File                   | Purpose                                    |
| ---------------------- | ------------------------------------------ |
| `download_center.html` | Mobile-friendly download interface         |
| `download_center.js`   | Handles file downloads and data management |
| `alert_banner.js`      | In-page alert banner injection (optional)  |

## 🚀 Installation

### Option 1: Mozilla Add-ons (Recommended)

1. Visit: https://addons.mozilla.org/en-US/firefox/addon/pixel-patrol-mobile-public/
2. Click **"Add to Firefox"** on your mobile device

### Option 2: Development Installation (Sideloading)

This process requires USB debugging and is intended for development/testing only.

#### Prerequisites

**On Android Device:**

1. Install **Firefox Nightly** from Google Play Store
2. Enable **Developer Options**:
   - Settings → About phone → Tap "Build number" 7 times
3. Enable **USB Debugging**:
   - Settings → System → Developer options → USB debugging
4. Enable **Remote debugging via USB** in Firefox Nightly settings

**On Development Machine:**

```bash
# Install required tools
sudo apt install android-platform-tools  # Linux
# or
brew install android-platform-tools      # macOS

npm install --global web-ext
```

#### Sideloading Process

1. **Build Extension**

   ```bash
   cd pp3d_defend/
   npm install
   rm -rf dist && npx webpack --mode development
   ```

2. **Connect Device**

   ```bash
   # Connect phone via USB and verify connection
   adb devices
   ```

3. **Deploy to Mobile**
   ```bash
   web-ext run -t firefox-android \
     --adb-device YOUR_DEVICE_ID \
     --firefox-apk org.mozilla.fenix
   ```

> ⚠️ **Note**: Sideloaded extensions are temporary and will be removed when Firefox restarts.

## 🔧 Mobile-Specific Features

### Touch-Optimized Interface

- Larger touch targets for mobile interaction
- Simplified popup layout for small screens
- Mobile-friendly warning dialogs

### Resource Management

- Optimized memory usage for mobile devices
- Efficient background processing
- Battery-conscious scanning intervals

### Download Management

- In-memory file buffering to work around mobile download limitations
- Download center interface for managing logs and screenshots
- Mobile-friendly file organization

### Enhanced Notifications

- Native Android notifications for threat alerts
- Full-screen alert tabs for better visibility
- Touch-optimized warning interfaces

## 🚨 Mobile-Specific Troubleshooting

### Extension Not Loading on Mobile

**Cause**: Firefox mobile has stricter extension policies
**Solution**: Ensure using Firefox Nightly and proper sideloading process

### Performance Issues on Mobile

**Cause**: Limited mobile hardware resources
**Solution**:

- Close other apps to free memory
- Use lower scan frequencies if needed
- Monitor battery usage

### Download Center Not Working

**Cause**: Mobile browser download restrictions
**Solution**: Use the built-in download center interface instead of direct downloads

### ADB Connection Issues

**Cause**: USB debugging not properly configured
**Solution**:

- Verify USB debugging is enabled
- Check ADB device authorization on phone
- Try different USB cable/port

## 🛠️ Mobile Development Notes

### Testing on Mobile

```bash
# Use Firefox Nightly for better debugging
# Monitor via desktop Firefox remote debugging
# Access via about:debugging in desktop Firefox
```

### Mobile-Specific Debugging

- Use remote debugging via desktop Firefox
- Monitor performance on actual mobile hardware
- Test across different Android versions and devices

### Performance Considerations

- Mobile inference times are significantly longer (2-4s typical)
- Memory usage should be monitored carefully
- Battery impact should be minimized

## 📞 Mobile-Specific Support

### Common Mobile Issues

1. **Extension disappears**: Normal for sideloaded extensions - reload via web-ext
2. **Slow performance**: Expected on mobile hardware - see performance tips
3. **Download issues**: Use download center instead of direct downloads
4. **Touch interface problems**: Ensure using mobile-optimized UI elements

### Mobile Performance Tips

1. **Close background apps** to free memory for extension
2. **Use WiFi** when possible for better performance
3. **Monitor battery usage** and adjust scan frequency if needed
4. **Keep Firefox Nightly updated** for best compatibility

### Getting Help

- **Mobile Extension Development**: https://extensionworkshop.com/documentation/develop/developing-extensions-for-firefox-for-android/
- **ADB/Debugging Issues**: Check Android developer documentation
- **Main Project Support**: See [main README](https://github.com/NISLabUGA/PixelPatrol3D_Code/blob/chrome/README.md) for general support
- **Mobile-Specific Issues**: Report with "Mobile" label on GitHub

---

**Note**: This mobile version maintains core detection functionality while adapting to mobile constraints and user interaction patterns. The detection model and scanning logic remain identical to desktop versions.

For complete technical documentation, architecture details, and usage instructions, refer to the [main PP_Defend README](https://github.com/NISLabUGA/PixelPatrol3D_Code/blob/chrome/pp_defend/README.md).
