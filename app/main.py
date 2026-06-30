import os
import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

app = FastAPI(
    title="Book Search API",
    description="Search for books using OpenLibrary.org",
    version=APP_VERSION,
)

OPENLIBRARY_URL = "http://openlibrary.org/search.json"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/version")
async def version():
    return {"version": APP_VERSION}


@app.get("/search")
async def search_books(
    title: str = Query(..., description="Book title to search for"),
    limit: int = Query(5, ge=1, le=20, description="Number of results (1-20)"),
):
    """Search for books by title using OpenLibrary.org."""
    params = {"title": title, "limit": limit, "fields": "title,author_name,first_publish_year,isbn,key"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OPENLIBRARY_URL, params=params)
            response.raise_for_status()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="OpenLibrary request timed out")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"OpenLibrary error: {e.response.status_code}")

    data = response.json()
    docs = data.get("docs", [])

    results = []
    for doc in docs:
        results.append(
            {
                "title": doc.get("title", "Unknown"),
                "authors": doc.get("author_name", []),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [])[:3],
                "openlibrary_key": doc.get("key", ""),
            }
        )

    return {
        "query": title,
        "total_found": data.get("numFound", 0),
        "results": results,
    }
