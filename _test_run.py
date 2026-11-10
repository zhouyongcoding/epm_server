import sys
print("Python version:", sys.version)
print("Starting import...")
from app.main import app
print("Import OK")
import uvicorn
print("Starting server...")
uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")