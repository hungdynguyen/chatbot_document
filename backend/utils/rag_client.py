# backend/utils/rag_client.py

import requests
import json
from typing import List, Dict

# Import từ config
from config import LANGFLOW_RAG_URL, HEADERS, QDRANT_COMPONENT_ID_RAG

REQUEST_TIMEOUT = 120

def query_rag_flow(question: str, collection_name: str, file_ids: List[str] = None, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Gửi một câu hỏi, collection_name và lịch sử chat (tùy chọn) tới Flow RAG
    và trả về câu trả lời dạng text.
    """
    if not question:
        return "Vui lòng cung cấp một câu hỏi."

    # Cấu trúc payload này cần phải khớp với những gì Flow RAG của bạn mong đợi.
    # Thông thường, `input_value` là câu hỏi chính.
    # Sử dụng tweaks để chỉ định collection_name động cho component Qdrant
    payload = {
        "input_value": question,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {
            QDRANT_COMPONENT_ID_RAG: {
                "collection_name": collection_name
            }
        }
    }

    print(f"  - Gửi tới RAG Flow với collection '{collection_name}': {question}")

    try:
        response = requests.post(LANGFLOW_RAG_URL, json=payload, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Phân tích cú pháp phản hồi từ LangFlow
        try:
            response_data = response.json()
            # Đường dẫn này phụ thuộc vào cấu trúc output của Flow RAG của bạn
            answer = response_data['outputs'][0]['outputs'][0]['results']['message']['text']
            return answer.strip() if answer else "Tôi không tìm thấy câu trả lời trong tài liệu."
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"  - Lỗi phân tích phản hồi RAG: {e}")
            return "Phản hồi từ hệ thống AI không hợp lệ."

    except requests.exceptions.RequestException as e:
        print(f"  - Lỗi gọi API RAG: {e}")
        return "Đã có lỗi xảy ra khi kết nối tới hệ thống AI. Vui lòng thử lại sau."