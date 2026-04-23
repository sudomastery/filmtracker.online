from pydantic import BaseModel


class ImportRequest(BaseModel):
    job_id: str


class ImportStatus(BaseModel):
    job_id: str
    status: str          # pending | processing | done | failed
    total: int
    processed: int
    matched: int
    unmatched: int


class ImportMovieResult(BaseModel):
    line: str
    matched: bool
    tmdb_id: int | None = None
    title: str | None = None
    poster_url: str | None = None
    release_year: int | None = None
    confidence: int | None = None


class ImportResults(BaseModel):
    job_id: str
    results: list[ImportMovieResult]
