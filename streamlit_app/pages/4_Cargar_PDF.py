import streamlit as st
import ollama
import requests
import tempfile
# load data
from langchain_community.document_loaders import PDFPlumberLoader
# import files to vector store
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
# db split documents into chunks
from langchain_experimental.text_splitter import SemanticChunker
from langchain_ollama import OllamaEmbeddings
# db save chunks to vector store
from langchain_qdrant import QdrantVectorStore
from langchain_qdrant import FastEmbedSparse, RetrievalMode

import os

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

# ----------------------------- FUNCIONES DE SISTEMA DE ARCHIVOS -----------------------------

def load_pdfs_from_folder(folder_path):
    all_documents = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                full_path = os.path.join(root, file)
                try:
                    loader = PDFPlumberLoader(full_path)
                    docs = loader.load()
                    all_documents.extend(docs)
                except Exception as e:
                    st.warning(f"No se pudo cargar {file}: {e}")
    
    return all_documents

def load_pdf(uploaded_file):
    # Save the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    # Load PDF using the temporary file path
    loader = PDFPlumberLoader(tmp_path)
    return loader.load()

# ----------------------------- VECTOR DB -----------------------------

def qdrant_create_vector_index(url, container_name, embedding_model_name, collection_name, documents):
    # verifica si el contenedor de Qdrant está en ejecución
    status = check_connection(url, container_name)

    # carga la url de la base de datos en el cliente
    client = QdrantClient(url=url)

    # Verifica si hay colecciones existentes
    if status == True:

        embeddings_model = OllamaEmbeddings(model=embedding_model_name)

        # seleccionar el modelo y hacer el pull si no existe
        with st.spinner("Semantic Chunker", show_time=True):
            text_splitter = SemanticChunker(embeddings_model)
            st.success("1/3 Chunking completado")
        
        with st.spinner("Dividiendo documento", show_time=True):
            document = text_splitter.split_documents(documents)
            st.success("2/3 División completada")
        
        with st.spinner("Creando índice vectorial", show_time=True):
            # definir el modelo sparse
            sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

            # crear el vector store
            vector_store = QdrantVectorStore.from_documents(
                document,
                embedding=embeddings_model,
                sparse_embedding=sparse_embeddings,
                location=url,
                prefer_grpc=True,
                collection_name=collection_name,
                retrieval_mode=RetrievalMode.HYBRID,
                force_recreate=True,
            )
            st.success("3/3 Índice vectorial creado")

# ----------------------------- MAIN -----------------------------

def main():
    
    st.set_page_config(
        page_title="Cargar PDF",
        page_icon="📁",
    )

    st.title("📁 Cargar PDF")

    # Mostrar parámetros solo si hay modelos disponibles
    st.sidebar.title('Ajustes')

    # Verificar si hay modelos cargados en Ollama
    ollama_check_model("http://ollama:11434", "Ollama")

    # Opción para subir archivo o carpeta
    upload_option = st.sidebar.radio("Selecciona fuente de datos:", ["Archivo PDF", "Carpeta con PDFs"])

    doc = None

    if upload_option == "Archivo PDF":
        uploaded_file = st.file_uploader("Sube tu archivo PDF", type="pdf")
        if uploaded_file is not None:
            doc = load_pdf(uploaded_file)
            st.success("Archivo PDF cargado con éxito!")

    elif upload_option == "Carpeta con PDFs":
        folder_path = st.text_input("Ruta local a la carpeta con PDFs")
        if folder_path and os.path.isdir(folder_path):
            doc = load_pdfs_from_folder(folder_path)
            st.success(f"Se cargaron {len(doc)} documentos desde la carpeta.")
        elif folder_path:
            st.warning("La ruta proporcionada no es válida.")

    # Conexión con Qdrant
    client = qdrant_check_db("http://qdrant:6333", "Qdrant")

    if st.button("Crear índice vectorial"):
        if not doc:
            st.warning("Primero sube un archivo o selecciona una carpeta.")
        else:
            if client:
                qdrant_create_vector_index(
                    url="http://qdrant:6333",
                    container_name="Qdrant",
                    embedding_model_name=st.session_state.selected_model,
                    collection_name=st.session_state.selected_db,
                    documents=doc
                )
                st.success(f"Índice vectorial '{st.session_state.selected_db}' creado con éxito!")

if __name__ == "__main__":
    main()
