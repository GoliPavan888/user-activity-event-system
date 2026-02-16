from fastapi import FastAPI

app = FastAPI(title="Consumer Service")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
