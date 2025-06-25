
# run command in powershell


# Activate virtual environment if needed
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# Run the FastAPI app using uvicorn
uvicorn fast_api:app --reload --host 0.0.0.0 --port 8000


