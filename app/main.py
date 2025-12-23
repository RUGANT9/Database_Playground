from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="FastAPI + MongoDB Masterclass")

app.include_router(router)
