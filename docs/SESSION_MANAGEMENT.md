# Session Management System Documentation

## Overview

The Session Management System controls how users progress through Nala's 4-week coaching program. It handles session unlocking, completion tracking, and visual progress indicators across the frontend and backend.

---

## Core Concepts

### The 4-Week Program

```
Week 1: Getting to know you (Always unlocked)
   ↓ Complete → Wait 7 days
Week 2: Building habits (Unlocks 7 days after Week 1)
   ↓ Complete → Wait 7 days
Week 3: Overcoming challenges (Unlocks 7 days after Week 2)
   ↓ Complete → Wait 7 days
Week 4: Reviewing progress (Unlocks 7 days after Week 3)
   ↓ Complete → Program finished
```

### Session States

1. **Locked** 🔒 - Not yet accessible (gray card)
2. **Unlocked** 🎯 - Ready to start (pink card)
3. **In Progress** 💬 - User is actively chatting
4. **Completed** ✅ - Session finished (green card)

---

## Backend Implementation

### Database Schema

#### `session_progress` Table

```sql
CREATE TABLE session_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(255) NOT NULL,
    session_number INTEGER NOT NULL,
    completed_at TIMESTAMP NULL,
    unlocked_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, session_number)
);
```

**Key Fields:**
- `completed_at`: When user finished this session (NULL if not complete)
- `unlocked_at`: When this session became available (NULL if still locked)

---

### API Endpoints

#### POST /session/complete

**Purpose:** Mark a session as complete and unlock the next one.

**Parameters:**
```
user_id: string       (query param)
session_number: int   (query param)
```

**Logic:**
1. Find or create `SessionProgress` record for current session
2. Call `progress.mark_complete(unlock_delay_days=7)`
   - Sets `completed_at` to current timestamp
   - Calculates unlock time for next session (now + 7 days)
3. Find or create `SessionProgress` for next session
4. Set `unlocked_at` on next session record
5. Commit to database

**Response:**
```json
{
  "message": "Session marked complete",
  "completed_session": {
    "session_number": 1,
    "completed_at": "2024-12-03T10:30:00Z",
    "unlocked_at": "2024-12-01T00:00:00Z"
  },
  "next_session": {
    "session_number": 2,
    "completed_at": null,
    "unlocked_at": "2024-12-10T10:30:00Z"
  }
}
```

**Implementation:**
```python
@router.post("/complete")
def mark_session_complete(
    user_id: str, session_number: int, db: Session = Depends(get_db)
):
    progress = (
        db.query(SessionProgress)
        .filter_by(user_id=user_id, session_number=session_number)
        .first()
    )

    if not progress:
        progress = SessionProgress(user_id=user_id, session_number=session_number)
        db.add(progress)

    # Mark complete and get unlock time for next
    unlock_time_for_next = progress.mark_complete(unlock_delay_days=7)

    # Unlock next session
    next_session_number = session_number + 1
    if next_session_number <= 4:
        next_session_progress = (
            db.query(SessionProgress)
            .filter_by(user_id=user_id, session_number=next_session_number)
            .first()
        )

        if not next_session_progress:
            next_session_progress = SessionProgress(
                user_id=user_id,
                session_number=next_session_number,
                unlocked_at=unlock_time_for_next,
            )
            db.add(next_session_progress)
        elif not next_session_progress.unlocked_at:
            next_session_progress.unlocked_at = unlock_time_for_next

    db.commit()
    # ...
```

---

#### GET /session/progress/{user_id}

**Purpose:** Get all session progress records for a user.

**Response:**
```json
[
  {
    "session_number": 1,
    "completed_at": "2024-12-01T10:00:00Z",
    "unlocked_at": "2024-11-28T00:00:00Z"
  },
  {
    "session_number": 2,
    "completed_at": null,
    "unlocked_at": "2024-12-08T10:00:00Z"
  },
  {
    "session_number": 3,
    "completed_at": null,
    "unlocked_at": null
  }
]
```

**Note:** Returns empty array `[]` if user has no progress yet.

---

### SessionProgress Model

**Location:** `backend/models/session_progress.py`

#### `mark_complete()` Method

```python
def mark_complete(self, unlock_delay_days: int = 7) -> datetime:
    """
    Mark this session as complete.

    Args:
        unlock_delay_days: Days until next session unlocks

    Returns:
        datetime: When next session should unlock
    """
    self.completed_at = datetime.utcnow()
    next_unlock = self.completed_at + timedelta(days=unlock_delay_days)
    return next_unlock
```

---

## Frontend Implementation

### ChatOverviewScreen.tsx

**Location:** `frontend/src/screens/ChatOverviewScreen.tsx`

#### Data Fetching

```typescript
useEffect(() => {
  const fetchProgress = async () => {
    try {
      const user = getAuth().currentUser;
      if (!user) throw new Error("User not logged in");

      const data = await ApiService.getUserProgress(user.uid);
      setProgress(data);
    } catch (error) {
      console.error("❌ Failed to fetch progress:", error);
      Alert.alert("Error", "Couldn't load your session progress.");
    } finally {
      setLoading(false);
    }
  };

  fetchProgress();
}, []);
```

---

#### Unlock Logic: `isSessionUnlocked()`

**Purpose:** Determine if a session is accessible to the user.

**Algorithm:**
```typescript
const isSessionUnlocked = (sessionNumber: number): boolean => {
  // Week 1 is always unlocked
  if (sessionNumber === 1) return true;

  // Check if current session has unlocked_at timestamp
  const current = progress.find((p) => p.session_number === sessionNumber);
  if (current?.unlocked_at) {
    // Compare unlock time with current time
    return new Date() >= new Date(current.unlocked_at);
  }

  // Fallback: check if previous session is complete
  const prev = progress.find((p) => p.session_number === sessionNumber - 1);
  return !!prev?.completed_at;
};
```

**Cases:**
1. **Session 1:** Always returns `true`
2. **Has `unlocked_at`:** Returns `true` if current time >= unlock time
3. **No `unlocked_at`:** Returns `true` if previous session has `completed_at`

---

#### Completion Logic: `isSessionComplete()`

```typescript
const isSessionComplete = (sessionNumber: number): boolean => {
  return !!progress.find(
    (p) => p.session_number === sessionNumber && p.completed_at
  );
};
```

**Simple check:** Does a record exist with both matching `session_number` AND non-null `completed_at`?

---

#### Countdown Display: `getUnlockCountdown()`

**Purpose:** Show "Unlocks in X days" for locked sessions.

```typescript
const getUnlockCountdown = (sessionNumber: number): string | null => {
  if (sessionNumber === 1) return null; // Week 1 has no countdown

  const prevSession = progress.find((p) => p.session_number === sessionNumber - 1);
  if (!prevSession || !prevSession.unlocked_at) return "Locked";

  const unlockTime = new Date(prevSession.unlocked_at);
  const now = new Date();
  const diffDays = Math.ceil((unlockTime.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays > 1) return `Unlocks in ${diffDays} days`;
  if (diffDays === 1) return "Unlocks tomorrow";
  if (diffDays === 0) return "Unlocks today";

  return "Unlocked";
};
```

**Note:** Currently checks `prevSession.unlocked_at` instead of current session. This should be updated to:
```typescript
const current = progress.find((p) => p.session_number === sessionNumber);
if (!current?.unlocked_at) return "Locked";

const unlockTime = new Date(current.unlocked_at);
// ... rest of calculation
```

---

#### Visual States

**Card Colors:**
```typescript
let cardColor = "#E5E7EB"; // Default: Locked (gray)
if (completed) cardColor = "#4A8B6F"; // Completed (green)
else if (unlocked) cardColor = "#BF5F83"; // Unlocked (pink)
```

**Icons:**
```tsx
{completed ? (
  <CheckCircle2 color="#FFF" size={22} />
) : unlocked ? (
  <Calendar color="#FFF" size={22} />
) : (
  <Lock color="#6B7280" size={22} />
)}
```

**Text:**
```tsx
<Text>
  {completed
    ? "Completed"
    : unlocked
    ? session.title  // "Getting to know you"
    : getUnlockCountdown(session.id) // "Unlocks in 3 days"
  }
</Text>
```

---

### ChatScreen.tsx

#### Completion Detection

In `sendUserMessage()`:
```typescript
const data = await res.json();

if (data.session_complete) {
  setSessionComplete(true);
  setTimeout(() => navigation.replace("ChatOverview"), 1800);
}
```

**Flow:**
1. Backend RAG system decides when session is complete
2. Backend responds with `session_complete: true`
3. Frontend sets local state and shows completion banner
4. **⚠️ Issue:** Frontend does NOT call `/session/complete` endpoint
5. User must manually call it or backend must do it automatically

---

#### Re-Entry Lock

```typescript
useEffect(() => {
  const fetchCompletionStatus = async () => {
    const res = await fetch(`${API_BASE}/session/progress/${userId}`);
    const data = await res.json();

    const matching = data.filter((s: any) => s.session_number === week);
    const isCompleted = matching.some((s: any) => s.completed_at);

    setSessionComplete(isCompleted);
  };

  fetchCompletionStatus();
}, [week]);
```

**Purpose:** When user revisits a completed session, show locked UI.

---

## Complete Session Flow (E2E)

### User Completes Week 1

#### 1. User in ChatScreen (Week 1)
```
User: "Thanks, this was really helpful!"
Nala: "I'm glad! You've made great progress. See you next week!"
```

#### 2. Backend RAG System Decides Completion
```python
# In AI-backend/rag_dynamic.py or chat route
if self.should_end_session(user_message, response):
    return {
        "response": response,
        "session_complete": True
    }
```

#### 3. Frontend Receives `session_complete: true`
```typescript
if (data.session_complete) {
  setSessionComplete(true);
  // TODO: Should call ApiService.markSessionComplete(userId, week)
  setTimeout(() => navigation.replace("ChatOverview"), 1800);
}
```

#### 4. Backend Marks Completion (via route)
```python
# POST /session/complete?user_id=abc&session_number=1
progress = SessionProgress.query.filter_by(user_id="abc", session_number=1).first()
progress.mark_complete(unlock_delay_days=7)
# Sets: completed_at = 2024-12-03 10:00:00

next_progress = SessionProgress(user_id="abc", session_number=2)
next_progress.unlocked_at = 2024-12-10 10:00:00  # 7 days later
db.commit()
```

#### 5. User Navigates to ChatOverview
```
Week 1: ✅ Completed (Green)
Week 2: 🔒 Unlocks in 7 days (Gray)
Week 3: 🔒 Locked (Gray)
Week 4: 🔒 Locked (Gray)
```

#### 6. Seven Days Later (Dec 10)
User opens app, `fetchProgress()` runs:
```json
[
  { "session_number": 1, "completed_at": "2024-12-03T10:00:00Z", ... },
  { "session_number": 2, "unlocked_at": "2024-12-10T10:00:00Z", ... }
]
```

`isSessionUnlocked(2)` checks:
```typescript
const current = progress.find(p => p.session_number === 2);
// current.unlocked_at = "2024-12-10T10:00:00Z"
// new Date() = "2024-12-10T15:00:00Z" (later)
return new Date() >= new Date(current.unlocked_at); // true ✅
```

**UI Updates:**
```
Week 1: ✅ Completed (Green)
Week 2: 🎯 Building habits (Pink) ← NOW CLICKABLE
Week 3: 🔒 Locked (Gray)
Week 4: 🔒 Locked (Gray)
```

---

## Edge Cases & Issues

### Issue 1: Frontend Doesn't Call `/session/complete`

**Problem:** When chat ends with `session_complete: true`, frontend doesn't notify backend.

**Current State:**
```typescript
if (data.session_complete) {
  setSessionComplete(true); // Only local state change
  setTimeout(() => navigation.replace("ChatOverview"), 1800);
}
```

**Solution:** Add API call:
```typescript
if (data.session_complete) {
  setSessionComplete(true);

  // Mark session complete in backend
  try {
    await ApiService.markSessionComplete(userId, week);
  } catch (err) {
    console.error("Failed to mark session complete:", err);
  }

  setTimeout(() => navigation.replace("ChatOverview"), 1800);
}
```

---

### Issue 2: Multiple Completion Records

**Problem:** Database might have multiple records for same user/session if:
- User starts session multiple times before completing
- Race conditions in session creation

**Solution:** Use database UNIQUE constraint:
```sql
UNIQUE(user_id, session_number)
```

And handle conflicts:
```python
progress = db.query(SessionProgress).filter_by(
    user_id=user_id,
    session_number=session_number
).first()

if not progress:
    progress = SessionProgress(...)
    db.add(progress)
```

---

### Issue 3: Countdown Uses Wrong Timestamp

**Problem:** `getUnlockCountdown()` checks `prevSession.unlocked_at` instead of current session's timestamp.

**Fix:**
```typescript
const getUnlockCountdown = (sessionNumber: number): string | null => {
  if (sessionNumber === 1) return null;

  // Get CURRENT session's unlock time
  const current = progress.find((p) => p.session_number === sessionNumber);
  if (!current?.unlocked_at) return "Locked";

  const unlockTime = new Date(current.unlocked_at);
  const now = new Date();
  const diffDays = Math.ceil((unlockTime.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays > 1) return `Unlocks in ${diffDays} days`;
  if (diffDays === 1) return "Unlocks tomorrow";
  if (diffDays === 0) return "Unlocks today";

  return null; // Already unlocked
};
```

---

### Issue 4: Week 1 Not Auto-Unlocked for New Users

**Problem:** Brand new users have no `session_progress` records, so Week 1 shows as locked.

**Solution:** Frontend already handles this:
```typescript
if (sessionNumber === 1) return true; // Week 1 always unlocked
```

But backend should pre-create record on user signup:
```python
# In user registration route
new_user = User(...)
db.add(new_user)

# Pre-unlock Week 1
week1_progress = SessionProgress(
    user_id=new_user.uid,
    session_number=1,
    unlocked_at=datetime.utcnow()
)
db.add(week1_progress)
db.commit()
```

---

## Testing Scenarios

### Scenario 1: New User First Session

**Steps:**
1. User signs up → Week 1 should be unlocked
2. User taps Week 1 → ChatScreen opens
3. User completes conversation → `session_complete: true`
4. Backend marks Week 1 complete, Week 2 unlocks in 7 days
5. User sees ChatOverview with Week 1 green, Week 2 gray with countdown

**Expected DB State:**
```sql
user_id | session_number | completed_at       | unlocked_at
--------|----------------|--------------------|-----------------
abc123  | 1              | 2024-12-03 10:00   | 2024-11-28 00:00
abc123  | 2              | NULL               | 2024-12-10 10:00
```

---

### Scenario 2: Time-Based Unlock

**Steps:**
1. User completed Week 1 on Dec 1 at 3pm
2. Week 2 unlocked at Dec 8 at 3pm
3. User opens app on Dec 8 at 2pm → Week 2 still locked
4. User opens app on Dec 8 at 4pm → Week 2 now unlocked

**Logic:**
```typescript
const unlockTime = new Date("2024-12-08T15:00:00Z");
const now = new Date("2024-12-08T16:00:00Z");
return now >= unlockTime; // true
```

---

### Scenario 3: Revisiting Completed Session

**Steps:**
1. User completed Week 2
2. User navigates back to ChatScreen for Week 2
3. `fetchCompletionStatus()` runs → finds `completed_at`
4. UI shows locked state with banner

**Expected UI:**
- 🎉 Session completed — chat locked.
- Input area shows: 🔒 Chat is locked for this completed session.
- No way to send messages

---

## Configuration

### Unlock Delay Duration

**Current:** 7 days (hardcoded)

**Location:** `backend/routes/session.py`
```python
unlock_time_for_next = progress.mark_complete(unlock_delay_days=7)
```

**To Change:**
1. Update in backend route or move to environment variable
2. Update in `SessionProgress.mark_complete()` default param

**For Testing:**
```python
# Set to 1 minute for quick testing
unlock_time_for_next = progress.mark_complete(unlock_delay_days=0.0007)  # ~1 min
```

---

## Related Files

### Backend
- [backend/routes/session.py](../backend/routes/session.py) - Session API endpoints
- [backend/models/session_progress.py](../backend/models/session_progress.py) - SessionProgress model

### Frontend
- [frontend/src/screens/ChatOverviewScreen.tsx](../frontend/src/screens/ChatOverviewScreen.tsx) - Visual dashboard
- [frontend/src/screens/ChatScreen.tsx](../frontend/src/screens/ChatScreen.tsx) - Chat interface
- [frontend/src/services/ApiService.ts](../frontend/src/services/ApiService.ts) - API client

---

**Last Updated:** December 3, 2024
