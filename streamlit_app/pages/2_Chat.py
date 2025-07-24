import streamlit as st
import ollama
import requests
from typing import Dict, Generator

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

# ----------------------------- GENERACIÓN CON LLM -----------------------------

def ollama_generator(model_name: str, messages: Dict) -> Generator:
    stream = ollama.chat(
        model=model_name,
        messages=messages,
        stream=True
        )
    for chunk in stream:
        yield chunk['message']['content']

# ----------------------------- MAIN -----------------------------

def main():
    
    st.set_page_config(
        page_title="Chatea con Ollama",
        page_icon="🦜",
    )

    st.title("🦜 Chatea con Ollama")

    # Verificar si hay modelos cargados en Ollama
    ollama_check_model("http://ollama:11434", "Ollama")

    # Display chat messages from history on app rerun
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create the chat interface
    if query := st.chat_input("Enter your query here..."):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(query)
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": query})

        # Get response from the model
        with st.chat_message('assistant'):
            response = st.write_stream(ollama_generator(st.session_state.selected_model, st.session_state.chat_messages))

        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
