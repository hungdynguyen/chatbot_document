# backend/utils/embedding_handler.py
import os, glob, shutil
from typing import List, Tuple
import numpy as np
from pathlib import Path
import uuid
from uuid import uuid4
from langchain_unstructured import UnstructuredLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
import json
import time

from config import (
    UPLOAD_DIRECTORY,
    QDRANT_HOST, QDRANT_PORT,
    EMBEDDING_MODEL_NAME,    
    EMBEDDING_DEVICE,         
    CHUNK_SIZE, CHUNK_OVERLAP
)
# from .document_parser import DocumentParser
from .document_parser2_llm_markdown import DocumentParser
# 0️⃣  Khởi tạo model 1 lần
print("🧠 Đang tải / khởi tạo embedding model …")
try:
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs=
        {"device": EMBEDDING_DEVICE,
            "trust_remote_code": True  
         },
    )
    print("✅ Embedding model sẵn sàng.")
except Exception as e:
    print(f"❌ Không khởi tạo được model: {e}")
    embedding_model = None

# Khởi tạo DocumentParser
document_parser = DocumentParser()

# 1️⃣  Qdrant client
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def cleanup_corrupted_collections():
    """Clean up any corrupted collections"""
    try:
        print("🧹 Cleaning up corrupted collections...")
        
        # Get list of collections
        collections = qdrant_client.get_collections()
        
        for collection in collections.collections:
            try:
                # Try to get collection info to test if it's corrupted
                info = qdrant_client.get_collection(collection.name)
                print(f"✅ Collection {collection.name} is healthy")
            except Exception as e:
                print(f"❌ Collection {collection.name} is corrupted: {e}")
                try:
                    qdrant_client.delete_collection(collection.name)
                    print(f"🗑️ Deleted corrupted collection: {collection.name}")
                except Exception as delete_error:
                    print(f"⚠️ Could not delete {collection.name}: {delete_error}")
                    
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")
        
        
        
def setup_small_to_big_data(markdown_content: str) -> Tuple[List[Document], List[Document], np.ndarray]:
    """
    Chuẩn bị dữ liệu cho chiến lược Small-to-Big.
    Returns: (parent_chunks, child_chunks, child_embeddings)
    """
    print("--- 셋업 Bước 1: Chuẩn bị dữ liệu Small-to-Big ---")
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

    parent_chunks = parent_splitter.create_documents([markdown_content])
    print(f"✅ Đã tạo {len(parent_chunks)} parent chunks (đoạn văn lớn).")

    all_child_chunks = []
    for parent_id, p_chunk in enumerate(parent_chunks):
        child_texts = child_splitter.split_text(p_chunk.page_content)
        for child_text in child_texts:
            child_doc = Document(page_content=child_text, metadata={"parent_id": parent_id})
            all_child_chunks.append(child_doc)
            
    print(f"✅ Đã tạo {len(all_child_chunks)} child chunks (câu nhỏ) từ các parent.")

    print("🧠 Đang embedding các child chunks...")
    child_contents = [c.page_content for c in all_child_chunks]
    child_embeddings = np.array(embedding_model.embed_documents(child_contents))
    print("✅ Embedding child chunks hoàn tất!")

    return parent_chunks, all_child_chunks, child_embeddings

async def embed_files_to_qdrant(file_ids: List[str]) -> str:
    """
    Thực hiện toàn bộ workflow INGESTION với logic lưu trữ thủ công và đáng tin cậy.
    """
    if embedding_model is None:
        raise RuntimeError("Embedding model chưa sẵn sàng")

    collection_name = f"session-s2b-{uuid.uuid4()}"
    print(f"🚀 Creating new ADVANCED RAG collection: {collection_name}")
    try:
        dim = len(embedding_model.embed_query("test"))
        qdrant_client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print(f"✅ Created collection '{collection_name}' with dimension {dim}")
    except Exception as e:
        raise RuntimeError(f"Collection creation failed: {e}")

    target_files = [os.path.join(UPLOAD_DIRECTORY, fid) for fid in file_ids]
    existing_files = [f for f in target_files if os.path.exists(f)]

    if not existing_files:
        print(f"⚠️ Không tìm thấy file hợp lệ nào trong thư mục {UPLOAD_DIRECTORY}.")
        return collection_name

    print(f"🔍 Tìm thấy {len(existing_files)} file hợp lệ để xử lý.")

    all_markdown_strings = []
    print(f"\n--- ⚙️ Bước 1: Parsing {len(existing_files)} file để lấy nội dung Markdown ---")
    for file_path_str in tqdm(existing_files, desc="Parsing files"):
        markdown_content = document_parser.parse_file(file_path_str)
        if markdown_content:
            all_markdown_strings.append(markdown_content)

    if not all_markdown_strings:
        print("⚠️ Không parse được nội dung từ bất kỳ file nào.")
        return collection_name

    combined_markdown = "\n\n---\n\n".join(all_markdown_strings)
    print(f"✅ Đã gộp nội dung từ {len(all_markdown_strings)} file...")

    print("\n--- ⚙️ Bước 2: Áp dụng Small-to-Big Chunking ---")
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    
    parent_chunks = parent_splitter.create_documents([combined_markdown])
    child_documents_to_embed = []
    for p_chunk in parent_chunks:
        child_texts = child_splitter.split_text(p_chunk.page_content)
        for child_text in child_texts:
            child_doc = Document(
                page_content=child_text,
                metadata={"parent_content": p_chunk.page_content}
            )
            child_documents_to_embed.append(child_doc)
            
    print(f"  ✅ Đã tạo {len(parent_chunks)} parent chunks và {len(child_documents_to_embed)} child chunks.")

    if not child_documents_to_embed:
        print("⚠️ Không có chunk nào được tạo ra để embedding.")
        return collection_name

    # --- SỬA LỖI NONE VECTORS Ở ĐÂY ---
    print(f"\n--- 🧠 Bước 3: Bắt đầu embedding và lưu {len(child_documents_to_embed)} child chunks ---")
    try:
        # 1. Tự embedding
        child_contents = [doc.page_content for doc in child_documents_to_embed]
        child_embeddings = np.array(embedding_model.embed_documents(child_contents))
        
        # 2. Tạo các PointStruct
        points = []
        for i, (doc, embedding) in enumerate(zip(child_documents_to_embed, child_embeddings)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload=doc.metadata  # Metadata chứa parent_content
            ))
            
        # 3. Tự upsert vào Qdrant
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True # Đợi cho đến khi việc upsert hoàn tất
        )

        print(f"✅ Upsert hoàn tất cho collection '{collection_name}'")
        
        final_info = qdrant_client.get_collection(collection_name)
        # Bây giờ sẽ hiển thị đúng số vector
        print(f"📊 Final collection status: {final_info.vectors_count} vectors")
        
    except Exception as e:
        print(f"❌ Lỗi khi embedding hoặc upsert vào Qdrant: {e}")
        try:
            qdrant_client.delete_collection(collection_name=collection_name)
            print(f"🗑️ Đã dọn dẹp collection bị lỗi: {collection_name}")
        except Exception as cleanup_error:
            print(f"⚠️ Không thể dọn dẹp collection: {cleanup_error}")
        raise
    
    return collection_name