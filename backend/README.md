# Nala Health Coach Backend

Basic FastAPI backend for the health coaching chatbot mobile app.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run development server:**
   ```bash
   python dev.py
   ```

3. **Access API:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health

## API Endpoints

### Chat
- `POST /api/v1/chat/message` - Send a message to the chatbot
- `POST /api/v1/chat/stream` - Stream chatbot responses
- `GET /api/v1/chat/conversation/{id}` - Get conversation history

### Health
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed system health

## Development

The backend currently uses mock responses. To integrate with Claude:

1. Add your Claude API key to `.env`:
   ```
   CLAUDE_API_KEY=your_api_key_here
   ```

2. Implement Claude service in `services/claude_service.py`

## Project Structure

```
backend/
├── app.py              # FastAPI application
├── dev.py              # Development server
├── routes/             # API route handlers
├── services/           # Business logic services
├── config/             # Configuration management
└── middleware/         # Custom middleware
```