from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import CHUNK_OVERLAP, CHUNK_SIZE

def split_documents(documents: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP
    )
    return splitter.split_documents(documents)