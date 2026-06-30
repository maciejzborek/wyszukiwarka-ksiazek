import os
import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

app = FastAPI(
    title="Book Search API",
    description="Search for books using OpenLibrary.org",
    version=APP_VERSION,
)

OPENLIBRARY_URL = "http://openlibrary.org/search.json"


@app.get("/", response_class=HTMLResponse)
async def index():
    return """<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Wyszukiwarka Książek</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }
    header { background: #16213e; padding: 24px; text-align: center; box-shadow: 0 2px 10px #0004; }
    header h1 { font-size: 2rem; color: #e94560; }
    header p { color: #aaa; margin-top: 4px; font-size: 0.9rem; }
    .search-box { display: flex; justify-content: center; gap: 10px; padding: 32px 16px; }
    .search-box input {
      width: 100%; max-width: 500px; padding: 12px 18px; border-radius: 8px;
      border: none; font-size: 1rem; background: #16213e; color: #eee;
      outline: 2px solid #e9456044;
    }
    .search-box input:focus { outline-color: #e94560; }
    .search-box button {
      padding: 12px 24px; background: #e94560; color: #fff; border: none;
      border-radius: 8px; font-size: 1rem; cursor: pointer; transition: background 0.2s;
    }
    .search-box button:hover { background: #c73652; }
    #status { text-align: center; color: #aaa; padding-bottom: 16px; min-height: 24px; }
    #results {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 24px; padding: 0 32px 48px;
      max-width: 1200px; margin: 0 auto;
    }
    .card {
      background: #16213e; border-radius: 12px; overflow: hidden;
      box-shadow: 0 4px 15px #0005; transition: transform 0.2s;
    }
    .card:hover { transform: translateY(-4px); }
    .card img { width: 100%; height: 240px; object-fit: cover; background: #0f3460; display: block; }
    .card .no-cover {
      width: 100%; height: 240px; display: flex; align-items: center; justify-content: center;
      background: #0f3460; color: #555; font-size: 3rem;
    }
    .card-body { padding: 12px; }
    .card-body h3 { font-size: 0.9rem; color: #eee; margin-bottom: 6px; line-height: 1.3; }
    .card-body p { font-size: 0.78rem; color: #aaa; }
    .card-body .year { margin-top: 4px; color: #e94560; font-size: 0.75rem; }
  </style>
</head>
<body>
  <header>
    <h1>📚 Wyszukiwarka Książek</h1>
    <p>Dane z OpenLibrary.org</p>
  </header>
  <div class="search-box">
    <input id="q" type="text" placeholder="Wpisz tytuł książki..." onkeydown="if(event.key==='Enter')searchBooks()"/>
    <button onclick="searchBooks()">Szukaj</button>
  </div>
  <div id="status"></div>
  <div id="results"></div>
  <script>
    async function searchBooks() {
      const q = document.getElementById('q').value.trim();
      if (!q) return;
      const status = document.getElementById('status');
      const results = document.getElementById('results');
      status.textContent = 'Szukam...';
      results.innerHTML = '';
      try {
        const res = await fetch('/search?title=' + encodeURIComponent(q) + '&limit=20');
        const data = await res.json();
        if (!res.ok) { status.textContent = 'Błąd: ' + (data.detail || res.status); return; }
        status.textContent = 'Znaleziono: ' + data.total_found + ' wyników (pokazuję ' + data.results.length + ')';
        data.results.forEach(book => {
          const isbn = book.isbn && book.isbn[0];
          const coverUrl = isbn ? 'http://covers.openlibrary.org/b/isbn/' + isbn + '-M.jpg' : null;
          const authors = book.authors && book.authors.length ? book.authors.join(', ') : 'Nieznany autor';
          const card = document.createElement('div');
          card.className = 'card';
          card.innerHTML = coverUrl
            ? '<img src="' + coverUrl + '" alt="okładka" onerror="this.outerHTML=\'<div class=no-cover>📖</div>\'">'
            : '<div class="no-cover">📖</div>';
          card.innerHTML += '<div class="card-body"><h3>' + escHtml(book.title) + '</h3>'
            + '<p>' + escHtml(authors) + '</p>'
            + (book.first_publish_year ? '<p class="year">' + book.first_publish_year + '</p>' : '')
            + '</div>';
          results.appendChild(card);
        });
      } catch(e) { status.textContent = 'Błąd połączenia.'; }
    }
    function escHtml(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }
  </script>
</body>
</html>"""


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
