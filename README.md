# Causal Video Games Missions Use Case LLM 

This repository contains a web solution for a video games use case powered by LLMs. It is designed for the casual/hybrid-casual video games domain, providing both a RESTful API and a web-based frontend. This solution allows game designers and developers to add, search, and generate game missions using NLP techniques. It uses embeddings from the *all-minilm:33m* model via Ollama and performs similarity search with FAISS. This project delivers a scalable and dynamic content management system tailored to modern video game development.

## Overview

- **Web API with FastAPI:** Exposes endpoints to add missions, search similar missions using vector embeddings, and generate new missions via a local LLM.

- **Embeddings & Similarity Search:**  
  - Generates 768-dimensional embeddings for mission texts using the *all-minilm:33m* model (via Ollama).  
  - Uses FAISS to perform efficient similarity search. Embeddings are L2-normalized, and an inner-product index (`IndexFlatIP`) is used to approximate cosine similarity.  
  - Cosine similarity is used as the metric, meaning higher inner product values indicate greater semantic similarity.

- **Local LLM Integration:**  
  Generates new missions using a local LLM (configured as "llama3.2", replaceable by Mistral) by providing contextual information from similar missions.

- **Web Solution:**  
  Includes a user-friendly web interface (HTML, CSS, JavaScript) that interacts with the API, allowing users to add, search, and generate missions directly from the browser.

- **Data Persistence:**  
  Missions are stored in a JSON file for simple persistence and easy modification.

## Technologies and Libraries

- **[FastAPI](https://fastapi.tiangolo.com/):** A modern, fast web framework for building APIs with Python 3.9+.
- **[FAISS](https://github.com/facebookresearch/faiss):** A library for efficient similarity search and clustering of dense vectors.
- **[Ollama](https://ollama.com/):** Used for interfacing with local LLMs and generating embeddings.
- **Python & Pydantic:** For data modeling and type validation.
- **HTML, CSS, JavaScript:** For the frontend web interface.

## Installation

1. **Clone the Repository:**
  ```bash
     git clone https://github.com/sgalle16/causal-video-games-use-case-llm.git
     cd causal-video-games-use-case-llm
  ```
2. **Set Up a Virtual Environment (Optional but Recommended):**
  ```bash
    python -m venv venv
    source venv/bin/activate  # For Linux/Mac
    venv\Scripts\activate     # For Windows
  ```

3. **Install dependencies:**
  ```bash
    pip install -r requirements.txt
  ```

### Running the Application

1. **Start the Ollama Service:**
Make sure your local LLM (e.g., llama3.2) and the embedding service are running on the configured ports.
  ```bash
  ollama serve 
  ollama pull nomic-embed-text
  ollama pull llama3.2
  ```
2. **Run the FastAPI server:**
  ```bash
  uvicorn main:app --reload
  ```
3. **Access the Frontend:**
  Open your browser and navigate to http://localhost:8000 or You can directly open the `index.html` file in your browser.

## API Endpoints

- `POST /generate_mission/`
Generates a new mission using the local LLM. This endpoint uses context from similar missions to guide the LLM in creating a new, context-aware mission.

- `POST /add_mission/`
Adds a new mission manually by providing a title and description.

- `GET /search_mission/?query=...`
Searches for missions similar to the query text using cosine similarity (inner-product on normalized embeddings).

- `GET /missions/`
Retrieves all missions stored in the JSON file.

### Similarity Metric
The system uses *cosine similarity* to measure semantic similarity between mission embeddings. This is achieved by:

- Normalizing embeddings using L2 normalization.
- Using FAISS’s IndexFlatIP (inner-product index): With normalized vectors, this index is equivalent to computing cosine similarity.
- Interpretation: Higher inner product values (or lower L2 distances on normalized vectors) indicate a higher degree of semantic similarity between missions.
