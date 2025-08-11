# # backend/utils/rag_client.py

# def query_rag_flow(question: str, collection_name: str, file_ids: List[str] = None, chat_history: List[Dict[str, str]] = None) -> str:
#     """
#     Gửi một câu hỏi, collection_name và lịch sử chat (tùy chọn) tới Flow RAG
#     và trả về câu trả lời dạng text.
#     """
#     if not question:
#         return "Vui lòng cung cấp một câu hỏi."

#     # Cấu trúc payload này cần phải khớp với những gì Flow RAG của bạn mong đợi.
#     # Thông thường, `input_value` là câu hỏi chính.
#     # Sử dụng tweaks để chỉ định collection_name động cho component Qdrant
#     payload = {
#         "input_value": question,
#         "output_type": "chat",
#         "input_type": "chat",
#         "tweaks": {
#             QDRANT_COMPONENT_ID_RAG: {
#                 "collection_name": collection_name
#             }
#         }
#     }

#     print(f"  - Gửi tới RAG Flow với collection '{collection_name}': {question}")

#     try:
#         response = requests.post(LANGFLOW_RAG_URL, json=payload, headers=HEADERS, timeout=REQUEST_TIMEOUT)
#         response.raise_for_status()

#         # Phân tích cú pháp phản hồi từ LangFlow
#         try:
#             response_data = response.json()
#             # Đường dẫn này phụ thuộc vào cấu trúc output của Flow RAG của bạn
#             answer = response_data['outputs'][0]['outputs'][0]['results']['message']['text']
#             return answer.strip() if answer else "Tôi không tìm thấy câu trả lời trong tài liệu."
#         except (KeyError, IndexError, json.JSONDecodeError) as e:
#             print(f"  - Lỗi phân tích phản hồi RAG: {e}")
#             return "Phản hồi từ hệ thống AI không hợp lệ."

#     except requests.exceptions.RequestException as e:
#         print(f"  - Lỗi gọi API RAG: {e}")
#         return "Đã có lỗi xảy ra khi kết nối tới hệ thống AI. Vui lòng thử lại sau."





from typing import List, Dict
from sentence_transformers import CrossEncoder
import uuid
import requests
import time
import json
from .embedding_handler import qdrant_client, embedding_model
# Import từ config
from config import RERANKER_MODEL_NAME, RERANKER_DEVICE, GOOGLE_API_KEY
from langchain_google_genai import ChatGoogleGenerativeAI
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
    llm_client = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY, temperature=0)
    print("✅ LLM client đã sẵn sàng.")
except Exception as e:
    llm_client = None
    print(f"❌ Không thể khởi tạo LLM client: {e}")
    
    
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
    print(f"  (1/3) Retrieval: Đang tìm kiếm {retrieve_k_children} child chunks liên quan...")
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

    print(f"  (2/3) Get Parents: Đã tìm thấy {len(candidate_parents)} parent chunk ứng viên.")
    if not candidate_parents:
        return ""

    # 3. RE-RANK: Chấm điểm lại các PARENT chunk
    print(f"  (3/3) Re-ranking: Đang chấm điểm lại các parent chunk...")
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

def query_rag_flow(question: str, collection_name: str, file_ids: List[str] = None, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Thực hiện RAG nâng cao 
    """
    if not question:
        return "Vui lòng cung cấp một câu hỏi."
    if reranker_model is None:
        return "Lỗi: Re-ranker model chưa được khởi tạo."
    if llm_client is None:
        return "Lỗi: LLM client chưa được khởi tạo."
    print(f"\n--- 🚀 Bắt đầu pipeline RAG nâng cao (với Langflow) cho câu hỏi: '{question[:50]}...' ---")
    start_time = time.time()

    # Bước 1: Lấy context chất lượng cao bằng logic nâng cao của chúng ta
    advanced_context = get_advanced_context(question, collection_name)

    if not advanced_context:
        return "Không tìm thấy thông tin nào liên quan trong tài liệu."

    # Bước 2: Tạo prompt cuối cùng để gửi cho Langflow
    # Prompt này hướng dẫn LLM trong Langflow chỉ cần làm việc với context đã có.
    final_prompt = f"""
    Dựa vào ngữ cảnh đã được cung cấp dưới đây, và chỉ dựa vào đó, hãy trả lời câu hỏi của người dùng một cách chính xác và đầy đủ.
    Hãy trích dẫn nguồn tài liệu (ví dụ: "Theo tài liệu X,...") nếu có thể.

    --- NGỮ CẢNH ---
    {advanced_context}
    ---

    Câu hỏi của người dùng: {question}

    Trả lời bằng tiếng Việt:
    """

    # Bước 3: Gọi LLM để sinh câu trả lời
    print(f"  - Gửi prompt đã xử lý tới LLM...")
    try:
        response = llm_client.invoke(final_prompt)
        answer = response.content
        
        end_time = time.time()
        print(f"✅ Hoàn tất pipeline trong {end_time - start_time:.2f} giây.")
        
        return answer.strip() if answer else "AI không thể tạo ra câu trả lời từ context được cung cấp."

    except Exception as e:
        print(f"  - Lỗi khi giao tiếp với LLM: {e}")
        return "Đã có lỗi xảy ra khi kết nối tới hệ thống AI."