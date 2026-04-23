"""
Tests for movie import endpoints:
  POST /import/txt            – upload a .txt file, returns job_id
  GET  /import/{job_id}/status – poll processing progress
  GET  /import/{job_id}/results – retrieve matched/unmatched results

The happy-path test makes real TMDB API calls for well-known films.
Fast-path (validation) tests are fully local.
"""
import asyncio
import pytest
from httpx import AsyncClient


# ─── Helpers ───────────────────────────────────────────────────────────────

async def register_user(client: AsyncClient, username: str) -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "password123",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def txt_file(content: str) -> dict:
    return {"file": ("movies.txt", content.encode(), "text/plain")}


# ─── Auth guard ────────────────────────────────────────────────────────────

async def test_import_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/import/txt",
        files=txt_file("The Dark Knight"),
    )
    assert resp.status_code == 401


# ─── Input validation ──────────────────────────────────────────────────────

async def test_import_rejects_non_txt(client: AsyncClient):
    tokens = await register_user(client, "importreject")
    resp = await client.post(
        "/api/v1/import/txt",
        headers=auth(tokens),
        files={"file": ("movies.csv", b"The Dark Knight", "text/csv")},
    )
    assert resp.status_code == 400
    assert "txt" in resp.json()["detail"].lower()


async def test_import_rejects_empty_file(client: AsyncClient):
    tokens = await register_user(client, "importempty")
    resp = await client.post(
        "/api/v1/import/txt",
        headers=auth(tokens),
        files=txt_file("# only comments\n\n   \n"),
    )
    assert resp.status_code == 400
    assert "No movie titles" in resp.json()["detail"]


async def test_import_unknown_job_status(client: AsyncClient):
    tokens = await register_user(client, "importstatus")
    resp = await client.get(
        "/api/v1/import/00000000-0000-0000-0000-000000000000/status",
        headers=auth(tokens),
    )
    assert resp.status_code == 404


async def test_import_unknown_job_results(client: AsyncClient):
    tokens = await register_user(client, "importresults")
    resp = await client.get(
        "/api/v1/import/00000000-0000-0000-0000-000000000000/results",
        headers=auth(tokens),
    )
    assert resp.status_code == 404


# ─── Status endpoint structure ─────────────────────────────────────────────

async def test_import_status_fields(client: AsyncClient):
    """Check that status response contains all expected fields."""
    tokens = await register_user(client, "importfields")
    upload = await client.post(
        "/api/v1/import/txt",
        headers=auth(tokens),
        files=txt_file("Inception"),
    )
    assert upload.status_code == 202
    job_id = upload.json()["job_id"]

    status_resp = await client.get(
        f"/api/v1/import/{job_id}/status",
        headers=auth(tokens),
    )
    assert status_resp.status_code == 200
    data = status_resp.json()
    for field in ("job_id", "status", "total", "processed", "matched", "unmatched"):
        assert field in data, f"missing field: {field}"
    assert data["total"] == 1


# ─── Happy path (real TMDB) ────────────────────────────────────────────────

async def test_import_well_known_films(client: AsyncClient):
    """
    Upload three well-known titles; expect all to be matched.
    Polls until done (max 30 s) then verifies results structure.
    """
    tokens = await register_user(client, "importhappy")

    content = "\n".join([
        "# favourite films",
        "The Dark Knight",
        "Inception",
        "Parasite",
    ])
    upload = await client.post(
        "/api/v1/import/txt",
        headers=auth(tokens),
        files=txt_file(content),
    )
    assert upload.status_code == 202
    job_id = upload.json()["job_id"]

    # Poll until done (30 s timeout)
    for _ in range(30):
        status_resp = await client.get(
            f"/api/v1/import/{job_id}/status",
            headers=auth(tokens),
        )
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status["total"] == 3   # comment line skipped
        if status["status"] == "done":
            break
        await asyncio.sleep(1)
    else:
        pytest.fail("Import job did not complete within 30 s")

    # Fetch results
    results_resp = await client.get(
        f"/api/v1/import/{job_id}/results",
        headers=auth(tokens),
    )
    assert results_resp.status_code == 200
    results = results_resp.json()["results"]
    assert len(results) == 3

    # Each matched result must have the required fields
    matched = [r for r in results if r["matched"]]
    assert len(matched) >= 2, "Expected at least 2 of 3 well-known films to match"

    for r in matched:
        assert r["tmdb_id"] is not None
        assert r["title"] is not None
        assert r["confidence"] is not None
        assert r["confidence"] >= 70

    # Verify movies were added to the user's watchlist
    wl_resp = await client.get("/api/v1/watchlist", headers=auth(tokens))
    assert wl_resp.status_code == 200
    wl_titles = [item["movie"]["title"] for item in wl_resp.json()]
    assert len(wl_titles) >= 2


async def test_import_comment_lines_skipped(client: AsyncClient):
    """Lines starting with # must not count toward total."""
    tokens = await register_user(client, "importcomments")

    content = "# this is a comment\nInception\n# another comment\nParasite\n"
    upload = await client.post(
        "/api/v1/import/txt",
        headers=auth(tokens),
        files=txt_file(content),
    )
    assert upload.status_code == 202
    job_id = upload.json()["job_id"]

    status_resp = await client.get(
        f"/api/v1/import/{job_id}/status",
        headers=auth(tokens),
    )
    assert status_resp.json()["total"] == 2  # only non-comment lines
