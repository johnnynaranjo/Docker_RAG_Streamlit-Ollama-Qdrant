import streamlit as st
import ollama
import requests
from typing import Dict, List, Tuple
from collections.abc import Iterator

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse, RetrievalMode
from langchain_ollama import OllamaLLM

from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# ----------------------------- FUNCIONES DE UTILIDAD -----------------------------

def check_connection(url, container_name: str):
    session_key = f"{container_name}_connection_ok"

    # Si ya fue verificado con éxito en esta sesión, no repetir
    if st.session_state.get(session_key, False):
        return True

    try:
        response = requests.get(url, timeout=(1, 2)) # 1s conectar, 2s leer
        if response.status_code == 200:
            st.success(f"✅ Conexión exitosa con {container_name}.")
            st.session_state[session_key] = True
            return True
        else:
            st.error(f"⚠️ El contenedor de {container_name} respondió con código {response.status_code}.")
            return False
    except requests.exceptions.ConnectTimeout:
        st.error(f"⏱️ Tiempo de espera agotado al conectar con {container_name}.")
        return False
    except requests.exceptions.ReadTimeout:
        st.error(f"⏱️ Tiempo de espera agotado esperando respuesta de {container_name}.")
        return False
    except requests.exceptions.ConnectionError:
        st.error(f"❌ No se pudo establecer conexión con {container_name}. Asegúrate de que esté en ejecución.")
        return False
    except Exception as e:
        st.error(f"⚠️ Error inesperado al conectar con {container_name}: {e}")
        return False

def ollama_check_model(url, container_name: str):
    # Verifica conexión
    if not check_connection(url, container_name):
        return  # Salida temprana si falla la conexión

    try:
        # Muestra los modelos disponibles
        modelos = ollama.list()["models"]
        if modelos:
            st.sidebar.selectbox("Modelos disponibles:", [model["model"] for model in modelos], key="selected_model")
        else:
            st.warning("No hay modelo disponible. Descarga uno.")
    except Exception as e:
        st.error(f"Error al obtener modelos de Ollama: {e}")

def qdrant_check_db(url, container_name: str):
    # Verifica conexión
    if not check_connection(url, container_name):
        return None  # Salida temprana si falla la conexión

    try:
        # carga la url de la base de datos en el cliente
        client = QdrantClient(url=url)
        # Verifica si hay colecciones existentes
        collections = client.get_collections().collections
        existing_collections = [col.name for col in collections]
        # Muestra las colecciones existentes
        if existing_collections:
            st.sidebar.selectbox("Colecciones disponibles:", existing_collections, key="selected_db")
        else:
            st.warning("No hay colecciones existentes. Crea una nueva.")

        return client

    except Exception as e:
        st.error(f"Error al conectar con Qdrant: {e}")
        return None

# ----------------------------- RECUPERACIÓN DE DOCUMENTOS -----------------------------

def retrieve_with_scores(client: QdrantClient, collection_name: str, query: str, embedding_model: str, top_k: int = 5) -> List[Tuple[str, float]]:
    dense_embeddings = OllamaEmbeddings(model=embedding_model)
    query_vector = dense_embeddings.embed_query(query)
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False
    )
    return [(hit.payload.get("page_content", ""), hit.score) for hit in search_result]

# ----------------------------- GENERACIÓN CON LLM -----------------------------

def generate_response_with_context(model_name: str, context_docs: List[str], query: str, temp: float = 0.1) -> Iterator[str]:

    llm = OllamaLLM(model=model_name, temperature=temp)
    prompt = PromptTemplate.from_template(
        """Responde la siguiente pregunta usando el contexto proporcionado. 
        Si no puedes responder basándote únicamente en el contexto, responde "No sé".

        Contexto:
        {context}

        Pregunta:
        {question}
        """
    )

    chain: RunnableSequence = (
        (lambda _: {"context": "\n\n".join(context_docs), "question": query})
        | prompt
        | llm
        | StrOutputParser()
    )

    full_response = ""
    for chunk in chain.stream(query):
        full_response += chunk
        yield chunk

# ----------------------------- MAIN -----------------------------

def main():
    st.set_page_config(
        page_title="Chatea con RAG",
        page_icon="🤖",
    )
    st.title("🤖 Chatea con RAG")

    ollama_check_model("http://localhost:11434", "Ollama")
    client = qdrant_check_db("http://localhost:6333", "Qdrant")

    st.sidebar.selectbox(
        "Embeddings disponibles:",
        [model["model"] for model in ollama.list()["models"]],
        key="embedding_model"
    )

    # Número de respuestas similares a mostrar
    st.sidebar.slider("Número de opciones similares:", min_value=1, max_value=10, value=3, key= "top_k")
    # Temperatura
    st.sidebar.slider("Temperatura:", min_value=0.0, max_value=2.0, value=0.7, step=0.1, key="temp")

    if "rag_messages" not in st.session_state:
        st.session_state.rag_messages = []

    for message in st.session_state.rag_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if query := st.chat_input("Escribe tu consulta..."):
        with st.chat_message("user"):
            st.markdown(query)

        st.session_state.rag_messages.append({"role": "user", "content": query})

        with st.chat_message("assistant"):
            st.markdown("### 🔍 Documentos similares encontrados:")

            results = retrieve_with_scores(
                client=client,
                collection_name=st.session_state.selected_db,
                query=query,
                embedding_model=st.session_state.embedding_model,
                top_k=st.session_state.top_k,
            )

            for i, (content, score) in enumerate(results):
                st.markdown(f"**Opción {i+1}** - Similitud: `{score:.2f}`")
                st.code(content, language="markdown")

            st.markdown("---")
            st.markdown("### 🤖 Generando respuesta...")

            response_stream = generate_response_with_context(
                model_name=st.session_state.selected_model,
                context_docs=[doc for doc, _ in results],
                query=query,
                temp=st.session_state.temp,
            )

            response_collected = ""
            for chunk in st.write_stream(response_stream):
                response_collected += chunk

        st.session_state.rag_messages.append({"role": "assistant", "content": response_collected})

if __name__ == "__main__":
    main()
