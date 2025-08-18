# backend/config.py

import os

# --- CẤU HÌNH UPLOAD ---
UPLOAD_DIRECTORY = "./uploaded_files"

origins = [
    "http://localhost:3000",
    "http://localhost:3002",
]
TOGETHER_API_KEY = "ee493f081e8bad724f15cbcc32d72ed090beadc0af0a0532e44715a5e5a1cee0"
DEEPSEEK_API_KEY = "sk-434edbafbf604a96849043af835fd563"
GOOGLE_API_KEY = "AIzaSyAJjgoDedtc3AXGrrlb7vPYCauivCY9OMw"
# --- CẤU HÌNH QDRANT & EMBEDDING ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

#Cau hinh Re-ranker model
RERANKER_MODEL_NAME = 'BAAI/bge-reranker-large'
RERANKER_DEVICE = "cuda"  

# Cấu hình model embedding
EMBEDDING_MODEL_NAME = "jinaai/jina-embeddings-v3"
EMBEDDING_DEVICE = "cuda" # Đổi thành "cuda" nếu có GPU

# Cấu hình chia nhỏ văn bản
CHUNK_SIZE = 800
CHUNK_OVERLAP = 50

# --- CẤU HÌNH LANGFLOW ---

# LANGFLOW_SKIP_AUTH_AUTO_LOGIN = True
# LANGFLOW_AUTH_TOKEN = None
# # Langflow cho trích xuất thông tin
# LANGFLOW_EXTRACTOR_URL = "http://localhost:7860/api/v1/run/a70ae3df-293c-42c7-8340-aae3a15b728f"


# # Langflow cho chat RAG
# LANGFLOW_RAG_URL = "http://localhost:7860/api/v1/run/d94a1ffb-9276-4a2f-9103-ff0e88a28258"

# HEADERS = {"Content-Type": "application/json; charset=utf-8"}

# # Component IDs trong các Langflow flows
# QDRANT_COMPONENT_ID_EXTRACTOR = "QdrantVectorStoreComponent-pUzsq"
# QDRANT_COMPONENT_ID_RAG = "QdrantVectorStoreComponent-BDczH"
