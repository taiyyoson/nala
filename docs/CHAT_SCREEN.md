# ChatScreen Component Documentation

## Overview

`ChatScreen.tsx` is the core conversation interface for Nala Health Coach. It handles real-time messaging between users and the AI coach, session state management, and displays session completion status.

**Location:** `frontend/src/screens/ChatScreen.tsx`

---

## Features

- ✅ **Real-time chat interface** with animated typing indicators
- ✅ **Session completion detection** - locks chat when session is done
- ✅ **Conversation persistence** - maintains conversation_id across messages
- ✅ **Dynamic text sizing** - respects user accessibility settings
- ✅ **Automatic session greeting** - sends `[START_SESSION]` on mount
- ✅ **Backend health check** - verifies API connectivity before starting
- ✅ **Auto-navigation** - redirects to overview 1.8s after completion

---

## Props

```typescript
type Props = {
  navigation: ChatScreenNavigationProp;
  route: ChatScreenRouteProp;
};
```

### Route Params

```typescript
route.params = {
  sessionId: string;  // e.g., "1", "2", "3", "4"
  week: number;       // 1-4 (session number)
  sessionNumber: number; // Redundant with week (should be same value)
}
```

---

## State Variables

### Message State

```typescript
const [messages, setMessages] = useState<Message[]>([]);
```

**Message Type:**
```typescript
type Message = {
  id: number;            // Timestamp-based unique ID
  sender: "nala" | "user";
  text: string;
  timestamp: Date;
  isLoading?: boolean;   // Shows typing indicator when true
};
```

### Session State

```typescript
const [sessionComplete, setSessionComplete] = useState(false);
const [loadingCompletionStatus, setLoadingCompletionStatus] = useState(true);
const [conversationId, setConversationId] = useState<string>("");
```

### UI State

```typescript
const [input, setInput] = useState("");
const [isLoading, setIsLoading] = useState(false);
const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
```

### Text Sizing

```typescript
const { size } = useTextSize();
const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;
```

---

## Key Functions

### `fetchCompletionStatus()`

**Purpose:** Check if the current session has been completed previously.

**Called:** On component mount (`useEffect` with `[week]` dependency)

**Logic:**
1. Fetches all progress for user: `GET /session/progress/{userId}`
2. Filters results where `session_number === week`
3. Checks if any matching record has `completed_at` timestamp
4. Sets `sessionComplete` to `true` if found

**Why?** Prevents users from re-doing completed sessions.

```typescript
useEffect(() => {
  const fetchCompletionStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/session/progress/${userId}`);
      const data = await res.json();

      const matching = data.filter((s: any) => s.session_number === week);
      const isCompleted = matching.some((s: any) => s.completed_at);

      setSessionComplete(isCompleted);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCompletionStatus(false);
    }
  };

  fetchCompletionStatus();
}, [week]);
```

---

### `sendInitialGreeting()`

**Purpose:** Send the session start signal to backend on first load.

**Called:** After backend health check passes and session is not complete.

**Message:** `"[START_SESSION]"` - a special command recognized by the RAG system.

**Flow:**
1. Creates loading message placeholder with `isLoading: true`
2. Sends POST to `/chat/message` with `[START_SESSION]`
3. Backend returns AI's opening greeting (e.g., "Hi! I'm Nala...")
4. Replaces placeholder with actual response
5. Stores `conversation_id` for subsequent messages

```typescript
const sendInitialGreeting = async (message = "[START_SESSION]") => {
  try {
    setIsLoading(true);

    const placeholder: Message = {
      id: Date.now(),
      sender: "nala",
      text: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages([placeholder]);

    const res = await fetch(`${API_BASE}/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        user_id: userId,
        session_number: week,
        conversation_id: conversationId || undefined,
      }),
    });

    const data = await res.json();
    if (data.conversation_id) setConversationId(data.conversation_id);

    setMessages([{ ...placeholder, text: data.response, isLoading: false }]);
  } finally {
    setIsLoading(false);
  }
};
```

---

### `sendUserMessage()`

**Purpose:** Send user's typed message to backend and get AI response.

**Triggered by:** Send button press

**Flow:**
1. Validates input is not empty/whitespace
2. Checks session is not complete
3. Adds user message to UI immediately (optimistic update)
4. Adds loading placeholder for AI response
5. Sends POST to `/chat/message`
6. Replaces loading placeholder with actual response
7. Checks if `session_complete: true` in response
8. If complete, navigates to ChatOverview after 1.8s

```typescript
const sendUserMessage = async () => {
  if (!input.trim() || isLoading || sessionComplete) return;

  const text = input.trim();
  setInput("");

  const userMsg: Message = {
    id: Date.now(),
    sender: "user",
    text,
    timestamp: new Date(),
  };

  const loadingMsg: Message = {
    id: Date.now() + 1,
    sender: "nala",
    text: "",
    timestamp: new Date(),
    isLoading: true,
  };

  setMessages((prev) => [...prev, userMsg, loadingMsg]);
  setIsLoading(true);

  try {
    const res = await fetch(`${API_BASE}/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        user_id: userId,
        conversation_id: conversationId || undefined,
        session_number: week,
      }),
    });

    const data = await res.json();

    if (data.conversation_id) setConversationId(data.conversation_id);
    if (data.session_complete) {
      setSessionComplete(true);
      setTimeout(() => navigation.replace("ChatOverview"), 1800);
    }

    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === loadingMsg.id
          ? { ...msg, text: data.response, isLoading: false }
          : msg
      )
    );
  } finally {
    setIsLoading(false);
  }
};
```

---

## UI Components

### Header

```tsx
<View style={styles.header}>
  <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
    <Text style={[styles.backArrow, { fontSize: fontScale + 6 }]}>←</Text>
  </TouchableOpacity>

  <Text style={[styles.headerTitle, { fontSize: fontScale + 2 }]}>
    Week {week} Session
  </Text>
</View>
```

**Features:**
- Green background (#4A8B6F)
- Back arrow to return to ChatOverview
- Displays current week number

---

### Session Complete Banner

```tsx
{sessionComplete && (
  <View style={styles.sessionCompleteBanner}>
    <Text style={[styles.sessionCompleteText, { fontSize: fontScale }]}>
      🎉 Session completed — chat locked.
    </Text>
  </View>
)}
```

**Shown when:** `sessionComplete === true`

**Purpose:** Visual indicator that session is done and chat is locked.

---

### Messages ScrollView

```tsx
<ScrollView
  ref={scrollViewRef}
  style={styles.messagesContainer}
  contentContainerStyle={styles.messagesContent}
>
  {messages.map((m) => (
    <View
      key={m.id}
      style={[
        styles.messageWrapper,
        m.sender === "user"
          ? styles.userMessageWrapper
          : styles.nalaMessageWrapper,
      ]}
    >
      <View
        style={[
          styles.messageBubble,
          m.sender === "user" ? styles.userBubble : styles.nalaBubble,
        ]}
      >
        {/* Sender label */}
        <Text style={[styles.senderName, ...]}>
          {m.sender === "user" ? "You" : "Nala"}
        </Text>

        {/* Message or typing indicator */}
        {m.isLoading ? (
          <TypingIndicator />
        ) : (
          <Text style={[styles.messageText, ...]}>{m.text}</Text>
        )}
      </View>
    </View>
  ))}
</ScrollView>
```

**Message Styling:**
- **User messages:** Green bubble (#2E7D32), right-aligned, white text
- **Nala messages:** Light green bubble (#E8F5E9), left-aligned, dark text
- **Sender labels:** "You" vs "Nala" at top of each bubble

---

### Typing Indicator

```tsx
function TypingIndicator() {
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    [dot1, dot2, dot3].forEach((dot, i) => {
      Animated.loop(
        Animated.sequence([
          Animated.timing(dot, { toValue: 1, duration: 400, delay: i * 200, useNativeDriver: true }),
          Animated.timing(dot, { toValue: 0, duration: 400, useNativeDriver: true }),
        ])
      ).start();
    });
  }, []);

  return (
    <View style={styles.typingContainer}>
      {[dot1, dot2, dot3].map((dot, i) => (
        <Animated.View key={i} style={[styles.dot, { opacity: ..., transform: ... }]} />
      ))}
    </View>
  );
}
```

**Animation:** 3 dots that fade and bounce in sequence.

**Shown when:** `message.isLoading === true`

---

### Input Area

**Normal State:**
```tsx
<View style={styles.inputArea}>
  <TextInput
    style={[styles.input, { fontSize: fontScale }]}
    placeholder="Type your message..."
    value={input}
    onChangeText={setInput}
    editable={!isLoading}
  />

  <TouchableOpacity
    style={[
      styles.sendButton,
      (!input.trim() || isLoading) && styles.sendButtonDisabled,
    ]}
    disabled={!input.trim() || isLoading}
    onPress={sendUserMessage}
  >
    <Text style={[styles.sendButtonText, { fontSize: fontScale + 2 }]}>→</Text>
  </TouchableOpacity>
</View>
```

**Locked State (when session complete):**
```tsx
<View style={styles.lockedContainer}>
  <Text style={[styles.lockedText, { fontSize: fontScale }]}>
    🔒 Chat is locked for this completed session.
  </Text>
</View>
```

---

## Backend Integration

### API Endpoint: POST /chat/message

**Request:**
```typescript
{
  message: string;          // User's message or "[START_SESSION]"
  user_id: string;          // Firebase UID
  session_number: number;   // 1-4
  conversation_id?: string; // Optional, for continuing conversation
}
```

**Response:**
```typescript
{
  response: string;          // AI's response text
  conversation_id: string;   // UUID for this conversation
  session_complete: boolean; // True when session is done
  metadata?: {
    model: string;           // "claude-sonnet-4" or "gpt-4"
    source_count: number;    // Number of RAG sources used
  }
}
```

---

## Session Completion Flow

1. **User sends final message** (determined by RAG system logic)
2. **Backend responds** with `session_complete: true`
3. **Frontend sets** `sessionComplete` state to `true`
4. **UI updates:**
   - Shows completion banner
   - Locks input area
   - Displays "Chat is locked" message
5. **Auto-navigation:** After 1.8 seconds, navigates to `ChatOverview`
6. **Backend marks session complete:** POST `/session/complete?user_id=X&session_number=Y`
7. **Next session unlocks:** 7 days after completion timestamp

---

## Accessibility Features

### Dynamic Text Sizing

All text elements use `fontScale` based on user's text size preference:

```typescript
const { size } = useTextSize();
const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;

// Applied to all text:
<Text style={{ fontSize: fontScale }}>...</Text>
<Text style={{ fontSize: fontScale - 2 }}>...</Text>  // Smaller text
<Text style={{ fontSize: fontScale + 2 }}>...</Text>  // Larger text
```

**Settings Path:** Settings → Text Size → Small/Medium/Large

---

## Error Handling

### Backend Connection Failure

```typescript
try {
  const res = await fetch(`${API_BASE}/health`);
  const ok = res.ok;
  setBackendConnected(ok);

  if (ok && !sessionComplete) {
    sendInitialGreeting("[START_SESSION]");
  }
} catch {
  setBackendConnected(false);
}
```

**If failed:** `backendConnected` is `false` (currently no UI indication shown)

### Message Send Failure

Errors are logged to console but not shown to user:
```typescript
} catch (error) {
  console.error("❌ Chat message failed:", error);
}
```

**TODO:** Add user-facing error messages/toasts.

---

## Known Issues

### 1. No Error UI
**Problem:** Network errors are logged but not shown to users.

**Solution:** Add error state and display toast/alert:
```typescript
const [error, setError] = useState<string | null>(null);

// In catch blocks:
setError("Failed to send message. Please try again.");

// In UI:
{error && <Text style={styles.errorText}>{error}</Text>}
```

---

### 2. ScrollView Auto-Scroll
**Problem:** New messages don't auto-scroll to bottom.

**Solution:** Add scroll-to-end after adding messages:
```typescript
scrollViewRef.current?.scrollToEnd({ animated: true });
```

---

### 3. Redundant Route Params
**Problem:** Both `week` and `sessionNumber` are passed with same value.

**Solution:** Remove `sessionNumber` from navigation params:
```typescript
// In ChatOverviewScreen:
navigation.navigate("Chat", {
  sessionId: session.id.toString(),
  week: session.id,
  // Remove sessionNumber
})
```

---

## Testing Checklist

- [ ] Initial greeting appears on first load
- [ ] User can send messages and receive responses
- [ ] Typing indicator shows while waiting
- [ ] Messages display correct sender (You vs Nala)
- [ ] Text size changes when adjusted in Settings
- [ ] Session complete banner shows when session ends
- [ ] Input is locked after session completion
- [ ] Auto-navigates to overview after completion
- [ ] Completed session shows locked UI on re-entry
- [ ] Back button returns to ChatOverview
- [ ] Conversation persists across multiple messages

---

## Related Files

- [ChatOverviewScreen.tsx](../frontend/src/screens/ChatOverviewScreen.tsx) - Session dashboard
- [ApiService.ts](../frontend/src/services/ApiService.ts) - HTTP client
- [TextSizeContext.tsx](../frontend/src/contexts/TextSizeContext.tsx) - Text size state
- [backend/routes/chat.py](../backend/routes/chat.py) - Chat endpoint
- [backend/routes/session.py](../backend/routes/session.py) - Session progress tracking

---

**Last Updated:** December 3, 2024
