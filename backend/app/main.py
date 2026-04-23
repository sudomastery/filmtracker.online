from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth, users, feed, movies, ratings, watchlist, import_, onboarding, notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (Alembic handles prod migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="FilmTracker API",
    version="1.0.0",
    description="Social movie tracking platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers under /api/v1
PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(feed.router, prefix=PREFIX)
app.include_router(movies.router, prefix=PREFIX)
app.include_router(ratings.router, prefix=PREFIX)
app.include_router(watchlist.router, prefix=PREFIX)
app.include_router(import_.router, prefix=PREFIX)
app.include_router(onboarding.router, prefix=PREFIX)
app.include_router(notifications.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
