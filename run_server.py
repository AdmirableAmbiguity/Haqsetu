try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
import os
import sys
import uvicorn

if __name__ == "__main__":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if "SARVAM_API_KEY" not in os.environ:
        os.environ["SARVAM_API_KEY"] = "sk_dwlnlpua_lms1lJhcnSxkZIGEB8WD9819"
    
    print("=" * 60)
    print("Starting VachanSetu Web Application...")
    print("URL: http://localhost:8000")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
