# Frontend Setup Guide

## Quick Start

```bash
cd frontend
npm install
npm start
```

Then scan the QR code with Expo Go app (iOS/Android).

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
- [Building & Deployment](#building--deployment)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

```bash
# Node.js (v18+ recommended)
node -v

# npm (v9+ recommended)
npm -v

# Expo CLI (optional, included in project)
npx expo --version
```

### Mobile Testing Options

**Option 1: Physical Device (Recommended)**
- iOS: Install [Expo Go](https://apps.apple.com/app/expo-go/id982107779) from App Store
- Android: Install [Expo Go](https://play.google.com/store/apps/details?id=host.exp.exponent) from Play Store

**Option 2: Emulator/Simulator**
- iOS: Xcode with iOS Simulator (macOS only)
- Android: Android Studio with Android Emulator

---

## Installation

### 1. Clone & Navigate

```bash
git clone https://github.com/yourusername/nala.git
cd nala/frontend
```

### 2. Install Dependencies

```bash
npm install
```

**This installs:**
- React Native 0.81.4
- Expo ~54.0
- React Navigation 7.x
- Firebase 12.4.0
- TypeScript 5.9.2
- Lucide React Native (icons)

**Install time:** ~2-3 minutes

---

## Configuration

### Firebase Setup

1. **Create Firebase project** at [console.firebase.google.com](https://console.firebase.google.com)

2. **Enable Authentication:**
   - Go to Authentication → Sign-in method
   - Enable "Email/Password"

3. **Get Firebase Config:**
   - Project Settings → General
   - Scroll to "Your apps" → Web app
   - Copy the `firebaseConfig` object

4. **Update `firebaseConfig.ts`:**

```typescript
// frontend/src/config/firebaseConfig.ts

const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "your-app.firebaseapp.com",
  projectId: "your-app",
  storageBucket: "your-app.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123",
};
```

---

### Backend API Configuration

**File:** `frontend/src/services/ApiService.ts`

**For Local Development:**
```typescript
const USE_DEPLOYED = false;
const BASE_URL = "http://127.0.0.1:8000";
```

**For Production/Testing:**
```typescript
const USE_DEPLOYED = true;
const BASE_URL = "https://nala-backend-serv.onrender.com";
```

**Note:** Make sure backend is running before testing locally.

---

## Development Workflow

### Starting the Development Server

```bash
npm start
```

**Output:**
```
› Metro waiting on exp://192.168.1.100:8081
› Scan the QR code above with Expo Go (Android) or Camera (iOS)

› Press a │ open Android
› Press i │ open iOS simulator
› Press w │ open web

› Press r │ reload app
› Press m │ toggle menu
```

### Opening on Device/Emulator

**Physical Device:**
1. Open Expo Go app
2. Scan QR code displayed in terminal
3. App loads in ~10-30 seconds

**iOS Simulator (macOS only):**
```bash
npm run ios
```

**Android Emulator:**
```bash
npm run android
```

---

### Development Tips

#### Hot Reload

Changes automatically reload when you save files. If not:
- Press `r` in terminal to manually reload
- Shake device → "Reload"

#### Clear Cache

If experiencing strange bugs:
```bash
npm start -- --clear
```

#### View Console Logs

**In Terminal:**
```bash
# All logs appear in terminal where npm start is running
```

**In Browser:**
Press `w` in terminal → Opens in browser with DevTools

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── onboarding/      # Onboarding slides
│   │       ├── WelcomeSlide.tsx
│   │       ├── HowItWorksSlide.tsx
│   │       ├── DetailsSlide.tsx
│   │       └── Consent.tsx
│   │
│   ├── contexts/
│   │   ├── AuthContext.tsx       # Firebase auth state
│   │   └── TextSizeContext.tsx   # Text size preference
│   │
│   ├── navigation/
│   │   ├── AppNavigator.tsx      # Root navigator
│   │   ├── AuthStack.tsx         # Login/signup/onboarding
│   │   └── MainStack.tsx         # Chat/settings (logged in)
│   │
│   ├── screens/
│   │   ├── WelcomeScreen.tsx     # Initial landing
│   │   ├── LoginScreen.tsx       # Email/password login
│   │   ├── SignUpScreen.tsx      # Registration
│   │   ├── OnboardingScreen.tsx  # First-time setup
│   │   ├── ChatOverviewScreen.tsx # 4-week dashboard
│   │   ├── ChatScreen.tsx        # Weekly coaching chat
│   │   └── Settings.tsx          # User settings
│   │
│   ├── services/
│   │   └── ApiService.ts         # Backend HTTP client
│   │
│   └── config/
│       └── firebaseConfig.ts     # Firebase initialization
│
├── assets/                   # Images, icons, fonts
├── app.json                  # Expo configuration
├── package.json              # Dependencies
└── tsconfig.json             # TypeScript config
```

---

## Key Dependencies

### Core Libraries

```json
{
  "react": "19.1.0",
  "react-native": "0.81.4",
  "expo": "~54.0.12",
  "@react-navigation/native": "^7.1.17",
  "@react-navigation/native-stack": "^7.3.26",
  "firebase": "^12.4.0",
  "typescript": "~5.9.2"
}
```

### Why These Versions?

- **React Native 0.81:** Latest stable with Expo 54
- **Firebase 12.4:** Modern SDK with better React Native support
- **React Navigation 7:** Type-safe navigation with TypeScript

---

## Building & Deployment

### Publish to Expo (Quick Share)

```bash
expo login
expo publish
```

**Output:**
```
Published to: exp://exp.host/@username/frontend
```

Share this link with testers who have Expo Go installed.

---

### Build Standalone Apps

#### Prerequisites

```bash
npm install -g eas-cli
eas login
```

#### Configure EAS Build

```bash
eas build:configure
```

This creates `eas.json`:
```json
{
  "build": {
    "preview": {
      "distribution": "internal"
    },
    "production": {}
  }
}
```

#### Build for iOS

```bash
eas build --platform ios --profile preview
```

**Requirements:**
- Apple Developer account ($99/year)
- iOS device UDID (for internal distribution)

**Output:** `.ipa` file for installation via TestFlight or direct install

---

#### Build for Android

```bash
eas build --platform android --profile preview
```

**Requirements:**
- None! Android builds are free

**Output:** `.apk` or `.aab` file

**Install APK on device:**
1. Download APK to Android device
2. Settings → Security → Allow from this source
3. Tap APK to install

---

### Update Published App

```bash
expo publish
```

**OTA (Over-The-Air) Updates:**
- Changes to JS/React code update automatically
- Native changes (dependencies, app.json) require new build

---

## Troubleshooting

### Issue: Metro Bundler Won't Start

**Symptoms:**
```
Error: EADDRINUSE: address already in use :::8081
```

**Solution:**
```bash
# Kill existing Metro process
lsof -ti:8081 | xargs kill -9

# Restart
npm start
```

---

### Issue: Firebase Auth Not Working

**Symptoms:**
- Login fails silently
- "No Firebase app initialized" error

**Solutions:**

1. **Check firebaseConfig.ts:**
   ```typescript
   // Must have all fields
   const firebaseConfig = {
     apiKey: "...",
     authDomain: "...",
     projectId: "...",
     // ... etc
   };
   ```

2. **Check Firebase Console:**
   - Authentication → Sign-in method
   - Email/Password must be **Enabled**

3. **Clear async storage:**
   ```bash
   # In Expo Go app: Shake device → Clear AsyncStorage
   ```

---

### Issue: Backend API Calls Failing

**Symptoms:**
- "Network request failed"
- "Failed to fetch"

**Solutions:**

1. **Check backend is running:**
   ```bash
   curl http://127.0.0.1:8000/api/v1/health
   ```

2. **Check API_BASE URL:**
   ```typescript
   // frontend/src/services/ApiService.ts
   const BASE_URL = "http://127.0.0.1:8000"; // For local
   // OR
   const BASE_URL = "https://nala-backend-serv.onrender.com"; // For deployed
   ```

3. **iOS: Enable localhost access**
   - iOS blocks localhost by default
   - Use computer's IP instead: `http://192.168.1.100:8000`

4. **Android: Use `10.0.2.2` for emulator**
   ```typescript
   const BASE_URL = "http://10.0.2.2:8000"; // Android emulator
   ```

---

### Issue: Expo Go Shows White Screen

**Symptoms:**
- App loads but shows blank white screen
- No error messages

**Solutions:**

1. **Check console for errors:**
   - Terminal where `npm start` is running
   - Press `w` to open in browser with DevTools

2. **Clear cache:**
   ```bash
   npm start -- --clear
   ```

3. **Check for missing dependencies:**
   ```bash
   npm install
   ```

4. **Reload app:**
   - Shake device → Reload
   - Or press `r` in terminal

---

### Issue: TypeScript Errors

**Symptoms:**
```
Property 'X' does not exist on type 'Y'
```

**Solutions:**

1. **Restart TypeScript server:**
   - VSCode: Cmd+Shift+P → "TypeScript: Restart TS Server"

2. **Check types are installed:**
   ```bash
   npm install --save-dev @types/react @types/react-native
   ```

3. **Ignore temporarily:**
   ```typescript
   // @ts-ignore
   const problematicCode = ...;
   ```

---

### Issue: Navigation Not Working

**Symptoms:**
- "navigate is not a function"
- "Cannot read property 'navigate' of undefined"

**Solution:**

Check screen is wrapped in navigation stack:
```typescript
// ✅ Correct
<Stack.Screen name="ChatScreen" component={ChatScreen} />

// ❌ Wrong
<ChatScreen /> // Not wrapped in navigator
```

---

### Issue: Text Size Not Updating

**Symptoms:**
- Change text size in Settings
- Text doesn't update in other screens

**Solution:**

Check `TextSizeProvider` wraps all screens:
```typescript
// AppNavigator.tsx
<AuthProvider>
  <TextSizeProvider>  {/* Must wrap everything */}
    <AppContent />
  </TextSizeProvider>
</AuthProvider>
```

And screens use the hook:
```typescript
const { size } = useTextSize();
const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;
```

---

## Environment-Specific Configuration

### Local Development

```typescript
// ApiService.ts
const USE_DEPLOYED = false;
const BASE_URL = "http://127.0.0.1:8000";
```

**Features:**
- Fast iteration
- Full control over backend
- Can debug backend code

---

### Staging/Testing

```typescript
const USE_DEPLOYED = true;
const BASE_URL = "https://nala-backend-serv.onrender.com";
```

**Features:**
- Test without running backend locally
- Share with testers easily
- Slower response times (cold starts)

---

### Production

Same as staging, but with:
- Error tracking (e.g., Sentry)
- Analytics (e.g., Firebase Analytics)
- Performance monitoring

---

## Useful Commands

```bash
# Start development server
npm start

# Clear cache and restart
npm start -- --clear

# Install dependencies
npm install

# Open on iOS simulator (macOS only)
npm run ios

# Open on Android emulator
npm run android

# Open in web browser
npm run web

# Type-check TypeScript
npx tsc --noEmit

# Publish to Expo
expo publish

# Build for iOS
eas build --platform ios

# Build for Android
eas build --platform android
```

---

## Related Documentation

- [React Native Docs](https://reactnative.dev/docs/getting-started)
- [Expo Docs](https://docs.expo.dev/)
- [React Navigation Docs](https://reactnavigation.org/docs/getting-started)
- [Firebase Docs](https://firebase.google.com/docs/auth)

---

## Next Steps

1. ✅ Set up Firebase project
2. ✅ Configure `firebaseConfig.ts`
3. ✅ Set API base URL in `ApiService.ts`
4. ✅ Run `npm install`
5. ✅ Start development: `npm start`
6. ✅ Test on device via Expo Go
7. ✅ Make changes and see hot reload in action

---

**Last Updated:** December 3, 2024
