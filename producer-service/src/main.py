from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Producer Service")

@app.get("/health")
def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"}
    )
