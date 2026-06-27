import requests
import streamlit as st
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API = "http://localhost:8000/api"

st.set_page_config(page_title="RAG — Document Q&A", page_icon="📄", layout="centered")
st.title("📄 RAG — Document Q&A")


def safe_json(resp: requests.Response) -> dict:
    """Parse JSON safely; return a dict with 'detail' on failure."""
    try:
        return resp.json()
    except Exception:
        return {"detail": resp.text or f"HTTP {resp.status_code} — no response body"}


def get_health() -> dict:
    try:
        resp = requests.get(f"{API}/health", timeout=3)
        data = safe_json(resp)
        data["reachable"] = resp.status_code == 200
        if resp.status_code != 200:
            data.setdefault("detail", "API health check failed.")
        return data
    except requests.exceptions.ConnectionError:
        return {
            "reachable": False,
            "detail": "Cannot reach the backend. Make sure the FastAPI server is running on port 8000.",
        }
    except requests.exceptions.Timeout:
        return {"reachable": False, "detail": "Backend health check timed out."}


def ingest_file(uploaded_file) -> tuple[bool, dict]:
    try:
        resp = requests.post(
            f"{API}/ingest",
            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
            timeout=120,
        )
        data = safe_json(resp)
        return resp.status_code == 200, data
    except requests.exceptions.ConnectionError:
        return False, {
            "detail": "Cannot reach the backend. Make sure the FastAPI server is running on port 8000."
        }
    except requests.exceptions.Timeout:
        return False, {"detail": "Request timed out. The PDF may be too large — try a smaller file."}


def ensure_document_loaded(uploaded_file) -> tuple[bool, str | None]:
    health = get_health()
    if not health.get("reachable"):
        return False, health.get("detail", "API unreachable — is the backend running?")
    if health.get("document_loaded"):
        return True, None
    if uploaded_file is None:
        return False, "No document loaded. Upload a PDF and click Ingest first."

    ok, data = ingest_file(uploaded_file)
    if ok:
        st.session_state["ready"] = True
        return True, None
    return False, data.get("detail", "Ingestion failed.")


# ── Sidebar: upload & ingest ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Upload Document")
    uploaded = st.file_uploader("Choose a PDF", type="pdf")

    if uploaded:
        if st.button("Ingest", use_container_width=True):
            with st.spinner("Ingesting…"):
                ok, data = ingest_file(uploaded)
                if ok:
                    st.success(data["message"])
                    st.caption(f"{data['pages']} pages · {data['chunks']} chunks")
                    st.session_state["ready"] = True
                    st.session_state["messages"] = []
                else:
                    st.error(data.get("detail", "Ingestion failed."))

    st.divider()
    health = get_health()
    if not health.get("reachable"):
        st.error(health.get("detail", "API unreachable — is the backend running?"))
    elif health.get("document_loaded"):
        st.success("Document loaded")
    elif health.get("mode") == "offline_demo":
        st.warning("Offline demo mode")
        st.caption("Add OPENAI_API_KEY to .env for OpenAI answers.")
    else:
        st.warning("No document loaded")

# ── Chat history ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Query input ───────────────────────────────────────────────────────────────
if question := st.chat_input("Ask a question about your document…"):
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Checking document…"):
            ready, error = ensure_document_loaded(uploaded)
        if not ready:
            st.error(error)
            st.session_state["messages"].append({"role": "assistant", "content": f"Error: {error}"})
        else:
            with st.spinner("Thinking…"):
                try:
                    resp = requests.post(
                        f"{API}/query",
                        json={"question": question},
                        timeout=60,
                    )
                    data = safe_json(resp)
                    if resp.status_code == 200:
                        st.markdown(data["answer"])
                        if data.get("sources"):
                            with st.expander("Sources"):
                                for src in data["sources"]:
                                    st.caption(src)
                        st.session_state["messages"].append({"role": "assistant", "content": data["answer"]})
                    elif resp.status_code == 400 and "No document loaded" in data.get("detail", ""):
                        ready, error = ensure_document_loaded(uploaded)
                        if not ready:
                            st.error(error)
                            st.session_state["messages"].append({"role": "assistant", "content": f"Error: {error}"})
                        else:
                            retry = requests.post(
                                f"{API}/query",
                                json={"question": question},
                                timeout=60,
                            )
                            retry_data = safe_json(retry)
                            if retry.status_code == 200:
                                st.markdown(retry_data["answer"])
                                if retry_data.get("sources"):
                                    with st.expander("Sources"):
                                        for src in retry_data["sources"]:
                                            st.caption(src)
                                st.session_state["messages"].append(
                                    {"role": "assistant", "content": retry_data["answer"]}
                                )
                            else:
                                detail = retry_data.get("detail", "Query failed.")
                                st.error(detail)
                                st.session_state["messages"].append(
                                    {"role": "assistant", "content": f"Error: {detail}"}
                                )
                    else:
                        detail = data.get("detail", "Query failed.")
                        st.error(detail)
                        st.session_state["messages"].append({"role": "assistant", "content": f"Error: {detail}"})
                except requests.exceptions.ConnectionError:
                    detail = "Cannot reach the backend. Make sure the FastAPI server is running on port 8000."
                    st.error(detail)
                    st.session_state["messages"].append({"role": "assistant", "content": f"Error: {detail}"})
                except requests.exceptions.Timeout:
                    detail = "Request timed out. Try a shorter or more specific question."
                    st.error(detail)
                    st.session_state["messages"].append({"role": "assistant", "content": f"Error: {detail}"})