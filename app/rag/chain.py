from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_groq import ChatGroq
from app.config import LLM_MODEL

_PROMPT = ChatPromptTemplate.from_template(
    """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use ten sentences maximum and keep the answer concise.

Question: {question}
Context: {context}
Answer:"""
)

def _format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)

def build_rag_chain(retriever):
    inputs = {"context": retriever | _format_docs, "question": RunnablePassthrough()}

    llm = ChatGroq(model=LLM_MODEL, temperature=0)
    return (
        inputs
        | _PROMPT
        | llm
        | StrOutputParser()
    )