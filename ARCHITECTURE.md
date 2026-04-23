# FilmTracker — Architecture & Technical Specification

> A movie-centric social platform where friends track, rate, and share what they're watching — built with a Twitter-inspired UI.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Features](#2-core-features)
3. [Recommended Tech Stack](#3-recommended-tech-stack)
4. [Directory Structure](#4-directory-structure)
5. [System Architecture](#5-system-architecture)
6. [Database Schema](#6-database-schema)
7. [API Design](#7-api-design)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Mobile (Android) Packaging](#9-mobile-android-packaging)
10. [TMDB Integration](#10-tmdb-integration)
11. [Movie Import (TXT File)](#11-movie-import-txt-file)
12. [Onboarding & User Recommendations](#12-onboarding--user-recommendations)
13. [Authentication & Security](#13-authentication--security)
14. [Deployment Strategy](#14-deployment-strategy)
15. [Implementation Roadmap](#15-implementation-roadmap)

---

## 1. Project Overview

FilmTracker is a social media platform centred entirely around movies. Users follow friends and curated reviewers, see a real-time feed of their ratings and recommendations, and discover films through people they trust — not algorithms. The UI takes inspiration from Twitter/X in its simplicity (feed-first, minimal friction), but improves on it with richer media cards, genre-aware personalisation, and a seamless mobile experience via Android packaging.

---

## 2. Core Features

| # | Feature | Priority |
|---|---------|----------|
| 1 | User registration & JWT-based authentication | P0 |
| 2 | Follow / unfollow users | P0 |
| 3 | Social feed (followed users' ratings & reviews) | P0 |
| 4 | Movie search & detail pages (TMDB-powered) | P0 |
| 5 | Rate & review a movie | P0 |
| 6 | Onboarding genre selection + user recommendations | P0 |
| 7 | TXT file import → personal movie list | P1 |
| 8 | Personal watchlist & watched list | P1 |
| 9 | Notifications (new follower, someone liked your review) | P1 |
| 10 | Explore / discovery page (trending, genre browsing) | P1 |
| 11 | Android APK packaging via Capacitor | P2 |
| 12 | Dark / light theme | P2 |

---

## 3. Recommended Tech Stack

### 3.1 Frontend (your choices — endorsed)

| Technology | Role | Notes |
|-----------|------|-------|
| **React 18** | UI framework | Concurrent rendering, Suspense |
| **TypeScript** | Type safety | Strict mode recommended |
| **TailwindCSS v3** | Styling | JIT engine; pair with `tailwind-merge` & `clsx` |
| **Zustand** | Client state | Auth state, UI toggles, cached user data |
| **TanStack Query v5** | Server state | Caching, background refetch, pagination — use *alongside* Zustand |
| **React Router v6** | Routing | File-based layout routes |
| **Axios** | HTTP client | Interceptors for JWT attachment & refresh |
| **Capacitor v6** | Android packaging | Wraps the React PWA into a native APK with zero rewrite |

> **Why TanStack Query alongside Zustand?**
> Zustand should own UI/client state (current user, theme, modal state). TanStack Query should own server-derived state (feeds, movie data, search results). Mixing both avoids re-implementing caching logic inside Zustand.

### 3.2 Backend (your choices — endorsed)

| Technology | Role | Notes |
|-----------|------|-------|
| **Python 3.12** | Runtime | |
| **FastAPI** | Web framework | Auto-generates OpenAPI docs at `/docs` |
| **PostgreSQL 16** | Primary database | JSONB columns for flexible movie metadata |
| **SQLAlchemy 2** | ORM | Async-first with `asyncpg` driver |
| **Alembic** | DB migrations | Version-controlled schema changes |
| **Pydantic v2** | Data validation | Integrated with FastAPI |
| **Redis** | Cache + task queue | TMDB response caching, session store |
| **Celery** | Background tasks | TXT file parsing, bulk TMDB lookups |
| **JWT (python-jose)** | Auth tokens | Access token (15 min) + Refresh token (30 days) |
| **Passlib + bcrypt** | Password hashing | |

### 3.3 Infrastructure

| Technology | Role |
|-----------|------|
| **Docker + Docker Compose** | Local dev parity, container builds |
| **Nginx** | Reverse proxy, serves frontend static files |
| **GitHub Actions** | CI/CD |

### 3.4 Additional Recommendations

- **`httpx`** (async HTTP) — for TMDB API calls from FastAPI instead of `requests`
- **`python-multipart`** — TXT file uploads in FastAPI
- **`slowapi`** — rate limiting on FastAPI endpoints (wraps `limits`)
- **Sentry** — error tracking (free tier covers small apps)
- **`react-hot-toast`** — toast notifications on the frontend

---

## 4. Directory Structure

```
filmtracker.online/
│
├── frontend/
│   ├── public/
│   │   └── icons/                  # PWA icons for Capacitor
│   ├── src/
│   │   ├── assets/                 # Static images, fonts
│   │   ├── components/
│   │   │   ├── ui/                 # Button, Input, Avatar, Card, Modal, Skeleton
│   │   │   ├── feed/               # FeedPost, FeedList, FeedSkeleton
│   │   │   ├── movie/              # MovieCard, MovieDetail, StarRating, GenreBadge
│   │   │   ├── auth/               # LoginForm, RegisterForm, AuthGuard
│   │   │   ├── onboarding/         # GenrePicker, SuggestedUsers, OnboardingWizard
│   │   │   ├── profile/            # ProfileHeader, FollowButton, MovieGrid
│   │   │   └── import/             # FileDropzone, ImportProgress, ImportResult
│   │   ├── pages/
│   │   │   ├── Home.tsx            # Feed
│   │   │   ├── Explore.tsx         # Discovery, trending
│   │   │   ├── Movie.tsx           # Single movie detail
│   │   │   ├── Profile.tsx         # User profile
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Onboarding.tsx
│   │   │   ├── Import.tsx
│   │   │   └── Notifications.tsx
│   │   ├── store/
│   │   │   ├── authStore.ts        # Zustand: current user, tokens
│   │   │   ├── uiStore.ts          # Zustand: theme, modals, sidebar
│   │   │   └── onboardingStore.ts  # Zustand: wizard progress
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useFeed.ts          # TanStack Query feed fetching
│   │   │   ├── useMovie.ts
│   │   │   └── useImport.ts
│   │   ├── services/
│   │   │   ├── api.ts              # Axios instance + interceptors
│   │   │   ├── auth.service.ts
│   │   │   ├── feed.service.ts
│   │   │   ├── movie.service.ts
│   │   │   ├── user.service.ts
│   │   │   └── import.service.ts
│   │   ├── types/
│   │   │   ├── user.ts
│   │   │   ├── movie.ts
│   │   │   ├── feed.ts
│   │   │   └── api.ts
│   │   ├── utils/
│   │   │   ├── formatDate.ts
│   │   │   ├── genreMap.ts
│   │   │   └── ratingHelpers.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── capacitor.config.ts         # Android/iOS packaging config
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py         # /auth/register, /auth/login, /auth/refresh
│   │   │   │   ├── users.py        # /users/{id}, /users/{id}/follow
│   │   │   │   ├── feed.py         # /feed
│   │   │   │   ├── movies.py       # /movies/search, /movies/{tmdb_id}
│   │   │   │   ├── ratings.py      # /ratings (POST), /ratings/{id}
│   │   │   │   ├── watchlist.py    # /watchlist
│   │   │   │   ├── import_.py      # /import/txt
│   │   │   │   ├── onboarding.py   # /onboarding/suggestions
│   │   │   │   └── notifications.py
│   │   │   └── dependencies/
│   │   │       ├── auth.py         # get_current_user dependency
│   │   │       └── db.py           # get_db session dependency
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── movie.py
│   │   │   ├── rating.py
│   │   │   ├── follow.py
│   │   │   ├── watchlist.py
│   │   │   └── notification.py
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── user.py
│   │   │   ├── movie.py
│   │   │   ├── rating.py
│   │   │   ├── feed.py
│   │   │   └── import_.py
│   │   ├── services/               # Business logic layer
│   │   │   ├── tmdb.py             # TMDB API client (httpx, cached in Redis)
│   │   │   ├── feed.py             # Feed assembly logic
│   │   │   ├── import_.py          # TXT parsing + TMDB bulk lookup
│   │   │   ├── recommendations.py  # Onboarding user suggestions
│   │   │   └── notifications.py
│   │   ├── core/
│   │   │   ├── config.py           # Settings via pydantic-settings (.env)
│   │   │   ├── security.py         # JWT encode/decode, bcrypt
│   │   │   └── database.py         # Async SQLAlchemy engine + session
│   │   ├── utils/
│   │   │   └── pagination.py
│   │   ├── worker.py               # Celery app definition
│   │   ├── tasks.py                # Celery tasks (bulk TMDB lookup etc.)
│   │   └── main.py                 # FastAPI app factory
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_feed.py
│   │   └── test_import.py
│   ├── .env.example
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/
│   └── api-spec.http               # VS Code REST Client request collection
│
├── docker-compose.yml              # Postgres + Redis + backend + frontend
├── .gitignore
└── ARCHITECTURE.md                 # This file
```

---

## 5. System Architecture

```
┌──────────────────────────────────────────────────────┐
│                     Client Layer                      │
│   React + TypeScript + TailwindCSS + Zustand          │
│   ┌─────────┐  ┌──────────────┐  ┌────────────────┐  │
│   │  Pages  │  │  Components  │  │  Zustand Store │  │
│   └────┬────┘  └──────┬───────┘  └───────┬────────┘  │
│        └──────────────┴──────────────────┘            │
│                  TanStack Query                        │
│                  Axios + JWT interceptor               │
└─────────────────────────┬────────────────────────────┘
                           │ HTTPS REST
┌─────────────────────────▼────────────────────────────┐
│                    Nginx (Reverse Proxy)               │
│          /api  →  FastAPI    /  →  React static        │
└──────────┬──────────────────────────────-─────────────┘
           │
┌──────────▼──────────────────────────────────────────┐
│                  FastAPI Backend                      │
│   ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│   │  Routes  │  │ Services  │  │   Celery Worker  │  │
│   └──────────┘  └─────┬─────┘  └────────┬─────────┘  │
│                        │                 │             │
│              ┌─────────▼──┐     ┌────────▼──────┐     │
│              │ PostgreSQL │     │     Redis     │     │
│              └────────────┘     └───────────────┘     │
│                                         ↕             │
│                               ┌─────────────────┐    │
│                               │   TMDB API      │    │
│                               └─────────────────┘    │
└──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────┐
│   Capacitor Build (Android APK) │
│   WebView → same React bundle   │
└─────────────────────────────────┘
```

---

## 6. Database Schema

### Core Tables

```sql
-- Users
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username    VARCHAR(30)  UNIQUE NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name  VARCHAR(60),
    avatar_url    TEXT,
    bio           TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Follows (self-referential many-to-many)
CREATE TABLE follows (
    follower_id UUID REFERENCES users(id) ON DELETE CASCADE,
    following_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id)
);

-- Movies (local cache of TMDB data)
CREATE TABLE movies (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tmdb_id      INTEGER UNIQUE NOT NULL,
    title        VARCHAR(255) NOT NULL,
    release_year SMALLINT,
    poster_url   TEXT,
    backdrop_url TEXT,
    overview     TEXT,
    genres       JSONB,          -- [{"id": 27, "name": "Horror"}]
    runtime      SMALLINT,
    tmdb_rating  NUMERIC(3,1),
    fetched_at   TIMESTAMPTZ DEFAULT NOW()
);

-- User Ratings & Reviews
CREATE TABLE ratings (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    movie_id   UUID REFERENCES movies(id) ON DELETE CASCADE,
    score      NUMERIC(3,1) CHECK (score >= 0 AND score <= 10),
    review     TEXT,
    contains_spoiler BOOLEAN DEFAULT FALSE,
    watched_on DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, movie_id)
);

-- Watchlist
CREATE TABLE watchlist (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    movie_id   UUID REFERENCES movies(id) ON DELETE CASCADE,
    status     VARCHAR(20) CHECK (status IN ('want_to_watch','watching','watched')),
    added_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, movie_id)
);

-- Genre preferences (for onboarding)
CREATE TABLE user_genre_preferences (
    user_id  UUID REFERENCES users(id) ON DELETE CASCADE,
    genre_id INTEGER,            -- TMDB genre ID
    PRIMARY KEY (user_id, genre_id)
);

-- Notifications
CREATE TABLE notifications (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,  -- recipient
    actor_id   UUID REFERENCES users(id) ON DELETE CASCADE,  -- who triggered it
    type       VARCHAR(40),     -- 'new_follower' | 'liked_review' | 'new_rating'
    entity_id  UUID,            -- rating_id or user_id depending on type
    read       BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Key Indexes

```sql
CREATE INDEX idx_ratings_user_id     ON ratings(user_id);
CREATE INDEX idx_ratings_movie_id    ON ratings(movie_id);
CREATE INDEX idx_ratings_created_at  ON ratings(created_at DESC);
CREATE INDEX idx_follows_follower    ON follows(follower_id);
CREATE INDEX idx_follows_following   ON follows(following_id);
CREATE INDEX idx_watchlist_user      ON watchlist(user_id);
CREATE INDEX idx_notifications_user  ON notifications(user_id, read, created_at DESC);
```

---

## 7. API Design

All endpoints are prefixed with `/api/v1`.

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Returns access + refresh tokens |
| POST | `/auth/refresh` | Exchange refresh token for new access token |
| POST | `/auth/logout` | Blacklist refresh token |

### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/me` | Current user profile |
| PATCH | `/users/me` | Update profile / avatar |
| GET | `/users/{username}` | Public profile |
| POST | `/users/{username}/follow` | Follow user |
| DELETE | `/users/{username}/follow` | Unfollow user |
| GET | `/users/{username}/followers` | Followers list |
| GET | `/users/{username}/following` | Following list |
| GET | `/users/{username}/ratings` | User's ratings |

### Feed

| Method | Path | Description |
|--------|------|-------------|
| GET | `/feed` | Paginated feed of followed users' ratings |
| GET | `/feed/global` | Public global feed (for unauthenticated explore) |

### Movies

| Method | Path | Description |
|--------|------|-------------|
| GET | `/movies/search?q=&page=` | Search TMDB |
| GET | `/movies/trending` | TMDB trending this week |
| GET | `/movies/{tmdb_id}` | Movie detail (TMDB cached locally) |
| GET | `/movies/{tmdb_id}/ratings` | Community ratings for a movie |

### Ratings & Reviews

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ratings` | Add/update a rating |
| DELETE | `/ratings/{id}` | Delete a rating |
| POST | `/ratings/{id}/like` | Like a review |

### Watchlist

| Method | Path | Description |
|--------|------|-------------|
| GET | `/watchlist` | Get current user's watchlist |
| POST | `/watchlist` | Add movie to watchlist |
| PATCH | `/watchlist/{id}` | Update status |
| DELETE | `/watchlist/{id}` | Remove from watchlist |

### Import

| Method | Path | Description |
|--------|------|-------------|
| POST | `/import/txt` | Upload TXT file, returns job_id |
| GET | `/import/{job_id}/status` | Poll import progress |
| GET | `/import/{job_id}/results` | Matched movies + unmatched lines |

### Onboarding

| Method | Path | Description |
|--------|------|-------------|
| POST | `/onboarding/genres` | Save selected genres |
| GET | `/onboarding/suggestions` | Suggested users based on genres |

---

## 8. Frontend Architecture

### State Management Strategy

```
Zustand (client state)          TanStack Query (server state)
─────────────────────           ─────────────────────────────
authStore                       useFeed()          → GET /feed
  ├─ currentUser                useMovie(tmdbId)   → GET /movies/:id
  ├─ accessToken                useProfile(user)   → GET /users/:user
  └─ isAuthenticated            useSearch(q)       → GET /movies/search
                                useWatchlist()     → GET /watchlist
uiStore
  ├─ theme (dark/light)
  ├─ sidebarOpen
  └─ activeModal

onboardingStore
  ├─ selectedGenres
  └─ step
```

### Page Layout (Twitter-like)

```
┌────────────────────────────────────────────────────┐
│  Sidebar (fixed left)   │  Main Feed  │  Right Panel│
│  • Home                 │             │  • Trending  │
│  • Explore              │  Post cards │  • Who to    │
│  • Notifications        │  (infinite  │    follow    │
│  • Profile              │   scroll)   │  • Genre tags│
│  • Import               │             │             │
│  [New Rating button]    │             │             │
└────────────────────────────────────────────────────┘
```

On mobile (< 768px): sidebar collapses to bottom nav bar.

### Movie Rating Post Card

Each feed item shows:
- User avatar + display name + username + timestamp
- Movie poster thumbnail (left) + title + release year + genres
- Star score (1–10, rendered as filled stars)
- Review text (capped at 3 lines, "Read more" expander)
- Action row: Like | Comment | Share

---

## 9. Mobile (Android) Packaging

**Recommended tool: Capacitor v6**

Capacitor converts your existing React web app into a native Android (and iOS) app via a WebView shell. It requires zero rewrite.

### Setup Steps

```bash
# 1. Install Capacitor in the frontend
npm install @capacitor/core @capacitor/cli @capacitor/android

# 2. Initialise
npx cap init FilmTracker com.filmtracker.app --web-dir=dist

# 3. Build the React app
npm run build

# 4. Add Android platform
npx cap add android

# 5. Sync assets
npx cap sync android

# 6. Open in Android Studio to build APK / AAB
npx cap open android
```

### `capacitor.config.ts` (key settings)

```typescript
import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.filmtracker.app',
  appName: 'FilmTracker',
  webDir: 'dist',
  server: {
    // In development, point to your local dev server for hot reload
    url: 'http://192.168.x.x:5173',
    cleartext: true,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
    },
  },
};

export default config;
```

### Native Plugins to Consider

| Plugin | Use Case |
|--------|---------|
| `@capacitor/camera` | Profile photo upload |
| `@capacitor/filesystem` | Read TXT files from device storage |
| `@capacitor/push-notifications` | Follow / like notifications |
| `@capacitor/haptics` | Haptic feedback on rating interactions |
| `@capacitor/status-bar` | Style Android status bar |

> **Why Capacitor over React Native?**
> The stack is already React + TypeScript. Capacitor reuses 100% of the web codebase with no second UI layer. React Native would require rewriting all components. Capacitor is the right call for this project.

---

## 10. TMDB Integration

### Configuration

Store the token in `.env`:

```
TMDB_READ_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiJ9...
```

### Caching Strategy (Redis)

TMDB has a rate limit of ~50 requests/second. Cache aggressively:

```
Key pattern                    TTL
────────────────────────────   ───────
tmdb:search:{query}:{page}     1 hour
tmdb:movie:{tmdb_id}           24 hours
tmdb:trending:week             6 hours
tmdb:genres                    7 days
```

### TMDB Service (backend/app/services/tmdb.py)

```python
import httpx
import json
from app.core.config import settings
from app.core.database import redis_client

BASE_URL = "https://api.themoviedb.org/3"
HEADERS  = {"Authorization": f"Bearer {settings.TMDB_READ_ACCESS_TOKEN}"}

async def get_movie(tmdb_id: int) -> dict:
    cache_key = f"tmdb:movie:{tmdb_id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/movie/{tmdb_id}", headers=HEADERS)
        r.raise_for_status()
        data = r.json()

    await redis_client.setex(cache_key, 86400, json.dumps(data))
    return data

async def search_movies(query: str, page: int = 1) -> dict:
    cache_key = f"tmdb:search:{query}:{page}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/search/movie",
            headers=HEADERS,
            params={"query": query, "page": page}
        )
        r.raise_for_status()
        data = r.json()

    await redis_client.setex(cache_key, 3600, json.dumps(data))
    return data
```

### Image URL Construction

```
Poster:   https://image.tmdb.org/t/p/w500/{poster_path}
Backdrop: https://image.tmdb.org/t/p/w1280/{backdrop_path}
Thumb:    https://image.tmdb.org/t/p/w92/{poster_path}
```

---

## 11. Movie Import (TXT File)

### File Format (user-facing)

```
# One movie title per line. Lines starting with # are comments.
The Dark Knight
Inception
Hereditary 2018
Parasite
The Godfather
```

### Import Flow

```
User uploads TXT
       │
       ▼
FastAPI /import/txt
  - Save file temporarily
  - Dispatch Celery task → return job_id immediately
       │
       ▼
Celery Worker (background)
  - Parse lines → list of titles
  - For each title:
      1. Check local movies table (exact/fuzzy match)
      2. If not found → TMDB search (query = title)
      3. Take top result if confidence ≥ 80%
      4. Cache in local movies table
      5. Add to user's watchlist with status='want_to_watch'
  - Store results in Redis under job_id
       │
       ▼
Frontend polls GET /import/{job_id}/status
  - Shows progress bar (processed / total)
  - On completion: show matched list + unmatched titles
  - User can manually search for unmatched titles
```

### Fuzzy Matching

Use Python's `rapidfuzz` library for title matching with year extraction:

```python
import re
from rapidfuzz import fuzz

def parse_title_year(line: str) -> tuple[str, int | None]:
    match = re.search(r'\b(19|20)\d{2}\b', line)
    year  = int(match.group()) if match else None
    title = line[:match.start()].strip() if match else line.strip()
    return title, year

def score_tmdb_result(query: str, result_title: str) -> int:
    return fuzz.token_sort_ratio(query.lower(), result_title.lower())
```

---

## 12. Onboarding & User Recommendations

### Flow

```
Register
   │
   ▼
Step 1 — Pick genres you love (multi-select grid, TMDB genre list)
   │
   ▼
Step 2 — System finds users who have:
  • Rated ≥ 5 movies in your selected genres
  • Rated them highly (avg score ≥ 7)
  • Sorted by: most ratings in that genre first
   │
   ▼
Step 3 — "People you might like" cards (avatar, stats, top rated movie)
         User must follow at least 1 before continuing
   │
   ▼
Home Feed (populated from followed users)
```

### Recommendation Query (SQL)

```sql
SELECT
    u.id,
    u.username,
    u.display_name,
    u.avatar_url,
    COUNT(r.id)          AS rating_count,
    AVG(r.score)         AS avg_score,
    array_agg(DISTINCT genres->>'name') AS genre_names
FROM users u
JOIN ratings r  ON r.user_id = u.id
JOIN movies  m  ON m.id = r.movie_id,
     jsonb_array_elements(m.genres) AS genres
WHERE genres->>'id' = ANY(:selected_genre_ids)
  AND r.score >= 7
  AND u.id != :current_user_id
GROUP BY u.id
HAVING COUNT(r.id) >= 5
ORDER BY rating_count DESC
LIMIT 20;
```

---

## 13. Authentication & Security

### Token Strategy

```
POST /auth/login
  → access_token  (JWT, 15 min, stored in memory / Zustand)
  → refresh_token (JWT, 30 days, stored in HttpOnly cookie)

Axios interceptor:
  - Attaches access_token to Authorization header
  - On 401 → calls /auth/refresh silently → retries request
  - On refresh failure → redirect to login
```

### Security Checklist

- [ ] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] Refresh tokens stored server-side (Redis) for revocation
- [ ] CORS restricted to known origins
- [ ] Rate limiting on `/auth/login` (5 req/min per IP)
- [ ] File upload validation: MIME type check + max size (1 MB for TXT)
- [ ] SQL injection: impossible via SQLAlchemy parameterised queries
- [ ] XSS: React escapes by default; sanitise review text with `bleach`
- [ ] HTTPS enforced in production via Nginx

---

## 14. Deployment Strategy

### Local Development (Docker Compose)

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: filmtracker
      POSTGRES_USER: filmtracker
      POSTGRES_PASSWORD: secret
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    depends_on: [postgres, redis]
    volumes: [./backend:/app]
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  celery:
    build: ./backend
    env_file: ./backend/.env
    depends_on: [postgres, redis]
    command: celery -A app.worker worker --loglevel=info

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    volumes: [./frontend:/app]
    command: npm run dev -- --host

volumes:
  postgres_data:
```

### Production Options

| Option | Cost | Suitability |
|--------|------|-------------|
| **Railway** | ~$5/mo | Best for solo/small team, zero-ops |
| **Render** | Free tier + $7/mo | Good free tier for prototyping |
| **Fly.io** | ~$5/mo | Global edge, great for FastAPI |
| **VPS (Hetzner CX22)** | €4/mo | Most control, cheapest at scale |
| **Supabase** (Postgres only) | Free tier | Managed Postgres with built-in auth option |

---

## 15. Implementation Roadmap

### Phase 1 — Foundation (Weeks 1–2)

- [ ] Docker Compose setup (Postgres, Redis)
- [ ] FastAPI project scaffold + Alembic migrations
- [ ] User registration & login (JWT)
- [ ] React project scaffold (Vite + TypeScript + Tailwind)
- [ ] Zustand auth store + Axios interceptors
- [ ] Login / Register pages

### Phase 2 — Core Social (Weeks 3–4)

- [ ] Follow / unfollow
- [ ] TMDB movie search + detail endpoint
- [ ] Rate & review a movie
- [ ] Feed assembly (followed users' ratings, cursor-based pagination)
- [ ] Feed page (infinite scroll, movie cards)
- [ ] Profile page

### Phase 3 — Onboarding & Import (Weeks 5–6)

- [ ] Genre selection onboarding wizard
- [ ] Recommended users on signup
- [ ] TXT file upload + Celery background processing
- [ ] Import progress polling + results UI

### Phase 4 — Polish & Mobile (Weeks 7–8)

- [ ] Notifications system
- [ ] Explore / trending page
- [ ] Dark / light theme (Tailwind `dark:` classes + uiStore)
- [ ] Capacitor Android setup
- [ ] Generate signed APK

### Phase 5 — Production (Week 9+)

- [ ] Deploy backend (Railway or Fly.io)
- [ ] Deploy frontend (Netlify / same host)
- [ ] Configure Nginx reverse proxy
- [ ] Set up GitHub Actions CI (lint + tests + build)
- [ ] Sentry error tracking
- [ ] Publish APK to Google Play (or direct distribute)

---

## Environment Variables Reference

### Backend (`backend/.env.example`)

```
DATABASE_URL=postgresql+asyncpg://filmtracker:secret@localhost/filmtracker
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-to-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
TMDB_READ_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiJ9...
TMDB_API_KEY=e43f621bb1a02899d3c09a6dbcfb2c35
CORS_ORIGINS=["http://localhost:5173","https://filmtracker.online"]
```

### Frontend (`frontend/.env.example`)

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_TMDB_IMAGE_BASE=https://image.tmdb.org/t/p
```

---

*Generated: 2026-04-22 — FilmTracker Architecture v1.0*
