import streamlit as st
import requests

# URL de la API pública de modelos de Ollama
API_URL = "https://ollamadb.dev/api/v1/models"

# ----------------------------- MAIN -----------------------------

def main():
       
    st.set_page_config(
        page_title="Modelos disponibles para descargar en Ollama",
        page_icon="📚",
    )

    st.title("📚 Modelos disponibles para descargar en Ollama")

    # Parámetros de búsqueda
    search_query = st.text_input("Buscar modelos por nombre o descripción:")

    # Número de resultados a mostrar
    limit = st.slider("Número de modelos a mostrar", min_value=1, max_value=50, value=10)

    # Botón para cargar los modelos
    if st.button("Cargar modelos"):
        params = {"search": search_query, "limit": limit}
        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            models = response.json().get("models", [])
            if models:
                for model in models:
                    st.subheader(model.get("model_name", "Nombre no disponible"))
                    st.markdown(f"**Descripción:** {model.get('description', 'Sin descripción')}")
                    
                    labels = model.get('labels', [])
                    if labels:
                        st.markdown(f"**Tamaño:** {labels[0]} parámetros")
                    else:
                        st.markdown("**Tamaño:** No especificado")

                    st.markdown(f"**Última actualización:** {model.get('last_updated_str', 'Desconocida')}")
                    st.markdown(f"[Ver en la biblioteca de Ollama]({model.get('url', '#')})")
                    st.markdown("---")
            else:
                st.info("No se encontraron modelos que coincidan con tu búsqueda.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error al conectar con la API de Ollama: {e}")

if __name__ == "__main__":
    main()