from fastapi import FastAPI
from app.api import router

app = FastAPI(title="Ensemble Query API")
app.include_router(router)
