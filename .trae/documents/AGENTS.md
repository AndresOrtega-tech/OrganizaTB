# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

OrganizaT is a mobile task management application with a React Native (Expo) frontend and FastAPI backend. The backend uses Supabase for authentication and database, and is deployed on Vercel.

## Repository Structure

The project is organized into two main directories:
- `frontend/` - React Native mobile app using Expo
- `backend/` - FastAPI REST API with Supabase integration

## Development Commands

### Backend (FastAPI)

Navigate to backend directory first: `cd backend`

**Setup:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Run development server:**
```powershell
uvicorn main:app --reload
```
- API available at: `http://127.0.0.1:8000`
- Interactive API docs: `http://127.0.0.1:8000/docs`

**Health check endpoints:**
- `GET /` - Basic health check
- `GET /health` - Supabase connection status
- `GET /tables` - List database tables (requires RPC function in Supabase)

### Frontend (React Native/Expo)

Navigate to frontend directory first: `cd frontend`

**Setup:**
```powershell
npm install
```

**Development commands:**
- `npm start` or `npx expo start` - Start Expo dev server
- `npm run android` - Launch on Android emulator
- `npm run ios` - Launch on iOS simulator (macOS only)
- `npm run web` - Launch in web browser

The Expo dev server provides a QR code to scan with the Expo Go app for testing on physical devices.

## Architecture

### Backend Architecture

**Module Structure:**
- `main.py` - FastAPI app entry point with CORS, rate limiting (SlowAPI), and router registration
- `database.py` - Supabase client initialization using environment variables
- `auth/` - Authentication module
  - `api.py` - Authentication endpoints (register, login)
  - `schemas.py` - Pydantic models for request/response validation
  - `models.py` - Currently empty, reserved for future ORM models
- `tags/` - Tags management module
  - `api.py` - Endpoints for creating, listing, updating, and deleting tags
  - `schemas.py` - Schemas for tag operations

**Database Schema:**
The database schema is defined in `backend/database.txt` and includes the following tables:
- `profiles`: Stores user profile information (linked to auth.users).
- `tags`: User-defined tags for tasks and notes (Unique constraint: user_id + name).
- `tasks`: Task management with due dates, reminders, and completion status.
- `notes`: User notes with optional media.
- `task_tags` & `note_tags`: Many-to-many relationships for tags.
- `improvement_insights`: Stores AI-generated insights for the user.
- Includes RLS policies and a trigger (`handle_new_user`) for automatic profile creation.
- **Security**: Row Level Security (RLS) is enabled on all tables. The backend uses `SUPABASE_SERVICE_ROLE_KEY` to bypass RLS for write operations where necessary (e.g., initial user creation), while `SUPABASE_ANON_KEY` is used for client-side operations.

**Import Pattern:**
The backend uses dual import paths to support both local development and Vercel deployment:
```python
try:
    from backend.database import supabase
except ImportError:
    from database import supabase
```
When adding new modules, follow this pattern to ensure compatibility in both environments.

**Authentication Flow:**
- User registration creates entries in both Supabase Auth and the `profiles` table
- Login returns JWT tokens (access_token, refresh_token) and user profile data (excluding sensitive auth IDs)
- Authentication middleware (`dependencies.py`) verifies JWT tokens using Supabase Auth
- **Avatar Update**: Dedicated endpoint `PATCH /api/auth/users/avatar` allows authenticated users to update their avatar URL (must be unique).

**Configuration:**
- Environment variables loaded from `backend/.env`
- Required: 
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY` (or `SERVICE_ROLE`) - Critical for backend write permissions
  - `SUPABASE_ANON_KEY` (or `ANON_KEY`)
- The database module prioritizes Service Role Key for backend operations to avoid RLS 401 errors during inserts.

**Deployment:**
- Configured for Vercel via `vercel.json`
- Routes all requests through `main.py`

### Frontend Architecture

**Current State:**
The frontend is a minimal Expo template with basic setup in `App.js`. It's ready for feature development.

**Configuration:**
- Expo config in `app.json` with:
  - New Architecture enabled
  - Edge-to-edge Android support
  - Cross-platform icon/splash screen assets

## Git Workflow

**Branch Strategy:**
- `development` - Main development branch (current)
- `production` (or `main`) - Production branch

All changes should be made in `development` and tested before merging to production.

**Commit Guidelines:**
When committing changes made by Warp agents, include co-author attribution:
```
Co-Authored-By: Warp <agent@warp.dev>
```

## Key Technical Details

### Backend
- **FastAPI** with async support
- **Rate limiting** via SlowAPI (configured per endpoint)
- **CORS** enabled for localhost origins (ports 3000, 8081) and wildcard
- **Supabase** handles password hashing automatically - never hash passwords manually
- **Logging** configured at INFO level via Python's logging module

### Frontend
- **React 19.1.0** with **React Native 0.81.5**
- **Expo SDK ~54.0.31**
- Entry point: `index.js` (imports App.js)

## Environment Variables

**Backend (.env file in backend/):**
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key # REQUIRED for backend inserts
```

**Security Note:** Never commit the `.env` file or expose secrets. It's already in `.gitignore`.

## Testing and Validation

Currently, no test framework is configured. When implementing tests:
1. Check for existing test setup in the codebase first
2. Follow common Python (pytest) or JavaScript (Jest) conventions
3. Consider integration tests for auth endpoints using Supabase test projects

## API Endpoints

### Authentication
- `POST /api/users` - Register new user
  - Body: `{"email": "user@example.com", "password": "password", "full_name": "optional", "avatar_url": "optional"}`
- `POST /api/auth/login` - User login
  - Body: `{"email": "user@example.com", "password": "password"}`
  - Returns: JWT tokens and user profile info (name, avatar, email)
- `PATCH /api/auth/users/avatar` - Update Avatar
  - Headers: `Authorization: Bearer <token>`
  - Body: `{"avatar_url": "new_url"}`

### Tags
- `POST /api/tags/` - Create new tag
  - Headers: `Authorization: Bearer <token>`
  - Body: `{"name": "Tag Name", "color": "#RRGGBB"}`
- `GET /api/tags/` - List user tags
- `PATCH /api/tags/{id}` - Update tag
- `DELETE /api/tags/{id}` - Delete tag

## Development Notes

- The backend uses PowerShell commands by default (Windows environment)
- Python version should support type hints with `|` operator (Python 3.10+)
- When adding new API routes, register them in `main.py` using `app.include_router()`
- Authentication tokens should be passed as Bearer tokens in Authorization headers
