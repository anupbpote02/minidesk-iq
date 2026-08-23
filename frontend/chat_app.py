import os
import sys

import requests
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import API_BASE_URL, POLICIES_DIR  # noqa: E402
from frontend.auth import render_login_gate  # noqa: E402
from frontend.theme import BASE_CSS, GRIDLINE, SURFACE, TEXT_MUTED  # noqa: E402

st.set_page_config(page_title="MiniDesk IQ", page_icon="🛠️", layout="wide")

render_login_gate(
    allowed_roles={"employee", "admin"},
    title="User Login",
    welcome_text="Welcome back to MiniDesk IQ",
    welcome_icon="🛠️",
)

EXTRA_CSS = f"""
<style>
    .kb-doc-card {{
        background-color: {SURFACE};
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border: 1px solid {GRIDLINE};
    }}
    .empty-state {{
        text-align: center;
        color: {TEXT_MUTED};
        padding: 60px 20px;
    }}
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown(EXTRA_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=30)
def get_kb_summary():
    try:
        resp = requests.get(f"{API_BASE_URL}/knowledge-base/summary", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def load_local_doc_previews() -> dict[str, str]:
    previews = {}
    if not os.path.isdir(POLICIES_DIR):
        return previews
    for fname in sorted(os.listdir(POLICIES_DIR)):
        if fname.endswith(".md"):
            with open(os.path.join(POLICIES_DIR, fname), "r", encoding="utf-8") as f:
                content = f.read()
            previews[fname] = content
    return previews


with st.sidebar:
    st.caption(f"Logged in as **{st.session_state.display_name}** ({st.session_state.user_email})")
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_role = None
        st.session_state.display_name = None
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("## 📚 Knowledge Base")

    kb_summary = get_kb_summary()
    previews = load_local_doc_previews()

    if kb_summary:
        st.markdown(
            f"**{kb_summary['doc_count']} documents** · **{kb_summary['chunk_count']} chunks** indexed"
        )
    else:
        st.warning("Backend not reachable. Showing local policy files only.")
        st.markdown(f"**{len(previews)} documents** found locally")

    st.markdown("---")

    for fname, content in previews.items():
        doc_col, delete_col = st.columns([6, 1])
        with doc_col:
            with st.expander(f"📄 {fname}"):
                st.markdown(content[:1500] + ("..." if len(content) > 1500 else ""))
        with delete_col:
            if st.button("🗑️", key=f"delete_{fname}", help=f"Delete {fname}"):
                try:
                    resp = requests.delete(
                        f"{API_BASE_URL}/knowledge-base/documents/{fname}", timeout=30
                    )
                    resp.raise_for_status()
                    get_kb_summary.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete {fname}: {e}")

    st.markdown("---")
    with st.expander("➕ Add a Policy Document"):
        st.caption("Upload a Markdown or PDF file to add it to the knowledge base.")
        uploaded_file = st.file_uploader(
            "Upload document", type=["md", "pdf", "txt"], label_visibility="collapsed"
        )
        if uploaded_file is not None:
            if st.button("Add to Knowledge Base", use_container_width=True):
                with st.spinner(f"Chunking and embedding {uploaded_file.name}..."):
                    try:
                        files = {
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type or "application/octet-stream",
                            )
                        }
                        resp = requests.post(
                            f"{API_BASE_URL}/knowledge-base/upload", files=files, timeout=120
                        )
                        resp.raise_for_status()
                        result = resp.json()
                        st.success(
                            f"Added '{result['uploaded_as']}' — knowledge base now has "
                            f"{result['doc_count']} documents / {result['chunk_count']} chunks."
                        )
                        get_kb_summary.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

st.markdown("# 🛠️ MiniDesk IQ")
st.caption("Your agentic IT service desk copilot")

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-state">
            <h3>👋 Ask me anything about IT policies</h3>
            <p>Try: "How do I request VPN access?" or "I need a new laptop, mine is broken."</p>
            <p>I can answer from our policy knowledge base, file tickets, and check ticket status.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("meta"):
            meta = msg["meta"]
            badges = []
            if meta.get("sources"):
                badges.append(f"📖 Sources: {', '.join(meta['sources'])}")
            if meta.get("tools_called"):
                badges.append(f"🔧 Tools: {', '.join(meta['tools_called'])}")
            if meta.get("is_knowledge_gap"):
                badges.append("⚠️ Knowledge gap logged")
            if badges:
                st.caption(" | ".join(badges))

if prompt := st.chat_input("Ask a question or make a request..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={"message": prompt, "requester": st.session_state.user_email},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data["response"]
                st.markdown(answer)
                badges = []
                if data.get("sources"):
                    badges.append(f"📖 Sources: {', '.join(data['sources'])}")
                if data.get("tools_called"):
                    badges.append(f"🔧 Tools: {', '.join(data['tools_called'])}")
                if data.get("is_knowledge_gap"):
                    badges.append("⚠️ Knowledge gap logged")
                if badges:
                    st.caption(" | ".join(badges))
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "meta": {
                            "sources": data.get("sources"),
                            "tools_called": data.get("tools_called"),
                            "is_knowledge_gap": data.get("is_knowledge_gap"),
                        },
                    }
                )
            except Exception as e:
                error_msg = f"Sorry, I couldn't reach the MiniDesk IQ backend: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
