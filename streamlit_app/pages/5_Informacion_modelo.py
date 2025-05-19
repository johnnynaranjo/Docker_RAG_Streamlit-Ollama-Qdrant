import streamlit as st
import ollama
import requests

def ollama_model_info(url, model_name):
    try:
        res = requests.post(f"{url}/api/show", json={"name": model_name})
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"No se pudo obtener la información: {e}"}

# ----------------------------- MAIN -----------------------------

def main():
   
    st.set_page_config(
        page_title="Información del Modelo de Ollama",
        page_icon="ℹ️",
    )

    st.title("ℹ️ Información del Modelo de Ollama")

    st.selectbox("Please select the model:", [model["model"] for model in ollama.list()["models"]], key = "selected_model")
    if st.button("Obtener información"):
        info = ollama_model_info("http://localhost:11434", st.session_state.selected_model)
        st.json(info)

if __name__ == "__main__":
    main()
