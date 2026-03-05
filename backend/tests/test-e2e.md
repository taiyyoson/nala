# E2E Test Guide

## Setup

All commands run from the `backend/` directory using the project venv.

## Run All 7 E2E Tests

```bash
venv/bin/python -m pytest tests/test_e2e_full_flow.py -v
```

## Run the Full Sequential Test (Standalone)

Runs the entire flow (onboarding -> session 1 -> 2 -> 3 -> 4) in a single test with a fresh user. No dependencies, always safe to run alone.

```bash
venv/bin/python -m pytest tests/test_e2e_full_flow.py::test_full_program_sequential -v
```

## Run Specific Tests

```bash
# Onboarding only
venv/bin/python -m pytest tests/test_e2e_full_flow.py::TestE2EFullFlow::test_new_user_onboarding -v

# Session 1
venv/bin/python -m pytest tests/test_e2e_full_flow.py::TestE2EFullFlow::test_session_1_full_flow -v

# Session 2
venv/bin/python -m pytest tests/test_e2e_full_flow.py::TestE2EFullFlow::test_session_2_full_flow -v

# Session 3
venv/bin/python -m pytest tests/test_e2e_full_flow.py::TestE2EFullFlow::test_session_3_full_flow -v

# Session 4
venv/bin/python -m pytest tests/test_e2e_full_flow.py::TestE2EFullFlow::test_session_4_full_flow -v

# Returning user check
venv/bin/python -m pytest tests/test_e2e_full_flow.py::TestE2EFullFlow::test_returning_user -v
```

## Run a Subset with `-k`

```bash
# Onboarding through session 2
venv/bin/python -m pytest tests/test_e2e_full_flow.py -k "onboarding or session_1 or session_2" -v
```

## Run All Tests (E2E + existing unit tests)

```bash
venv/bin/python -m pytest tests/ -v
```

## Important: Test Dependencies

The class-based tests (`TestE2EFullFlow`) share state and run sequentially:

- `test_new_user_onboarding` - no dependencies
- `test_session_1_full_flow` - needs onboarding
- `test_session_2_full_flow` - needs session 1
- `test_session_3_full_flow` - needs sessions 1-2
- `test_session_4_full_flow` - needs sessions 1-3
- `test_returning_user` - needs all 4 sessions

Running a later test in isolation won't error (the mock doesn't require prior sessions), but assertions about earlier session progress will fail.

`test_full_program_sequential` is fully independent — it creates its own user and runs the entire flow. Always safe to run alone.

## How It Works

- **StatefulMockAIService** replaces the real AI/LLM service
- Each mock instance counts `generate_response()` calls and transitions to `"end_session"` state after 3 messages
- This triggers the chat router's session completion logic (marks `SessionProgress`, calls `save_session()`)
- No real LLM calls, no API keys needed — tests run in ~0.2s
