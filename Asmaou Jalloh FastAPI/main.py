from fastapi import FastAPI
from datetime import date, timedelta
from typing import Optional

app = FastAPI()

# ── In-Memory Database ───────────────────────────────
books_db = {
    1: {"id":1,"title":"Clean Code","author":"Robert C. Martin","category":"Programming","available":True},
    2: {"id":2,"title":"Python Crash Course","author":"Eric Matthes","category":"Programming","available":True},
    3: {"id":3,"title":"The Great Gatsby","author":"F. Scott Fitzgerald","category":"Fiction","available":True},
    4: {"id":4,"title":"Atomic Habits","author":"James Clear","category":"Self-Help","available":True},
    5: {"id":5,"title":"Intro to Algorithms","author":"Thomas H. Cormen","category":"Comp Sci","available":True},
}

users_db = {
    101: {"id":101,"name":"Aminata Kamara","email":"aminata@limkokwing.edu.sl"},
    102: {"id":102,"name":"Mohamed Sesay","email":"mohamed@limkokwing.edu.sl"},
    103: {"id":103,"name":"Fatima Bangura","email":"fatima@limkokwing.edu.sl"},
}

borrow_records = []
FINE_PER_DAY = 0.50


# ── Endpoint 1: Search Books ─────────────────────────
@app.get("/books")
async def get_books(
    title: Optional[str] = None,
    author: Optional[str] = None,
    category: Optional[str] = None
):
    results = list(books_db.values())

    if title:
        results = [b for b in results if title.lower() in b["title"].lower()]

    if author:
        results = [b for b in results if author.lower() in b["author"].lower()]

    if category:
        results = [b for b in results if category.lower() == b["category"].lower()]

    return results


# ── Endpoint 2: Borrow Book ──────────────────────────
@app.post("/borrow")
async def borrow_book(user_id: int, book_id: int):

    if user_id not in users_db:
        return {"error": f"User {user_id} not found."}

    if book_id not in books_db:
        return {"error": f"Book {book_id} not found."}

    if not books_db[book_id]["available"]:
        return {"error": f"Book '{books_db[book_id]['title']}' not available."}

    books_db[book_id]["available"] = False

    due_date = date.today() + timedelta(days=14)

    borrow_records.append({
        "user_id": user_id,
        "book_id": book_id,
        "borrow_date": str(date.today()),
        "due_date": str(due_date),
        "returned": False
    })

    return {
        "message": f"Book '{books_db[book_id]['title']}' borrowed successfully.",
        "user": users_db[user_id]["name"],
        "due_date": str(due_date)
    }


# ── Endpoint 3: Return Book ──────────────────────────
@app.post("/return")
async def return_book(user_id: int, book_id: int):

    record = next(
        (
            r for r in borrow_records
            if r["user_id"] == user_id
            and r["book_id"] == book_id
            and not r["returned"]
        ),
        None
    )

    if not record:
        return {"error": "No active borrow record found."}

    record["returned"] = True
    books_db[book_id]["available"] = True

    due = date.fromisoformat(record["due_date"])

    fine = round((date.today() - due).days * FINE_PER_DAY, 2) if date.today() > due else 0.0

    return {
        "message": f"Book '{books_db[book_id]['title']}' returned.",
        "user": users_db[user_id]["name"],
        "fine_usd": fine
    }


# ── Endpoint 4: Overdue Books ────────────────────────
@app.get("/overdue")
async def get_overdue_books():

    today = date.today()

    return [
        {
            "user": users_db.get(r["user_id"], {}).get("name", "?"),
            "book": books_db.get(r["book_id"], {}).get("title", "?"),
            "due_date": r["due_date"],
            "days_overdue": (today - date.fromisoformat(r["due_date"])).days,
            "fine_usd": round(
                (today - date.fromisoformat(r["due_date"])).days * FINE_PER_DAY,
                2
            )
        }
        for r in borrow_records
        if not r["returned"] and today > date.fromisoformat(r["due_date"])
    ]


# ── Endpoint 5: Register User ────────────────────────
@app.post("/register")
async def register_user(name: str, email: str):

    new_id = max(users_db.keys(), default=100) + 1

    users_db[new_id] = {
        "id": new_id,
        "name": name,
        "email": email
    }

    return {
        "message": "User registered successfully.",
        "user_id": new_id,
        "name": name
    }
