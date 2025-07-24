import streamlit as st
import ollama
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

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
        st.error(f"❌ No se pudo establecer conexión con {container_name} usando {url}. Asegúrate de que esté en ejecución.")
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

def ollama_pull_model(model_name: str):
    try:
        with st.spinner(f"Descargando modelo '{model_name}'...", show_time=True):
            ollama.pull(model_name)
        st.success(f"Modelo '{model_name}' descargado con éxito.")
    except Exception as e:
        st.error(f"No se pudo descargar el modelo '{model_name}': {e}")

def ollama_delete_model(url, container_name: str):
    if not check_connection(url, container_name):
        return

    try:
        modelos = ollama.list()["models"]
        if modelos:
            selected_model = st.selectbox("Selecciona el modelo a eliminar:", [model["model"] for model in modelos], key="delete_model")
            if st.button("Eliminar modelo", key="delete_model_button"):
                ollama.delete(model=selected_model)
                st.success(f"Modelo '{selected_model}' eliminado con éxito.")
        else:
            st.info("No hay modelos disponibles para eliminar.")
    except Exception as e:
        st.error(f"Error al eliminar modelo: {e}")

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

def qdrant_create_db(db_to_create, client):

    # Crea la coleccion en Qdrant
    client.create_collection(
        collection_name=db_to_create,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    # Verifica que se ha creado la colección
    if client.collection_exists(db_to_create):
        st.success(f"Colección '{db_to_create}' creada correctamente.")
    else:
        st.error(f"No se pudo crear la colección '{db_to_create}'.")
    # else:
    #     st.warning(f"La colección '{db_name}' ya existe.")

def qdrant_delete_db(url, container_name: str):
    if not check_connection(url, container_name):
        return

    try:
        client = QdrantClient(url=url)
        collections = client.get_collections().collections
        existing_collections = [col.name for col in collections]

        if existing_collections:
            selected_collection = st.selectbox("Selecciona la colección a eliminar:", existing_collections, key="delete_collection")
            if st.button("Eliminar colección", key="delete_collection_button"):
                client.delete_collection(collection_name=selected_collection)
                st.success(f"Colección '{selected_collection}' eliminada con éxito.")
        else:
            st.info("No hay colecciones disponibles para eliminar.")
    except Exception as e:
        st.error(f"Error al eliminar colección: {e}")

def main():

    st.set_page_config(
        page_title="Ajustes de la aplicación",
        page_icon="⚙️",
    )

    st.title("⚙️ Ajustes de la aplicación")

    # Verificar si hay modelos cargados en Ollama
    ollama_check_model("http://ollama:11434", "Ollama")

    # Opción para descargar nuevo modelo
    with st.form("llm_form"):
        model_to_pull = st.text_input("Nombre del modelo a descargar (ej. `llama3.2` o `mxbai-embed-large`):")
        submit_pull = st.form_submit_button("Descargar modelo")
        if submit_pull and model_to_pull:
            ollama_pull_model(model_to_pull)
 
    # Verificar si hay modelos cargados en Qdrant
    client = qdrant_check_db("http://qdrant:6333", "Qdrant")

    # # Dimension del embedding
    # embedding_dim = st.sidebar.number_input("Dimensión del embedding", value=1024, step=1)
    # st.session_state.embedding_dim = int(embedding_dim)

    if client is not None:
        # Opción para crear nueva colección
        with st.form("vector_form"):
            db_to_create = st.text_input("Nombre de la nueva colección:")
            submit_pull = st.form_submit_button("Crear colección")
            if submit_pull and db_to_create:
                qdrant_create_db(db_to_create, client)
    else:
        st.error("No se pudo conectar con Qdrant. No se puede crear colección.")

    # Eliminar modelos
    with st.expander("🗑️ Eliminar modelos de Ollama"):
        ollama_delete_model("http://ollama:11434", "Ollama")

    # Eliminar colecciones
    with st.expander("🗑️ Eliminar colecciones de Qdrant"):
        qdrant_delete_db("http://qdrant:6333", "Qdrant")

if __name__ == "__main__":
    main()
