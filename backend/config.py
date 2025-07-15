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
EMBEDDING_DEVICE = "cuda" # Đổi thành "cuda" nếu có GPU

# Cấu hình chia nhỏ văn bản
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

# --- CẤU HÌNH LANGFLOW ---
# Langflow cho trích xuất thông tin
LANGFLOW_EXTRACTOR_URL = "http://127.0.0.1:7860/api/v1/run/133dbbaf-9091-480d-a055-4eb60e6e1275"
 
# Langflow cho chat RAG
LANGFLOW_RAG_URL = "http://127.0.0.1:7860/api/v1/run/9b1177c7-250f-44ef-84aa-32d09cb7fc93"

HEADERS = {"Content-Type": "application/json; charset=utf-8"}

# Component IDs trong các Langflow flows
QDRANT_COMPONENT_ID_EXTRACTOR = "QdrantVectorStoreComponent-IEpPF"
QDRANT_COMPONENT_ID_RAG = "QdrantVectorStoreComponent-VEffS"