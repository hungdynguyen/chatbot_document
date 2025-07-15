import os
import glob
from typing import List
from uuid import uuid4
from tqdm import tqdm

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from config import (
    UPLOAD_DIRECTORY,
    QDRANT_HOST,
    QDRANT_PORT,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DEVICE,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

# Import DocumentParser mới
from .document_parser import DocumentParser

# Initialize components
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedding_model = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={'device': EMBEDDING_DEVICE}
)
document_parser = DocumentParser()

async def embed_files_to_qdrant(file_ids: List[str]) -> str:
    """
    Embed multiple files (PDF, Excel, Word, PowerPoint, Text) into Qdrant
    """
    collection_name = f"session-{uuid4()}"
    print(f"🚀 New collection: {collection_name}")
    
    # A. Create collection
    try:
        dim = len(embedding_model.embed_query("test"))
    except Exception:
        dim = 384  # Default for multilingual-MiniLM
        
    qdrant_client.recreate_collection(
        collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    # B. Find uploaded files
    uploaded_files = glob.glob(os.path.join(UPLOAD_DIRECTORY, "*"))
    target_files = [
        f for fid in file_ids
        for f in uploaded_files
        if os.path.basename(f).startswith(fid)
    ]
    
    if not target_files:
        print("⚠️ Không tìm thấy file hợp lệ.")
        return collection_name

    # C. Parse documents using DocumentParser
    docs_raw = []
    for fp in tqdm(target_files, desc="Đọc file"):
        try:
            print(f"📄 Parsing: {fp}")
            # Use DocumentParser instead of UnstructuredFileLoader
            parsed_docs = document_parser.parse_file(fp)
            docs_raw.extend(parsed_docs)
            print(f"✅ Parsed {len(parsed_docs)} documents from {fp}")
        except Exception as e:
            print(f"Lỗi {fp}: {e}")

    # D. Split documents into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    docs = splitter.split_documents(docs_raw)
    
    if not docs:
        print("⚠️ Không có chunk.")
        return collection_name

    print(f"📄 Tổng cộng: {len(docs)} chunks từ {len(target_files)} files")

    # E. Embed and store in Qdrant
    print("⏳ Embedding & ghi Qdrant …")
    qstore = Qdrant(
        client=qdrant_client,
        collection_name=collection_name,
        embeddings=embedding_model,
    )
    qstore.add_documents(docs, batch_size=32)  # Giảm batch size để ổn định hơn
    
    print(f"✅ Hoàn tất collection {collection_name} với {len(docs)} documents")
    return collection_name