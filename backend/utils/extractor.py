import requests
import json
import asyncio
from typing import List, Dict

# Import từ config
from config import LANGFLOW_EXTRACTOR_URL, HEADERS, QDRANT_COMPONENT_ID_EXTRACTOR

# (QDRANT_COMPONENT_ID được import từ config) 

MAX_ITERATIONS = 20
INITIAL_BATCH_SIZE = 6
MIN_BATCH_SIZE_TO_SPLIT = 2

FIELDS_TO_EXTRACT = [
    "tên đầy đủ của doanh nghiệp",
    "mã số doanh nghiệp",
    "ngày cấp giấy chứng nhận đăng ký kinh doanh",
    "nơi cấp giấy chứng nhận đăng ký kinh doanh",
    "địa chỉ trụ sở chính",
    "ngành nghề kinh doanh chính",
    "vốn điều lệ",
    "tên người đại diện theo pháp luật",
    "chức vụ người đại diện",
    "số CCCD/CMND của người đại diện",
    "số tiền đề nghị vay",
    "thời hạn vay (tháng)",
    "mục đích vay vốn",
    "sản phẩm tín dụng đăng ký",
    "lãi suất cho vay (%/năm)",
    "phí trả nợ trước hạn (%)",
    "phương thức trả nợ",
    "doanh thu năm gần nhất",
    "lợi nhuận ròng năm gần nhất",
    "tổng tài sản ước tính",
    "dự báo doanh thu năm 1 sau khi vay",
    "kế hoạch phân bổ vốn vay cho đầu tư kho lạnh",
    "điểm tín dụng doanh nghiệp (CIC)",
    "xếp hạng tín dụng doanh nghiệp (CIC)",
    "phân loại nợ hiện tại của doanh nghiệp (CIC)",
    "tổng dư nợ tại các tổ chức tín dụng khác",
    "dư nợ tại Vietcombank (CIC)",
    "lịch sử trả nợ 12 tháng gần nhất (chuỗi trạng thái CIC)",
    "loại tài sản bảo đảm chính",
    "chủ sở hữu tài sản bảo đảm",
    "giá trị tài sản bảo đảm theo thẩm định",
    "đơn vị thẩm định giá",
    "tỷ lệ cho vay tối đa trên tài sản bảo đảm (%)",
    "tên người bảo lãnh cho khoản vay"
]

# --- 2. CÁC HÀM HỖ TRỢ ---

def create_prompt(fields_list: list) -> str:
    """Tạo prompt để yêu cầu LLM trích xuất các trường thông tin cụ thể."""
    if not fields_list:
        return ""
    fields_as_text_list = "\n- ".join(fields_list)
    if len(fields_list) == 1:
        return f"{fields_as_text_list}"
    else:
        return f"- {fields_as_text_list}"

def is_valid_value(value) -> bool:
    """Kiểm tra xem giá trị trích xuất có hợp lệ hay không."""
    return value is not None and str(value).strip() != ""

# --- HÀM QUERY LANGFLOW ĐÃ NÂNG CẤP HOÀN CHỈNH ---
def query_langflow_for_json(question_prompt: str, collection_name: str) -> dict:
    """
    Gửi yêu cầu đến Langflow, SỬ DỤNG TWEAKS để chỉ định collection_name động.
    """
    if not question_prompt:
        return {}

    # Payload giờ đây sẽ ghi đè collection_name của component Qdrant trong flow
    payload = {
        "input_value": question_prompt,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {
            QDRANT_COMPONENT_ID_EXTRACTOR: {
                "collection_name": collection_name
            }
        }
    }
    
    print(f"  - Đang gửi yêu cầu tới Langflow, ghi đè collection thành: '{collection_name}'")

    try:
        response = requests.post(LANGFLOW_EXTRACTOR_URL, json=payload, headers=HEADERS, timeout=120)
        response.raise_for_status()
        
        langflow_data = response.json()
        # Đường dẫn tới message có thể thay đổi tùy theo cấu trúc flow, cần kiểm tra kỹ
        llm_response_text = langflow_data['outputs'][0]['outputs'][0]['results']['message']['text']
        
        start = llm_response_text.find('{')
        end = llm_response_text.rfind('}')
        
        if start != -1 and end != -1:
            json_str = llm_response_text[start : end + 1]
            # Thêm try-except để bắt lỗi JSON không hợp lệ
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"  - Lỗi: Chuỗi JSON không hợp lệ: {json_str}")
                return {}
        else:
            print("  - Lỗi: Không tìm thấy đối tượng JSON hợp lệ trong phản hồi của LLM.")
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"  - Lỗi kết nối tới Langflow: {e}")
        return {}
    except (KeyError, IndexError) as e:
        print(f"  - Lỗi: Cấu trúc phản hồi từ Langflow không như mong đợi. Lỗi: {e}")
        print(f"  - Phản hồi nhận được: {langflow_data}")
        return {}
    except Exception as e:
        print(f"  - Lỗi không xác định khi query Langflow: {e}")
        return {}


# --- 3. LOGIC TRÍCH XUẤT CHÍNH (ĐÃ NÂNG CẤP HOÀN CHỈNH) ---

async def extract_information_from_docs(prompt: str, file_ids: List[str], collection_name: str) -> Dict:
    """
    Hàm chính điều khiển luồng trích xuất thông tin thông minh,
    giờ đây nhận `collection_name` để query đúng vào VectorDB của phiên làm việc.
    """
    final_result = {}
    work_queue = [
        FIELDS_TO_EXTRACT[i:i + INITIAL_BATCH_SIZE]
        for i in range(0, len(FIELDS_TO_EXTRACT), INITIAL_BATCH_SIZE)
    ]
    current_iteration = 0
    print(f"🚀 Bắt đầu quá trình trích xuất thông tin từ collection '{collection_name}'...")

    while work_queue and current_iteration < MAX_ITERATIONS:
        current_iteration += 1
        current_batch = work_queue.pop(0)
        
        print(f"\n--- VÒNG LẶP {current_iteration}/{MAX_ITERATIONS} | Đang xử lý lô {len(current_batch)} trường ---")
        
        batch_prompt = create_prompt(current_batch)
        
        # Chạy hàm requests đồng bộ trong một luồng riêng để không chặn vòng lặp sự kiện của FastAPI
        loop = asyncio.get_event_loop()
        # Truyền collection_name vào hàm query
        response_json = await loop.run_in_executor(
            None, query_langflow_for_json, batch_prompt, collection_name
        )

        newly_found_fields = []
        if response_json:
            for field in current_batch:
                if field in response_json and is_valid_value(response_json[field]):
                    value = response_json[field]
                    print(f"    ✅ Đã tìm thấy '{field}': {value}")
                    final_result[field] = value
                    newly_found_fields.append(field)
        
        failed_fields = [f for f in current_batch if f not in newly_found_fields]
        
        if failed_fields:
            print(f"  - Không tìm thấy {len(failed_fields)} trường: {', '.join(failed_fields)}")
            if len(failed_fields) >= MIN_BATCH_SIZE_TO_SPLIT:
                print(f"  -> Chia nhỏ lô thất bại...")
                mid_point = len(failed_fields) // 2
                first_half = failed_fields[:mid_point]
                second_half = failed_fields[mid_point:]
                work_queue.insert(0, second_half)
                work_queue.insert(0, first_half)
            else:
                print(f"  -> Lô quá nhỏ, không chia nữa.")
        
        await asyncio.sleep(1) # Có thể giảm thời gian sleep

    print("\n\n✅ Quá trình trích xuất hoàn tất!")
    
    # Trả về kết quả cuối cùng dưới dạng một dictionary
    return final_result