# Move A Mind — mobile release

The repository is prepared for native Android and iOS shells using Capacitor.

- App name: Move A Mind
- Bundle / application ID: com.moveamind.app
- Production content: https://move-a-mind-v08-production.up.railway.app
- Android output for Google Play: signed Android App Bundle (.aab)
- iOS output for App Store Connect: signed archive uploaded from Xcode

## Build
Run npm install, then:
- npx cap add android
- npx cap add ios
- npx cap sync

Store signing, developer-team selection, store metadata, screenshots, privacy declarations and submission are completed in the owner's Google Play Console and Apple Developer / App Store Connect accounts.
