from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import RETRIEVER_K

def build_vectorstore(chunks: list) -> FAISS:
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        encode_kwargs={"normalize_embeddings": True}
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local("../data/faiss_index")
    return vectorstore

def load_vectorstore_local():
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        encode_kwargs={"normalize_embeddings": True}
    )
    vectorstore = FAISS.load_local(
        "../data/faiss_index",
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )
    return vectorstore

def get_retriever():
    vectorstore = load_vectorstore_local()
    return vectorstore.as_retriever(
        search_kwargs = {"k" : RETRIEVER_K}
    )