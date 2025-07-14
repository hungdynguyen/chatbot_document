# import os
# import glob
# from typing import List
# from uuid import uuid4

# from huggingface_hub import hf_hub_download
# from langchain_community.document_loaders import UnstructuredFileLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Qdrant
# from qdrant_client import QdrantClient
# from qdrant_client.http.models import Distance, VectorParams
# from tqdm import tqdm

# from config import (
#     UPLOAD_DIRECTORY,
#     QDRANT_HOST,
#     QDRANT_PORT,
#     EMBEDDING_MODEL_NAME,
#     EMBEDDING_DEVICE,
#     CHUNK_SIZE,
#     CHUNK_OVERLAP
# )

# # —— Chuẩn bị cache_dir và chỉ download những file cần —— #
# cache_dir = os.path.join(UPLOAD_DIRECTORY, ".cache", EMBEDDING_MODEL_NAME.replace("/", "_"))
# os.makedirs(cache_dir, exist_ok=True)

# print("🧠 Đang cache model safetensors + config/tokenizer…")
# # Trọng số
# hf_hub_download(
#     repo_id=EMBEDDING_MODEL_NAME,
#     filename="model.safetensors",
#     cache_dir=cache_dir,
# )
# # Config
# hf_hub_download(
#     repo_id=EMBEDDING_MODEL_NAME,
#     filename="config.json",
#     cache_dir=cache_dir,
# )
# # Tokenizer (tuỳ model có thể là tokenizer.json, vocab.txt, merges.txt…)
# hf_hub_download(
#     repo_id=EMBEDDING_MODEL_NAME,
#     filename="tokenizer.json",
#     cache_dir=cache_dir,
# )

# # —— Khởi tạo embedding model từ cache —— #
# print("🧠 Đang khởi tạo embedding model từ cache…")
# try:
#     embedding_model = HuggingFaceEmbeddings(
#         model_name=cache_dir,
#         model_kwargs={"device": EMBEDDING_DEVICE}
#     )
#     print("✅ Embedding model đã sẵn sàng.")
# except Exception as e:
#     print(f"❌ Lỗi khởi tạo embedding model: {e}")
#     embedding_model = None

# # Khởi Qdrant client như cũ
# qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# async def embed_files_to_qdrant(file_ids: List[str]) -> str:
#     """
#     Đọc các file từ UPLOAD_DIRECTORY, chia nhỏ, embedding và đẩy vào một collection Qdrant MỚI.
#     Trả về tên của collection mới được tạo.
#     """
#     if not embedding_model:
#         raise ValueError("Embedding model chưa được khởi tạo thành công.")

#     # --- 1. Tạo một collection duy nhất cho phiên làm việc này ---
#     collection_name = f"session-{uuid4()}"
#     print(f"🚀 Tạo collection Qdrant mới cho phiên làm việc: {collection_name}")
    
#     # Lấy dimension của vector từ model
#     try:
#         # Thử với attribute client trước
#         if hasattr(embedding_model, 'client'):
#             embed_dim = embedding_model.client.get_sentence_embedding_dimension()
#         else:
#             # Fallback: encode một câu sample để lấy dimension
#             sample_embedding = embedding_model.embed_query("test")
#             embed_dim = len(sample_embedding)
#     except Exception as e:
#         print(f"⚠️ Không thể lấy dimension tự động, sử dụng 384 (default): {e}")
#         embed_dim = 384

#     qdrant_client.recreate_collection(
#         collection_name=collection_name,
#         vectors_config=VectorParams(size=embed_dim, distance=Distance.COSINE)
#     )

#     # --- 2. Tìm và tải các file được yêu cầu ---
#     all_documents = []
#     print(f"🔍 Đang tìm và tải {len(file_ids)} file...")
    
#     # Tìm tất cả các file trong thư mục upload
#     # Cách này đơn giản nhưng không hiệu quả nếu có hàng nghìn file
#     # Một cách tốt hơn là lưu ánh xạ file_id -> file_path vào DB
#     all_uploaded_files = glob.glob(os.path.join(UPLOAD_DIRECTORY, "*"))
    
#     target_files = []
#     for file_id in file_ids:
#         # Tìm file có tên bắt đầu bằng file_id
#         found = next((f for f in all_uploaded_files if os.path.basename(f).startswith(file_id)), None)
#         if found:
#             target_files.append(found)
#         else:
#             print(f"⚠️ Cảnh báo: Không tìm thấy file cho ID: {file_id}")
    
#     if not target_files:
#         print("❌ Không có file nào hợp lệ để embedding.")
#         return collection_name # Trả về tên collection rỗng

#     for file_path in tqdm(target_files, desc="Đang tải nội dung file"):
#         try:
#             # UnstructuredFileLoader có thể đọc nhiều loại file (pdf, docx, txt...)
#             loader = UnstructuredFileLoader(file_path)
#             all_documents.extend(loader.load())
#         except Exception as e:
#             print(f"Lỗi khi tải file {file_path}: {e}")

#     # --- 3. Chia nhỏ văn bản ---
#     print(f"🔄 Đang chia nhỏ {len(all_documents)} document...")
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=CHUNK_SIZE,
#         chunk_overlap=CHUNK_OVERLAP,
#     )
#     docs_for_db = text_splitter.split_documents(all_documents)
#     print(f"✅ Đã chia thành {len(docs_for_db)} chunk.")

#     # --- 4. Thêm các chunk vào Qdrant ---
#     if not docs_for_db:
#         print("⚠️ Không có chunk nào được tạo ra để embedding.")
#         return collection_name

#     print("⏳ Đang thực hiện embedding và lưu vào Qdrant...")
#     qdrant_vector_store = Qdrant(
#         client=qdrant_client,
#         collection_name=collection_name,
#         embeddings=embedding_model
#     )
#     qdrant_vector_store.add_documents(documents=docs_for_db, batch_size=64)

#     print(f"✅ Đã embedding thành công vào collection '{collection_name}'.")
#     return collection_name

# backend/utils/embedding_handler.py
import os, glob
from typing import List
from uuid import uuid4

from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
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
            docs_raw.extend(UnstructuredFileLoader(fp).load())
        except Exception as e:
            print(f"Lỗi {fp}: {e}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    docs = splitter.split_documents(docs_raw)
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
    qstore.add_documents(docs, batch_size=64)
    print(f"✅ Hoàn tất collection {collection_name}")
    return collection_name
