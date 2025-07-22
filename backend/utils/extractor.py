import requests
import json
import asyncio
import os
from typing import List, Dict

# Import từ config
from config import LANGFLOW_EXTRACTOR_URL, HEADERS, QDRANT_COMPONENT_ID_EXTRACTOR

# (QDRANT_COMPONENT_ID được import từ config) 

MAX_ITERATIONS = 20
INITIAL_BATCH_SIZE = 6
MIN_BATCH_SIZE_TO_SPLIT = 2

# Đường dẫn tới thư mục schemas
SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")

def load_template_schema(template_id: str) -> Dict:
    """
    Tải schema từ file JSON cho template_id đã cho.
    """
    schema_file = os.path.join(SCHEMAS_DIR, f"{template_id}.json")
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Không tìm thấy schema file cho template '{template_id}'. Sử dụng mặc định.")
        # Fallback to template1 if schema not found
        return load_template_schema("template1")
    except Exception as e:
        print(f"❌ Lỗi khi đọc schema '{template_id}': {e}")
        return {"fields": [], "mapping": {}}

def structure_data_for_loan_assessment_report(flat_data: Dict, mapping: Dict) -> Dict:
    """
    Chuyển đổi dữ liệu phẳng từ LLM thành cấu trúc JSON lồng nhau cho Template 3&4 (Báo cáo thẩm định).
    """
    structured_data = {
        "thongTinChung": {},
        "thongTinKhachHang": {
            "phapLy": {},
            "banLanhDao": {"ten": "", "tyLeVon": "", "chucVu": "", "mucDoAnhHuong": "", "danhGia": ""},
            "nhanXet": {}
        },
        "hoatDongKinhDoanh": {
            "linhVuc": {"linhVuc": "", "sanPham": "", "tyTrongN1": "", "tyTrongN": ""},
            "tyTrongTheoNhomHang": {"nhomHang": "", "nam2023": "", "nam10T2024": ""},
            "moTaSanPham": {"sanPham": "", "loiThe": "", "nangLucDauThau": ""},
            "quyTrinhVanHanhText": "",
            "dauVao": {"matHang": "", "chiTiet": "", "pttt": ""},
            "dauRa": {"kenh": "", "tyTrong": "", "pttt": ""},
            "nhanXetHoatDong": ""
        },
        "thongTinNganh": {
            "cungCau": "",
            "nhanXet": ""
        },
        "kiemTraQuyDinh": {}
    }
    
    # Tạo reverse mapping để tra cứu hiệu quả hơn
    reverse_mapping = {}
    for category, fields in mapping.items():
        if isinstance(fields, dict):
            for key, llm_name in fields.items():
                if isinstance(llm_name, str):
                    reverse_mapping[llm_name] = (category, key)
                elif isinstance(llm_name, dict):
                    # Xử lý nested fields như phapLy, banLanhDao, nhanXet
                    for nested_key, nested_llm_name in llm_name.items():
                        reverse_mapping[nested_llm_name] = (category, key, nested_key)

    # Áp dụng mapping từ flat_data vào structured_data
    for llm_name, value in flat_data.items():
        if llm_name in reverse_mapping:
            mapping_path = reverse_mapping[llm_name]
            
            if len(mapping_path) == 2:
                # Direct mapping: category -> key
                category, key = mapping_path
                if category in structured_data:
                    structured_data[category][key] = value
                    
            elif len(mapping_path) == 3:
                # Nested mapping: category -> subcategory -> key
                category, subcategory, key = mapping_path
                if category in structured_data and subcategory in structured_data[category]:
                    if isinstance(structured_data[category][subcategory], dict):
                        structured_data[category][subcategory][key] = value

    # Đảm bảo tất cả các key cần thiết đều tồn tại với giá trị mặc định
    for category, fields in mapping.items():
        if category not in structured_data:
            structured_data[category] = {}
        
        if isinstance(fields, dict):
            for key, llm_name in fields.items():
                if isinstance(llm_name, str):
                    # Direct field
                    if key not in structured_data[category]:
                        structured_data[category][key] = ""
                elif isinstance(llm_name, dict):
                    # Nested field
                    if key not in structured_data[category]:
                        if key == "banLanhDao":
                            structured_data[category][key] = [{"ten": "", "tyLeVon": "", "chucVu": "", "mucDoAnhHuong": "", "danhGia": ""}]
                        else:
                            structured_data[category][key] = {}
                    
                    if isinstance(structured_data[category][key], dict):
                        for nested_key in llm_name.keys():
                            if nested_key not in structured_data[category][key]:
                                structured_data[category][key][nested_key] = ""

    return structured_data

# --- DEPRECATED CONTENT REMOVED ---
# Tất cả fields và mapping giờ đây được load từ file JSON schema


# --- 2. CÁC HÀM HỖ TRỢ ---

def create_prompt(fields_list: list) -> str:
    """
    Tạo prompt để yêu cầu LLM trích xuất các trường thông tin cụ thể.
    Đã được cập nhật để giống với logic trong notebook test.ipynb cho hiệu quả tốt hơn.
    """
    if not fields_list:
        return ""
    
    fields_as_text_list = "\n- ".join(fields_list)
    
    if len(fields_list) == 1:
        # Prompt cho một trường duy nhất
        return f"{fields_as_text_list}"
    else:
        # Prompt cho nhiều trường, định dạng với newline để LLM dễ xử lý hơn
        return f"\n- {fields_as_text_list}\n"



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


def structure_data_for_new_template(flat_data: Dict, mapping: Dict) -> Dict:
    """
    Chuyển đổi dữ liệu phẳng từ LLM thành cấu trúc JSON lồng nhau cho Template 2.
    """
    structured_data = {
        "headerInfo": {}, "creditInfo": {}, "businessInfo": {},
        "legalInfo": {}, "tcbRelationship": {},
        # Khởi tạo các trường phức tạp là array rỗng
        "management": {"members": []},
        "financialStatus": {"pnl": [], "businessPlan": []},
    }
    
    # Tạo một map ngược để tra cứu hiệu quả hơn: { "Tên đầy đủ...": "tenDayDu" }
    reverse_mapping = {}
    for category, fields in mapping.items():
        if isinstance(fields, dict):
            for key, llm_name in fields.items():
                if isinstance(llm_name, str):
                    reverse_mapping[llm_name] = (category, key)

    for llm_name, value in flat_data.items():
        if llm_name in reverse_mapping:
            category, key = reverse_mapping[llm_name]
            if category not in structured_data:
                structured_data[category] = {}
            structured_data[category][key] = value

    # Đảm bảo tất cả các key đều tồn tại, điền giá trị mặc định nếu thiếu
    for category, fields in mapping.items():
        if isinstance(fields, dict):
            if category not in structured_data:
                structured_data[category] = {}
            for key in fields.keys():
                if key not in structured_data[category]:
                    structured_data[category][key] = "" # Hoặc None

    return structured_data


# --- 3. LOGIC TRÍCH XUẤT CHÍNH (ĐÃ NÂNG CẤP HOÀN CHỈNH) ---

async def extract_information_from_docs(prompt: str, file_ids: List[str], collection_name: str, template_id: str) -> Dict:
    """
    Hàm chính điều khiển luồng trích xuất thông tin thông minh,
    giờ đây nhận `collection_name` và `template_id` để query đúng và trích xuất đúng trường.
    """
    # Tải schema từ file JSON
    schema = load_template_schema(template_id)
    fields_to_extract = schema.get("fields", [])
    mapping = schema.get("mapping", {})
    
    print(f"📋 Sử dụng template '{template_id}' với {len(fields_to_extract)} trường cần trích xuất.")

    final_result = {}
    work_queue = [
        fields_to_extract[i:i + INITIAL_BATCH_SIZE]
        for i in range(0, len(fields_to_extract), INITIAL_BATCH_SIZE)
    ]
    current_iteration = 0
    print(f"🚀 Bắt đầu quá trình trích xuất thông tin từ collection '{collection_name}' cho template '{template_id}'...")

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
    
    # Cấu trúc lại dữ liệu dựa trên template_id
    if template_id == "template2":
        print("🔄 Cấu trúc lại dữ liệu cho Template2...")
        structured_result = structure_data_for_new_template(final_result, mapping)
        return structured_result
    elif template_id == "template3":
        print("🔄 Cấu trúc lại dữ liệu cho Template3...")
        structured_result = structure_data_for_loan_assessment_report(final_result, mapping)
        return structured_result
    elif template_id == "template4":
        print("🔄 Cấu trúc lại dữ liệu cho Template4...")
        structured_result = structure_data_for_loan_assessment_report(final_result, mapping)
        return structured_result

    # Trả về kết quả cuối cùng dưới dạng một dictionary cho mẫu cũ
    return final_result