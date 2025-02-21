from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import faiss
import numpy as np
import requests
import uvicorn
import json
import os
import ollama

# Constantes y configuración
JSON_FILE = "data/missions.json"
EMBEDDING_DIM = 768  # salida de all-minilm:33m

# Configuración de CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# MODELOS DE DATOS
# -------------------------------


class MissionInput(BaseModel):
    title: str
    description: str


class GenerationInput(BaseModel):
    query: str


class QueryModel(BaseModel):
    text: str

# -------------------------------
# FUNCIONES AUXILIARES
# -------------------------------


def get_embedding(text: str) -> np.ndarray:
    """
    Llama al modelo de embeddings (nomic-embed-text) para obtener el embedding del texto.
    Se asume que el modelo 'all-minilm:33m' está configurado internamente en Ollama.
    """
    try:
        response = ollama.embeddings(model='nomic-embed-text', prompt=text)
        embedding = response['embedding']
        print(f"Embedding generado para '{text}': {embedding[:5]}...")
        return np.array(embedding, dtype='float32')
    except Exception as e:
        print(f"Error generando embedding: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generando embeddings: {str(e)}")


def load_missions() -> list:
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


def save_missions(missions: list):
    with open(JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(missions, file, indent=4, ensure_ascii=False)


# -------------------------------
# INICIALIZACIÓN DE DATOS Y FAISS
# -------------------------------
missions = load_missions()
mission_map = {}  # Mapea el índice interno a la misión
index = faiss.IndexFlatIP(EMBEDDING_DIM)


def initialize_index():
    global mission_map
    for i, mission in enumerate(missions):
        text = f"{mission['title']}: {mission['description']}"
        embedding = get_embedding(text).reshape(1, -1)
        faiss.normalize_L2(embedding)  # Normalizar para coseno de similityd
        index.add(embedding)
        mission_map[i] = mission


initialize_index()

# -------------------------------
# ENDPOINTS DE LA API
# -------------------------------


@app.post("/add_mission/", response_class=JSONResponse)
def add_mission(mission: MissionInput):
    # Verifica que no exista una misión con el mismo título
    for existing in missions:
        if existing["title"].lower() == mission.title.lower():
            raise HTTPException(status_code=400, detail="La misión ya existe.")

    mission_id = len(missions)
    mission_data = mission.model_dump()
    missions.append(mission_data)
    save_missions(missions)

    text = f"{mission.title}: {mission.description}"
    embedding = get_embedding(text).reshape(1, -1)
    faiss.normalize_L2(embedding)
    index.add(embedding)
    mission_map[mission_id] = mission_data

    return {"message": "Misión añadida correctamente", "mission_id": mission_id}


@app.get("/search_mission/", response_class=JSONResponse)
def search_mission(query: str = Query(..., description="Texto de la misión a buscar"), top_k: int = 3):
    if not missions:
        raise HTTPException(
            status_code=404, detail="No hay misiones disponibles.")

    query_embedding = get_embedding(query).reshape(1, -1)
    faiss.normalize_L2(query_embedding)
    _, indices = index.search(query_embedding, top_k)

    results = [mission_map[i] for i in indices[0] if i in mission_map]
    return {"results": results}


@app.post("/generate_mission/", response_class=JSONResponse)
def generate_mission(input_data: GenerationInput):
    """
    Genera una misión nueva usando un LLM local.
    Se realiza una búsqueda de misiones similares para obtener contexto.
    """
    query = input_data.query
    query_embedding = get_embedding(query).reshape(1, -1)
    faiss.normalize_L2(query_embedding)
    _, indices = index.search(query_embedding, 3)


    similar_missions = [missions[i] for i in indices[0] if i < len(missions)]
    context = "\n".join(
        [f"{m['title']}: {m['description']}" for m in similar_missions])

    prompt = f"""Basado en las siguientes misiones:
{context}

Genera una nueva misión relacionada con: {query}.
Proporciona un título corto y una descripción detallada.
    """

    try:
        # Llamada al LLM local {Mistral} (ajustar la URL y params según implementación)
        response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": "llama3.2",  # Modelo LLM a usar
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        response.raise_for_status()
        llm_result = response.json()
        new_text = llm_result["choices"][0]["message"]["content"]

        new_mission_data = {
            "title": query.capitalize() + " Quest",
            "description": new_text.strip()
        }
        missions.append(new_mission_data)
        save_missions(missions)

        # Agregar el embedding de la nueva misión al índice
        text_new = f"{new_mission_data['title']}: {new_mission_data['description']}"
        new_embedding = get_embedding(text_new).reshape(1, -1)
        faiss.normalize_L2(new_embedding)
        index.add(new_embedding)
        mission_map[len(missions) - 1] = new_mission_data

        # Retornamos misión generada para mostrarla en frontend
        return {"message": "Misión generada correctamente", "mission": new_mission_data}

    except requests.exceptions.RequestException as e:
        print(f"Error al llamar a Ollama: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error al generar la misión: {e}")


@app.get("/missions/", response_class=JSONResponse)
def get_all_missions():
    return {"missions": missions}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # Sirve el frontend
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
