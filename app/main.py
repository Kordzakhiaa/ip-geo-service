from fastapi import FastAPI, status

from app.api.v1 import endpoints
from app.core.settings import API_V1_PREFIX

app = FastAPI(title="IP Geo Service", version="1.0")
app.include_router(endpoints.router, prefix=API_V1_PREFIX)


@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "Hello World"}
