# CI/CD Pipeline

This repository uses GitHub Actions for continuous integration and deployment.

## Workflow Overview

The CI/CD pipeline (`ci.yml`) runs on:
- Push to `main`, `develop`, and `taiyo-backend-skeleton` branches
- Pull requests to `main` and `develop` branches

## Pipeline Steps

### 1. Test Job
- Sets up Python 3.11
- Installs dependencies from `backend/requirements.txt`
- Runs linting with flake8
- Checks code formatting with black and isort
- Runs all tests with pytest
- Specifically tests API endpoints

### 2. Security Job (Placeholder)
- Currently disabled
- Ready for security scanning tools

### 3. Deploy Job
- Runs only on main branch
- Currently a placeholder for deployment steps

## Local Development

To run the same checks locally:

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v

# Check linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Check formatting
black --check .
isort --check-only .

# Auto-format code
black .
isort .
```

## API Tests

The pipeline includes comprehensive API endpoint tests that verify:
- Health check endpoints
- Chat message functionality
- Conversation flow
- Error handling
- Streaming responses