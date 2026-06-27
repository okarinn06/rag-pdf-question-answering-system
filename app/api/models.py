from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

class IngestResponse(BaseModel):
    message: str
    pages: int
    chunks: int