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
LANGFLOW_EXTRACTOR_URL = "http://127.0.0.1:7860/api/v1/run/fb81426e-2615-4cff-9f00-90ea297cbd03"
 
# Langflow cho chat RAG
LANGFLOW_RAG_URL = "http://127.0.0.1:7860/api/v1/run/dd931858-3057-47d8-a28d-12c962bd0539"

HEADERS = {"Content-Type": "application/json; charset=utf-8"}

# Component IDs trong các Langflow flows
QDRANT_COMPONENT_ID_EXTRACTOR = "QdrantVectorStoreComponent-DZYG7"
QDRANT_COMPONENT_ID_RAG = "QdrantVectorStoreComponent-C1U3r"