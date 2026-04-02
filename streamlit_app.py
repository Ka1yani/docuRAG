import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="docuRAG", page_icon="📚", layout="wide")

st.title("📚 docuRAG - Local Document Querying")
st.write("Upload your documents (PDF, DOCX, TXT) and ask questions. Powered by FastAPI, PostgreSQL Full-Text Search, and Mistral (Ollama).")

# Sidebar for document management
with st.sidebar:
    st.header("📄 Custom Documents")
    
    uploaded_file = st.file_uploader("Upload a new document", type=["pdf", "doc", "docx", "txt"])
    if st.button("Upload to System"):
        if uploaded_file is not None:
            with st.spinner("Processing document..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_URL}/upload", files=files)
                    if response.status_code == 201:
                        st.success(f"{uploaded_file.name} uploaded successfully!")
                    else:
                        st.error(f"Failed to upload: {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to backend: {e}")
        else:
            st.warning("Please select a file to upload.")
            
    st.divider()
    st.subheader("Available Documents")
    try:
        doc_resp = requests.get(f"{API_URL}/documents")
        if doc_resp.status_code == 200:
            docs = doc_resp.json()
            if not docs:
                st.write("No documents uploaded yet.")
            for d in docs:
                st.write(f"- {d['file_name']}")
        else:
            st.write("Could not fetch documents.")
    except:
        st.write("Backend not reachable.")

# Main Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        citations_placeholder = st.empty()
        
        with st.spinner("Searching documents and thinking..."):
            try:
                response = requests.post(f"{API_URL}/ask", json={"query": prompt}, timeout=120)
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("final_answer", "Error getting answer.")
                    citations = data.get("citations", [])
                    
                    # Formatting citations
                    cite_text = ""
                    if citations:
                        cites_str = ", ".join([f"`{c['file_name']}` (Page {c['page_number']})" for c in citations])
                        cite_text = f"\n\n**Sources:** {cites_str}"
                    
                    full_response = answer + cite_text
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    msg = f"Error: {response.status_code} - {response.text}"
                    message_placeholder.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
            except Exception as e:
                msg = f"Failed to reach FastAPI backend: {e}"
                message_placeholder.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
