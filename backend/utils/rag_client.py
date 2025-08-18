from typing import List, Dict
from sentence_transformers import CrossEncoder
import uuid
import requests
import time
import json
import re
import os
from .embedding_handler import qdrant_client, embedding_model
# Import từ config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from config import DEEPSEEK_API_KEY, RERANKER_MODEL_NAME, RERANKER_DEVICE
REQUEST_TIMEOUT = 120

# --- KHỞI TẠO RE-RANKER MODEL (CHỈ MỘT LẦN) ---
print("🧠 Đang khởi tạo Re-ranker model...")
try:
    reranker_model = CrossEncoder(RERANKER_MODEL_NAME, device=RERANKER_DEVICE)
    print("✅ Re-ranker model đã sẵn sàng.")
except Exception as e:
    reranker_model = None
    print(f"❌ Không thể khởi tạo Re-ranker model: {e}")

print("🧠 Đang khởi tạo LLM client cho RAG...")
try:
    llm_client = ChatOpenAI(
        model='deepseek-chat',
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1" 
    )
    print("✅ LLM client (DeepSeek) đã sẵn sàng.")
except Exception as e:
    llm_client = None
    print(f"❌ Không thể khởi tạo LLM client (DeepSeek): {e}")
    
    
def get_advanced_context(
    question: str, 
    collection_name: str, 
    top_k_final: int = 3, 
    retrieve_k_children: int = 15
) -> str:
    """
    Thực hiện các bước Retrieval và Re-ranking nâng cao để lấy ra context chất lượng nhất.
    """
    # 1. RETRIEVE (Lần 1): Tìm kiếm trên các CHILD chunks trong Qdrant
    # print(f"  (1/3) Retrieval: Đang tìm kiếm {retrieve_k_children} child chunks liên quan...")
    try:
        retrieved_child_docs = qdrant_client.search(
            collection_name=collection_name,
            query_vector=embedding_model.embed_query(question),
            limit=retrieve_k_children,
            with_payload=True
        )
    except Exception as e:
        print(f"  ❌ Lỗi khi truy vấn Qdrant: {e}")
        return ""

    if not retrieved_child_docs:
        return ""

    # 2. GET PARENTS: Lấy ra các parent chunk ứng viên
    candidate_parents = {}
    for hit in retrieved_child_docs:
        if hit.payload:
            parent_content = hit.payload.get("parent_content")
            source = hit.payload.get("source", "Không rõ nguồn")
            if parent_content:
                candidate_parents[parent_content] = source

    # print(f"  (2/3) Get Parents: Đã tìm thấy {len(candidate_parents)} parent chunk ứng viên.")
    if not candidate_parents:
        return ""

    # 3. RE-RANK: Chấm điểm lại các PARENT chunk
    # print(f"  (3/3) Re-ranking: Đang chấm điểm lại các parent chunk...")
    parent_contents = list(candidate_parents.keys())
    pairs = [(question, content) for content in parent_contents]
    
    scores = reranker_model.predict(pairs)
    
    reranked_results = sorted(zip(scores, parent_contents), key=lambda x: x[0], reverse=True)
    
    final_docs = reranked_results[:top_k_final]
    
    # Tạo context cuối cùng với thông tin nguồn
    final_context = "\n\n---\n\n".join(
        [f"Trích từ tài liệu: {candidate_parents[content]}\n\nNội dung: {content}" for score, content in final_docs]
    )
    
    return final_context

def query_rag_flow(question: str, collection_name: str, file_ids: List[str] = None, chat_history: List[Dict[str, str]] = None, context_dir: str = None) -> str:
    """
    Thực hiện RAG nâng cao với log chi tiết kết quả LLM
    """
    if not question:
        return "Vui lòng cung cấp một câu hỏi."
    if reranker_model is None:
        return "Lỗi: Re-ranker model chưa được khởi tạo."
    if llm_client is None:
        return "Lỗi: LLM client chưa được khởi tạo."
    
    # Tạo ID duy nhất cho request này để dễ theo dõi trong logs
    request_id = str(uuid.uuid4())[:8]
    print(f"\n--- 🚀 [Request: {request_id}] Bắt đầu pipeline RAG nâng cao cho câu hỏi: '{question[:50]}...' ---")
    start_time = time.time()

    # Bước 1: Lấy context chất lượng cao bằng logic nâng cao của chúng ta
    advanced_context = get_advanced_context(question, collection_name)

    if not advanced_context:
        return "Không tìm thấy thông tin nào liên quan trong tài liệu."

    # Kiểm tra xem câu hỏi có yêu cầu JSON hay không hoặc là truy vấn bảng
    is_json_request = "json" in question.lower() or "định dạng json" in question.lower()
    is_table_request = any(keyword in question.lower() for keyword in ["thong_tin_ban_lanh_dao_day_du", "thong_tin_dau_vao_day_du", "thong_tin_dau_ra_day_du", "array", "mảng", "bảng"])
    
    # Bước 2: Tạo prompt cuối cùng để gửi cho LLM
    # Thêm hướng dẫn định dạng JSON nếu cần
    format_instruction = ""
    if is_json_request or is_table_request:
        format_instruction = """
        QUAN TRỌNG - HƯỚNG DẪN ĐỊNH DẠNG:
        
        Trả về kết quả CHÍNH XÁC dưới dạng JSON. Đảm bảo đúng cú pháp JSON với dấu {} và "" đầy đủ.
        KHÔNG thêm bất kỳ giải thích hoặc văn bản phụ nào ngoài chuỗi JSON.
        
        Nếu là dữ liệu bảng, hãy trả về một JSON array:
        [
          {"thuocTinh1": "giaTri1", "thuocTinh2": "giaTri2"...},
          {"thuocTinh1": "giaTri3", "thuocTinh2": "giaTri4"...}
        ]
        
        Ví dụ cho Ban lãnh đạo:
        [
          {"ten": "Nguyễn Văn A", "chucVu": "Giám đốc", "tyLeVon": "51%", "mucDoAnhHuong": "Chủ doanh nghiệp", "danhGia": "Nhiều kinh nghiệm trong ngành"},
          {"ten": "Trần Thị B", "chucVu": "Phó Giám đốc", "tyLeVon": "25%", "mucDoAnhHuong": "Cổ đông", "danhGia": "Chuyên môn cao"}
        ]
        
        Ví dụ cho Đầu vào:
        [
          {"matHang": "Nguyên liệu A", "chiTiet": "Nhập từ công ty X", "pttt": "Chuyển khoản T+30"},
          {"matHang": "Nguyên liệu B", "chiTiet": "Nhập từ công ty Y", "pttt": "Tiền mặt"}
        ]
        
        Ví dụ cho Đầu ra:
        [
          {"kenh": "Đại lý phân phối", "tyTrong": "60%", "pttt": "Chuyển khoản T+15"},
          {"kenh": "Bán lẻ trực tiếp", "tyTrong": "40%", "pttt": "Tiền mặt"}
        ]
        """
    
    final_prompt = f"""
        Bạn là một robot API chuyên trích xuất dữ liệu. Nhiệm vụ của bạn là trả về MỘT GIÁ TRỊ DUY NHẤT, chính xác dựa trên NGỮ CẢNH và CÂU HỎI.
        Bạn hãy suy luận từ các câu hỏi và các câu trả lời trước đó. Đừng bị hallucinate lấy ra các công ty không phải khách hàng, và các thông tin không liên quan.
        --- QUY TẮC TUYỆT ĐỐI ---
        1.  **TRỰC TIẾP & NGẮN GỌN:** Câu trả lời PHẢI là giá trị trực tiếp, ngắn gọn nhất có thể. Ví dụ: nếu hỏi "Ngày thành lập", chỉ trả lời "01/01/2020".
        2.  **KHÔNG DÙNG CÂU HOÀN CHỈNH:** Tránh dùng câu cú hoàn chỉnh. Nếu hỏi "tên công ty", chỉ trả về "Công ty A", TUYỆT ĐỐI KHÔNG trả lời "Tên của công ty là Công ty A."
        3.  **KHÔNG GIẢI THÍCH:** Cấm tuyệt đối việc thêm lời chào, giải thích, bình luận, hay bất kỳ văn bản nào khác ngoài dữ liệu được yêu cầu.
        4.  **ĐỊNH DẠNG JSON:** Nếu câu hỏi yêu cầu định dạng JSON (ví dụ: cho bảng dữ liệu), hãy tuân thủ nghiêm ngặt. Chỉ trả về chuỗi JSON, không gì khác.
        5.  **TRUNG THỰC:** Nếu không thể tìm thấy thông tin trong ngữ cảnh được cung cấp, hãy trả về một chuỗi rỗng ("").

        {format_instruction}

        --- NGỮ CẢNH ---
        {advanced_context}
        ---

        Câu hỏi của người dùng: {question}

        Giá trị trả về (Value only):
        
        """

    # Bước 3: Gọi LLM để sinh câu trả lời
    print(f"  - [Request: {request_id}] Gửi prompt đã xử lý tới LLM...")
    try:
        response = llm_client.invoke(final_prompt)
        answer = response.content
        
        # In ra kết quả thô từ LLM để debug
        print(f"\n🔍 [Request: {request_id}] RAW LLM RESPONSE:\n{'-'*80}\n{answer}\n{'-'*80}")
        
        # Xử lý JSON response - đặc biệt cho các truy vấn bảng
        if is_json_request or is_table_request or "[" in answer or "{" in answer:
            try:
                # Sử dụng regex để tìm khối JSON hoặc Array đầu tiên (kể cả khi bị bao bọc)
                json_match = re.search(r'```json\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```|(\{[\s\S]*\}|\[[\s\S]*\])', answer, re.DOTALL)
                
                if json_match:
                    # Ưu tiên lấy nội dung bên trong ```json nếu có
                    json_str = json_match.group(1) or json_match.group(2)
                    
                    # Parse chuỗi JSON đã được trích xuất
                    json_obj = json.loads(json_str)
                    
                    # Nếu thành công, thay thế câu trả lời bằng JSON đã được định dạng lại đẹp đẽ
                    answer = json.dumps(json_obj, ensure_ascii=False, indent=2)
                    print(f"  - [Request: {request_id}] Đã parse và làm sạch JSON thành công")
                    
                else:
                    print(f"  - [Request: {request_id}] Không tìm thấy chuỗi JSON hợp lệ trong phản hồi")
                    
            except json.JSONDecodeError as je:
                print(f"  - [Request: {request_id}] Lỗi khi parse chuỗi JSON đã trích xuất: {je}")
            except Exception as e:
                print(f"  - [Request: {request_id}] Lỗi không xác định khi xử lý JSON: {e}")
        
        # Ghi log kết quả thô nếu có context_dir
        if context_dir:
            # Tạo tên file an toàn dựa trên câu hỏi
            safe_question = re.sub(r'[^\w\-_]', '_', question[:30])
            log_file = f"{context_dir}/llm_responses_{safe_question}_{request_id}.log"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"QUESTION: {question}\n\n")
                f.write(f"CONTEXT (TRUNCATED): {advanced_context[:500]}...\n\n")
                f.write(f"RESPONSE:\n{answer}")
            print(f"  - [Request: {request_id}] Đã lưu log chi tiết: {log_file}")
            
            # Nếu là yêu cầu JSON, ghi ra file JSON riêng
            if is_json_request or is_table_request or "{" in answer or "[" in answer:
                try:
                    # Kiểm tra xem answer có phải là JSON hợp lệ không
                    try:
                        json_obj = json.loads(answer)
                        json_file = f"{context_dir}/parsed_json_{request_id}.json"
                        with open(json_file, "w", encoding="utf-8") as f:
                            json.dump(json_obj, f, indent=2, ensure_ascii=False)
                        print(f"  - [Request: {request_id}] Đã lưu JSON hợp lệ: {json_file}")
                    except json.JSONDecodeError:
                        # Tìm phần JSON trong câu trả lời
                        json_start = answer.find("{") if "{" in answer else answer.find("[")
                        json_end = answer.rfind("}") + 1 if "}" in answer else answer.rfind("]") + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_content = answer[json_start:json_end]
                            # Cố gắng parse JSON để kiểm tra tính hợp lệ
                            json_obj = json.loads(json_content)
                            json_file = f"{context_dir}/parsed_json_{request_id}.json"
                            with open(json_file, "w", encoding="utf-8") as f:
                                json.dump(json_obj, f, indent=2, ensure_ascii=False)
                            print(f"  - [Request: {request_id}] Đã tách JSON hợp lệ: {json_file}")
                except Exception as json_err:
                    print(f"  - [Request: {request_id}] Không thể parse JSON: {str(json_err)}")
        
        end_time = time.time()
        print(f"✅ [Request: {request_id}] Hoàn tất pipeline trong {end_time - start_time:.2f} giây.")
        
        return answer.strip() if answer else "AI không thể tạo ra câu trả lời từ context được cung cấp."

    except Exception as e:
        print(f"  - [Request: {request_id}] Lỗi khi giao tiếp với LLM: {e}")
        return "Đã có lỗi xảy ra khi kết nối tới hệ thống AI."