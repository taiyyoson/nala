# Frontend Guide

The Nala frontend is a React Native application built with Expo and TypeScript. It manages onboarding, authentication, chat interactions, text size preferences, and navigation.

## Quick Start

```bash
cd frontend
npm install
npx expo start
```

Scan the QR code with Expo Go (iOS/Android), press `i` for iOS simulator, or `w` for web.

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react-native | 0.81.4 | Mobile framework |
| expo | ~54.0 | Development platform |
| typescript | ~5.9.2 | Type safety |
| @react-navigation/native | ^7.1.17 | Navigation |
| @react-navigation/native-stack | ^7.3.26 | Stack navigation |
| firebase | ^12.4.0 | Authentication |
| lucide-react-native | - | Icons |

## Folder Structure

```
frontend/src/
├── components/onboarding/
│   ├── BackButton.tsx          # Back navigation button
│   ├── Button.tsx              # Styled next button
│   ├── Consent.tsx             # Consent information slide
│   ├── DetailsSlide.tsx        # User information slide
│   ├── HowItWorksSlide.tsx     # Coaching process explanation
│   └── WelcomeSlide.tsx        # Welcome slide
├── config/
│   └── firebaseConfig.ts       # Firebase initialization
├── contexts/
│   ├── AuthContext.tsx          # Auth state (user, onboarding status)
│   └── TextSizeContext.tsx      # Font size preference (small/medium/large)
├── navigation/
│   ├── AppNavigator.tsx         # Root navigator (chooses stack)
│   ├── AuthStack.tsx            # Login, SignUp screens
│   └── MainStack.tsx            # Chat, Overview, Settings screens
├── screens/
│   ├── WelcomeScreen.tsx        # Landing page before login
│   ├── LoginScreen.tsx          # Email/password login
│   ├── SignUpScreen.tsx         # Account creation
│   ├── OnboardingScreen.tsx     # Multi-slide onboarding flow
│   ├── ChatOverviewScreen.tsx   # 4-week session dashboard
│   ├── ChatScreen.tsx           # Coaching chat interface
│   ├── Settings.tsx             # Text size, logout, support
│   ├── LoadingScreen.tsx        # Firebase auth state check
│   └── FirebaseTestScreen.tsx   # Dev-only Firebase test
└── services/
    └── ApiService.ts            # Backend HTTP client
```

## Navigation Flow

AppNavigator determines which stack to show:

```
No user          → AuthStack (Login / SignUp)
User, no onboarding → OnboardingScreen
Onboarding done  → MainStack (ChatOverview, Chat, Settings)
```

## Authentication

1. User logs in or signs up via email/password (Firebase Auth)
2. Firebase returns a user object
3. `AuthContext` stores the user and checks onboarding status via `GET /user/status/{uid}`
4. `AppNavigator` switches to the appropriate stack
5. Logout calls Firebase `signOut()` and resets context state

## Onboarding

New users go through 4 slides: Welcome → How It Works → Details → Consent.

On completion:
1. Frontend calls `POST /user/onboarding` to save completion state
2. `AuthContext` updates `hasCompletedOnboarding = true`
3. `AppNavigator` transitions to `MainStack`

This flag is persistent — users only see onboarding once.

## Chat System

### ChatScreen.tsx

The core conversation interface. Key behavior:

**On mount:**
1. Checks if session is already completed via `GET /session/progress/{userId}`
2. If not complete, sends `[START_SESSION]` to `POST /chat/message` to get AI greeting
3. Stores `conversation_id` from response for subsequent messages

**Sending messages:**
1. Adds user message to UI immediately (optimistic update)
2. Shows typing indicator (animated 3-dot bounce)
3. Sends `POST /chat/message` with message, user_id, session_number, conversation_id
4. Replaces typing indicator with AI response
5. If `session_complete: true` in response, shows completion banner and auto-navigates after 1.8s

**State:**
```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [sessionComplete, setSessionComplete] = useState(false);
const [conversationId, setConversationId] = useState<string>("");
const [isLoading, setIsLoading] = useState(false);
```

**Message type:**
```typescript
type Message = {
  id: number;
  sender: "nala" | "user";
  text: string;
  timestamp: Date;
  isLoading?: boolean;
};
```

### ChatOverviewScreen.tsx

Displays all 4 weeks as color-coded cards:
- **Gray:** Locked (not accessible)
- **Pink (#BF5F83):** Unlocked (ready to start)
- **Green (#4A8B6F):** Completed

Fetches progress via `GET /session/progress/{userId}` on mount. Shows unlock countdown for locked sessions.

## Text Size System

Global font size preference managed by `TextSizeContext`:
- Small = 14pt
- Medium = 16pt (default)
- Large = 20pt

Updated in Settings, applied across Chat, Overview, and other screens via:
```typescript
const { size } = useTextSize();
const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;
```

## Session Unlock Logic

The frontend does not calculate unlock timing — it reads timestamps from the backend:

```typescript
const isSessionUnlocked = (sessionNumber: number): boolean => {
  if (sessionNumber === 1) return true;

  const current = progress.find(p => p.session_number === sessionNumber);
  if (current?.unlocked_at) {
    return new Date() >= new Date(current.unlocked_at);
  }

  const prev = progress.find(p => p.session_number === sessionNumber - 1);
  return !!prev?.completed_at;
};
```

## API Integration (ApiService.ts)

Configured with a `USE_DEPLOYED` flag:
- `true` → https://nala-backend-serv.onrender.com
- `false` → http://127.0.0.1:8000

All endpoints prefixed with `/api/v1`. Uses native `fetch` with JSON request bodies. Failed requests are logged and thrown or returned as null.

## Common Issues

| Problem | Solution |
|---------|----------|
| App stuck on splash screen | Restart Expo, clear cache: `npx expo start -c` |
| Environment variables not updating | Restart Expo completely |
| Metro bundler errors | Delete `node_modules/`, run `npm install` |
| "Network request failed" | Backend is offline or URL is wrong |
| Backend 503 errors | Render free tier spindown — wait 15-30s |
| iOS can't reach localhost | Use computer's IP instead of 127.0.0.1 |
| Android emulator can't reach localhost | Use `10.0.2.2` instead of 127.0.0.1 |
| Text size not updating globally | Ensure `TextSizeProvider` wraps all screens in `AppNavigator` |

## Building & Deployment

### Expo Publish (recommended for dev/testing)

```bash
cd frontend
npx expo login
npx expo publish
```

Publishes to https://nala-chatbot.expo.app/ — users open this in Expo Go or a web browser.

### Standalone Builds (for App Store / Play Store)

Only needed when adding native modules, changing permissions, or creating .ipa/.apk files.

```bash
npm install -g eas-cli
eas build:configure
eas build --platform ios    # Requires Apple Developer account
eas build --platform android
```
