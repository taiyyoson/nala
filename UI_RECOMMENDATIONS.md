# Nala — UI Recommendations

**Audience:** People actively seeking goal-help in health, wellness, and habit formation. They need to feel supported, not judged. Every friction point is a potential drop-off.

**Implementor note:** This document is a spec, not a wishlist. Every value is specific and copy-pasteable. Priorities:
- **P0** — Blocks trust or usability. Fix before any other work.
- **P1** — Meaningfully improves the core experience. Fix in the next sprint.
- **P2** — Polish that separates good from great. Schedule after P0/P1.

---

## 1. Typography & Readability

### 1.1 Adopt a Single Font Family (P1)

**What to change:** Import and use `Inter` (via `expo-google-fonts` or bundled in `assets/fonts/`). Apply it globally through a `ThemeContext` or a `Text` wrapper component.

**Why:** The app currently relies on the system font (San Francisco on iOS, Roboto on Android). This causes subtle visual inconsistency between platforms and misses a branding opportunity. Inter is purpose-built for screen legibility and is free.

**Implementation:**
```
npx expo install @expo-google-fonts/inter expo-font
```
Font weights to load: `Inter_400Regular`, `Inter_500Medium`, `Inter_600SemiBold`, `Inter_700Bold`.

Create `src/constants/typography.ts`:
```ts
export const typography = {
  body:        { fontFamily: 'Inter_400Regular',   fontSize: 16, lineHeight: 24 },
  bodySmall:   { fontFamily: 'Inter_400Regular',   fontSize: 14, lineHeight: 20 },
  label:       { fontFamily: 'Inter_500Medium',    fontSize: 14, lineHeight: 20 },
  title:       { fontFamily: 'Inter_700Bold',      fontSize: 22, lineHeight: 30 },
  heading:     { fontFamily: 'Inter_700Bold',      fontSize: 28, lineHeight: 36 },
  caption:     { fontFamily: 'Inter_400Regular',   fontSize: 12, lineHeight: 16 },
  button:      { fontFamily: 'Inter_600SemiBold',  fontSize: 16, lineHeight: 24 },
  chatNala:    { fontFamily: 'Inter_400Regular',   fontSize: 16, lineHeight: 26 }, // extra line height for reading comfort
  chatUser:    { fontFamily: 'Inter_500Medium',    fontSize: 16, lineHeight: 24 },
};
```

### 1.2 Fix Line Height in Chat Messages (P0)

**What to change:** `ChatScreen.tsx` line 429: `messageText` has no `lineHeight`. Long Nala responses are dense and hard to read.

**Why:** Health coaching messages are conversational paragraphs. Without line height, text walls feel overwhelming — exactly the wrong emotion.

**Implementation:** Set `lineHeight: 26` on `styles.messageText` and `lineHeight: 24` on `styles.userMessageText`. For the `fontScale` dynamic path, set `lineHeight: fontScale * 1.6`.

### 1.3 Minimum Body Font Size (P0)

**What to change:** `fontScale` for "small" setting is `14px`. The `senderName` label is `fontScale - 2 = 12px`. Timestamps (not yet shown) would also be tiny.

**Why:** WCAG 2.1 AA requires 4.5:1 contrast ratio for text under 18px. At 12px the labels fail both size and contrast requirements for users who chose "small" precisely because they have visual preferences.

**Implementation:** Clamp the minimum font size. In every screen that uses `fontScale`:
```ts
const BASE = size === 'small' ? 14 : size === 'medium' ? 16 : 20;
const fontScale = BASE;
const fontScaleSub = Math.max(12, BASE - 2); // clamp sender/caption labels
const fontScaleCaption = Math.max(11, BASE - 4); // clamp footer text only
```
Never go below 11px for any visible text. Never go below 13px for anything interactive.

---

## 2. Color Palette Refinement

### 2.1 Full Design System Palette (P1)

**What to change:** The app uses `#4A8B6F`, `#2E7D32`, `#4CAF50`, `#BF5F83`, `#FF6B35`, and `#E8F5E9` spread across files with no shared source of truth. Colors are hardcoded in each screen's `StyleSheet`.

**Why:** Inconsistency signals low polish to users. The pink (`#BF5F83`) on session cards is jarring next to the green brand. The orange (`#FF6B35`) on the login screen is unrelated to any other color in the app.

**Implementation:** Create `src/constants/colors.ts`:

```ts
export const colors = {
  // Brand
  primary:        '#4A8B6F', // Sage green — main brand
  primaryDark:    '#2D5E4A', // Pressed states, header gradient end
  primaryLight:   '#9ACDAF', // Onboarding dot active, avatar bg
  primaryFaint:   '#E8F5E9', // Nala bubble bg, success banner bg

  // Accent — warm, motivating, not alarming
  accent:         '#E8935A', // CTAs on light bg (replaces #FF6B35 orange)
  accentLight:    '#FEF3E2', // Motivation card bg (already used — keep)

  // Secondary — for "incomplete" session cards (replaces #BF5F83 pink)
  secondary:      '#7B8EC8', // Calm periwinkle blue
  secondaryDark:  '#4A5FA0',
  secondaryLight: '#E8ECF8',

  // Neutrals
  background:     '#F5F9F7', // App background (already used — keep)
  surface:        '#FFFFFF', // Cards, input areas
  surfaceAlt:     '#F3F4F6', // Text size option bg, unselected states
  border:         '#E0E0E0', // Input borders, separators
  borderLight:    '#C8E6C9', // Nala bubble border, subtle dividers

  // Text
  textPrimary:    '#111827', // Headings, important labels
  textSecondary:  '#4B5563', // Body text (replaces #333, #555)
  textMuted:      '#6B7280', // Subtitles, metadata (already used in Settings)
  textDisabled:   '#9CA3AF', // Placeholder, footer text

  // Semantic
  success:        '#4A8B6F', // Same as primary — completion, positive states
  successBg:      '#E8F5E9',
  successBorder:  '#C8E6C9',
  error:          '#DC2626', // Replaces #FF3B30 and #B91C1C with one value
  errorBg:        '#FEF2F2',
  errorBorder:    '#FECACA',
  warning:        '#D97706',
  warningBg:      '#FEF3C7',

  // Chat-specific
  userBubble:     '#2D5E4A', // Slightly darker than primary — better contrast on white
  userBubbleText: '#FFFFFF',
  nalaBubble:     '#E8F5E9',
  nalaBubbleText: '#111827',

  // Dark mode (see Section 12)
  dark: {
    background:   '#0F1A15',
    surface:      '#1A2E23',
    surfaceAlt:   '#243D2F',
    border:       '#2D4A39',
    textPrimary:  '#F0F7F4',
    textSecondary:'#A3C4B5',
    textMuted:    '#6B9E85',
    userBubble:   '#4A8B6F',
    nalaBubble:   '#1A2E23',
  }
};
```

**Migration steps:**
1. Create the file above.
2. Search for hardcoded hex values across all screens and replace with `colors.*` references.
3. Change the session card incomplete color from `#BF5F83` to `colors.secondary` (`#7B8EC8`).
4. Change `forgotPassword` and `signUpLink` in `LoginScreen.tsx` from `#FF6B35` to `colors.accent` (`#E8935A`).

---

## 3. Chat UI Improvements

### 3.1 Auto-Scroll to Bottom on New Messages (P0)

**What to change:** `ChatScreen.tsx` `ScrollView` has a `ref` (`scrollViewRef`) but `scrollToEnd` is never called. When Nala responds, the message appears off-screen.

**Why:** Users will think the app is broken or slow if they send a message and nothing appears to happen.

**Implementation:** After `setMessages(...)` in both `sendInitialGreeting` and `sendUserMessage`, add:
```ts
setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 100);
```
The `setTimeout` gives React one render cycle to paint the new message before scrolling.

### 3.2 Switch ScrollView to FlatList (P1)

**What to change:** Replace the `ScrollView` + `.map()` in `ChatScreen.tsx` with a `FlatList`.

**Why:** As conversation history grows, `ScrollView` renders every message. `FlatList` virtualizes the list and keeps memory flat on long sessions.

**Implementation:**
```tsx
<FlatList
  ref={flatListRef} // change type to useRef<FlatList>(null)
  data={messages}
  keyExtractor={(item) => item.id.toString()}
  renderItem={({ item: m }) => <MessageBubble message={m} fontScale={fontScale} />}
  contentContainerStyle={styles.messagesContent}
  onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
  onLayout={() => flatListRef.current?.scrollToEnd({ animated: false })}
  showsVerticalScrollIndicator={false}
/>
```
Extract bubble rendering into a `MessageBubble` component in `src/components/chat/MessageBubble.tsx` and wrap it in `React.memo`.

### 3.3 Timestamp Display (P1)

**What to change:** Messages have a `timestamp: Date` field that is never rendered.

**Why:** For a coaching app where sessions matter over time, timestamps provide context and reinforce that this is a real conversation.

**Implementation:** Add below each message bubble:
```tsx
<Text style={styles.timestamp}>
  {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
</Text>
```
Style: `fontSize: 11, color: colors.textDisabled, marginTop: 4, alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start'`

Only show the timestamp on the last message of each contiguous group from the same sender (group detection: compare `messages[i].sender !== messages[i+1]?.sender`).

### 3.4 Better Message Bubble Tails (P2)

**What to change:** Bubbles are plain rectangles with uniform `borderRadius: 16`. They have no directional cue.

**Why:** Chat bubbles with a pointed tail on the leading corner are a universal mental model. It reduces cognitive load.

**Implementation:** Use asymmetric border radii:
```ts
// User bubble (right-aligned)
userBubble: {
  borderRadius: 18,
  borderBottomRightRadius: 4, // tail effect
}
// Nala bubble (left-aligned)
nalaBubble: {
  borderRadius: 18,
  borderBottomLeftRadius: 4,
}
```

### 3.5 Remove "Sender Name" Label from Every Bubble (P1)

**What to change:** Currently every message bubble shows "You" or "Nala" as a label above the text.

**Why:** In a 1:1 chat between two parties, sender labels on every message add visual noise. iMessage, WhatsApp, and every major chat app only shows names in group chats. The bubble alignment (left vs right) is sufficient to identify sender. Remove the label entirely and rely on alignment + color.

**Implementation:** Delete the `senderName`, `userSenderName`, and `nalaSenderName` styles and the `<Text>` rendering them. Add a small avatar circle on the left of Nala bubbles only to reinforce brand identity:
```tsx
// Nala message row
<View style={styles.nalaRow}>
  <View style={styles.nalaAvatar}>
    <Text style={styles.nalaAvatarText}>N</Text>
  </View>
  <View style={[styles.messageBubble, styles.nalaBubble]}>
    ...
  </View>
</View>
```
Avatar: `width: 28, height: 28, borderRadius: 14, backgroundColor: colors.primaryLight` with initial `N` in white at 12px.

### 3.6 Input Area Padding Fix (P1)

**What to change:** `inputArea` has `padding: 25` on all sides. This is excessive — it pushes the input field very high above the keyboard on shorter phones.

**Why:** On an iPhone SE (375x667), `padding: 25` on a `KeyboardAvoidingView` with `behavior: 'padding'` creates a visible gap between keyboard and input.

**Implementation:**
```ts
inputArea: {
  flexDirection: 'row',
  paddingHorizontal: 16,
  paddingVertical: 12,
  paddingBottom: Platform.OS === 'ios' ? 16 : 12,
  backgroundColor: colors.surface,
  borderTopWidth: StyleSheet.hairlineWidth,
  borderTopColor: colors.border,
}
```

---

## 4. Micro-interactions & Animations

### 4.1 Send Button Press Feedback (P1)

**What to change:** The send button (`TouchableOpacity` with `→`) has no visual press animation beyond the default opacity fade.

**Why:** Tactile feedback on send confirms the action was registered. This is especially important when the network is slow.

**Implementation:** Replace `TouchableOpacity` with an `Animated.View`-wrapped component using a scale spring:
```ts
const scaleAnim = useRef(new Animated.Value(1)).current;

const handlePressIn = () => {
  Animated.spring(scaleAnim, { toValue: 0.88, useNativeDriver: true }).start();
};
const handlePressOut = () => {
  Animated.spring(scaleAnim, { toValue: 1, friction: 3, useNativeDriver: true }).start();
};
```
Apply `transform: [{ scale: scaleAnim }]` to the send button `Animated.View`.

### 4.2 Message Appear Animation (P1)

**What to change:** New messages pop in instantly with no entrance animation.

**Why:** A subtle fade+slide makes the conversation feel alive and responsive.

**Implementation:** In `MessageBubble` component, on mount:
```ts
const opacity = useRef(new Animated.Value(0)).current;
const translateY = useRef(new Animated.Value(8)).current;

useEffect(() => {
  Animated.parallel([
    Animated.timing(opacity, { toValue: 1, duration: 200, useNativeDriver: true }),
    Animated.timing(translateY, { toValue: 0, duration: 200, useNativeDriver: true }),
  ]).start();
}, []);
```

### 4.3 Session Card Press Ripple (P1)

**What to change:** Session cards use `activeOpacity={0.9}`, barely visible on press.

**Why:** Cards look like decorative tiles rather than interactive buttons. Lower opacity + slight scale gives a satisfying tap response.

**Implementation:**
```ts
activeOpacity={0.82}
// or wrap with Animated.View:
transform: [{ scale: pressed ? 0.97 : 1 }] // use Pressable's pressed state
```
Migrate session cards from `TouchableOpacity` to `Pressable` to access the `pressed` boolean cleanly.

### 4.4 Session Completion Celebration (P0)

**What to change:** When `data.session_complete` is true, the app waits 1800ms then silently navigates away. There is no celebration.

**Why:** Session completion is the most important positive event in the app. Missing a celebration moment breaks the habit loop — users need to feel rewarded to return.

**Implementation:**
1. Show a full-screen overlay for 2 seconds before navigating.
2. Use `react-native-reanimated` (already likely available via Expo) for a confetti-style burst or a simple scale+fade animation on a trophy/checkmark icon.

Minimal version (no third-party dependency):
```tsx
// Trigger when sessionComplete becomes true
{sessionJustCompleted && (
  <Animated.View style={[styles.celebrationOverlay, { opacity: celebrationOpacity }]}>
    <Text style={styles.celebrationEmoji}>✓</Text>
    <Text style={styles.celebrationTitle}>Session complete!</Text>
    <Text style={styles.celebrationSub}>Great work today.</Text>
  </Animated.View>
)}
```
Styles: `celebrationOverlay` is `position: absolute, top: 0, left: 0, right: 0, bottom: 0, backgroundColor: colors.primary, justifyContent: 'center', alignItems: 'center', zIndex: 100`.

For a richer experience: install `react-native-confetti-cannon` — it's lightweight and Expo-compatible.

### 4.5 Onboarding Dot Width Transition (P2)

**What to change:** The active onboarding dot already grows from `width: 8` to `width: 22`. This change is instantaneous.

**Why:** Animating the width transition makes the step indicator feel polished rather than snapping.

**Implementation:** Animate the active dot width using `Animated.timing`:
```ts
const dotWidth = useRef(new Animated.Value(8)).current;
useEffect(() => {
  Animated.timing(dotWidth, {
    toValue: isActive ? 22 : 8,
    duration: 250,
    useNativeDriver: false, // width cannot use native driver
  }).start();
}, [isActive]);
```

---

## 5. Empty States

### 5.1 No Messages Empty State (P1)

**What to change:** When a session starts, `messages` is `[]` and the screen shows a blank white area while `sendInitialGreeting` runs.

**Why:** A blank screen during loading looks broken. Users may tap back.

**Implementation:** Show a centered state before messages arrive:
```tsx
{messages.length === 0 && !isLoading && (
  <View style={styles.emptyState}>
    <Text style={styles.emptyStateEmoji}>💬</Text>
    <Text style={styles.emptyStateText}>Starting your session...</Text>
  </View>
)}
```
Longer-term: replace the emoji with an SVG illustration of Nala's logo or a simple chat bubble pair.

### 5.2 Progress Loading State (P1)

**What to change:** `ChatOverviewScreen.tsx` shows a plain `ActivityIndicator` with "Loading your progress..." when fetching sessions.

**Why:** A spinner with no context makes users anxious about wait times on a slow connection (the backend is noted to have Render cold-starts).

**Implementation:** Replace with a skeleton loading state — three placeholder cards with a shimmer animation:
```tsx
// SkeletonCard component
<View style={styles.skeletonCard}>
  <Animated.View style={[styles.skeletonShimmer, { opacity: shimmerAnim }]} />
</View>
```
Render 4 skeleton cards (one per session) while `loading === true`. Shimmer: `opacity` oscillates between `0.4` and `0.9` in an `Animated.loop`.

### 5.3 Error State on Progress Fetch Failure (P1)

**What to change:** The error path in `ChatOverviewScreen` shows an `Alert.alert()` and renders nothing. The screen stays blank.

**Why:** An alert dismisses and leaves the user staring at a loader. Inline error states with a retry button keep users in the flow.

**Implementation:** Add `error` state, and replace the `Alert.alert` with inline rendering:
```tsx
{error && (
  <View style={styles.errorState}>
    <Text style={styles.errorStateTitle}>Couldn't load your sessions</Text>
    <Text style={styles.errorStateBody}>Check your connection and try again.</Text>
    <TouchableOpacity style={styles.retryButton} onPress={fetchProgress}>
      <Text style={styles.retryButtonText}>Retry</Text>
    </TouchableOpacity>
  </View>
)}
```

---

## 6. Progress Visualization

### 6.1 Overall Progress Bar in ChatOverview Header (P1)

**What to change:** The header shows "4-week wellness coaching program" as plain text. There is no visual indicator of how far through the program the user is.

**Why:** Progress visibility is one of the most powerful motivators for goal-pursuers. Showing "Week 2 of 4" as a filled bar makes the remaining effort feel manageable.

**Implementation:** Add below `headerSubtitle` in the header View:
```tsx
const completedCount = sessions.filter(s => isSessionComplete(s.id)).length;
const progressPercent = (completedCount / sessions.length) * 100;

// In JSX:
<View style={styles.progressBarContainer}>
  <View style={[styles.progressBarFill, { width: `${progressPercent}%` }]} />
</View>
<Text style={styles.progressLabel}>{completedCount} of {sessions.length} sessions done</Text>
```
Styles:
```ts
progressBarContainer: {
  height: 4,
  backgroundColor: 'rgba(255,255,255,0.3)',
  borderRadius: 2,
  marginTop: 10,
  width: '100%',
},
progressBarFill: {
  height: 4,
  backgroundColor: '#fff',
  borderRadius: 2,
},
progressLabel: {
  color: 'rgba(255,255,255,0.8)',
  fontSize: 12,
  marginTop: 4,
}
```

### 6.2 Completed Session Card Redesign (P1)

**What to change:** Completed sessions show only "Completed" as their text, replacing the session title entirely. The session title is lost.

**Why:** Users should see what they accomplished, not just that something is done. Showing "Getting to know you — Completed" is more satisfying than just "Completed".

**Implementation:**
```tsx
// In the card, always render the title:
<Text style={styles.sessionTitle}>{session.title}</Text>

// Below it, conditionally show status:
{completed && (
  <View style={styles.completedBadge}>
    <CheckCircle2 size={12} color={colors.surface} />
    <Text style={styles.completedBadgeText}>Completed</Text>
  </View>
)}
```
`completedBadge`: `flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 3, alignSelf: 'flex-start'`

### 6.3 Per-Card Progress Ring (P2)

**What to change:** There is no progress ring or visual completion indicator on individual session cards.

**Why:** A circular progress ring (even a simple 0% or 100% binary for now) is more compelling than a flat checkmark. It hints at future granular progress tracking.

**Implementation:** Use `react-native-svg` (available in Expo) to draw a lightweight `ProgressRing` component:
```tsx
// src/components/ProgressRing.tsx
import Svg, { Circle } from 'react-native-svg';

interface Props { size: number; progress: number; color: string; }

export function ProgressRing({ size, progress, color }: Props) {
  const radius = (size - 4) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - progress);
  return (
    <Svg width={size} height={size}>
      <Circle cx={size/2} cy={size/2} r={radius} stroke="rgba(255,255,255,0.3)" strokeWidth={3} fill="none" />
      <Circle
        cx={size/2} cy={size/2} r={radius}
        stroke={color} strokeWidth={3} fill="none"
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        strokeLinecap="round"
        transform={`rotate(-90, ${size/2}, ${size/2})`}
      />
    </Svg>
  );
}
```
Use `<ProgressRing size={40} progress={completed ? 1 : 0} color="#fff" />` in the top-right of each card instead of the plain icon.

---

## 7. Navigation & Layout

### 7.1 Add a Bottom Tab Bar (P1)

**What to change:** The app is stack-only with no persistent navigation anchor. The user reaches Settings via a question-mark icon that has no label.

**Why:** For a health app with distinct areas (sessions, settings, profile), a bottom tab bar creates spatial awareness. Users know where they are and what else exists. It also increases discoverability — hidden navigation leads to users never finding features.

**Implementation:** Wrap `ChatOverview` and `Settings` in a bottom tab navigator:

```ts
// src/navigation/MainTabs.tsx
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Home, Settings as SettingsIcon } from 'lucide-react-native';

const Tab = createBottomTabNavigator();

export function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: Platform.OS === 'ios' ? 84 : 64,
          paddingBottom: Platform.OS === 'ios' ? 28 : 8,
        },
        tabBarLabelStyle: { fontFamily: 'Inter_500Medium', fontSize: 12 },
      }}
    >
      <Tab.Screen
        name="Sessions"
        component={ChatOverviewScreen}
        options={{ tabBarIcon: ({ color }) => <Home size={22} color={color} /> }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsPage}
        options={{ tabBarIcon: ({ color }) => <SettingsIcon size={22} color={color} /> }}
      />
    </Tab.Navigator>
  );
}
```
Remove the logout button (`←`) from `ChatOverviewScreen` header — it should live in Settings. The `MessageCircleQuestionMark` icon pointing to Settings should be removed since Settings is now a visible tab.

### 7.2 Safe Area Handling Consistency (P0)

**What to change:** `ChatScreen.tsx` hardcodes `paddingTop: Platform.OS === 'ios' ? 55 : 30` for the header. `ChatOverviewScreen` hardcodes `paddingTop: 60`. `Settings.tsx` hardcodes `paddingTop: 60`.

**Why:** These hardcoded values break on notched devices (iPhone 14/15 Dynamic Island) and on Android devices with varying status bar heights.

**Implementation:**
```
npx expo install react-native-safe-area-context
```
Wrap the app root in `<SafeAreaProvider>`. In each screen:
```tsx
import { useSafeAreaInsets } from 'react-native-safe-area-context';
const insets = useSafeAreaInsets();

// Replace hardcoded paddingTop with:
paddingTop: insets.top + 16
```

### 7.3 LoginScreen Back Button Layout Bug (P0)

**What to change:** `LoginScreen.tsx` line 212: `backButtonContainer` has `marginTop: -200`. This is a hack to position the back button.

**Why:** Negative margins are a red flag that layout is not using the right approach. On some screen sizes this will overlap the button with the title text.

**Implementation:** Use `position: 'absolute'` instead:
```ts
backButtonContainer: {
  position: 'absolute',
  top: 0,
  left: 0,
  padding: 16,
}
```
And inside the `content` View add `position: 'relative'`.

---

## 8. Accessibility

### 8.1 Touch Target Minimum Sizes (P0)

**What to change:**
- `ChatScreen.tsx` back button: `padding: 10` around an arrow character. The tap area is ~36x36px.
- `LoginScreen.tsx` back button: no explicit size — defaults to text size.
- Onboarding dots in `OnboardingScreen.tsx`: `width: 8, height: 8` — untappable as navigation controls.

**Why:** WCAG 2.1 Success Criterion 2.5.5 and Apple HIG both require 44x44pt minimum touch targets. Anything smaller creates accessibility failures and frustration for users with larger fingers or motor difficulties.

**Implementation:**
- All icon buttons: `style={{ width: 44, height: 44, justifyContent: 'center', alignItems: 'center' }}`
- Onboarding dots: if tappable, minimum `padding: 8` around each dot. If purely decorative, add `accessibilityElementsHidden={true}`.

### 8.2 accessibilityLabel on All Interactive Elements (P0)

**What to change:** No `accessibilityLabel` props anywhere in the codebase.

**Why:** VoiceOver/TalkBack users hear "button" for every `TouchableOpacity`. They cannot navigate the app.

**Implementation — specific additions needed:**

`ChatScreen.tsx`:
```tsx
// Back button
<TouchableOpacity accessibilityLabel="Go back" accessibilityRole="button" ...>

// Send button
<TouchableOpacity accessibilityLabel="Send message" accessibilityRole="button" ...>

// Input
<TextInput accessibilityLabel="Message input" accessibilityHint="Type your message to Nala" ...>
```

`ChatOverviewScreen.tsx`:
```tsx
// Each session card
<TouchableOpacity
  accessibilityLabel={`Week ${session.id}: ${session.title}. ${completed ? 'Completed.' : 'Tap to begin.'}`}
  accessibilityRole="button"
  ...>
```

`LoginScreen.tsx`:
```tsx
<TextInput accessibilityLabel="Email address" ... />
<TextInput accessibilityLabel="Password" ... />
<TouchableOpacity accessibilityLabel={showPassword ? 'Hide password' : 'Show password'} ...>
<TouchableOpacity accessibilityLabel="Log in" accessibilityRole="button" ...>
```

### 8.3 Error Message Accessibility (P1)

**What to change:** Error text in `LoginScreen` is just a styled `Text`. Screen readers will not announce it when it appears.

**Why:** Users who cannot see will not know login failed.

**Implementation:**
```tsx
{error ? (
  <Text
    style={styles.errorText}
    accessibilityLiveRegion="polite"
    accessibilityRole="alert"
  >
    {error}
  </Text>
) : null}
```

### 8.4 Color Contrast Fixes (P0)

**What to change:**
- `nalaSenderName`: `color: '#2E7D32'` on `backgroundColor: '#E8F5E9'` — contrast ratio ~3.8:1. Fails WCAG AA (requires 4.5:1 for small text).
- `sessionFooterText`: `color: 'rgba(255,255,255,0.8)'` on card backgrounds — at 80% opacity white on `#BF5F83` the ratio is ~3.2:1. Fails.
- `textMuted #6B7280` on `#F3F4F6` background — ratio ~4.1:1. Marginal fail.

**Implementation:**
- Change `nalaSenderName` color from `#2E7D32` to `#1B5E3A` (contrast 5.2:1 on `#E8F5E9`).
- Change `sessionFooterText` opacity from 0.8 to 1.0 on the incomplete (`#7B8EC8`) card variant — white on `#7B8EC8` at full opacity is 4.9:1.
- Change `textMuted` from `#6B7280` to `#4B5563` on light backgrounds.

---

## 9. Session Cards

### 9.1 Gradient Backgrounds (P2)

**What to change:** Session cards have a flat `backgroundColor`. Completed cards are `#4A8B6F`, incomplete cards are `#BF5F83` (to be changed to `#7B8EC8`).

**Why:** Subtle gradients add depth and make cards feel premium. Health apps like Headspace and Calm use gradients extensively to convey warmth and calm.

**Implementation:**
```
npx expo install expo-linear-gradient
```
```tsx
import { LinearGradient } from 'expo-linear-gradient';

// Replace TouchableOpacity background color with:
<LinearGradient
  colors={completed ? ['#4A8B6F', '#2D5E4A'] : ['#7B8EC8', '#4A5FA0']}
  start={{ x: 0, y: 0 }}
  end={{ x: 1, y: 1 }}
  style={[styles.sessionCard]}
>
  {/* ...card contents... */}
</LinearGradient>
```
Wrap in `TouchableOpacity` (or `Pressable`) with `style` applied to the outer component, and `style.borderRadius: 24` on the `LinearGradient` to keep corners rounded.

### 9.2 Motivational Subtext per Session (P2)

**What to change:** Cards show the session title (or "Completed"). There is no motivational subtext.

**Why:** Context lines like "What drives you?" (Week 1) or "Turning plans into routines" (Week 2) make the program feel curated and intentional, not generic.

**Implementation:** Extend the `sessions` array in `ChatOverviewScreen`:
```ts
const sessions = [
  { id: 1, title: 'Getting to know you',    subtitle: 'Discover what drives you' },
  { id: 2, title: 'Building habits',        subtitle: 'Small steps, lasting change' },
  { id: 3, title: 'Overcoming challenges',  subtitle: 'Working through what holds you back' },
  { id: 4, title: 'Reviewing progress',     subtitle: 'Celebrating how far you\'ve come' },
];
```
Render `subtitle` below `title` in a lighter weight: `fontSize: fontScaleSub, color: 'rgba(255,255,255,0.75)', fontFamily: 'Inter_400Regular'`.

### 9.3 Estimated Duration Badge (P1)

**What to change:** "10-min check-in" appears in `sessionFooter` only for incomplete sessions, using the `Calendar` icon.

**Why:** Knowing a session takes 10 minutes lowers the commitment barrier significantly. This needs to be visible at a glance, even for the first look, not hidden in fine print.

**Implementation:** Move the duration badge to a more prominent position — beside the Week badge at the top of the card:
```tsx
<View style={styles.cardTopRow}>
  <WeekBadge week={session.id} />
  <DurationBadge minutes={10} />
</View>
```
`DurationBadge`: `backgroundColor: 'rgba(255,255,255,0.25)', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 3`. Text: `10 min` at 11px.

---

## 10. Input Area

### 10.1 Multiline Text Input (P1)

**What to change:** `ChatScreen.tsx` `TextInput` is single-line (`style.height` not set, no `multiline` prop).

**Why:** Health coaching questions invite personal reflection. Users often write 2-3 sentences. Forcing them into a single line truncates their input visually and makes long messages feel cramped.

**Implementation:**
```tsx
<TextInput
  style={[styles.input, { fontSize: fontScale, maxHeight: 120 }]}
  placeholder="Type your message..."
  value={input}
  onChangeText={setInput}
  editable={!isLoading}
  multiline
  numberOfLines={1}
  textAlignVertical="center" // Android
/>
```
When `multiline` is true, the input grows to fit content up to `maxHeight: 120` (approx 4 lines at default size). The send button should `alignSelf: 'flex-end'` so it stays anchored to the bottom of the input.

### 10.2 Placeholder Refinement (P1)

**What to change:** `placeholder="Type your message..."` is generic.

**Why:** Contextual placeholders reduce cognitive load and model the behavior you want. For a health coaching app, the placeholder can gently prompt reflection.

**Implementation:** Rotate placeholder text based on context:
```ts
const placeholders = [
  'Share what\'s on your mind...',
  'How are you feeling today?',
  'What would you like to work on?',
];
// Pick one randomly on mount, or use the session week to select:
const placeholder = week === 1
  ? 'Tell Nala about your goals...'
  : week === 4
  ? 'Reflect on your journey...'
  : 'Share what\'s on your mind...';
```

### 10.3 Character Count (P2)

**What to change:** No character count indicator exists.

**Why:** For users who write long messages, a soft character limit indicator (appearing only after 200 characters) prevents accidentally sending a wall of text.

**Implementation:**
```tsx
{input.length > 200 && (
  <Text style={styles.charCount}>
    {input.length}/500
  </Text>
)}
```
Style: `position: 'absolute', bottom: 14, right: 70, fontSize: 11, color: input.length > 450 ? colors.error : colors.textDisabled`.

### 10.4 Locked Session State (P1)

**What to change:** The locked state shows `🔒 Chat is locked for this completed session.` in a gray box with `fontStyle: 'italic'`.

**Why:** Italic gray text is dismissive. A completed session is an achievement. The locked state should feel celebratory, not restrictive.

**Implementation:**
```tsx
<View style={styles.completedBar}>
  <CheckCircle2 size={16} color={colors.primary} />
  <Text style={styles.completedBarText}>Session complete — great work!</Text>
  <TouchableOpacity onPress={() => navigation.navigate('ChatOverview')}>
    <Text style={styles.completedBarLink}>Back to sessions</Text>
  </TouchableOpacity>
</View>
```
Style: `backgroundColor: colors.successBg, borderTopWidth: 1, borderTopColor: colors.successBorder, padding: 16, flexDirection: 'row', alignItems: 'center', gap: 8`.

---

## 11. Onboarding

### 11.1 Add a Skip Button (P1)

**What to change:** There is no skip option in `OnboardingScreen.tsx`. Users must complete all 4 slides.

**Why:** Returning users who log out, or users who already understand the product, are forced through onboarding every time. More importantly: for new users who want to "just try it", forced onboarding is a conversion killer.

**Implementation:** Add a `Skip` button in the top-right corner of the first 3 slides (not on the consent slide, which is required):
```tsx
// In OnboardingScreen, overlay on the SafeAreaView:
{currentSlide < slides.length - 1 && (
  <TouchableOpacity
    style={styles.skipButton}
    onPress={() => goToSlide(slides.length - 1)} // jump to consent
    accessibilityLabel="Skip to last step"
  >
    <Text style={styles.skipText}>Skip</Text>
  </TouchableOpacity>
)}
```
Position: `position: 'absolute', top: 16, right: 20`. Style: `color: colors.textMuted, fontSize: 14, fontFamily: 'Inter_500Medium'`.

### 11.2 Progress Dots — Move Out of Absolute Positioning (P1)

**What to change:** Progress dots are `position: 'absolute', bottom: 28`. This overlaps slide content on short screens (iPhone SE).

**Why:** Absolute positioning of navigation elements means slide content can be hidden behind them. On an iPhone SE (568pt height), a slide with a long form at the bottom will be obscured.

**Implementation:** Remove `position: 'absolute'` from `progressContainer`. Place the `FlatList` and the dot row in a `View` with `flex: 1`:
```tsx
<SafeAreaView style={styles.container}>
  <FlatList style={{ flex: 1 }} ... />
  <View style={styles.progressContainer}>
    {/* dots */}
  </View>
</SafeAreaView>
```
Add `paddingBottom: 16` to `progressContainer`.

### 11.3 Swipe Gesture Feedback (P2)

**What to change:** The onboarding `FlatList` is swipeable but there is no gesture handle or instruction.

**Why:** Many users will not discover swipe navigation without a hint. This causes drop-off at the first slide.

**Implementation:** Add a "Swipe to continue" hint on the first slide only, that fades out after 2 seconds:
```ts
// In WelcomeSlide component:
useEffect(() => {
  const timer = setTimeout(() => setShowSwipeHint(false), 2000);
  return () => clearTimeout(timer);
}, []);
```
Render: small animated arrow pair `→` at the bottom of the first slide.

### 11.4 Visual Consistency of Onboarding Dot Colors (P1)

**What to change:** Inactive dots are `#e0e0e0`. Active dot is `#9ACDAF`. This uses a different green from the brand green `#4A8B6F`.

**Why:** `#9ACDAF` is `colors.primaryLight` — that's fine, but inactive dots at `#e0e0e0` are too faint on a white background.

**Implementation:**
```ts
dot:       { backgroundColor: colors.border },       // #E0E0E0 → acceptable but raise to #C8E6C9
dotActive: { backgroundColor: colors.primaryLight },  // #9ACDAF — keep
```
Change inactive dot `backgroundColor` to `#B8D4C5` for better distinction on white.

---

## 12. Dark Mode

### 12.1 Implement a Dark Mode Theme (P2)

**What to change:** The app has no dark mode support. `useColorScheme()` from React Native is not used anywhere.

**Why:** A significant percentage of users keep their phones in dark mode 24/7 (40-60% on iOS). Health apps used in the evening (for journaling, reflection) especially benefit from dark mode.

**Implementation:** Extend `ThemeContext` (or create it) to expose light/dark variants:

```ts
// src/contexts/ThemeContext.tsx
import { useColorScheme } from 'react-native';
import { colors } from '../constants/colors';

export function useTheme() {
  const scheme = useColorScheme();
  const isDark = scheme === 'dark';
  return {
    isDark,
    c: {
      background:    isDark ? colors.dark.background    : colors.background,
      surface:       isDark ? colors.dark.surface       : colors.surface,
      surfaceAlt:    isDark ? colors.dark.surfaceAlt    : colors.surfaceAlt,
      border:        isDark ? colors.dark.border        : colors.border,
      textPrimary:   isDark ? colors.dark.textPrimary   : colors.textPrimary,
      textSecondary: isDark ? colors.dark.textSecondary : colors.textSecondary,
      textMuted:     isDark ? colors.dark.textMuted     : colors.textMuted,
      userBubble:    isDark ? colors.dark.userBubble    : colors.userBubble,
      nalaBubble:    isDark ? colors.dark.nalaBubble    : colors.nalaBubble,
      // primary, accent, error stay the same in both modes
      primary:       colors.primary,
      accent:        colors.accent,
      error:         colors.error,
    }
  };
}
```

Dark mode palette (already defined in `colors.dark` above):

| Token | Dark Value | Notes |
|---|---|---|
| background | `#0F1A15` | Deep forest green-black |
| surface | `#1A2E23` | Card backgrounds |
| surfaceAlt | `#243D2F` | Input bg, unselected options |
| border | `#2D4A39` | Hairline separators |
| textPrimary | `#F0F7F4` | Near-white with a green tint |
| textSecondary | `#A3C4B5` | Body text |
| textMuted | `#6B9E85` | Labels, captions |
| userBubble | `#4A8B6F` | Same as primary — pops on dark bg |
| nalaBubble | `#1A2E23` | Same as surface |

The header gradients remain the same in dark mode — they are already dark green.

---

## 13. Brand Personality

### 13.1 Replace Unicode Arrows with Lucide Icons (P1)

**What to change:** Back buttons across all screens use `←` as a `Text` character. The send button uses `→`.

**Why:** Unicode arrows are system glyphs with inconsistent rendering across Android devices. They break the visual consistency of the `lucide-react-native` icon set already used in the codebase.

**Implementation:**
```tsx
import { ArrowLeft, Send } from 'lucide-react-native';

// Back button:
<ArrowLeft size={22} color={colors.surface} />

// Send button — replace the → text with:
<Send size={18} color={colors.surface} />
```

### 13.2 Add a Nala Logo/Avatar Mark (P1)

**What to change:** The app has no brand mark. The header shows text only. The chat uses a text initial "N" in `initialCircle`.

**Why:** A health coaching app builds trust through identity consistency. A simple leaf + circle mark (SVG, ~500 bytes) in the header and chat avatar reinforces brand memory.

**Implementation:** Create `src/assets/NalaAvatar.tsx` as an SVG component (using `react-native-svg`). Place it:
- In the chat header replacing or beside "Week X Session" text.
- As the Nala message avatar (replacing the `N` text initial).
- As a splash screen element.

Minimum viable version: a circle with a green-to-teal gradient and the letter N in Inter Bold white at 16px is already better than the current state.

### 13.3 Consistent Motivational Tone (P1)

**What to change:** The motivation card in `ChatOverviewScreen` says `"💪 Keep it up! Complete your next session."` The completion banner in `ChatScreen` says `"🎉 Session completed — chat locked."`.

**Why:** "Chat locked" is a system constraint framed as a punishment. "💪 Keep it up!" is fine but generic. Health coaching apps should feel like a supportive friend, not a to-do list app.

**Implementation — specific copy changes:**

| Current | Replace with |
|---|---|
| `"🎉 Session completed — chat locked."` | `"You completed this session. Well done."` |
| `"🔒 Chat is locked for this completed session."` | `"This session is complete. Head back to continue your journey."` |
| `"💪 Keep it up! Complete your next session."` | Rotate between 3 messages based on `completedCount`: 0: `"Your journey starts with one conversation."`, 1-2: `"You're building momentum. Keep going."`, 3: `"Almost there — one session left."`, 4: `"You've completed the full program. Remarkable."` |
| `"Checking session status..."` | `"Getting things ready..."` |
| `"Loading your progress..."` | `"Loading your journey..."` |

### 13.4 Settings Profile Card Polish (P1)

**What to change:** The profile card in `Settings.tsx` shows the raw email address as the "name" (`nameText`) and `"Logged in with Firebase"` as a subtitle.

**Why:** "Logged in with Firebase" is an implementation detail that means nothing to users. It makes the app feel like a demo rather than a product. Showing the email as a name is fine as a fallback, but the subtitle should be meaningful.

**Implementation:**
```tsx
// Replace:
<Text style={styles.emailText}>Logged in with Firebase</Text>

// With:
<Text style={styles.emailText}>Nala Health Coaching member</Text>
```
If the user's `displayName` is available from Firebase, show it as the primary name and move email to secondary:
```tsx
const displayName = user?.displayName;
const nameLabel = displayName || email;
const subLabel  = displayName ? email : 'Nala Health Coaching member';
```

---

## Implementation Priority Summary

| Priority | Count | Items |
|---|---|---|
| P0 (fix immediately) | 8 | Auto-scroll, line height, font size floor, safe area, back button layout, touch targets, accessibilityLabel, contrast ratios |
| P1 (next sprint) | 22 | Color palette, font family, FlatList migration, timestamps, sender label removal, input padding, send feedback, message animation, session completion, empty states, error states, progress bar, session card copy, input multiline, placeholder, locked state, skip button, dot positioning, tab bar, Lucide icons, logo, copy tone, profile card |
| P2 (polish sprint) | 8 | Bubble tails, card gradients, progress rings, character count, swipe hint, dot animation, dark mode, motivational quotes |

---

## File Locations for Implementation

| File | Changes needed |
|---|---|
| `src/constants/colors.ts` | Create (new file) |
| `src/constants/typography.ts` | Create (new file) |
| `src/contexts/ThemeContext.tsx` | Create (new file) |
| `src/components/chat/MessageBubble.tsx` | Extract from ChatScreen (new file) |
| `src/components/ProgressRing.tsx` | Create (new file) |
| `src/screens/ChatScreen.tsx` | Auto-scroll, FlatList, multiline input, animations, locked state copy, accessibilityLabels |
| `src/screens/ChatOverviewScreen.tsx` | Progress bar, card redesign, skeleton loader, error state, tab nav |
| `src/screens/LoginScreen.tsx` | Back button layout, color refs, accessibilityLabels |
| `src/screens/OnboardingScreen.tsx` | Skip button, dot positioning, dot colors |
| `src/screens/Settings.tsx` | Profile card copy, color refs |
| `src/navigation/MainTabs.tsx` | Create bottom tab navigator (new file) |
