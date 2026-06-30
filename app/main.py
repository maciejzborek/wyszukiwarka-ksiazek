import os
import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

app = FastAPI(
    title="Book Search API",
    description="Search for books using Google Books API",
    version=APP_VERSION,
)

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


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
    """Search for books by title using Google Books API."""
    params = {"q": f"intitle:{title}", "maxResults": limit, "printType": "books"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(GOOGLE_BOOKS_URL, params=params)
            response.raise_for_status()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Google Books request timed out")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Google Books error: {e.response.status_code}")

    data = response.json()
    items = data.get("items", [])

    results = []
    for item in items:
        info = item.get("volumeInfo", {})
        results.append(
            {
                "title": info.get("title", "Unknown"),
                "authors": info.get("authors", []),
                "first_publish_year": info.get("publishedDate", "")[:4] or None,
                "isbn": [
                    id["identifier"]
                    for id in info.get("industryIdentifiers", [])
                    if id["type"] in ("ISBN_13", "ISBN_10")
                ][:3],
                "google_books_id": item.get("id", ""),
            }
        )

    return {
        "query": title,
        "total_found": data.get("totalItems", 0),
        "results": results,
    }
