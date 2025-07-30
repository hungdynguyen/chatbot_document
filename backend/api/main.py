import os
import uuid
import json
import time
from datetime import datetime
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
from utils.embedding_handler import embed_files_to_qdrant, qdrant_client 
from utils.document_parser import DocumentParser 
from utils.auto_evaluator import auto_evaluator
import shutil 

# -------------------------------------------------------------
# 1. KHỞI TẠO APP VÀ CẤU HÌNH
# -------------------------------------------------------------
app = FastAPI(title="Loan Assessment Backend")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Khởi tạo DocumentParser
document_parser = DocumentParser()

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
    enable_auto_evaluation: bool = False  # Thêm flag để bật/tắt auto evaluation
    run_full_metrics: bool = True  # Chạy toàn bộ metrics (faithfulness, answer_relevancy, context_precision, context_recall)

class RagRequest(BaseModel):
    question: str
    file_ids: List[str]
    collection_name: Optional[str] = None
    chat_history: List[Dict[str, str]] = Field(default_factory=list)

class FullEvaluationRequest(BaseModel):
    template_id: str = "template4"
    max_ragas_samples: int = 10  # Giới hạn số mẫu Ragas để tránh timeout
    run_full_metrics: bool = True  # Chạy toàn bộ metrics

# -------------------------------------------------------------
# 3. ENDPOINT UPLOAD 
# -------------------------------------------------------------
@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Lưu file
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        new_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, new_filename)
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Parse ngay để kiểm tra tính hợp lệ
        documents = document_parser.parse_file(file_path)
        
        print(f"✅ File '{file.filename}' đã được upload và parse thành công")
        print(f"📄 Tổng số documents: {len(documents)}")
        
        return {
            "file_id": file_id, 
            "filename": new_filename,
            "document_count": len(documents),
            "file_type": file_extension,
            "parsed_successfully": len(documents) > 0
        }
    except Exception as e:
        print(f"❌ Lỗi khi upload/parse file: {e}")
        raise HTTPException(status_code=500, detail=f"Không thể xử lý file: {str(e)}")


# -------------------------------------------------------------
# 4. ENDPOINT XỬ LÝ TRÍCH XUẤT 
# -------------------------------------------------------------
@app.post("/process_prompt")
async def process_prompt(request: ProcessRequest):
    """
    Nhận prompt, file_ids và template_id, thực hiện embedding và trích xuất thông tin.
    Tự động chạy evaluation nếu enable_auto_evaluation=True.
    """
    num_files = len(request.file_ids)
    if num_files == 0:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file.")

    print(f"🚀 Nhận được yêu cầu xử lý cho {num_files} file với prompt: '{request.prompt}' và template: '{request.template_id}'")
    print(f"   Các File ID: {request.file_ids}")
    print(f"   Auto Evaluation: {'Bật' if request.enable_auto_evaluation else 'Tắt'}")

    collection_name = None
    start_time = time.time()
    
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

        # Tính latency
        end_time = time.time()
        latency = end_time - start_time

        # --- BƯỚC 3: AUTO EVALUATION (NẾU ĐƯỢC BẬT) ---
        evaluation_result = None
        if request.enable_auto_evaluation:
            print(f"\n🎯 Bắt đầu auto-evaluation với full metrics: {request.run_full_metrics}...")
            evaluation_result = auto_evaluator.auto_evaluate(
                extracted_data=extracted_data,
                template_id=request.template_id,
                collection_name=collection_name,
                file_ids=request.file_ids,
                latency=latency,
                run_full_metrics=request.run_full_metrics
            )

        # Trả về kết quả, bao gồm cả collection_name để client có thể dùng cho chat
        response_data = {
            "summary": "Quá trình trích xuất thông tin đã hoàn tất.",
            "extracted_data": extracted_data,
            "prompt": request.prompt,
            "file_ids": request.file_ids,
            "collection_name": collection_name,
            "processing_time": latency
        }
        
        # Thêm kết quả evaluation nếu có
        if evaluation_result:
            response_data["auto_evaluation"] = evaluation_result
            print(f"✅ Kết quả auto-evaluation đã được thêm vào response")
        
        return response_data
        
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
# 8. ENDPOINT MỚI: FULL EVALUATION
# -------------------------------------------------------------
@app.post("/run_full_evaluation")
async def run_full_evaluation(request: FullEvaluationRequest):
    """
    Chạy full evaluation tương tự run_evaluation.py nhưng tích hợp vào backend.
    """
    print(f"🎯 Nhận yêu cầu chạy full evaluation cho template: {request.template_id}")
    
    # Cấu hình files cho test (có thể config từ ngoài)
    test_files = [
        "call-rp.xlsx",
        "DN HMTD CAG 2024 (1).docx",
        "DKKD lan 8 ngay 12.04.2023.pdf" 
    ]
    
    docs_directory = "data/data_real"
    
    try:
        # Load ground truth
        ground_truth_json = auto_evaluator.load_ground_truth(request.template_id)
        if not ground_truth_json:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy ground truth cho template: {request.template_id}")
        
        # Upload test files
        print("📤 Upload các file test...")
        file_id_map = {}
        for filename in test_files:
            filepath = os.path.join(docs_directory, filename)
            if os.path.exists(filepath):
                # Simulate file upload để có file_id
                file_id = str(uuid.uuid4())
                file_extension = Path(filename).suffix
                new_filename = f"{file_id}{file_extension}"
                new_file_path = os.path.join(UPLOAD_DIRECTORY, new_filename)
                
                # Copy file to upload directory
                shutil.copy2(filepath, new_file_path)
                file_id_map[filename] = file_id
                print(f"   ✅ {filename} -> {file_id}")
            else:
                print(f"   ⚠️ File không tìm thấy: {filepath}")
        
        if not file_id_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy file test nào!")
        
        # Chạy extraction với auto evaluation
        extraction_request = ProcessRequest(
            prompt="Trích xuất thông tin theo mẫu Báo cáo thẩm định.",
            file_ids=list(file_id_map.values()),
            template_id=request.template_id,
            enable_auto_evaluation=True,
            run_full_metrics=request.run_full_metrics
        )
        
        result = await process_prompt(extraction_request)
        
        # Nếu có auto evaluation, trả về kết quả chi tiết
        if "auto_evaluation" in result:
            evaluation_data = result["auto_evaluation"]
            
            metrics = {
                "processing_time": evaluation_data["latency"],
                "exact_match": evaluation_data["exact_match"],
                "semantic_similarity": evaluation_data["semantic_similarity"],
                "factual_correctness": evaluation_data["factual_correctness"],
                "jaccard_similarity": evaluation_data["jaccard_similarity"],
                "sequence_matcher": evaluation_data["sequence_matcher"],
                "levenshtein_ratio": evaluation_data["levenshtein_ratio"],
                "bleu_score": evaluation_data["bleu_score"],
                "rouge_1_f": evaluation_data["rouge_1_f"],
                "rouge_2_f": evaluation_data["rouge_2_f"],
                "rouge_l_f": evaluation_data["rouge_l_f"],
                "faithfulness": evaluation_data["faithfulness"],
                "answer_relevancy": evaluation_data["answer_relevancy"],
                "hallucination_rate": evaluation_data["hallucination_rate"]
            }
            
            # Thêm metrics bổ sung nếu chạy full
            if request.run_full_metrics and "context_precision" in evaluation_data:
                metrics.update({
                    "context_precision": evaluation_data["context_precision"],
                    "context_recall": evaluation_data["context_recall"]
                })
            
            return {
                "status": "success",
                "template_id": request.template_id,
                "test_files": list(file_id_map.keys()),
                "collection_name": result["collection_name"],
                "evaluation_metrics": metrics,
                "report_path": evaluation_data.get("report_path"),
                "evaluated_at": evaluation_data["evaluated_at"],
                "metrics_used": evaluation_data.get("metrics_used", "full"),
                "extracted_data": result["extracted_data"]
            }
        else:
            return {
                "status": "extraction_only",
                "message": "Trích xuất hoàn tất nhưng không có evaluation (thiếu ground truth)",
                "extracted_data": result["extracted_data"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Lỗi trong full evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi full evaluation: {e}")


# -------------------------------------------------------------
# 9. ENDPOINT: LẤY LỊCH SỬ AUTO EVALUATION
# -------------------------------------------------------------
@app.get("/evaluation_history")
async def get_evaluation_history():
    """
    Lấy danh sách các báo cáo auto evaluation đã tạo.
    """
    try:
        reports_dir = auto_evaluator.reports_dir
        if not os.path.exists(reports_dir):
            return {"reports": []}
        
        reports = []
        for filename in os.listdir(reports_dir):
            if filename.endswith('.xlsx') and filename.startswith('auto_eval_'):
                filepath = os.path.join(reports_dir, filename)
                stat = os.stat(filepath)
                reports.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sắp xếp theo thời gian tạo mới nhất
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"reports": reports, "total_count": len(reports)}
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy lịch sử evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy lịch sử evaluation: {e}")


# -------------------------------------------------------------
# 10. ĐIỂM BẮT ĐẦU
# -------------------------------------------------------------
if __name__ == "__main__":
    # Bạn cần file config.py có định nghĩa biến 'origins'
    # ví dụ: origins = ["http://localhost:3000"]
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)