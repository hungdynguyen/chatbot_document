import requests
import json
import asyncio
import os
from typing import List, Dict, Tuple
import re
import time
import uuid
from datetime import datetime
# Import từ config
from config import LANGFLOW_EXTRACTOR_URL, HEADERS, QDRANT_COMPONENT_ID_EXTRACTOR
# (QDRANT_COMPONENT_ID được import từ config) 

MAX_ITERATIONS = 100  # Tăng lên vì sẽ xử lý từng field riêng lẻ
# Giới hạn số từ cho prompt đầu vào của embedding model - giảm xuống mức an toàn
MAX_PROMPT_WORDS = 80  # Giảm từ 128 xuống 80 để đảm bảo an toàn với model embedding

# Timeout settings để tránh bị limit API
FIELD_PROCESSING_DELAY = 4.1  # Delay giữa các field (giây)
TABLE_PROCESSING_DELAY = 4.1  # Delay cho xử lý bảng (giây)
API_REQUEST_TIMEOUT = 180  # Timeout cho mỗi request (3 phút) 

# Đường dẫn tới thư mục schemas
SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")

# Đường dẫn tới thư mục context
CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "..", "context")

def create_context_session():
    """Tạo session ID unique cho mỗi lần chạy extraction"""
    session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    session_dir = os.path.join(CONTEXT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    return session_id, session_dir

def save_field_context(session_dir: str, field_name: str, prompt: str, documents_context: str, response: str):
    """Lưu context của một trường được trích xuất"""
    
    # Parse context thành array các documents riêng biệt
    formatted_context = documents_context
    if isinstance(documents_context, str) and documents_context.strip():
        try:
            # Decode Unicode escape sequences trước
            decoded_context = documents_context.encode().decode('unicode_escape')
            
            # Tách context thành các documents riêng biệt bằng \n\n
            if '\n\n{' in decoded_context:
                # Tách bằng double newline + JSON object
                doc_parts = decoded_context.split('\n\n')
                parsed_docs = []
                
                for part in doc_parts:
                    part = part.strip()
                    if part and part.startswith('{') and part.endswith('}'):
                        try:
                            doc_obj = json.loads(part)
                            parsed_docs.append(doc_obj)
                        except json.JSONDecodeError:
                            # Nếu không parse được thì giữ string
                            parsed_docs.append(part)
                    elif part:  # Text không phải JSON
                        parsed_docs.append(part)
                
                if parsed_docs:
                    formatted_context = parsed_docs
                else:
                    formatted_context = decoded_context
            else:
                # Nếu không có pattern \n\n thì chỉ decode Unicode
                formatted_context = decoded_context
                
        except Exception as e:
            # Nếu lỗi thì chỉ decode Unicode
            try:
                formatted_context = documents_context.encode().decode('unicode_escape')
            except:
                # Nếu decode cũng lỗi thì giữ nguyên
                formatted_context = documents_context
    
    context_data = {
        "timestamp": datetime.now().isoformat(),
        "field_name": field_name,
        "prompt": prompt,
        "documents_context": formatted_context,
        "raw_response": response,
        "prompt_word_count": len(prompt.split()),
        "context_word_count": len(str(formatted_context).split()) if isinstance(formatted_context, str) else sum(len(str(doc).split()) for doc in formatted_context) if isinstance(formatted_context, list) else 0
    }
    
    # Tạo tên file an toàn
    safe_field_name = re.sub(r'[^\w\-_]', '_', field_name)
    filename = f"{safe_field_name}.json"
    filepath = os.path.join(session_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(context_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Đã lưu context: {filename}")

def save_session_summary(session_dir: str, session_id: str, total_fields: int, success_count: int, error_count: int):
    """Lưu tóm tắt session"""
    summary = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "total_fields": total_fields,
        "success_count": success_count, 
        "error_count": error_count,
        "success_rate": f"{(success_count/total_fields*100):.1f}%" if total_fields > 0 else "0%"
    }
    
    filepath = os.path.join(session_dir, "_session_summary.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Đã lưu tóm tắt session: {session_id}")

# --- DANH SÁCH CÁC TRƯỜNG ĐẶC BIỆT DẠNG BẢNG ---
# Chúng ta sẽ xử lý các trường này bằng một chiến lược riêng
TABLE_FIELDS_TEMPLATE4 = [
    "thong_tin_ban_lanh_dao_day_du",
    "thong_tin_dau_vao_day_du", 
    "thong_tin_dau_ra_day_du"
]

# -- Kho prompt chi tiết đã được cập nhật --
TEMPLATE4_DETAILED_PROMPTS = {
    # --- PROMPT CHO CÁC BẢNG (ĐÃ TỐI ƯU) ---
    "thong_tin_ban_lanh_dao_day_du": """
    Tìm thông tin chi tiết ban lãnh đạo. Trả về JSON array:
    [{"ten":"họ tên thành viên", "chucVu":"chức vụ cụ thể", "tyLeVon":"tỷ lệ góp vốn", "mucDoAnhHuong":"chủ doanh nghiệp hay chỉ là người góp vốn", "danhGia":"năng lực, uy tín, kinh nghiệm"}]
    """,
    
    "thong_tin_dau_vao_day_du": """
    Tìm thông tin đầu vào kinh doanh. Trả về JSON array:
    [{"matHang":"tên nguyên vật liệu", "chiTiet":"nguồn mua, nhà cung cấp", "pttt":"phương thức thanh toán, thời hạn"}]
    """,
    
    "thong_tin_dau_ra_day_du": """
    Tìm thông tin đầu ra sản phẩm. Trả về JSON array:
    [{"kenh":"kênh phân phối, bán hàng", "tyTrong":"% tỷ trọng theo kênh", "pttt":"phương thức TT khách hàng"}]
    """,

    # --- CÁC TRƯỜNG THÔNG TIN CHUNG (ĐÃ RÚT GỌN) ---
    "Tên đầy đủ của khách hàng": "Tìm tên đầy đủ công ty/doanh nghiệp khách hàng",
    "Giấy ĐKKD/GP đầu tư": "Tìm số Giấy Đăng Ký Kinh Doanh hoặc Giấy Phép đầu tư",
    "ID trên T24": "Tìm ID của khách hàng trên hệ thống T24 của TCB",
    "Phân khúc": "Xác định phân khúc: Micro (siêu nhỏ), SME (nhỏ vừa), SME+ (nâng cao), MM (trung cấp), CIB (lớn)",
    "Loại khách hàng": "Tìm loại KH: ETC (Exclusive Trading - độc quyền) hoặc OTC (đại trà)",
    "Ngành nghề HĐKD theo ĐKKD": "Tìm ngành nghề chính theo ĐKKD lần 8",
    "Mục đích báo cáo": "Xác định: cấp tín dụng mới hay cấp lại cho KH",
    "Kết quả phân luồng": "Tìm kết quả phân luồng khách hàng",
    "XHTD": "Tìm bậc xếp hạng tín dụng XHTD",

    # --- THÔNG TIN PHÁP LÝ (RÚT GỌN) ---
    "Ngày thành lập": "Tìm ngày thành lập theo ĐKKD lần đầu tiên (không phải sửa đổi), format DD/MM/YYYY",
    "Địa chỉ trên ĐKKD": "Tìm địa chỉ đầy đủ, chi tiết theo ĐKKD",
    "Người đại diện theo Pháp luật": "Tìm họ tên người đại diện theo ĐKKD hoặc giấy đề nghị cấp TD",
    "Có kinh doanh Ngành nghề kinh doanh có điều kiện": "Có kinh doanh ngành cần GP đặc biệt (vốn, giấy phép, nhân sự...)? Có/Không",

    # --- NHẬN XÉT (SUY LUẬN - ĐÃ TỐI ƯU) ---
    "Nhận xét - Thông tin khách hàng": "Tóm tắt: năm thành lập, số năm hoạt động, lĩnh vực, sản phẩm chính",
    "Nhận xét - Pháp lý/GPKD có ĐK": "Tóm tắt: số ĐKKD, ngày cấp lần đầu, cơ quan cấp, các lần thay đổi",
    "Nhận xét - Chủ doanh nghiệp/Ban lãnh đạo": "Nhận xét về chủ doanh nghiệp, kinh nghiệm, thành tích, khả năng quản lý của công ty này với những thông tin được cung cấp",
    "Nhận xét - KYC": "Đánh giá chủ quan về tình trạng hoạt động ổn định của DN",

    # --- HOẠT ĐỘNG KINH DOANH (ĐÃ RÚT GỌN) ---
    "Lĩnh vực kinh doanh": "Tìm lĩnh vực chung: Xây lắp, Thương mại, Sản xuất, Dịch vụ...",
    "Sản phẩm/Dịch vụ": "Liệt kê sản phẩm/dịch vụ cụ thể, chi tiết",
    "Tỷ trọng doanh thu năm N-1 (%)": "Tìm % doanh thu năm N-1",
    "Tỷ trọng doanh thu năm N (%)": "Tìm % doanh thu năm N",
    "Nhóm mặt hàng": "Liệt kê các nhóm mặt hàng kinh doanh",
    "Tỷ trọng doanh thu 2023": "Tìm % doanh thu năm 2023",
    "Tỷ trọng doanh thu 10T/2024": "Tìm % doanh thu 10 tháng 2024",
    "Mô tả chung sản phẩm": "Mô tả chi tiết sản phẩm đầu ra",
    "Mô tả lợi thế cạnh tranh": "Tìm lợi thế so với đối thủ",
    "Mô tả năng lực đấu thầu": "Tìm chi tiết: tham gia bao nhiêu gói, trúng bao nhiêu, trượt bao nhiêu, chờ KQ",
    "Quy trình vận hành (tóm tắt)": "Mô tả cơ bản quy trình sản xuất/vận hành từ call report",
    "Đầu vào - Mặt hàng": "Liệt kê từng loại nguyên vật liệu đầu vào cụ thể",
    "Đầu vào - Chi tiết": "Nguồn mua: từ đâu, nhà cung cấp nào",
    "Đầu vào - Phương thức thanh toán": "PTTT với nhà cung cấp + thời hạn thanh toán",
    "Đầu ra - Kênh phân phối": "Các kênh bán hàng, phân phối cụ thể",
    "Đầu ra - Tỷ trọng": "% tỷ trọng theo từng kênh phân phối",
    "Đầu ra - Phương thức thanh toán": "PTTT của khách hàng + thời hạn thanh toán",
    "Nhận xét tổng quan hoạt động kinh doanh": "Nhận xét: pháp lý, quy mô, kế hoạch tương lai",

    # --- THÔNG TIN NGÀNH (RÚT GỌN) ---
    "Phân tích cung cầu ngành": "Tìm phân tích cung cầu ngành",
    "Nhận xét thông tin ngành": "Tìm nhận xét về ngành"
}

def load_template_schema(template_id: str) -> Dict:
    """
    Tải schema từ file JSON cho template_id đã cho.
    """
    schema_file = os.path.join(SCHEMAS_DIR, f"{template_id}.json")
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Không tìm thấy schema file cho template '{template_id}'.")
        return {"fields": [], "mapping": {}}
    except Exception as e:
        print(f"❌ Lỗi khi đọc schema '{template_id}': {e}")
        return {"fields": [], "mapping": {}}



def structure_data_for_loan_assessment_report(flat_data: Dict, mapping: Dict) -> Dict:
    """
    Chuyển đổi dữ liệu phẳng từ LLM thành cấu trúc JSON lồng nhau cho Template 4 (Báo cáo thẩm định).
    Đã cập nhật để xử lý 3 loại bảng: ban lãnh đạo, đầu vào, đầu ra.
    """
    print(f"\n🏗️ BẮT ĐẦU CẤU TRÚC LẠI DỮ LIỆU...")
    print(f"📥 Input có {len(flat_data)} trường dữ liệu thô")
    
    structured_data = {
        "thongTinChung": {},
        "thongTinKhachHang": {
            "phapLy": {},
            # Khởi tạo là một danh sách rỗng để chứa các thành viên
            "banLanhDao": [], 
            "nhanXet": {}
        },
        "hoatDongKinhDoanh": {
            "linhVuc": {},
            "tyTrongTheoNhomHang": {},
            "moTaSanPham": {},
            "quyTrinhVanHanhText": "",
            "dauVao": [],  # Đổi thành array để chứa dữ liệu bảng
            "dauRa": [],   # Đổi thành array để chứa dữ liệu bảng
            "nhanXetHoatDong": {}  # Đổi thành object để chứa phân tích chi tiết
        },
        "thongTinNganh": {
            "cungCau": "",
            "nhanXet": ""
        },
        "kiemTraQuyDinh": {}
    }
    
    # === XỬ LÝ DỮ LIỆU BẢNG TRƯỚC ===
    print(f"📋 Xử lý dữ liệu bảng...")
    
    # 1. Bảng Ban lãnh đạo (5 cột)
    leadership_list = flat_data.get("thong_tin_ban_lanh_dao_day_du", [])
    if isinstance(leadership_list, list) and leadership_list:
        structured_data["thongTinKhachHang"]["banLanhDao"] = [
            {
                "ten": member.get("ten"),
                "tyLeVon": member.get("tyLeVon"),
                "chucVu": member.get("chucVu"),
                "mucDoAnhHuong": member.get("mucDoAnhHuong"),
                "danhGia": member.get("danhGia")
            }
            for member in leadership_list
        ]
        print(f"   ✅ Ban lãnh đạo: {len(leadership_list)} thành viên")
    else:
        print(f"   ❌ Ban lãnh đạo: không có dữ liệu")

    # 2. Bảng Đầu vào (3 cột)
    input_list = flat_data.get("thong_tin_dau_vao_day_du", [])
    if isinstance(input_list, list) and input_list:
        structured_data["hoatDongKinhDoanh"]["dauVao"] = [
            {
                "matHang": item.get("matHang"),
                "chiTiet": item.get("chiTiet"),
                "pttt": item.get("pttt")
            }
            for item in input_list
        ]
        print(f"   ✅ Đầu vào: {len(input_list)} mục")
    else:
        print(f"   ❌ Đầu vào: không có dữ liệu")

    # 3. Bảng Đầu ra (3 cột) 
    output_list = flat_data.get("thong_tin_dau_ra_day_du", [])
    if isinstance(output_list, list) and output_list:
        structured_data["hoatDongKinhDoanh"]["dauRa"] = [
            {
                "kenh": item.get("kenh"),
                "tyTrong": item.get("tyTrong"),
                "pttt": item.get("pttt")
            }
            for item in output_list
        ]
        print(f"   ✅ Đầu ra: {len(output_list)} kênh")
    else:
        print(f"   ❌ Đầu ra: không có dữ liệu")

    # === XỬ LÝ CÁC TRƯỜNG CÒN LẠI ===
    print(f"📝 Xử lý các trường đơn lẻ...")
    reverse_mapping = {}
    for category, fields in mapping.items():
        if isinstance(fields, dict):
            for key, llm_name in fields.items():
                if isinstance(llm_name, str):
                    reverse_mapping[llm_name] = (category, key)
                elif isinstance(llm_name, dict):
                    # Bỏ qua các bảng đã xử lý riêng ở trên
                    if key in ["banLanhDao", "dauVao", "dauRa"]: continue
                    for nested_key, nested_llm_name in llm_name.items():
                        reverse_mapping[nested_llm_name] = (category, key, nested_key)
    for llm_name, value in flat_data.items():
        # Bỏ qua các trường bảng đã xử lý
        if llm_name in ["thong_tin_ban_lanh_dao_day_du", "thong_tin_dau_vao_day_du", "thong_tin_dau_ra_day_du"]:
            continue
            
        if llm_name in reverse_mapping:
            path = reverse_mapping[llm_name]
            if len(path) == 2:
                cat, key = path
                if cat not in structured_data: structured_data[cat] = {}
                structured_data[cat][key] = value
            elif len(path) == 3:
                cat, sub_cat, key = path
                if cat not in structured_data: structured_data[cat] = {}
                if sub_cat not in structured_data[cat]: structured_data[cat][sub_cat] = {}
                structured_data[cat][sub_cat][key] = value
    
    print(f"✅ Hoàn tất cấu trúc dữ liệu!")
    return structured_data

def truncate_text_by_words(text: str, max_words: int) -> str:
    """
    Cắt ngắn văn bản theo số lượng từ tối đa.
    Ưu tiên giữ lại phần đầu của prompt để không mất thông tin quan trọng.
    """
    words = text.split()
    if len(words) > max_words:
        # Cắt ngắn và thêm dấu hiệu để biết đã bị cắt
        truncated = " ".join(words[:max_words])
        return truncated + "..."
    return text

def is_valid_value(value) -> bool:
    """Kiểm tra xem giá trị trích xuất có hợp lệ hay không (không null, không rỗng)."""
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    # Cho phép list rỗng đi qua để xử lý sau, nhưng ở đây ta coi nó là không hợp lệ
    if isinstance(value, list) and not value:
        return False
    return True

def query_langflow_for_json_with_context(question_prompt: str, collection_name: str) -> Tuple[dict, str]:
    """
    Gửi yêu cầu đến Langflow và trả về cả kết quả và context thực.
    Returns: (result_dict, documents_context)
    """
    if not question_prompt:
        return {}, ""

    # --- KIỂM TRA ĐỘ DÀI PROMPT ---
    word_count = len(question_prompt.split())
    if word_count > MAX_PROMPT_WORDS:
        print(f"  ⚠️ Prompt có {word_count} từ, cắt xuống {MAX_PROMPT_WORDS} từ")
        truncated_prompt = truncate_text_by_words(question_prompt, MAX_PROMPT_WORDS)
    else:
        truncated_prompt = question_prompt
    
    # Double-check sau khi cắt ngắn
    final_word_count = len(truncated_prompt.split())
    if final_word_count > MAX_PROMPT_WORDS:
        # Cắt cứng nếu vẫn quá dài
        words = truncated_prompt.split()
        truncated_prompt = " ".join(words[:MAX_PROMPT_WORDS])
        print(f"  - 🔪 Cắt cứng xuống {MAX_PROMPT_WORDS} từ để đảm bảo an toàn tuyệt đối")
    
    payload = {
        "input_value": truncated_prompt,  # Sử dụng prompt đã được kiểm tra an toàn
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {
            QDRANT_COMPONENT_ID_EXTRACTOR: {
                "collection_name": collection_name
            }
        }
    }
    
    print(f"  - 📤 Gửi request (collection: '{collection_name}', độ dài cuối: {len(truncated_prompt.split())} từ)")

    try:
        response = requests.post(LANGFLOW_EXTRACTOR_URL, json=payload, headers=HEADERS, timeout=120)
        print(f"  - 🔍 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  - ❌ Response error: {response.text}")
            return {}, f"HTTP Error {response.status_code}: {response.text}"
            
        response.raise_for_status()
        
        langflow_data = response.json()
        print(f"  - 🔍 Langflow response có {len(langflow_data['outputs'][0]['outputs'])} outputs")
        
        # Lấy kết quả từ LLM (output đầu tiên)
        llm_response_text = langflow_data['outputs'][0]['outputs'][0]['results']['message']['text']
        print(f"  - 🔍 LLM response text length: {len(llm_response_text)}")
        print(f"  - 🔍 LLM response preview: {llm_response_text[:200]}...")
        
        # Lấy context thực từ ParserComponent (output thứ hai nếu có)
        documents_context = ""
        if len(langflow_data['outputs'][0]['outputs']) > 1:
            try:
                context_output = langflow_data['outputs'][0]['outputs'][1]
                if 'artifacts' in context_output and 'message' in context_output['artifacts']:
                    context_message = context_output['artifacts']['message']
                    
                    # Context có thể là string hoặc object
                    if isinstance(context_message, str):
                        documents_context = context_message
                    elif isinstance(context_message, dict):
                        documents_context = str(context_message)
                    
                    print(f"  - ✅ Lấy context thực từ Langflow: {len(documents_context)} chars")
                else:
                    print(f"  - ⚠️ Context output không có artifacts.message")
                    
            except Exception as e:
                print(f"  - ⚠️ Lỗi khi trích xuất context từ Langflow: {e}")
                documents_context = f"Lỗi trích xuất context: {str(e)}"
        else:
            print(f"  - ⚠️ Chỉ có 1 output, không có context riêng")
            documents_context = "Không có context output từ Langflow"
        
        # Tìm kiếm JSON linh hoạt hơn (tìm cả object `{...}` và array `[...]`)
        start_brace = llm_response_text.find('{')
        start_bracket = llm_response_text.find('[')
        
        # Xác định vị trí bắt đầu của JSON (ưu tiên array cho trường hợp bảng)
        if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
            start = start_bracket
            end = llm_response_text.rfind(']')
        elif start_brace != -1:
            start = start_brace
            end = llm_response_text.rfind('}')
        else:
            start, end = -1, -1

        if start != -1 and end != -1:
            json_str = llm_response_text[start : end + 1]
            try:
                result = json.loads(json_str)
                print(f"  - ✅ Thành công parse JSON response")
                return result, documents_context
            except json.JSONDecodeError:
                print(f"  - ❌ Lỗi parse JSON: {json_str[:100]}...")
                return {}, documents_context
        else:
            print("  - ❌ Không tìm thấy JSON/Array hợp lệ trong response")
            return {}, documents_context
            
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ Lỗi kết nối tới Langflow: {e}")
        return {}, ""
    except (KeyError, IndexError) as e:
        print(f"  - ❌ Lỗi cấu trúc response: {e}")
        return {}, ""
    except Exception as e:
        print(f"  - ❌ Lỗi không xác định: {e}")
        return {}, ""

def query_langflow_for_json(question_prompt: str, collection_name: str) -> dict:
    """
    Gửi yêu cầu đến Langflow, tự động cắt ngắn prompt nếu cần thiết.
    Đã được tối ưu để tránh lỗi embedding.
    """
    result, _ = query_langflow_for_json_with_context(question_prompt, collection_name)
    return result

# Bỏ hàm structure_data_for_new_template vì không liên quan đến template4



async def extract_information_from_docs(prompt: str, file_ids: List[str], collection_name: str, template_id: str) -> Dict:
    """
    Trích xuất thông tin từ tài liệu với logic mới:
    - Mỗi trường (không phải bảng) = 1 prompt = 1 API call
    - Xử lý bảng riêng để lấy cấu trúc nhiều dòng
    - Có timeout để tránh bị limit API
    """
    # Tạo session context cho lần chạy này
    session_id, session_dir = create_context_session()
    print(f"🆔 Session ID: {session_id}")
    print(f"📁 Context folder: {session_dir}")
    
    schema = load_template_schema(template_id)
    fields_to_extract = schema.get("fields", [])
    mapping = schema.get("mapping", {})
    final_result = {}
    
    # Tracking variables for session summary
    success_count = 0
    error_count = 0

    prompt_dictionary = {}
    if template_id == 'template4':
        prompt_dictionary = TEMPLATE4_DETAILED_PROMPTS
        # Lấy danh sách các trường bảng cần xử lý cho template này
        table_fields_to_run = [f for f in TABLE_FIELDS_TEMPLATE4 if f in fields_to_extract]
    else:
        table_fields_to_run = []

    # Phân loại các trường: bảng và không phải bảng
    non_table_fields = [f for f in fields_to_extract if f not in table_fields_to_run]
    
    total_fields = len(non_table_fields) + len(table_fields_to_run)
    print(f"🚀 Bắt đầu trích xuất cho {total_fields} trường:")
    print(f"   - {len(non_table_fields)} trường đơn lẻ")
    print(f"   - {len(table_fields_to_run)} trường bảng")
    
    current_field_count = 0
    
    # --- XỬ LÝ CÁC TRƯỜNG ĐƠN LẺ (MỖI TRƯỜNG = 1 API CALL) ---
    if non_table_fields:
        print("\n� Bắt đầu xử lý các trường đơn lẻ...")
        
        for field in non_table_fields:
            current_field_count += 1
            print(f"\n--- [{current_field_count}/{total_fields}] Xử lý trường: '{field}' ---")
            
            # Tạo prompt cho trường này
            if field in prompt_dictionary:
                # Có prompt chi tiết
                prompt_template = prompt_dictionary[field]
                final_prompt = f"{prompt_template}. Trả về JSON với key='{field}'"
            else:
                # Prompt đơn giản
                final_prompt = f"Trích xuất thông tin: {field}"
            
            # Kiểm tra và cắt ngắn prompt nếu cần
            if len(final_prompt.split()) > MAX_PROMPT_WORDS:
                final_prompt = f"Tìm: {field}"
                print(f"  - ⚠️ Prompt đã được rút gọn do giới hạn độ dài")
            
            # Gửi request với context
            loop = asyncio.get_event_loop()
            response_json, documents_context = await loop.run_in_executor(None, query_langflow_for_json_with_context, final_prompt, collection_name)
            
            # Lưu context cho trường này
            save_field_context(session_dir, field, final_prompt, documents_context, str(response_json))
            
            # Xử lý kết quả
            if response_json:
                if field in response_json and is_valid_value(response_json[field]):
                    final_result[field] = response_json[field]
                    success_count += 1
                    print(f"  ✅ Đã tìm thấy: '{field}'")
                elif len(response_json) == 1:
                    # Nếu chỉ có 1 key trong response, lấy value đó
                    key, value = next(iter(response_json.items()))
                    if is_valid_value(value):
                        final_result[field] = value
                        success_count += 1
                        print(f"  ✅ Đã tìm thấy (key khác): '{field}'")
                    else:
                        final_result[field] = None
                        error_count += 1
                        print(f"  ❌ Không tìm thấy giá trị hợp lệ: '{field}'")
                else:
                    final_result[field] = None
                    error_count += 1
                    print(f"  ❌ Không tìm thấy trong response: '{field}'")
            else:
                final_result[field] = None
                error_count += 1
                print(f"  ❌ Không có response hợp lệ: '{field}'")
            
            # Delay giữa các field để tránh limit API
            if current_field_count < len(non_table_fields):  # Không delay ở field cuối
                print(f"  ⏱️ Chờ {FIELD_PROCESSING_DELAY}s trước khi xử lý field tiếp theo...")
                await asyncio.sleep(FIELD_PROCESSING_DELAY)

    # --- XỬ LÝ CÁC TRƯỜNG BẢNG (CẤU TRÚC NHIỀU DÒNG) ---
    if table_fields_to_run:
        print(f"\n� Bắt đầu xử lý các trường bảng...")
        
        for field in table_fields_to_run:
            current_field_count += 1
            print(f"\n--- [{current_field_count}/{total_fields}] Xử lý bảng: '{field}' ---")
            
            prompt_template = prompt_dictionary.get(field)
            if not prompt_template:
                print(f"  ❌ Lỗi: Không tìm thấy prompt chuyên dụng cho bảng '{field}'. Bỏ qua.")
                final_result[field] = []
                continue

            # Kiểm tra và cắt ngắn prompt cho bảng nếu cần
            if len(prompt_template.split()) > MAX_PROMPT_WORDS:
                print(f"  - ⚠️ Prompt bảng quá dài ({len(prompt_template.split())} từ), sử dụng prompt đơn giản...")
                # Prompt backup dựa theo loại bảng
                if "ban_lanh_dao" in field:
                    final_prompt = "Tìm ban lãnh đạo. JSON array: ten, chucVu, tyLeVon, mucDoAnhHuong, danhGia"
                elif "dau_vao" in field:
                    final_prompt = "Tìm đầu vào. JSON array: matHang, chiTiet (nguồn mua), pttt"
                elif "dau_ra" in field:
                    final_prompt = "Tìm đầu ra. JSON array: kenh, tyTrong (%), pttt"
                else:
                    final_prompt = "Tìm thông tin bảng. Trả về JSON array"
            else:
                final_prompt = prompt_template
            
            # Double-check độ dài
            if len(final_prompt.split()) > MAX_PROMPT_WORDS:
                if "ban_lanh_dao" in field:
                    final_prompt = "Trích xuất thông tin ban lãnh đạo dạng JSON array"
                elif "dau_vao" in field:
                    final_prompt = "Trích xuất thông tin đầu vào dạng JSON array"
                elif "dau_ra" in field:
                    final_prompt = "Trích xuất thông tin đầu ra dạng JSON array"
                else:
                    final_prompt = "Trích xuất thông tin bảng dạng JSON array"
                print(f"  - 🔄 Sử dụng prompt rất đơn giản do giới hạn độ dài")
            
            # Gửi request cho bảng với context
            loop = asyncio.get_event_loop()
            response_json, documents_context = await loop.run_in_executor(None, query_langflow_for_json_with_context, final_prompt, collection_name)

            # Lưu context cho trường bảng này
            save_field_context(session_dir, field, final_prompt, documents_context, str(response_json))

            # Xử lý response cho bảng
            extracted_data = None
            if isinstance(response_json, dict) and field in response_json:
                extracted_data = response_json[field]
            elif isinstance(response_json, list):
                extracted_data = response_json
            elif isinstance(response_json, dict) and len(response_json) == 1:
                # Nếu chỉ có 1 key, lấy value đó
                key, value = next(iter(response_json.items()))
                if isinstance(value, list):
                    extracted_data = value
            
            if extracted_data and isinstance(extracted_data, list) and len(extracted_data) > 0:
                final_result[field] = extracted_data
                success_count += 1
                print(f"  ✅ Đã tìm thấy bảng '{field}' với {len(extracted_data)} dòng")
                # In preview dòng đầu tiên
                if extracted_data[0]:
                    print(f"      Preview dòng đầu: {str(extracted_data[0])[:100]}...")
            else:
                final_result[field] = []
                error_count += 1
                print(f"  ❌ Không tìm thấy dữ liệu bảng hợp lệ cho '{field}'")
            
            # Delay sau khi xử lý bảng (lâu hơn vì bảng phức tạp)
            if current_field_count < total_fields:  # Không delay ở field cuối
                print(f"  ⏱️ Chờ {TABLE_PROCESSING_DELAY}s sau khi xử lý bảng...")
                await asyncio.sleep(TABLE_PROCESSING_DELAY)

    print(f"\n\n✅ Hoàn tất trích xuất {total_fields} trường!")
    print(f"   - Thành công: {success_count} trường")
    print(f"   - Lỗi: {error_count} trường")
    print(f"   - Tỷ lệ thành công: {(success_count/total_fields*100):.1f}%")
    
    # Lưu session summary
    save_session_summary(session_dir, session_id, total_fields, success_count, error_count)

    # === LOG CHI TIẾT KẾT QUẢ TRÍCH XUẤT ===
    print(f"\n📋 CHI TIẾT KẾT QUẢ TRÍCH XUẤT:")
    print("=" * 80)
    
    successful_fields = []
    failed_fields = []
    
    for field, value in final_result.items():
        if value is not None and value != []:
            successful_fields.append(field)
            if isinstance(value, list):
                print(f"✅ {field}: ARRAY với {len(value)} phần tử")
                if len(value) > 0:
                    print(f"    └─ Phần tử đầu: {str(value[0])[:150]}...")
            else:
                print(f"✅ {field}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
        else:
            failed_fields.append(field)
            print(f"❌ {field}: KHÔNG TÌM THẤY")
    
    print(f"\n📊 THỐNG KÊ:")
    print(f"   - Thành công: {len(successful_fields)}/{total_fields} trường")
    print(f"   - Thất bại: {len(failed_fields)}/{total_fields} trường")
    
    if failed_fields:
        print(f"\n🔍 CÁC TRƯỜNG THẤT BẠI:")
        for field in failed_fields:
            print(f"   - {field}")

    # --- CẤU TRÚC LẠI DỮ LIỆU ---
    if template_id == "template4":
        structured_result = structure_data_for_loan_assessment_report(final_result, mapping)
        
        # Serialize JSON để log với format đẹp
        import json
        try:
            json_output = json.dumps(structured_result, indent=2, ensure_ascii=False)
            print(json_output)
        except Exception as e:
            print(f"❌ Lỗi serialize JSON: {e}")
            print(f"📊 Raw data: {structured_result}")
            
        print(f"{'='*80}")
        print(f"✅ KẾT THÚC LOG DỮ LIỆU FRONTEND")
        print(f"{'='*80}\n")
        
        return structured_result
    
    return final_result 
