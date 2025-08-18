from typing import Dict, List, Any, Type, Tuple
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import json
import os
import traceback
import re
import uuid
from datetime import datetime
import requests
import time

# Import từ config
from .rag_client import query_rag_flow

# Constants
MAX_ITERATIONS = 100
MAX_PROMPT_WORDS = 80
FIELD_PROCESSING_DELAY = 4.1
TABLE_PROCESSING_DELAY = 4.1
API_REQUEST_TIMEOUT = 180

# Đường dẫn tới thư mục schemas
SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")

# Đường dẫn tới thư mục context
CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "..", "context")

class ExtractionSchema(BaseModel):
    prompt: str = Field(description="Yêu cầu trích xuất của người dùng, ví dụ: 'trích xuất báo cáo thẩm định'")
    file_ids: List[str] = Field(description="Danh sách ID của các file cần trích xuất.")
    collection_name: str = Field(description="Tên collection Qdrant cho session này.")
    template_id: str = Field(description="ID của template cần trích xuất, ví dụ 'template4'.")

class StructuredExtractionTool(BaseTool):
    """Extracts structured information from documents based on a predefined template."""
    name: str = "structured_extraction"
    description: str = "Extracts structured information from documents based on a predefined template."
    args_schema: Type[BaseModel] = ExtractionSchema
    
    # Biến để ngăn đệ quy vô hạn
    _extraction_in_progress = False

    async def _arun(self, prompt: str, file_ids: List[str], collection_name: str, template_id: str) -> Dict[str, Any]:
        print(f"Tool: Extracting info with prompt '{prompt}' from collection '{collection_name}' using template '{template_id}'")
        
        # THÊM CHECK ĐỂ TRÁNH ĐỆ QUY
        if self.__class__._extraction_in_progress:
            print("⚠️ Phát hiện đệ quy! Ngăn chặn vòng lặp vô tận.")
            return {"extracted_data": {"error": "Recursive call detected"}, 
                    "message": "Stopped recursive extraction"}
            
        try:
            self.__class__._extraction_in_progress = True
            
            # Cải thiện prompt để đảm bảo kết quả luôn là JSON
            improved_prompt = f"{prompt}\n\n"
            improved_prompt += "QUAN TRỌNG: Kết quả trả về PHẢI là một đối tượng JSON hợp lệ, không phải văn bản tự do. "
            improved_prompt += "Đảm bảo đối tượng JSON tuân theo schema của template4 với các key chính là: "
            improved_prompt += "thongTinChung, thongTinKhachHang, hoatDongKinhDoanh, thongTinNganh. "
            improved_prompt += "CHỈ trả về object JSON, không thêm văn bản hay giải thích."
            
            # Sử dụng extract_information_from_docs để lấy dữ liệu có cấu trúc
            extracted_data = await extract_information_from_docs(improved_prompt, file_ids, collection_name, template_id)
            
            # Kiểm tra và đảm bảo dữ liệu trả về là dict hợp lệ
            if not isinstance(extracted_data, dict):
                print("⚠️ Dữ liệu trả về không phải là dict! Chuyển đổi sang dict rỗng.")
                extracted_data = {}
            
            # Kiểm tra xem có đủ các trường chính trong template4 không
            expected_keys = ["thongTinChung", "thongTinKhachHang", "hoatDongKinhDoanh", "thongTinNganh"]
            missing_keys = [key for key in expected_keys if key not in extracted_data]
            
            if missing_keys:
                print(f"⚠️ Thiếu các trường chính trong kết quả: {missing_keys}")
                # Tạo cấu trúc cho các trường bị thiếu
                for key in missing_keys:
                    extracted_data[key] = {}
            
            # Lưu JSON kết quả để debug
            try:
                debug_dir = os.path.join(os.path.dirname(__file__), "..", "debug_output")
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, f"extraction_result_{template_id}_{hash(prompt)}.json")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(extracted_data, f, ensure_ascii=False, indent=2)
                print(f"✅ Đã lưu kết quả JSON để debug tại: {debug_file}")
            except Exception as debug_err:
                print(f"⚠️ Không thể lưu file debug: {debug_err}")
            
            # In ra cấu trúc dữ liệu để debug
            print("\n🔍 CẤU TRÚC DỮ LIỆU ĐÃ PARSE:")
            print("-"*50)
            import pprint
            debug_keys = {}
            for k in extracted_data.keys():
                if isinstance(extracted_data[k], dict):
                    debug_keys[k] = {subk: "..." for subk in extracted_data[k].keys()}
                else:
                    debug_keys[k] = "..."
            pprint.pprint(debug_keys)
            print("-"*50 + "\n")
            
            return {"extracted_data": extracted_data, "message": "Extraction complete"}
            
        except Exception as e:
            print(f"Error during extraction: {e}")
            traceback_str = traceback.format_exc()
            print(f"Traceback: {traceback_str}")
            
            # Trả về cấu trúc template4 rỗng thay vì None
            empty_template4 = {
                "thongTinChung": {},
                "thongTinKhachHang": {},
                "hoatDongKinhDoanh": {},
                "thongTinNganh": {}
            }
            
            return {"extracted_data": empty_template4, "message": f"Error: {str(e)}"}
        finally:
            self.__class__._extraction_in_progress = False

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
    Trích xuất TOÀN BỘ thông tin chi tiết về Ban lãnh đạo trong ngữ cảnh. Lấy tất cả các thành viên.
    Trả về DUY NHẤT một JSON array với cấu trúc:
    [
      {"ten":"...", "chucVu":"...", "tyLeVon":"...", "mucDoAnhHuong":"...", "danhGia":"..."}
    ]
    Nếu một trường thông tin không có, hãy để giá trị là một chuỗi rỗng "".
    KHÔNG GIẢI THÍCH. Nếu không có thông tin, trả về [].
    """,
    
    "thong_tin_dau_vao_day_du": """
    Trích xuất TOÀN BỘ thông tin về đầu vào kinh doanh trong ngữ cảnh. Lấy tất cả các mặt hàng.
    Trả về DUY NHẤT một JSON array với cấu trúc:
    [
      {"matHang":"...", "chiTiet":"...", "pttt":"..."}
    ]
    Nếu một trường thông tin không có, hãy để giá trị là một chuỗi rỗng "".
    KHÔNG GIẢI THÍCH. Nếu không có thông tin, trả về [].
    """,
    
    "thong_tin_dau_ra_day_du": """
    Trích xuất TOÀN BỘ thông tin về đầu ra sản phẩm trong ngữ cảnh. Lấy tất cả các kênh phân phối.
    Trả về DUY NHẤT một JSON array với cấu trúc:
    [
      {"kenh":"...", "tyTrong":"...", "pttt":"..."}
    ]
    Nếu một trường thông tin không có, hãy để giá trị là một chuỗi rỗng "".
    KHÔNG GIẢI THÍCH. Nếu không có thông tin, trả về [].
    """,

    # --- CÁC TRƯỜNG THÔNG TIN CHUNG (ĐÃ RÚT GỌN) ---
    "Tên đầy đủ của khách hàng": "Tìm tên đầy đủ công ty/doanh nghiệp khách hàng",
    "Giấy ĐKKD/GP đầu tư": "Dựa vào tên đầy đủ của khách hàng. Tìm số Giấy Đăng Ký Kinh Doanh hoặc Giấy Phép đầu tư",
    "ID trên T24": "Dựa vào tên đầy đủ của khách hàng. Tìm ID của khách hàng trên hệ thống",
    "Phân khúc": "Dựa vào tên đầy đủ của khách hàng. Xác định phân khúc: Micro (siêu nhỏ), SME (nhỏ vừa), SME+ (nâng cao), MM (trung cấp), CIB (lớn)",
    "Loại khách hàng": "Dựa vào tên đầy đủ của khách hàng. Tìm loại KH: ETC (Exclusive Trading - độc quyền) hoặc OTC (đại trà)",
    "Ngành nghề HĐKD theo ĐKKD": "Dựa vào tên đầy đủ của khách hàng. Tìm ngành nghề chính theo ĐKKD (Đăng ký kinh doanh)",
    "Mục đích báo cáo": "Dựa vào tên đầy đủ của khách hàng. Xác định: cấp tín dụng mới hay cấp lại cho khách hàng",
    "Kết quả phân luồng": "Dựa vào tên đầy đủ của khách hàng. Tìm kết quả phân luồng khách hàng",
    "XHTD": "Dựa vào tên đầy đủ của khách hàng. Tìm bậc xếp hạng tín dụng XHTD (xếp hạng tín dụng của khách hàng). Nếu thấy các giá trị như Aa3, Aa1, Bb1, Aa2,... thì đó là xếp hạng tín dụng",

    # --- THÔNG TIN PHÁP LÝ (RÚT GỌN) ---
    "Ngày thành lập": "Dựa vào tên đầy đủ của khách hàng. Tìm ngày thành lập theo ĐKKD lần đầu tiên (không phải sửa đổi), format DD/MM/YYYY",
    "Địa chỉ trên ĐKKD": "Dựa vào tên đầy đủ của khách hàng. Tìm địa chỉ đầy đủ, chi tiết theo ĐKKD",
    "Người đại diện theo Pháp luật": "Dựa vào tên đầy đủ của khách hàng. Tìm họ tên người đại diện theo ĐKKD hoặc giấy đề nghị cấp TD",
    "Có kinh doanh Ngành nghề kinh doanh có điều kiện": "Dựa vào tên đầy đủ của khách hàng. Có kinh doanh ngành có điều kiện (an ninh quốc gia, có yếu tố nước ngoài, tài chính ngân hàng, y tế, giáo dục và đào tạo)? Có/Không",

    # --- NHẬN XÉT (SUY LUẬN - ĐÃ TỐI ƯU) ---
    "Nhận xét - Thông tin khách hàng": "Dựa vào tên đầy đủ của khách hàng. Tóm tắt: năm thành lập, số năm hoạt động, lĩnh vực, sản phẩm chính. Tạo thành 1 đoạn văn ngắn 1,2 câu",
    "Nhận xét - Pháp lý/GPKD có ĐK": "Dựa vào tên đầy đủ của khách hàng. Tóm tắt: số ĐKKD, ngày cấp lần đầu, cơ quan cấp, các lần thay đổi. Tạo thành 1 đoạn văn ngắn 1,2 câu",
    "Nhận xét - Chủ doanh nghiệp/Ban lãnh đạo": "Dựa vào tên đầy đủ của khách hàng. Nhận xét về chủ doanh nghiệp, kinh nghiệm, thành tích, khả năng quản lý của công ty này với những thông tin được cung cấp. Tạo thành 1 đoạn văn ngắn 1,2 câu",
    "Nhận xét - KYC": "Dựa vào tên đầy đủ của khách hàng. Đánh giá chủ quan về tình trạng hoạt động ổn định của DN. Tạo thành 1 đoạn văn ngắn 1,2 câu",

    # --- HOẠT ĐỘNG KINH DOANH (ĐÃ RÚT GỌN) ---
    "Lĩnh vực kinh doanh": "Dựa vào tên đầy đủ của khách hàng. Tìm lĩnh vực chung: Xây lắp, Thương mại, Sản xuất, Dịch vụ...",
    "Sản phẩm/Dịch vụ": "Dựa vào tên đầy đủ của khách hàng. Liệt kê sản phẩm/dịch vụ cụ thể, chi tiết",
    "Tỷ trọng doanh thu năm N-1 (%)": "Dựa vào tên đầy đủ của khách hàng. Tìm % doanh thu năm N-1",
    "Tỷ trọng doanh thu năm N (%)": "Dựa vào tên đầy đủ của khách hàng. Tìm % doanh thu năm N",
    "Nhóm mặt hàng": "Dựa vào tên đầy đủ của khách hàng. Liệt kê các nhóm mặt hàng kinh doanh",
    "Tỷ trọng doanh thu 2023": "Dựa vào tên đầy đủ của khách hàng. Tìm % doanh thu năm 2023",
    "Tỷ trọng doanh thu 10T/2024": "Dựa vào tên đầy đủ của khách hàng. Tìm % doanh thu 10 tháng 2024",
    "Mô tả chung sản phẩm": "Dựa vào tên đầy đủ của khách hàng. Mô tả chi tiết sản phẩm đầu ra",
    "Mô tả lợi thế cạnh tranh": "Dựa vào tên đầy đủ của khách hàng. Tìm lợi thế so với đối thủ",
    "Mô tả năng lực đấu thầu": "Dựa vào tên đầy đủ của khách hàng. Tìm chi tiết: tham gia bao nhiêu gói, trúng bao nhiêu, trượt bao nhiêu, chờ KQ",
    "Quy trình vận hành (tóm tắt)": "Dựa vào tên đầy đủ của khách hàng. Mô tả cơ bản quy trình sản xuất/vận hành từ call report",
    "Đầu vào - Mặt hàng": "Dựa vào tên đầy đủ của khách hàng. Liệt kê từng loại nguyên vật liệu đầu vào cụ thể",
    "Đầu vào - Chi tiết": "Dựa vào tên đầy đủ của khách hàng. Nguồn mua: từ đâu, nhà cung cấp nào",
    "Đầu vào - Phương thức thanh toán": "Dựa vào tên đầy đủ của khách hàng. PTTT với nhà cung cấp + thời hạn thanh toán",
    "Đầu ra - Kênh phân phối": "Dựa vào tên đầy đủ của khách hàng. Các kênh bán hàng, phân phối cụ thể",
    "Đầu ra - Tỷ trọng": "Dựa vào tên đầy đủ của khách hàng. % tỷ trọng theo từng kênh phân phối",
    "Đầu ra - Phương thức thanh toán": "Dựa vào tên đầy đủ của khách hàng. PTTT của khách hàng + thời hạn thanh toán",
    "Nhận xét tổng quan hoạt động kinh doanh": "Dựa vào tên đầy đủ của khách hàng. Nhận xét: pháp lý, quy mô, kế hoạch tương lai. Tạo thành 1 đoạn văn ngắn 1,2 câu",

    # --- THÔNG TIN NGÀNH (RÚT GỌN) ---
    "Phân tích cung cầu ngành": "Dựa vào tên đầy đủ của khách hàng. Tìm phân tích cung cầu ngành. Tạo thành 1 đoạn văn ngắn 1,2 câu",
    "Nhận xét thông tin ngành": "Dựa vào tên đầy đủ của khách hàng. Tìm nhận xét về ngành. Tạo thành 1 đoạn văn ngắn 1,2 câu"
}

def _clean_llm_response(raw_response: Any) -> Any:
    """
    Làm sạch output thô từ LLM để lấy giá trị cốt lõi.
    - Cố gắng parse JSON nếu output là string chứa JSON.
    - Loại bỏ các ký tự không cần thiết và văn bản giới thiệu.
    """
    if not isinstance(raw_response, str):
        return raw_response # Trả về nguyên bản nếu không phải là chuỗi (ví dụ: đã là list)

    response_str = raw_response.strip()

    # Ưu tiên 1: Cố gắng tìm và parse JSON array hoặc object
    try:
        # Sử dụng regex để tìm cấu trúc JSON đầu tiên trong chuỗi
        json_match = re.search(r'(\[.*\]|\{.*\})', response_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            # Cố gắng load nó thành đối tượng Python
            return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        # Nếu thất bại, tiếp tục các bước làm sạch văn bản
        pass

    # Ưu tiên 2: Làm sạch văn bản đơn giản
    # Loại bỏ các tiền tố phổ biến
    prefixes_to_remove = [
        "Trả lời:", "Câu trả lời là:", "Đây là câu trả lời:", "Kết quả là:",
        "Dữ liệu trích xuất được là:", "The answer is:", "Answer:"
    ]
    for prefix in prefixes_to_remove:
        if response_str.lower().startswith(prefix.lower()):
            response_str = response_str[len(prefix):].strip()

    # Loại bỏ dấu ngoặc kép hoặc nháy đơn ở đầu và cuối nếu có
    if response_str.startswith(('"', "'")) and response_str.endswith(('"', "'")):
        response_str = response_str[1:-1]
        
    return response_str.strip()

def create_context_session():
    """Tạo session ID unique cho mỗi lần chạy extraction"""
    session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    session_dir = os.path.join(CONTEXT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    return session_id, session_dir

def save_field_context(session_dir: str, field_name: str, prompt: str, raw_response: str, cleaned_response: str):
    """Lưu context của một trường được trích xuất (đã đơn giản hóa)."""
    
    context_data = {
        "timestamp": datetime.now().isoformat(),
        "field_name": field_name,
        "prompt": prompt,
        "raw_response_from_rag": raw_response,
        "cleaned_response": cleaned_response,
        "prompt_word_count": len(prompt.split()),
        "response_word_count": len(str(cleaned_response).split())
    }
    
    # Tạo tên file an toàn
    safe_field_name = re.sub(r'[^\w\-_]', '_', field_name)
    filename = f"{safe_field_name}.json"
    filepath = os.path.join(session_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(context_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Đã lưu tóm tắt trích xuất: {filename}")

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
        print(f"⚠️ Lỗi khi đọc schema file: {e}")
        return {"fields": [], "mapping": {}}

def structure_data_for_loan_assessment_report(flat_data: Dict, mapping: Dict) -> Dict:
    """
    Chuyển đổi dữ liệu phẳng từ LLM thành cấu trúc JSON lồng nhau cho Template 4 (Báo cáo thẩm định).
    Đã cập nhật để xử lý 3 loại bảng: ban lãnh đạo, đầu vào, đầu ra.
    """
    print(f"\n🏗️ BẮT ĐẦU CẤU TRÚC LẠI DỮ LIỆU...")
    print(f"📥 Input có {len(flat_data)} trường dữ liệu thô")
    
    # Khởi tạo cấu trúc dữ liệu chính xác theo template4.json
    structured_data = {
        "thongTinChung": {
            "tenKhachHang": "",
            "giayPhep": "",
            "idT24": "",
            "phanKhuc": "",
            "loaiKhachHang": "",
            "nganhNghe": "",
            "mucDichBaoCao": "",
            "ketQuaPhanLuong": "",
            "xhtd": ""
        },
        "thongTinKhachHang": {
            "phapLy": {
                "ngayThanhLap": "",
                "diaChi": "",
                "nguoiDaiDien": "",
                "nganhNgheCoDieuKien": ""
            },
            "banLanhDao": [],
            "nhanXet": {
                "thongTinChung": "",
                "phapLyGpkd": "",
                "chuDoanhNghiep": "",
                "kyc": ""
            }
        },
        "hoatDongKinhDoanh": {
            "linhVuc": {
                "linhVuc": "",
                "sanPham": "",
                "tyTrongN1": "",
                "tyTrongN": ""
            },
            "tyTrongTheoNhomHang": {
                "nhomHang": "",
                "nam2023": "",
                "nam10T2024": ""
            },
            "moTaSanPham": {
                "sanPham": "",
                "loiThe": "",
                "nangLucDauThau": ""
            },
            "quyTrinhVanHanhText": "",
            "dauVao": [],
            "dauRa": [],
            "nhanXetHoatDong": ""
        },
        "thongTinNganh": {
            "cungCau": "",
            "nhanXet": ""
        }
    }
    
    # === XỬ LÝ DỮ LIỆU BẢNG TRƯỚC ===
    print(f"📋 Xử lý dữ liệu bảng...")
    
    # 1. Bảng Ban lãnh đạo (5 cột)
    leadership_list = flat_data.get("thong_tin_ban_lanh_dao_day_du", [])
    # Xử lý trường hợp dữ liệu không phải là list
    if not isinstance(leadership_list, list):
        try:
            if isinstance(leadership_list, str) and leadership_list.strip():
                leadership_list = json.loads(leadership_list)
            else:
                leadership_list = []
        except:
            leadership_list = []
    
    if isinstance(leadership_list, list) and leadership_list:
        structured_data["thongTinKhachHang"]["banLanhDao"] = leadership_list
        print(f"  ✓ Bảng Ban lãnh đạo: {len(leadership_list)} dòng")
    else:
        print(f"  ✗ Bảng Ban lãnh đạo: Không có dữ liệu")
        structured_data["thongTinKhachHang"]["banLanhDao"] = []

    # 2. Bảng Đầu vào (3 cột)
    input_list = flat_data.get("thong_tin_dau_vao_day_du", [])
    # Xử lý trường hợp dữ liệu không phải là list
    if not isinstance(input_list, list):
        try:
            if isinstance(input_list, str) and input_list.strip():
                input_list = json.loads(input_list)
            else:
                input_list = []
        except:
            input_list = []
    
    if isinstance(input_list, list) and input_list:
        structured_data["hoatDongKinhDoanh"]["dauVao"] = input_list
        print(f"  ✓ Bảng Đầu vào: {len(input_list)} dòng")
    else:
        print(f"  ✗ Bảng Đầu vào: Không có dữ liệu")
        structured_data["hoatDongKinhDoanh"]["dauVao"] = []

    # 3. Bảng Đầu ra (3 cột) 
    output_list = flat_data.get("thong_tin_dau_ra_day_du", [])
    # Xử lý trường hợp dữ liệu không phải là list
    if not isinstance(output_list, list):
        try:
            if isinstance(output_list, str) and output_list.strip():
                output_list = json.loads(output_list)
            else:
                output_list = []
        except:
            output_list = []
    
    if isinstance(output_list, list) and output_list:
        structured_data["hoatDongKinhDoanh"]["dauRa"] = output_list
        print(f"  ✓ Bảng Đầu ra: {len(output_list)} dòng")
    else:
        print(f"  ✗ Bảng Đầu ra: Không có dữ liệu")
        structured_data["hoatDongKinhDoanh"]["dauRa"] = []

    # === XỬ LÝ CÁC TRƯỜNG CÒN LẠI ===
    print(f"📝 Xử lý các trường đơn lẻ...")
    
    # Ánh xạ trực tiếp theo template4.json
    # Thông tin chung
    structured_data["thongTinChung"]["tenKhachHang"] = flat_data.get("Tên đầy đủ của khách hàng", "")
    structured_data["thongTinChung"]["giayPhep"] = flat_data.get("Giấy ĐKKD/GP đầu tư", "")
    structured_data["thongTinChung"]["idT24"] = flat_data.get("ID trên T24", "")
    structured_data["thongTinChung"]["phanKhuc"] = flat_data.get("Phân khúc", "")
    structured_data["thongTinChung"]["loaiKhachHang"] = flat_data.get("Loại khách hàng", "")
    structured_data["thongTinChung"]["nganhNghe"] = flat_data.get("Ngành nghề HĐKD theo ĐKKD", "")
    structured_data["thongTinChung"]["mucDichBaoCao"] = flat_data.get("Mục đích báo cáo", "")
    structured_data["thongTinChung"]["ketQuaPhanLuong"] = flat_data.get("Kết quả phân luồng", "")
    structured_data["thongTinChung"]["xhtd"] = flat_data.get("XHTD", "")
    
    # Thông tin khách hàng - Pháp lý
    structured_data["thongTinKhachHang"]["phapLy"]["ngayThanhLap"] = flat_data.get("Ngày thành lập", "")
    structured_data["thongTinKhachHang"]["phapLy"]["diaChi"] = flat_data.get("Địa chỉ trên ĐKKD", "")
    structured_data["thongTinKhachHang"]["phapLy"]["nguoiDaiDien"] = flat_data.get("Người đại diện theo Pháp luật", "")
    structured_data["thongTinKhachHang"]["phapLy"]["nganhNgheCoDieuKien"] = flat_data.get("Có kinh doanh Ngành nghề kinh doanh có điều kiện", "")
    
    # Thông tin khách hàng - Nhận xét
    structured_data["thongTinKhachHang"]["nhanXet"]["thongTinChung"] = flat_data.get("Nhận xét - Thông tin khách hàng", "")
    structured_data["thongTinKhachHang"]["nhanXet"]["phapLyGpkd"] = flat_data.get("Nhận xét - Pháp lý/GPKD có ĐK", "")
    structured_data["thongTinKhachHang"]["nhanXet"]["chuDoanhNghiep"] = flat_data.get("Nhận xét - Chủ doanh nghiệp/Ban lãnh đạo", "")
    structured_data["thongTinKhachHang"]["nhanXet"]["kyc"] = flat_data.get("Nhận xét - KYC", "")
    
    # Hoạt động kinh doanh - Lĩnh vực
    structured_data["hoatDongKinhDoanh"]["linhVuc"]["linhVuc"] = flat_data.get("Lĩnh vực kinh doanh", "")
    structured_data["hoatDongKinhDoanh"]["linhVuc"]["sanPham"] = flat_data.get("Sản phẩm/Dịch vụ", "")
    structured_data["hoatDongKinhDoanh"]["linhVuc"]["tyTrongN1"] = flat_data.get("Tỷ trọng doanh thu năm N-1 (%)", "")
    structured_data["hoatDongKinhDoanh"]["linhVuc"]["tyTrongN"] = flat_data.get("Tỷ trọng doanh thu năm N (%)", "")
    
    # Hoạt động kinh doanh - Tỷ trọng theo nhóm hàng
    structured_data["hoatDongKinhDoanh"]["tyTrongTheoNhomHang"]["nhomHang"] = flat_data.get("Nhóm mặt hàng", "")
    structured_data["hoatDongKinhDoanh"]["tyTrongTheoNhomHang"]["nam2023"] = flat_data.get("Tỷ trọng doanh thu 2023", "")
    structured_data["hoatDongKinhDoanh"]["tyTrongTheoNhomHang"]["nam10T2024"] = flat_data.get("Tỷ trọng doanh thu 10T/2024", "")
    
    # Hoạt động kinh doanh - Mô tả sản phẩm
    structured_data["hoatDongKinhDoanh"]["moTaSanPham"]["sanPham"] = flat_data.get("Mô tả chung sản phẩm", "")
    structured_data["hoatDongKinhDoanh"]["moTaSanPham"]["loiThe"] = flat_data.get("Mô tả lợi thế cạnh tranh", "")
    structured_data["hoatDongKinhDoanh"]["moTaSanPham"]["nangLucDauThau"] = flat_data.get("Mô tả năng lực đấu thầu", "")
    
    # Hoạt động kinh doanh - Quy trình vận hành
    structured_data["hoatDongKinhDoanh"]["quyTrinhVanHanhText"] = flat_data.get("Quy trình vận hành (tóm tắt)", "")
    structured_data["hoatDongKinhDoanh"]["nhanXetHoatDong"] = flat_data.get("Nhận xét tổng quan hoạt động kinh doanh", "")
    
    # Thông tin ngành
    structured_data["thongTinNganh"]["cungCau"] = flat_data.get("Phân tích cung cầu ngành", "")
    structured_data["thongTinNganh"]["nhanXet"] = flat_data.get("Nhận xét thông tin ngành", "")
    
    print(f"✅ Hoàn tất cấu trúc dữ liệu!")
    return structured_data

def truncate_text_by_words(text: str, max_words: int) -> str:
    """
    Cắt ngắn văn bản theo số lượng từ tối đa.
    Ưu tiên giữ lại phần đầu của prompt để không mất thông tin quan trọng.
    """
    words = text.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words])
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

def _get_answer_from_rag(question_prompt: str, collection_name: str, session_dir: str) -> str:
    """
    Hàm bao bọc mới để gọi trực tiếp logic RAG nội bộ.
    Nó sẽ truyền session_dir để có thể ghi log chi tiết.
    """
    print(f"  - 🧠 Gọi RAG nội bộ (collection: '{collection_name}')")
    try:
        # Gọi thẳng hàm query_rag_flow từ rag_client.py
        # Truyền session_dir vào context_dir để RAG có thể ghi log
        answer = query_rag_flow(
            question=question_prompt,
            collection_name=collection_name,
            context_dir=session_dir 
        )
        return answer
    except Exception as e:
        print(f"  - ❌ Lỗi khi đang gọi RAG nội bộ: {e}")
        # In traceback để debug dễ hơn
        traceback.print_exc()
        return ""

async def extract_information_from_docs(prompt: str, file_ids: List[str], collection_name: str, template_id: str) -> Dict:
    """
    Trích xuất thông tin từ tài liệu với logic mới, đã được sửa lỗi và tối ưu hóa.
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
    table_fields_to_run = []
    if template_id == 'template4':
        prompt_dictionary = TEMPLATE4_DETAILED_PROMPTS
        table_fields_to_run = TABLE_FIELDS_TEMPLATE4
    else:
        # Tạo prompt mặc định cho các template khác
        prompt_dictionary = {field: f"Trích xuất thông tin về: {field}" for field in fields_to_extract}

    # Phân loại các trường: bảng và không phải bảng
    non_table_fields = [f for f in fields_to_extract if f not in table_fields_to_run]
    
    total_fields = len(non_table_fields) + len(table_fields_to_run)
    print(f"🚀 Bắt đầu trích xuất cho {total_fields} trường:")
    print(f"   - {len(non_table_fields)} trường đơn lẻ")
    print(f"   - {len(table_fields_to_run)} trường bảng")
    
    current_field_count = 0
    
    # --- XỬ LÝ CÁC TRƯỜNG ĐƠN LẺ ---
    if non_table_fields:
        print(f"\n🔎 Trích xuất {len(non_table_fields)} trường đơn lẻ...")
        
        for field in non_table_fields:
            current_field_count += 1
            field_prompt = prompt_dictionary.get(field, f"Trích xuất thông tin về: {field}")
            
            print(f"\n[{current_field_count}/{total_fields}] 🔍 Đang trích xuất: {field}")
            try:
                raw_result = _get_answer_from_rag(field_prompt, collection_name, session_dir)
                cleaned_result = _clean_llm_response(raw_result)
                
                if is_valid_value(cleaned_result):
                    final_result[field] = cleaned_result
                    success_count += 1
                    print(f"  - ✅ Trích xuất thành công")
                    save_field_context(session_dir, field, field_prompt, str(raw_result), str(cleaned_result))
                else:
                    error_count += 1
                    final_result[field] = ""
                    print(f"  - ⚠️ Kết quả không hợp lệ hoặc rỗng")
                
                time.sleep(FIELD_PROCESSING_DELAY)
                
            except Exception as e:
                error_count += 1
                final_result[field] = ""
                print(f"  - ❌ Lỗi khi xử lý trường '{field}': {str(e)}")

    # --- XỬ LÝ CÁC TRƯỜNG BẢNG ---
    if table_fields_to_run:
        print(f"\n📊 Trích xuất {len(table_fields_to_run)} trường bảng...")
        
        for field in table_fields_to_run:
            current_field_count += 1
            table_prompt = prompt_dictionary.get(field)
            
            if not table_prompt:
                print(f"\n[{current_field_count}/{total_fields}] ⚠️ Không có prompt cho bảng: {field}")
                final_result[field] = []
                error_count += 1
                continue
                
            print(f"\n[{current_field_count}/{total_fields}] 📋 Đang trích xuất bảng: {field}")
            
            try:
                ## BUG FIX: Sử dụng 'table_prompt' thay vì 'field_prompt'
                raw_result = _get_answer_from_rag(table_prompt, collection_name, session_dir)
                cleaned_result = _clean_llm_response(raw_result)
                
                ## OPTIMIZATION: Đơn giản hóa logic parse vì _clean_llm_response đã làm việc này
                parsed_result = []
                if isinstance(cleaned_result, list):
                    parsed_result = cleaned_result
                
                # Lưu kết quả
                final_result[field] = parsed_result
                
                if parsed_result:
                    success_count += 1
                    print(f"  - ✅ Trích xuất thành công: {len(parsed_result)} mục")
                    save_field_context(session_dir, field, table_prompt, str(raw_result), str(parsed_result))
                else:
                    error_count += 1
                    print(f"  - ⚠️ Không tìm thấy dữ liệu bảng hoặc không parse được")
                
                time.sleep(TABLE_PROCESSING_DELAY)
                    
            except Exception as e:
                error_count += 1
                final_result[field] = []
                print(f"  - ❌ Lỗi khi trích xuất bảng '{field}': {str(e)}")

    print(f"\n\n✅ Hoàn tất trích xuất {total_fields} trường!")
    print(f"   - Thành công: {success_count} trường")
    print(f"   - Lỗi: {error_count} trường")
    print(f"   - Tỷ lệ thành công: {(success_count/total_fields*100):.1f}%" if total_fields > 0 else "0%")
    
    save_session_summary(session_dir, session_id, total_fields, success_count, error_count)

    print(f"\n📋 CHI TIẾT KẾT QUẢ TRÍCH XUẤT:")
    print("=" * 80)
    
    successful_fields = []
    failed_fields = []
    
    for field, value in final_result.items():
        if is_valid_value(value):
            successful_fields.append(field)
        else:
            failed_fields.append(field)
    
    print(f"\n📊 THỐNG KÊ:")
    print(f"   - Thành công: {len(successful_fields)}/{total_fields} trường")
    print(f"   - Thất bại: {len(failed_fields)}/{total_fields} trường")
    
    if failed_fields:
        print(f"   - Các trường thất bại: {', '.join(failed_fields)}")

    if template_id == "template4":
        return structure_data_for_loan_assessment_report(final_result, mapping)
    
    return final_result
