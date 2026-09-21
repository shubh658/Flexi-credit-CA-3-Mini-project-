import uvicorn
from app import database

if __name__ == "__main__":
    print("=========================================================")
    print("  [AegisResponse AI] Public Safety Incident Agent")
    print("  Initializing SQLite Database & Emergency Fleet...")
    database.init_db()
    print("  Server launching at http://localhost:8000")
    print("=========================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
