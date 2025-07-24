import os
import uuid
from pathlib import Path
from typing import List, Dict, Optional

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- IMPORT CÁC UTILITY ---
# Giả sử bạn có file config.py để quản lý các hằng số
from config import UPLOAD_DIRECTORY, origins 
# Import các hàm xử lý logic
from utils.extractor import extract_information_from_docs, load_template_schema
from utils.rag_client import query_rag_flow
from utils.embedding_handler_lang import embed_files_to_qdrant, qdrant_client 

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
    template_id: str = "template1" # Thêm template_id, mặc định là template1

class RagRequest(BaseModel):
    question: str
    file_ids: List[str]
    collection_name: Optional[str] = None
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
    Nhận prompt, file_ids và template_id, thực hiện embedding và trích xuất thông tin.
    """
    num_files = len(request.file_ids)
    if num_files == 0:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file.")

    print(f"🚀 Nhận được yêu cầu xử lý cho {num_files} file với prompt: '{request.prompt}' và template: '{request.template_id}'")
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
            collection_name=collection_name,
            template_id=request.template_id
        )

        # Trả về kết quả, bao gồm cả collection_name để client có thể dùng cho chat
        return {
            "summary": "Quá trình trích xuất thông tin đã hoàn tất.",
            "extracted_data": extracted_data,
            "prompt": request.prompt,
            "file_ids": request.file_ids,
            "collection_name": collection_name,
        }
    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng trong quá trình xử lý: {e}")
        # Nếu có lỗi, và đã tạo collection, hãy xóa nó đi
        if collection_name:
            try:
                print(f"🧹 Dọn dẹp collection '{collection_name}' do có lỗi xảy ra...")
                qdrant_client.delete_collection(collection_name=collection_name)
                print(f"✅ Đã xóa collection '{collection_name}' do lỗi.")
            except Exception as cleanup_e:
                print(f"⚠️ Lỗi khi dọn dẹp collection '{collection_name}' sau lỗi chính: {cleanup_e}")
        # Bắt lỗi và trả về lỗi 500 cho frontend
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý phía server: {e}")
    # Bỏ khối finally đi để tránh xóa collection ngay lập tức


# -------------------------------------------------------------
# 5. ENDPOINT MỚI CHO CHỨC NĂNG CHAT RAG (ĐÃ TỐI ƯU)
# -------------------------------------------------------------
@app.post("/chat_rag")
async def chat_rag(request: RagRequest):
    if not request.file_ids:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp file_ids để thực hiện RAG.")

    print(f"🗨️ Nhận được câu hỏi RAG: '{request.question}'")
    
    collection_name = request.collection_name
    new_collection_created = False

    try:
        # Nếu không có collection_name, hoặc có nhưng không tồn tại trên server, tạo mới
        if not collection_name:
            print("Không có collection_name, sẽ tạo collection mới...")
            collection_name = await embed_files_to_qdrant(request.file_ids)
            new_collection_created = True
            print(f"⭐️ Các file cho RAG đã được embedding vào collection mới: {collection_name}")
        else:
            # Kiểm tra xem collection có thực sự tồn tại không
            try:
                # Cách đơn giản để kiểm tra là thử lấy thông tin collection
                qdrant_client.get_collection(collection_name=collection_name)
                print(f"🔄 Sử dụng lại collection đã có: {collection_name}")
            except Exception:
                # Nếu không tìm thấy, có thể collection đã bị xóa do timeout, tạo lại
                print(f"⚠️ Collection '{collection_name}' không tồn tại. Sẽ tạo lại...")
                collection_name = await embed_files_to_qdrant(request.file_ids)
                new_collection_created = True
                print(f"⭐️ Đã tạo lại collection: {collection_name}")

        # BƯỚC 2: GỌI RAG FLOW VỚI COLLECTION_NAME
        answer = query_rag_flow(
            question=request.question,
            collection_name=collection_name,
            file_ids=request.file_ids,
            chat_history=request.chat_history
        )
        
        response_data = {"answer": answer}
        # Nếu một collection mới được tạo, trả về tên của nó cho client
        if new_collection_created:
            response_data["collection_name"] = collection_name
            
        return response_data

    except Exception as e:
        print(f"❌ Lỗi trong quá trình RAG: {e}")
        # Nếu lỗi xảy ra và chúng ta đã tạo collection mới, hãy dọn dẹp nó
        if new_collection_created and collection_name:
            print(f"🧹 Dọn dẹp collection '{collection_name}' do có lỗi xảy ra...")
            try:
                qdrant_client.delete_collection(collection_name=collection_name)
                print(f"✅ Đã xóa collection '{collection_name}' do lỗi.")
            except Exception as cleanup_e:
                print(f"⚠️ Lỗi khi dọn dẹp collection '{collection_name}' sau lỗi chính: {cleanup_e}")
        
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý RAG: {e}")


# -------------------------------------------------------------
# 6. ENDPOINT DỌN DẸP SESSION
# -------------------------------------------------------------
class ClearSessionRequest(BaseModel):
    collection_name: str

@app.post("/clear_rag_session")
async def clear_rag_session(request: ClearSessionRequest):
    collection_name = request.collection_name
    if not collection_name:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp collection_name.")
    
    try:
        print(f"🧹 Nhận yêu cầu dọn dẹp RAG collection: {collection_name}")
        # Thử xóa collection
        qdrant_client.delete_collection(collection_name=collection_name)
        print(f"✅ RAG Collection '{collection_name}' đã được xóa thành công.")
        return {"status": "success", "message": f"Collection '{collection_name}' đã được xóa."}
    except Exception as e:
        # Lỗi có thể xảy ra nếu collection không tồn tại, hoặc do vấn đề kết nối
        # Trong trường hợp không tìm thấy, coi như đã thành công
        if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
            print(f"ℹ️ Collection '{collection_name}' không tìm thấy, có thể đã được xóa trước đó.")
            return {"status": "not_found", "message": f"Collection '{collection_name}' không tìm thấy."}
        
        print(f"⚠️ Lỗi khi dọn dẹp RAG collection '{collection_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa collection: {e}")


# -------------------------------------------------------------
# 7. ENDPOINT LẤY DANH SÁCH TEMPLATES
# -------------------------------------------------------------
@app.get("/templates")
async def get_templates():
    """
    Trả về danh sách các template có sẵn trong hệ thống.
    """
    try:
        import glob
        schemas_dir = os.path.join(os.path.dirname(__file__), "..", "utils", "..", "schemas")
        schema_files = glob.glob(os.path.join(schemas_dir, "*.json"))
        
        templates = []
        for schema_file in schema_files:
            try:
                schema = load_template_schema(os.path.basename(schema_file).replace('.json', ''))
                templates.append({
                    "template_id": schema.get("template_id"),
                    "template_name": schema.get("template_name"),
                    "description": schema.get("description")
                })
            except Exception as e:
                print(f"Lỗi khi đọc schema {schema_file}: {e}")
                continue
        
        return {"templates": templates}
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách templates: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy danh sách templates: {e}")


# -------------------------------------------------------------
# 8. ĐIỂM BẮT ĐẦU
# -------------------------------------------------------------
if __name__ == "__main__":
    # Bạn cần file config.py có định nghĩa biến 'origins'
    # ví dụ: origins = ["http://localhost:3000"]
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)