# Installing Rakshak as an app (Android and iOS) and packaging an APK

SafePay with Rakshak is a Progressive Web App: it installs from the browser onto the home screen, launches full-screen with its own icon, and keeps microphone access and the live WebSocket call. No store is needed for the demo or the judges.

## 1. Install on a phone (30 seconds, no build)

**Android (Chrome):** open https://rakshak-223197895518.asia-southeast1.run.app/ and either tap the **Install SafePay on this phone** button under Developer options, or use Chrome's menu and choose **Install app** / **Add to Home screen**. The app opens standalone (no browser bars). The caller phone installs separately from https://rakshak-223197895518.asia-southeast1.run.app/call (its manifest is "Rakshak Caller").

**iPhone (Safari):** open the same URL, tap Share, then **Add to Home Screen**. iOS runs it full-screen; allow the microphone when asked.

What makes it installable: `web/manifest.json` (name, icons, standalone display, shortcuts to /call, /family and /desk), `web/sw.js` served at `/sw.js` (network-first service worker; the app shell is cached for instant launch, API and WebSocket traffic is never cached), icons in `web/icons/`, and the HTTPS Cloud Run origin.

## 2. Produce an APK or AAB (Play-store package) in the browser

Google's own route for shipping a PWA on Android is a Trusted Web Activity, and PWABuilder does the packaging without an Android SDK:

1. Open https://www.pwabuilder.com and enter `https://rakshak-223197895518.asia-southeast1.run.app/`.
2. Check the report (manifest, service worker, HTTPS all pass), then **Package for stores** and choose **Android**.
3. Keep the defaults (package id for example `in.rakshak.safepay`, app name SafePay, display standalone, signing key generated for you) and download the zip.
4. The zip contains a signed **APK** for sideloading and an **AAB** for the Play Console, plus `assetlinks.json`.
5. For the address bar to disappear in the installed app, host the `assetlinks.json` from the zip at `web/.well-known/assetlinks.json` (served at `/.well-known/assetlinks.json`), redeploy, and reinstall the APK. Without it the app still works, with a thin Chrome bar.
6. Install the APK on the demo phones: copy the file, allow "install from this source", open it.

Command-line alternative with the same result: `npm i -g @bubblewrap/cli`, then `bubblewrap init --manifest https://rakshak-223197895518.asia-southeast1.run.app/static/manifest.json` and `bubblewrap build` (it downloads a JDK and the Android SDK on first run).

## 3. What a native app would add in production

The web app already does everything the demo needs. A bank's production app would add the Tier 0 call-state signal (phone-state permission), a foreground service to keep listening while the screen is off, push notifications for the trusted contact (Firebase Cloud Messaging), and the OS or telco audio channel described in docs/PRIVACY_TIERS.md. None of those change the Rakshak backend.
