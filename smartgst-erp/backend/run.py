#!/usr/bin/env python
"""
SmartGST AI ERP - Backend Startup Script
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Change to backend directory
os.chdir(backend_dir)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SmartGST AI ERP - Backend Server")
    print("="*60)
    print(f"Starting on http://127.0.0.1:8000")
    print(f"API Docs: http://127.0.0.1:8000/api/docs")
    print(f"ReDoc: http://127.0.0.1:8000/api/redoc")
    print("="*60 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True,
    )
