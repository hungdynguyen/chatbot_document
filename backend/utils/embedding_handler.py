# backend/utils/embedding_handler.py
import os, glob, shutil
from typing import List
from uuid import uuid4

from langchain_unstructured import UnstructuredLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from tqdm import tqdm
import json
import time

from config import (
    UPLOAD_DIRECTORY,
    QDRANT_HOST, QDRANT_PORT,
    EMBEDDING_MODEL_NAME,     # = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DEVICE,         # = "cpu" | "cuda"
    CHUNK_SIZE, CHUNK_OVERLAP
)
from .document_parser import DocumentParser

# 0️⃣  Khởi tạo model 1 lần
print("🧠 Đang tải / khởi tạo embedding model …")
try:
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": EMBEDDING_DEVICE},
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

async def embed_files_to_qdrant(file_ids: List[str]) -> str:
    """
    Đọc file, chunk, embed, đẩy vào collection mới. Trả về tên collection.
    """
    
    cleanup_corrupted_collections()
    
    if os.path.exists("parsed_output"):
        shutil.rmtree("parsed_output")
        print("🧹 Đã xóa thư mục parsed_output cũ")
        
    os.makedirs("parsed_output", exist_ok=True)
    print("📁 Tạo thư mục parsed_output mới")
    
    if embedding_model is None:
        raise RuntimeError("Embedding model chưa sẵn sàng")

    # A. tạo collection mới
    collection_name = f"session-{uuid4()}"
    print(f"🚀 New collection: {collection_name}")
    
    
    
    # Get embedding dimension with proper error handling
    try:
        test_embedding = embedding_model.embed_query("test")
        dim = len(test_embedding)
        print(f"🔢 Embedding dimension: {dim}")
    except Exception as e:
        print(f"❌ Could not determine embedding dimension: {e}")
        raise RuntimeError(f"Embedding model error: {e}")

    # # dimension
    # try:
    #     dim = embedding_model.client.get_sentence_embedding_dimension()
    # except Exception:
    #     dim = len(embedding_model.embed_query("test"))
        
        
    # qdrant_client.recreate_collection(
    #     collection_name,
    #     vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    # )
    
    
    # Create collection with validation
    try:
        # Delete if exists (safety measure)
        try:
            qdrant_client.delete_collection(collection_name)
        except:
            pass
            
        # Create new collection
        qdrant_client.create_collection(
            collection_name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print(f"✅ Created collection {collection_name} with dimension {dim}")
        
        # Validate collection was created properly
        collection_info = qdrant_client.get_collection(collection_name)
        print(f"✅ Collection validation passed: {collection_info.status}")
        
    except Exception as e:
        print(f"❌ Failed to create collection: {e}")
        raise RuntimeError(f"Collection creation failed: {e}")

    # B. gom file theo file_ids
    uploaded_files = glob.glob(os.path.join(UPLOAD_DIRECTORY, "*"))
    target_files = [
        f for fid in file_ids
        for f in uploaded_files
        if os.path.basename(f).startswith(fid)
    ]
    if not target_files:
        print("⚠️ Không tìm thấy file hợp lệ.")
        return collection_name

    # C. Sử dụng DocumentParser
    docs = []
    for fp in tqdm(target_files, desc="Đọc file với DocumentParser"):
        try:
            extension = fp.split('.')[-1] if '.' in os.path.basename(fp) else 'unknown'
            output_dir = f"parsed_output/{extension}"
            os.makedirs(output_dir, exist_ok=True)
            # Parse file với DocumentParser
            parsed_docs = document_parser.parse_file(fp)
            print(f"📄 Parsed {len(parsed_docs)} documents from {fp}")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f"{output_dir}/{os.path.basename(fp)}_{timestamp}.json"
            # Ghi parsed documents vào file JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([{'page_content': doc.page_content, 'metadata': doc.metadata} for doc in parsed_docs], f, indent=4, ensure_ascii=False)
            print(f"✅ Ghi parsed documents vào {os.path.basename(fp)}_{timestamp}.json")
            docs.extend(parsed_docs)
        except Exception as e:
            print(f"Lỗi parse {fp}: {e}")
    if not docs:
        print("⚠️ Không có document nào được parse.")
        return collection_name

    # # D. ghi vào Qdrant
    # print(f"⏳ Embedding {len(docs)} documents & ghi Qdrant …")
    # qstore = Qdrant(
    #     client=qdrant_client,
    #     collection_name=collection_name,
    #     embeddings=embedding_model,
    # )
    # qstore.add_documents(docs)
    # print(f"✅ Hoàn tất collection {collection_name} với {len(docs)} documents")
    # return collection_name
    
    # D. ghi vào Qdrant với error handling
    print(f"⏳ Embedding {len(docs)} documents & ghi Qdrant …")
    try:
        # Batch processing để tránh memory issues
        batch_size = 50
        total_batches = (len(docs) + batch_size - 1) // batch_size
        
        qstore = Qdrant(
            client=qdrant_client,
            collection_name=collection_name,
            embeddings=embedding_model,
        )
        
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} docs)")
            
            try:
                qstore.add_documents(batch)
                print(f"✅ Batch {batch_num} completed successfully")
            except Exception as batch_error:
                print(f"❌ Batch {batch_num} failed: {batch_error}")
                # Continue with next batch rather than failing completely
                continue
        
        # Validate final collection
        final_info = qdrant_client.get_collection(collection_name)
        print(f"✅ Final collection status: {final_info.vectors_count} vectors")
        
    except Exception as e:
        print(f"❌ Lỗi khi thêm documents vào Qdrant: {e}")
        # Cleanup collection nếu có lỗi
        try:
            qdrant_client.delete_collection(collection_name=collection_name)
            print(f"🗑️ Cleaned up failed collection: {collection_name}")
        except Exception as cleanup_error:
            print(f"⚠️ Could not cleanup collection: {cleanup_error}")
        raise
    
    return collection_name
