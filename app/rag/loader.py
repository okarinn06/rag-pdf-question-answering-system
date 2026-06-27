import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader

def load_pdf(file_path: str) -> list:
    return PyPDFLoader(file_path).load()

def load_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> list:
    suffix = os.path.splitext(filename)[-1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        docs = load_pdf(tmp_path)
        for doc in docs:
            doc.metadata["source"] = filename
        return docs
    finally:
        os.unlink(tmp_path)