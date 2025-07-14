# backend/config.py

import os

# --- CẤU HÌNH UPLOAD ---
UPLOAD_DIRECTORY = "./uploaded_files"

origins = [
    "http://localhost:3000",
    "http://localhost:3002",
    # Thêm các domain khác nếu có (ví dụ: domain của staging, production)
]

# --- CẤU HÌNH QDRANT & EMBEDDING ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
# Tên collection sẽ được tạo động cho mỗi session để tránh lẫn lộn dữ liệu

# Cấu hình model embedding
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DEVICE = "cpu" # Đổi thành "cuda" nếu có GPU

# Cấu hình chia nhỏ văn bản
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

# --- CẤU HÌNH LANGFLOW ---
# Langflow cho trích xuất thông tin
LANGFLOW_EXTRACTOR_URL = "http://localhost:7860/api/v1/run/70017ce4-caba-479c-a03c-067faebf3c6c"
 
# Langflow cho chat RAG
LANGFLOW_RAG_URL = "http://localhost:7860/api/v1/run/129d05dd-3f4d-4a81-b1f2-85e436e4d0a8"

HEADERS = {"Content-Type": "application/json; charset=utf-8"}

# Component IDs trong các Langflow flows
QDRANT_COMPONENT_ID_EXTRACTOR = "QdrantVectorStoreComponent-IEpPF"
QDRANT_COMPONENT_ID_RAG = "QdrantVectorStoreComponent-VEffS"