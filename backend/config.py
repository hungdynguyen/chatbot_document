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
CHUNK_SIZE = 800
CHUNK_OVERLAP = 50

# --- CẤU HÌNH LANGFLOW ---

LANGFLOW_SKIP_AUTH_AUTO_LOGIN = True
LANGFLOW_AUTH_TOKEN = None
# Langflow cho trích xuất thông tin
LANGFLOW_EXTRACTOR_URL = "http://localhost:7860/api/v1/run/a70ae3df-293c-42c7-8340-aae3a15b728f"


# Langflow cho chat RAG
LANGFLOW_RAG_URL = "http://localhost:7860/api/v1/run/d94a1ffb-9276-4a2f-9103-ff0e88a28258"

HEADERS = {"Content-Type": "application/json; charset=utf-8"}

# Component IDs trong các Langflow flows
QDRANT_COMPONENT_ID_EXTRACTOR = "QdrantVectorStoreComponent-pUzsq"
QDRANT_COMPONENT_ID_RAG = "QdrantVectorStoreComponent-BDczH"
