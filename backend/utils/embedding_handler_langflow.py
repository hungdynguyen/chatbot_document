# backend/utils/embedding_handler.py
import os, glob
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

from config import (
    UPLOAD_DIRECTORY,
    QDRANT_HOST, QDRANT_PORT,
    EMBEDDING_MODEL_NAME,     # = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DEVICE,         # = "cpu" | "cuda"
    CHUNK_SIZE, CHUNK_OVERLAP
)

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

# 1️⃣  Qdrant client
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


async def embed_files_to_qdrant(file_ids: List[str]) -> str:
    """
    Đọc file, chunk, embed, đẩy vào collection mới. Trả về tên collection.
    """
    if embedding_model is None:
        raise RuntimeError("Embedding model chưa sẵn sàng")

    # A. tạo collection mới
    collection_name = f"session-{uuid4()}"
    print(f"🚀 New collection: {collection_name}")

    # dimension
    try:
        dim = embedding_model.client.get_sentence_embedding_dimension()
    except Exception:
        dim = len(embedding_model.embed_query("test"))
    qdrant_client.recreate_collection(
        collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

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

    # C. load & chunk
    docs_raw = []
    for fp in tqdm(target_files, desc="Đọc file"):
        try:
            docs_raw.extend(UnstructuredLoader(fp).load())
        except Exception as e:
            print(f"Lỗi {fp}: {e}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    full_text = "\n\n".join(doc.page_content for doc in docs_raw)
    single_doc = Document(page_content=full_text, metadata={})
    docs = splitter.split_documents([single_doc])
    # docs = splitter.split_documents(docs_raw)
    if not docs:
        print("⚠️ Không có chunk.")
        return collection_name

    # D. ghi vào Qdrant
    print("⏳ Embedding & ghi Qdrant …")
    qstore = Qdrant(
        client=qdrant_client,
        collection_name=collection_name,
        embeddings=embedding_model,
    )
    qstore.add_documents(docs)
    print(f"✅ Hoàn tất collection {collection_name}")
    return collection_name