import streamlit as st

def main():

    # Initialize session variables
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = ""
    if "embedding_model" not in st.session_state:
        st.session_state.embedding_model = ""
    if "selected_db" not in st.session_state:
        st.session_state.selected_db = ""
    if "embedding_dim" not in st.session_state:
        st.session_state.embedding_dim = ""
    if "temp" not in st.session_state:
        st.session_state.temp = 0.7
    if "top_k" not in st.session_state:
        st.session_state.top_k = 3
    if "chat_max_tok" not in st.session_state:
        st.session_state.chat_max_tok = 256
    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    # Initialize chat history
    if "rag_messages" not in st.session_state:
        st.session_state.rag_messages = []

    st.set_page_config(
    page_title="streamlit-ollama",
    page_icon="👋",
    )

    st.title("🧠 LLM Chat App con Streamlit + Ollama + Qdrant")

    st.sidebar.success("Selecciona página")

    st.markdown("""
        Esta aplicación multipágina te permite:
        - Interactuar con un modelo de lenguaje grande (LLM) usando Ollama
        - Realizar preguntas y obtener respuestas
        - Cargar archivos PDF para responder preguntas específicas
        - Ver información del modelo
    """)
    st.image("https://streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.png", width=300)

if __name__ == "__main__":
    main()