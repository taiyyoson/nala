# Nala Health Coach — Full Sweep: Debug, Security, Cleanup & E2E Outline

## Context
The app is a 4-week AI health coaching platform (React Native + FastAPI + RAG). A full audit found **11 security issues**, **8 dead code areas**, **7 code organization problems**, and gaps in the sign-in → session-4 E2E flow. This plan addresses all findings in priority order.

---

## Phase 1: Critical Security Fixes

### 1A. Rotate all leaked API keys (MANUAL — user action)
- OpenAI, Anthropic, and PostgreSQL credentials were committed in earlier git history
- User must rotate keys on OpenAI dashboard, Anthropic console, and Render DB
- Optionally run BFG Repo-Cleaner to scrub `.env` from git history

### 1B. Wire up authentication middleware to all API routes
- **`backend/app.py`**: Register the existing `auth_router` from `authentication/auth_routes.py`
- **`backend/routes/chat.py`**: Add `Depends(verify_token)` to `send_message`, `get_conversation`, `get_conversations`, `delete_conversation`. Extract `user_id` from the decoded token, not from `request.user_id`
- **`backend/routes/session.py`**: Add `Depends(verify_token)` to all endpoints. Extract `user_id` from token
- **`backend/routes/user.py`**: Add `Depends(verify_token)` to `update_onboarding_status` and `get_user_status`. Replace raw `dict` param with a Pydantic model
- **`backend/authentication/auth_routes.py`**: Rename the inner `verify_token` function to `verify_token_endpoint` to fix the name collision (line 53)

### 1C. Frontend sends Firebase ID tokens
- **`frontend/src/services/ApiService.ts`**: Add a helper that calls `getAuth().currentUser?.getIdToken()` and attaches `Authorization: Bearer <token>` header to every request
- Update all fetch calls in `ChatScreen.tsx` and any direct API calls to use this helper

### 1D. Restrict CORS origins
- **`backend/config/settings.py`** line 26: Change `cors_origins` default from `["*"]` to `["http://localhost:8000", "http://localhost:19006"]`
- Production origins can be added via `.env`

### 1E. Add rate limiting on chat endpoint
- Install `slowapi` in `backend/requirements.txt`
- **`backend/app.py`**: Add `Limiter` middleware
- **`backend/routes/chat.py`**: Decorate `send_message` with `@limiter.limit("20/minute")`

### 1F. Wire up input validation
- **`backend/routes/chat.py`**: Add `max_length=5000` to `ChatRequest.message` field
- Call existing `RequestAdapter.validate_message_content()` or inline the constraint via Pydantic `Field`

### 1G. Stop leaking internal errors
- **`backend/routes/chat.py`** line 270 (and similar in other routes): Log full exception server-side, return generic `detail="Internal server error"` to client

### 1H. Disable debug mode by default
- **`backend/config/settings.py`** line 9: Change `debug: bool = True` → `debug: bool = False`

---

## Phase 2: Dead / Redundant Code Removal

| # | What to delete | Path |
|---|---------------|------|
| 1 | Unused RAG service | `backend/services/rag_service.py` |
| 2 | Unused events directory | `backend/events_future/` (entire dir) |
| 3 | Dead Firebase test screen | `frontend/src/screens/FirebaseTestScreen.tsx` |
| 4 | Unused StorageService | `frontend/src/services/StorageService.ts` |
| 5 | Unused styles in WelcomeScreen | `frontend/src/screens/WelcomeScreen.tsx` — remove `orText`, `socialButtonsContainer`, `socialButton`, `socialButtonText` styles |
| 6 | Commented-out session locking code | `frontend/src/screens/ChatOverviewScreen.tsx` lines 82-94 and scattered commented imports |

### Unused imports to clean up

| File | Unused Import |
|------|--------------|
| `backend/app.py` | `HTTPException`, `StreamingResponse` |
| `backend/routes/chat.py` | `asyncio`, `json`, `RequestAdapter` (unless wired in 1F) |
| `backend/services/ai_service.py` | `os` |
| `backend/models/session_progress.py` | `declarative_base` |
| `backend/models/__init__.py` | `"User"` and `"session_progress"` in `__all__` |

---

## Phase 3: Code Organization Improvements

### 3A. Fix unbounded AI service cache
- **`backend/routes/chat.py`** line 30: Replace bare `Dict` cache with an `OrderedDict` or `functools.lru_cache` with max 100 entries. Evict on session completion

### 3B. Extract send_message logic into service layer
- **`backend/routes/chat.py`** lines 167-270: Move session completion detection, AI service orchestration, and database writes into `backend/services/chat_service.py`. Handler should be ~20 lines

### 3C. Centralize `sys.path` manipulation
- **`chat.py`, `session.py`, `ai_service.py`, `rag_service.py`**: All insert `AI-backend` path. Centralize in `backend/config/__init__.py` or a shared `setup_paths.py`

### 3D. Extract shared fontScale helper
- **`ChatScreen.tsx`, `ChatOverviewScreen.tsx`, `Settings.tsx`**: All have identical `fontScale = size === "small" ? 14 : ...` ternary. Export `getFontScale(size)` from `TextSizeContext.tsx`

### 3E. Fix wildcard import
- **`backend/authentication/auth_service.py`** line 2: Change `from config.firebase_config import *` → `import config.firebase_config`

### 3F. Remove or consolidate duplicate root package.json
- Root `package.json` duplicates frontend deps. Either delete it or set up npm workspaces

### 3G. Fix `mark_complete` double-write of `unlocked_at`
- **`backend/models/session_progress.py`** lines 21-33: Guard against re-setting `unlocked_at` if already set. Clarify that unlock time belongs on the NEXT session's record only

---

## Phase 4: E2E Test Outline (Sign-in → Session 4 Completion)

### Flow 1: New User Registration & Onboarding
1. Open app → lands on `LoginScreen`
2. Tap "Sign Up" → navigate to `SignUpScreen`
3. Enter email + password → Firebase creates account
4. Auto-login → `AuthContext` sets `loggedInUser`
5. Backend check: `GET /user/status/{uid}` → 404 (new user)
6. Route to `OnboardingScreen` → swipe through 4 slides
7. Tap "Get Started" → `POST /user/onboarding` → `onboarding_completed: true`
8. Navigate to `ChatOverviewScreen`
- **Assert**: 4 week cards visible. Week 1 = unlocked (pink). Weeks 2-4 = locked (gray) [currently all unlocked for demo]

### Flow 2: Session 1 — "Getting to Know You"
1. Tap Week 1 card → navigate to `ChatScreen {sessionNumber: 1}`
2. On mount: `POST /chat/message {message: "[START_SESSION]", session_number: 1}`
3. **Assert**: AI greeting appears, typing indicator shown during load
4. User sends message → `POST /chat/message` → AI responds
5. Conversation progresses through states: INTRO → DISCOVERY → GOAL_SETTING → END_SESSION
6. **Assert**: When `session_complete: true` returned, input disables, completion UI shows
7. Backend: `SessionProgress(uid, 1)` marked complete, `SessionProgress(uid, 2)` created with `unlocked_at = now + 7 days`
8. Auto-navigate back to `ChatOverviewScreen`
- **Assert**: Week 1 = completed (green), Week 2 = locked with countdown (or unlocked if demo mode)

### Flow 3: Session 2 — "Building Habits"
1. [In production: wait 7 days or mock time. In demo: immediately clickable]
2. Tap Week 2 → `ChatScreen {sessionNumber: 2}`
3. `POST /chat/message {message: "[START_SESSION]", session_number: 2}`
4. **Assert**: AI references Session 1 data (user's name, goals, profile)
5. Session2Manager loads previous session data via `AIService`
6. Complete conversation flow → `session_complete: true`
7. **Assert**: Session 2 marked complete, Session 3 unlock scheduled

### Flow 4: Session 3 — "Overcoming Challenges"
- Same flow as Session 2, Session3Manager references Sessions 1-2 data
- **Assert**: AI references previously set goals and habits

### Flow 5: Session 4 — "Reviewing Progress"
1. Tap Week 4 → `ChatScreen {sessionNumber: 4}`
2. AI reviews all 3 prior sessions' goals, habits, challenges
3. Complete conversation → `session_complete: true`
4. **Assert**: All 4 sessions show completed (green) on `ChatOverviewScreen`
5. **Assert**: No more sessions to unlock, program complete

### Flow 6: Returning User Login
1. Log out → back to `LoginScreen`
2. Log in with existing credentials
3. `GET /user/status/{uid}` → `onboarding_completed: true`
4. Route directly to `ChatOverviewScreen`
5. **Assert**: All session progress preserved, completed sessions still green

### Edge Cases to Cover
- **Network failure mid-conversation**: Frontend should handle fetch errors gracefully
- **Double-tap on send**: Should not send duplicate messages
- **Session already completed**: Tapping a completed session should not allow re-entry (currently not enforced — potential bug)
- **Token expiry**: Firebase token refresh should happen transparently
- **Empty message**: Frontend should prevent sending empty strings
- **Very long message**: Should be rejected by backend validation (once 1F is implemented)
- **Concurrent sessions**: User opens Session 1 in two tabs — cache and DB should handle gracefully

---

## Verification

1. **Security**: After implementing Phase 1, manually test each endpoint with and without a valid Firebase token. Verify 401 responses for unauthenticated requests
2. **Dead code**: Run `grep -r` for any remaining imports of deleted files to ensure nothing breaks
3. **Organization**: Run the backend (`uvicorn backend.app:app`) and frontend (`npx expo start`) to confirm no import errors
4. **E2E**: Walk through Flows 1-6 manually against the running app. Each assertion point should pass
