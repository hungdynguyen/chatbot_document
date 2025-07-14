import os
import uuid
from pathlib import Path
from typing import List, Dict

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- IMPORT CÁC UTILITY ---
# Giả sử bạn có file config.py để quản lý các hằng số
from config import UPLOAD_DIRECTORY, origins 
# Import các hàm xử lý logic
from utils.extractor import extract_information_from_docs
from utils.rag_client import query_rag_flow
from utils.embedding_handler import embed_files_to_qdrant, qdrant_client 

# -------------------------------------------------------------
# 1. KHỞI TẠO APP VÀ CẤU HÌNH
# -------------------------------------------------------------
app = FastAPI(title="Loan Assessment Backend")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# 2. ĐỊNH NGHĨA MODEL
# -------------------------------------------------------------
class ProcessRequest(BaseModel):
    prompt: str
    file_ids: List[str]

class RagRequest(BaseModel):
    question: str
    file_ids: List[str]
    chat_history: List[Dict[str, str]] = Field(default_factory=list)

# -------------------------------------------------------------
# 3. ENDPOINT UPLOAD 
# -------------------------------------------------------------
@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        new_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, new_filename)
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        print(f"✅ File '{file.filename}' đã được lưu thành công với tên '{new_filename}'")
        return {"file_id": file_id, "filename": new_filename}
    except Exception as e:
        print(f"❌ Lỗi khi upload file: {e}")
        raise HTTPException(status_code=500, detail="Không thể upload file")


# -------------------------------------------------------------
# 4. ENDPOINT XỬ LÝ TRÍCH XUẤT 
# -------------------------------------------------------------
@app.post("/process_prompt")
async def process_prompt(request: ProcessRequest):
    """
    Nhận prompt và file_ids, thực hiện embedding và trích xuất thông tin.
    """
    num_files = len(request.file_ids)
    if num_files == 0:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file.")

    print(f"🚀 Nhận được yêu cầu xử lý cho {num_files} file với prompt: '{request.prompt}'")
    print(f"   Các File ID: {request.file_ids}")

    collection_name = None
    try:
        # --- BƯỚC 1: EMBEDDING CÁC FILE VỪA UPLOAD ---
        # Hàm này sẽ tạo một collection mới và trả về tên của nó
        collection_name = await embed_files_to_qdrant(request.file_ids)
        print(f"Các file đã được embedding vào collection: {collection_name}")

        # --- BƯỚC 2: GỌI HÀM XỬ LÝ TRÍCH XUẤT VÀ TRUYỀN COLLECTION_NAME VÀO ---
        extracted_data = await extract_information_from_docs(
            prompt=request.prompt,
            file_ids=request.file_ids,
            collection_name=collection_name 
        )

        # Trả về kết quả
        return {
            "summary": "Quá trình trích xuất thông tin đã hoàn tất.",
            "extracted_data": extracted_data,
            "prompt": request.prompt,
            "file_ids": request.file_ids,
        }
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng trong quá trình xử lý: {e}")
        # Bắt lỗi và trả về lỗi 500 cho frontend
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý phía server: {e}")
    finally:
        # --- BƯỚC 3: DỌN DẸP (RẤT QUAN TRỌNG) ---
        # Dù thành công hay thất bại, cũng xóa collection đã tạo cho phiên này
        if collection_name:
            try:
                print(f"🧹 Dọn dẹp, xóa collection: {collection_name}")
                qdrant_client.delete_collection(collection_name=collection_name)
                print(f"✅ Collection '{collection_name}' đã được xóa.")
            except Exception as e:
                # Ghi lại lỗi dọn dẹp nhưng không raise exception để không ảnh hưởng đến client
                print(f"⚠️ Lỗi khi dọn dẹp collection '{collection_name}': {e}")


# -------------------------------------------------------------
# 5. ENDPOINT MỚI CHO CHỨC NĂNG CHAT RAG 
# -------------------------------------------------------------
@app.post("/chat_rag")
async def chat_rag(request: RagRequest):
    if not request.file_ids:
         raise HTTPException(status_code=400, detail="Vui lòng cung cấp file_ids để thực hiện RAG.")

    print(f"🗨️ Nhận được câu hỏi RAG: '{request.question}'")
    print(f"   Trên các File ID: {request.file_ids}")

    collection_name = None
    try:
        # BƯỚC 1: EMBEDDING
        collection_name = await embed_files_to_qdrant(request.file_ids)
        print(f"⭐️ Các file cho RAG đã được embedding vào collection: {collection_name}")

        # BƯỚC 2: GỌI RAG FLOW VỚI COLLECTION_NAME ĐỘNG
        # Bạn cần cập nhật hàm query_rag_flow để nhận collection_name
        answer = query_rag_flow(
            question=request.question,
            collection_name=collection_name, # <-- Truyền collection_name
            file_ids=request.file_ids,
            chat_history=request.chat_history
        )
        return {"answer": answer}

    except Exception as e:
        print(f"❌ Lỗi trong quá trình RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý RAG: {e}")
    finally:
        # BƯỚC 3: DỌN DẸP
        if collection_name:
            try:
                print(f"🧹 Dọn dẹp RAG collection: {collection_name}")
                qdrant_client.delete_collection(collection_name=collection_name)
                print(f"✅ RAG Collection '{collection_name}' đã được xóa.")
            except Exception as e:
                print(f"⚠️ Lỗi khi dọn dẹp RAG collection '{collection_name}': {e}")


# -------------------------------------------------------------
# 6. ĐIỂM BẮT ĐẦU
# -------------------------------------------------------------
if __name__ == "__main__":
    # Bạn cần file config.py có định nghĩa biến 'origins'
    # ví dụ: origins = ["http://localhost:3000"]
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)