from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import router

app = FastAPI(title="RAG API", 
              version="1.0.0", 
              description="PDF-based RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "RAG API is running. Visit /docs for the interactive API reference."}