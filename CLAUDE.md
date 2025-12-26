# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-RSS-Client is the frontend component of the AI-RSS-PROJECT monorepo. It provides a web interface for the AI-RSS-Hub backend API.

Currently, this directory is a placeholder. The frontend application has not been implemented yet.

## Backend API Integration

The frontend will connect to **AI-RSS-Hub**, a FastAPI backend that provides:

### Public Endpoints
- `GET /api/health` - Health check
- `GET /api/status` - System status including scheduler info
- `GET /api/feeds` - List all RSS sources (query: `active_only=true`)
- `GET /api/articles` - List articles (query: `limit`, `days`, `category`)

### Protected Endpoints (require `X-API-Token` header)
- `POST /api/feeds` - Add new RSS source
- `POST /api/feeds/fetch` - Manually trigger RSS fetch

### Interactive Documentation
Swagger UI available at `/docs` when the backend is running.

### Default Backend Configuration
- Base URL: `http://localhost:8000`
- CORS origins: `localhost:3000`, `localhost:8000` (configurable via backend `CORS_ORIGINS`)

## Data Models

### Feed
```typescript
{
  id: number;
  name: string;
  url: string;
  category: string;
  is_active: boolean;
  created_at: string;
}
```

### Article
```typescript
{
  id: number;
  feed_id: number;
  title: string;
  link: string;
  content?: string;
  summary?: string;  // AI-generated summary
  published_at?: string;
  created_at: string;
}
```

## Development Setup

The backend (AI-RSS-Hub) must be running before starting the frontend:

```bash
# In the AI-RSS-Hub directory
cd ../AI-RSS-Hub
python -m app.main
```

### Development Script

The `dev.sh` script sets up a tmux session with three windows:
1. **editor** - For coding
2. **server** - For running the frontend server
3. **monitor** - With htop for system monitoring

```bash
./dev.sh
```

## Tech Stack Decision

When implementing the frontend, consider the following requirements:

1. **Single Page Application** - React, Vue, or similar framework
2. **API Client** - Fetch or axios for REST API calls
3. **State Management** - Depending on complexity (Context API, Redux, Zustand, etc.)
4. **UI Components** - Component library (Material-UI, Tailwind CSS, Chakra UI, etc.)
5. **Development Server** - Vite, Next.js, or similar for hot reload

## Common Tasks

### Test Backend Connection

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/feeds
curl http://localhost:8000/api/articles?limit=10
```

### Add RSS Feed via API

```bash
curl -X POST http://localhost:8000/api/feeds \
  -H "Content-Type: application/json" \
  -H "X-API-Token: YOUR_TOKEN" \
  -d '{
    "name": "GitHub Blog",
    "url": "https://github.blog/feed/",
    "category": "tech",
    "is_active": true
  }'
```

## Important Notes

1. **CORS Configuration**: The backend CORS origins are configured in `AI-RSS-Hub/.env`. Update `CORS_ORIGINS` if running the frontend on a different port/domain.

2. **API Token**: Protected endpoints require an `X-API-Token` header. Generate a token in the backend directory with `python scripts/generate_token.py`.

3. **Article Summaries**: The `summary` field is AI-generated and may be null if summarization failed or hasn't completed yet.

4. **Date Formats**: All timestamps are in ISO 8601 format (e.g., `2025-12-26T10:32:00`).

5. **Database**: The backend uses SQLite with file `AI-RSS-Hub/ai_rss_hub.db`. Direct database access can be useful for debugging:

```bash
sqlite3 ../AI-RSS-Hub/ai_rss_hub.db
> SELECT * FROM feed;
> SELECT * FROM article LIMIT 10;
> .quit
```
