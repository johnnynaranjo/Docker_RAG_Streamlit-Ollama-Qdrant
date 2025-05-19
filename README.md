# 🧠 LLM Chat App con Streamlit + Ollama + Qdrant

Este repositorio contiene una aplicación web construida con **Streamlit** que funciona como una interfaz gráfica (GUI) para interactuar con un modelo de lenguaje (LLM). La aplicación corre dentro de un contenedor Docker, junto con otros dos servicios: **Ollama** (para servir el modelo) y **Qdrant** (para almacenamiento vectorial y funcionalidades RAG).

---

## 🚀 Características principales

- 🦜 **Chatea con Ollama** carga tu LLM preferido e interactua a través de una interfaz intuitiva en Streamlit.
- 🤖 **Chatea con RAG** cargando tus archivos en la base de datos vectorial.
- 📂 **Carga de archivos** para hacer preguntas tipo RAG (Retrieval-Augmented Generation).
- ℹ️ **Consulta de información del modelo** activo.
- 📚 **Descarga de modelos** desde la interfaz para utilizarlos localmente.

---

## 🐳 Arquitectura con Docker

Este proyecto utiliza Docker Compose para levantar tres contenedores:

1. **Streamlit App** - Interfaz gráfica del usuario.
2. **Ollama** - Servidor de modelos LLM.
3. **Qdrant** - Base de datos vectorial para funcionalidades RAG.

```bash
# Levantar el entorno completo
docker-compose up --build
```

---

## 📁 Carga de Archivos

Puedes subir archivos (PDF, TXT, etc.) a través de la interfaz para hacer preguntas basadas en su contenido. Los documentos se vectorizan y almacenan en Qdrant para permitir búsquedas semánticas.

---

## 🧠 Modelos

- Visualiza los modelos disponibles y el modelo actual en ejecución.
- Descarga modelos directamente desde la aplicación.

---

## 📦 Requisitos

- Docker
- Docker Compose

---

## 📄 Uso

```bash
git clone https://github.com/tuusuario/tu-repo.git
cd tu-repo
docker-compose up --build
```

Abre tu navegador en: [http://localhost:8501](http://localhost:8501)

---

## 🔧 Personalización

Puedes modificar el modelo por defecto, el almacenamiento en Qdrant, o la lógica de procesamiento editando los archivos de configuración en el proyecto.

---

## 📃 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más información.

---

## 🙌 Agradecimientos

- [Ollama](https://ollama.com/)
- [Qdrant](https://qdrant.tech/)
- [Streamlit](https://streamlit.io/)
