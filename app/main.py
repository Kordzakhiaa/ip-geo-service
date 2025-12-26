from fastapi import FastAPI
from fastapi import status

app = FastAPI()


@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok"}
