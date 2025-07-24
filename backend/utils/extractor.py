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



FLEXIBLE_TABLE_PROMPT_LEADERSHIP = """
**Nhiệm vụ:** Tìm và trích xuất thông tin về ban lãnh đạo, cổ đông, hoặc thành viên góp vốn từ các bảng trong tài liệu.

**Yêu cầu:**
1.  Tìm bất kỳ bảng nào có chứa thông tin về danh sách cá nhân liên quan đến công ty.
2.  Các cột trong bảng có thể có tên khác nhau. Nhiệm vụ của bạn là nhận diện và mapping chúng một cách thông minh vào các key chuẩn sau: `ten`, `tyLeVon`, `chucVu`, `cccd`.
    *   `ten`: Có thể đến từ cột có header là 'Họ tên', 'Tên thành viên góp vốn/ban lãnh đạo', hoặc tương tự.
    *   `tyLeVon`: Có thể đến từ cột 'Tỷ lệ góp vốn', '% góp vốn', hoặc tương tự.
    *   `chucVu`: Có thể đến từ cột 'Chức vụ'. Nếu cột này không tồn tại trong bảng, hãy trả về giá trị `null`.
    *   `cccd`: Có thể đến từ cột 'CCCD/CMND/Hộ chiếu'. Nếu không có, trả về `null`.
3.  Trích xuất thông tin của TẤT CẢ các thành viên trong bảng.
4.  Trả về một đối tượng JSON duy nhất có key là "leadership_data" và value là một MẢNG (array) các đối tượng.

**Ví dụ 1 (Bảng có đầy đủ thông tin):**
Nếu bảng có dạng:
| Tên thành viên góp vốn/ban lãnh đạo | Tỷ lệ vốn góp (%) | Chức vụ       |
|------------------------------------|--------------------|---------------|
| Đào Công Duy                       | 90%                | Tổng giám đốc |
Kết quả phải là:
{ "leadership_data": [{ "ten": "Đào Công Duy", "tyLeVon": "90%", "chucVu": "Tổng giám đốc", "cccd": null }] }

**Ví dụ 2 (Bảng thiếu thông tin 'Chức vụ'):**
Nếu bảng có dạng:
| Họ tên         | CCCD/CMND/Hộ chiếu | Tỷ lệ góp vốn |
|----------------|--------------------|----------------|
| Đào Công Duy   | 034067001074       | 90%            |
| Thái Thị Kim Dung | 040174000053       | 8%             |
Kết quả phải là:
{
  "leadership_data": [
    { "ten": "Đào Công Duy", "tyLeVon": "90%", "chucVu": null, "cccd": "034067001074" },
    { "ten": "Thái Thị Kim Dung", "tyLeVon": "8%", "chucVu": null, "cccd": "040174000053" }
  ]
}

Nếu không tìm thấy bảng nào phù hợp, trả về một mảng rỗng.
"""

# -- Kho prompt chi tiết cho từng trường riêng lẻ --
TEMPLATE4_DETAILED_PROMPTS = {
    
    '**system_prompt**: Lưu ý không được bịa thông tin, nếu không tìm thấy thông tin thì hãy trả về null.'
    # --- Phần Thông Tin Chung ---
    "Tên đầy đủ của khách hàng": "Trích xuất tên đầy đủ và hợp pháp của công ty khách hàng.",
    "Giấy ĐKKD/GP đầu tư": "Tìm và trích xuất số Giấy chứng nhận Đăng ký kinh doanh (ĐKKD) hoặc Giấy phép đầu tư.",
    "ID trên T24": "Tìm và trích xuất ID của khách hàng trên hệ thống T24.",
    "Phân khúc": "Tìm và trích xuất Phân khúc của khách hàng. Phân khúc có thể là một trong những keyword sau: 'MM', 'SME+', 'Micro', 'Small', 'Medium', 'LC', 'PS'. Nếu không có thì trả về null.",
    "Loại khách hàng": "Tìm thông tin về loại khách hàng. Các từ khóa có thể là 'ETC' (Exclusive Trading Company) hoặc 'OTC' (Over-the-counter). Nếu không có, trả về null.",
    "Ngành nghề HĐKD theo ĐKKD": "Trích xuất các ngành nghề hoạt động kinh doanh chính được ghi trên Giấy ĐKKD. Nếu không có thông tin hãy suy luận từ tên đầy đủ công ty. VÍ dụ: 'Xây dựng', 'Thương mại', 'Sản xuất'.",
    "Mục đích báo cáo": "Xác định mục đích của báo cáo thẩm định này là gì? Ví dụ: 'Cấp mới hạn mức tín dụng', 'Tái cấp tín dụng',...",
    "Kết quả phân luồng": "Tìm và trích xuất kết quả phân luồng của khách hàng. Ví dụ: 'Luồng chuẩn', 'Luồng thông thường', 'Luồng chuyên sâu'.",
    "XHTD": "Trích xuất Xếp hạng tín dụng (XHTD) gần nhất của khách hàng. Các giá trị có thể là: 'Aa3', 'Aa2', 'Aa1', 'A3', 'A2', 'A1', 'Baa3', 'Baa2', 'Baa1', 'Ba3', 'Ba2', 'Ba1', 'B3', 'B2', 'B1', 'Caa3', 'Caa2', 'Caa1'. Nếu không có, trả về null.",

    # --- Phần Thông Tin Khách Hàng - Pháp Lý ---
    "Ngày thành lập": "Tìm ngày thành lập của công ty. Trả về ngày tháng dưới dạng chuỗi có định dạng DD/MM/YYYY.",
    "Địa chỉ trên ĐKKD": "Trích xuất địa chỉ đầy đủ của công ty được ghi trên Giấy ĐKKD.",
    "Người đại diện theo Pháp luật": "Tìm và trích xuất tên đầy đủ của Người đại diện theo Pháp luật của công ty.",
    "Có kinh doanh Ngành nghề kinh doanh có điều kiện": """
    Dựa vào ngành nghề kinh doanh của công ty (có thể suy luận lại từ Ngành nghề HĐKD theo ĐKKD hoặc tên đầy đủ của công ty), hãy xác định xem công ty có hoạt động trong các ngành nghề kinh doanh có điều kiện theo pháp luật Việt Nam hay không.
    Một số ví dụ về ngành nghề có điều kiện: bất động sản, dịch vụ tài chính, sản xuất hóa chất, kinh doanh vận tải, giáo dục, y tế...
    Trả lời chỉ "Có" hoặc "Không".
    """,

    # --- Phần Thông Tin Khách Hàng - Nhận Xét (SUY LUẬN & TÓM TẮT) ---
    "Nhận xét - Thông tin khách hàng": """
    Dựa vào toàn bộ tài liệu, hãy viết một đoạn văn tóm tắt (2-4 câu) về thông tin khách hàng. Đoạn văn cần bao gồm các ý: 
    1. Công ty được thành lập năm nào và đã hoạt động bao lâu.
    2. Hoạt động trong lĩnh vực chính nào.
    3. Các sản phẩm hoặc dịch vụ cốt lõi là gì.
    """,
    "Nhận xét - Pháp lý/GPKD có ĐK": """
    Dựa vào thông tin trên Giấy ĐKKD, hãy tạo một câu nhận xét về tình trạng pháp lý, bao gồm các chi tiết:
    - Số giấy ĐKKD.
    - Cơ quan cấp.
    - Ngày cấp lần đầu.
    - Thông tin về lần đăng ký thay đổi gần nhất (nếu có).
    
    Ví dụ: '•	Công ty kinh doanh theo giấy ĐKKD số xxx cấp lần đầu ngày xxx do Sở kế hoạch và đầu tư cấp, ĐK thay đổi lần thứ x ngày xxx.
            •	Giấy chứng nhận đủ ĐK kinh doanh dược cấp ngày xxx
            •	Giấy chứng nhận thực  hành tốt phân phối thuốc (GDP) cấp ngày xxx'
    """,
    "Nhận xét - Chủ doanh nghiệp/Ban lãnh đạo": """
    Dựa vào số năm hoạt động của công ty và thông tin về ban lãnh đạo, hãy suy luận và đưa ra một nhận xét ngắn gọn (1-2 câu) về kinh nghiệm của họ trong ngành.
    Ví dụ: 'Với 20 năm hoạt động, ban lãnh đạo công ty cho thấy kinh nghiệm dày dặn trong lĩnh vực thi công nhôm kính.'
    """,
    "Nhận xét - KYC": "Tìm trong tài liệu phần nhận xét KYC (Know Your Customer). Đây thường là nhận xét chủ quan của người đi thẩm định. Nếu không tìm thấy, hãy trả về giá trị null.",
    
    # --- Phần Hoạt Động Kinh Doanh ---
    "Lĩnh vực kinh doanh": "Xác định lĩnh vực kinh doanh tổng quan của công ty. Ví dụ: 'Xây lắp', 'Thương mại', 'Sản xuất', Dịch vu xây lắp, lắp đặt",
    "Sản phẩm/Dịch vụ": "Liệt kê các sản phẩm hoặc dịch vụ mà công ty cung cấp một cách ngắn gọn. Ví dụ: Nhôm kính, mặt kính, vách kính mặt dựng tại các tòa nhà cao tầng,... ",
    "Tỷ trọng doanh thu năm N-1 (%)": "Tìm tỷ trọng doanh thu theo từng sản phẩm/dịch vụ của năm N-1 (năm trước).",
    "Tỷ trọng doanh thu năm N (%)": "Tìm tỷ trọng doanh thu theo từng sản phẩm/dịch vụ của năm N (năm hiện tại hoặc gần nhất).",
    "Nhóm mặt hàng": "Liệt kê các nhóm mặt hàng kinh doanh chính của công ty.",
    "Tỷ trọng doanh thu 2023": "Tìm tỷ trọng doanh thu theo nhóm mặt hàng của năm 2023.",
    "Tỷ trọng doanh thu 10T/2024": "Tìm tỷ trọng doanh thu theo nhóm mặt hàng trong 10 tháng đầu năm 2024.",
    "Mô tả chung sản phẩm": """
    Trích xuất đoạn văn mô tả chi tiết về sản phẩm, dịch vụ và khách hàng đầu ra của công ty. 
    Hãy chú ý đến các chi tiết như: sản phẩm là hàng may đo hay sản xuất hàng loạt, khách hàng là chủ đầu tư hay tổng thầu, loại công trình (dân dụng, nhà nước)...
    """,
    "Mô tả lợi thế cạnh tranh": "Tìm đoạn văn mô tả lợi thế cạnh tranh của công ty trên thị trường. Nếu không có, trả về null.",
    "Mô tả năng lực đấu thầu": "Tìm thông tin về năng lực đấu thầu của công ty, ví dụ: số lượng gói thầu đã tham gia, tỷ lệ trúng thầu. Nếu không có, trả về null.",
    "Quy trình vận hành (tóm tắt)": "Tìm và trích xuất đoạn văn mô tả quy trình vận hành hoặc sản xuất của công ty, từ khâu đầu vào đến khi ra thành phẩm.",
    "Đầu vào - Mặt hàng": "Liệt kê các loại nguyên vật liệu, hàng hóa đầu vào chính của công ty.",
    "Đầu vào - Chi tiết": "Trích xuất thông tin chi tiết về nguồn cung cấp đầu vào, ví dụ: 'nhập khẩu từ Trung Quốc', 'mua từ nhà cung cấp trong nước'.",
    "Đầu vào - Phương thức thanh toán": "Tìm phương thức và thời hạn thanh toán cho nhà cung cấp đầu vào. Nếu không có, trả về null.",
    "Đầu ra - Kênh phân phối": "Mô tả các kênh phân phối sản phẩm đầu ra của công ty.",
    "Đầu ra - Tỷ trọng": "Tìm tỷ trọng phân phối theo từng kênh đầu ra (nếu có).",
    "Đầu ra - Phương thức thanh toán": "Tìm phương thức và thời hạn thanh toán của khách hàng đầu ra. Nếu không có, trả về null.",
    "Nhận xét tổng quan hoạt động kinh doanh": "Dựa vào toàn bộ tài liệu, hãy viết một đoạn văn nhận xét tổng quan về hoạt động kinh doanh của công ty, bao gồm các điểm mạnh, điểm yếu, và kế hoạch tương lai.",
    
    # --- Phần Thông Tin Ngành ---
    "Phân tích cung cầu ngành": "Tìm đoạn văn phân tích về tình hình cung và cầu của ngành mà công ty đang hoạt động. Nếu không có, trả về null.",
    "Nhận xét thông tin ngành": "Trích xuất các nhận xét, đánh giá về ngành mà công ty đang hoạt động. Nếu không có, trả về null."
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
    if "thong_tin_ban_lanh_dao_day_du" in flat_data:
        leadership_list = flat_data.get("thong_tin_ban_lanh_dao_day_du", [])
        if leadership_list: # Chỉ xử lý nếu danh sách không rỗng
            # Cấu trúc lại thành dạng mà template mong muốn
            structured_data["thongTinKhachHang"]["banLanhDao"] = [
                {
                    "ten": member.get("ten", ""),
                    "tyLeVon": member.get("tyLeVon", ""),
                    "chucVu": member.get("chucVu", ""),
                    "mucDoAnhHuong": "", # Sẽ được điền sau nếu có logic
                    "danhGia": "" # Sẽ được điền sau nếu có logic
                }
                for member in leadership_list
            ]
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

# async def extract_information_from_docs(prompt: str, file_ids: List[str], collection_name: str, template_id: str) -> Dict:
#     """
#     Hàm chính điều khiển luồng trích xuất thông tin thông minh,
#     giờ đây nhận `collection_name` và `template_id` để query đúng và trích xuất đúng trường.
#     """
#     # Tải schema từ file JSON
#     schema = load_template_schema(template_id)
#     fields_to_extract = schema.get("fields", [])
#     mapping = schema.get("mapping", {})
    
#     print(f"📋 Sử dụng template '{template_id}' với {len(fields_to_extract)} trường cần trích xuất.")

#     final_result = {}
#     work_queue = [
#         fields_to_extract[i:i + INITIAL_BATCH_SIZE]
#         for i in range(0, len(fields_to_extract), INITIAL_BATCH_SIZE)
#     ]
#     current_iteration = 0
#     print(f"🚀 Bắt đầu quá trình trích xuất thông tin từ collection '{collection_name}' cho template '{template_id}'...")

#     while work_queue and current_iteration < MAX_ITERATIONS:
#         current_iteration += 1
#         current_batch = work_queue.pop(0)
        
#         print(f"\n--- VÒNG LẶP {current_iteration}/{MAX_ITERATIONS} | Đang xử lý lô {len(current_batch)} trường ---")
        
#         batch_prompt = create_prompt(current_batch)
        
#         # Chạy hàm requests đồng bộ trong một luồng riêng để không chặn vòng lặp sự kiện của FastAPI
#         loop = asyncio.get_event_loop()
#         # Truyền collection_name vào hàm query
#         response_json = await loop.run_in_executor(
#             None, query_langflow_for_json, batch_prompt, collection_name
#         )

#         newly_found_fields = []
#         if response_json:
#             for field in current_batch:
#                 if field in response_json and is_valid_value(response_json[field]):
#                     value = response_json[field]
#                     print(f"    ✅ Đã tìm thấy '{field}': {value}")
#                     final_result[field] = value
#                     newly_found_fields.append(field)
        
#         failed_fields = [f for f in current_batch if f not in newly_found_fields]
        
#         if failed_fields:
#             print(f"  - Không tìm thấy {len(failed_fields)} trường: {', '.join(failed_fields)}")
#             if len(failed_fields) >= MIN_BATCH_SIZE_TO_SPLIT:
#                 print(f"  -> Chia nhỏ lô thất bại...")
#                 mid_point = len(failed_fields) // 2
#                 first_half = failed_fields[:mid_point]
#                 second_half = failed_fields[mid_point:]
#                 work_queue.insert(0, second_half)
#                 work_queue.insert(0, first_half)
#             else:
#                 print(f"  -> Lô quá nhỏ, không chia nữa.")
        
#         await asyncio.sleep(1) # Có thể giảm thời gian sleep

#     print("\n\n✅ Quá trình trích xuất hoàn tất!")
    
#     # Cấu trúc lại dữ liệu dựa trên template_id
#     if template_id == "template2":
#         print("🔄 Cấu trúc lại dữ liệu cho Template2...")
#         structured_result = structure_data_for_new_template(final_result, mapping)
#         return structured_result
#     elif template_id == "template3":
#         print("🔄 Cấu trúc lại dữ liệu cho Template3...")
#         structured_result = structure_data_for_loan_assessment_report(final_result, mapping)
#         return structured_result
#     elif template_id == "template4":
#         print("🔄 Cấu trúc lại dữ liệu cho Template4...")
#         structured_result = structure_data_for_loan_assessment_report(final_result, mapping)
#         return structured_result

#     # Trả về kết quả cuối cùng dưới dạng một dictionary cho mẫu cũ
#     return final_result


async def extract_information_from_docs(prompt: str, file_ids: List[str], collection_name: str, template_id: str) -> Dict:
    schema = load_template_schema(template_id)
    fields_to_extract = schema.get("fields", [])
    mapping = schema.get("mapping", {})
    final_result = {} # Nơi lưu trữ dữ liệu phẳng (flat data) đã trích xuất

    # Xác định bộ prompt cần dùng cho template này
    prompt_dictionary = {}
    if template_id == 'template4':
        prompt_dictionary = TEMPLATE4_DETAILED_PROMPTS
    # (Bạn có thể thêm các bộ prompt cho template khác ở đây)
    
    # --- GIAI ĐOẠN 1: TRÍCH XUẤT CÁC TRƯỜNG ĐƠN GIẢN (BATCH) ---
    print("🚀 Bắt đầu Giai đoạn 1: Trích xuất theo lô các trường đơn giản...")
    
    # Lọc ra các trường đơn giản: không có trong kho prompt chi tiết và không thuộc bảng
    simple_fields = [
        f for f in fields_to_extract 
        if f not in prompt_dictionary 
        and f not in ["Tên thành viên góp vốn/ban lãnh đạo", "Tỷ lệ vốn góp (%)", "Chức vụ"]
    ]
    
    work_queue = [
        simple_fields[i:i + INITIAL_BATCH_SIZE]
        for i in range(0, len(simple_fields), INITIAL_BATCH_SIZE)
    ]
    # ... (Giữ nguyên logic lặp và query của bạn cho Giai đoạn 1) ...
    current_iteration = 0
    while work_queue and current_iteration < MAX_ITERATIONS:
        # (Code Giai đoạn 1 của bạn ở đây...)
        current_iteration += 1
        current_batch = work_queue.pop(0)
        
        print(f"\n--- Lô {current_iteration} | Đang xử lý {len(current_batch)} trường ---")
        batch_prompt = create_prompt(current_batch)
        
        loop = asyncio.get_event_loop()
        response_json = await loop.run_in_executor(None, query_langflow_for_json, batch_prompt, collection_name)

        if response_json:
            for field in current_batch:
                if field in response_json and is_valid_value(response_json[field]):
                    final_result[field] = response_json[field]
                    print(f"    ✅ (GĐ1) Đã tìm thấy: '{field}'")


    # --- GIAI ĐOẠN 2: TRÍCH XUẤT DỮ LIỆU BẢNG (NẾU CÓ) ---
    if template_id == 'template4':
        print("\n🚀 Bắt đầu Giai đoạn 2: Trích xuất thông tin dạng bảng (Linh hoạt)...")
        
        # Chúng ta không cần lọc file nữa, vì prompt này đủ thông minh để tìm đúng bảng
        # trong toàn bộ ngữ cảnh được cung cấp.
        
        loop = asyncio.get_event_loop()
        # SỬ DỤNG PROMPT MỚI
        table_response_json = await loop.run_in_executor(None, query_langflow_for_json, FLEXIBLE_TABLE_PROMPT_LEADERSHIP, collection_name)

        # Xử lý kết quả trả về từ prompt mới
        if table_response_json and "leadership_data" in table_response_json:
            members_data = table_response_json["leadership_data"]
            if isinstance(members_data, list) and members_data:
                print(f"    ✅ (GĐ2) Tìm thấy {len(members_data)} thành viên.")
                
                # Unpack dữ liệu từ mảng đối tượng vào các key phẳng của final_result
                # Chúng ta sẽ giữ lại cấu trúc mảng để tiện xử lý ở frontend
                final_result["thong_tin_ban_lanh_dao_day_du"] = members_data

                # Để tương thích với logic cũ, bạn cũng có thể tạo các danh sách riêng lẻ
                final_result["Tên thành viên góp vốn/ban lãnh đạo"] = [m.get("ten") for m in members_data]
                final_result["Tỷ lệ vốn góp (%)"] = [m.get("tyLeVon") for m in members_data]
                final_result["Chức vụ"] = [m.get("chucVu") for m in members_data]
                # Thêm trường mới nếu cần
                final_result["CCCD/CMND/Hộ chiếu"] = [m.get("cccd") for m in members_data]

            else:
                print("    ❌ (GĐ2) Không tìm thấy dữ liệu ban lãnh đạo.")
    
    # --- GIAI ĐOẠN 3: TRÍCH XUẤT CÁC TRƯỜNG CHI TIẾT/SUY LUẬN ---
    print("\n🚀 Bắt đầu Giai đoạn 3: Trích xuất các trường chi tiết và suy luận...")
    detailed_fields_to_run = [f for f in fields_to_extract if f in prompt_dictionary]

    for field in detailed_fields_to_run:
        # Chạy ngay cả khi đã tìm thấy ở Giai đoạn 1, vì GĐ3 có prompt chất lượng hơn
        print(f"  -> Đang xử lý chi tiết trường: '{field}'")
        prompt_template = prompt_dictionary[field]
        
        # Tạo prompt cuối cùng yêu cầu trả về JSON
        final_prompt = f"Dựa vào tài liệu, hãy thực hiện yêu cầu sau: '{prompt_template}'. Trả về một đối tượng JSON với key là '{field}' và value là kết quả tìm được."
        
        loop = asyncio.get_event_loop()
        response_json = await loop.run_in_executor(None, query_langflow_for_json, final_prompt, collection_name)

        if response_json and field in response_json and is_valid_value(response_json[field]):
            final_result[field] = response_json[field] # Ghi đè kết quả từ GĐ1 nếu có
            print(f"    ✅ (GĐ3) Đã tìm thấy: '{field}'")
        else:
            # Nếu GĐ3 không tìm thấy, nhưng GĐ1 đã tìm thấy, thì giữ lại kết quả GĐ1
            if field not in final_result:
                 print(f"    ❌ (GĐ3) Không tìm thấy: '{field}'")
                 final_result[field] = None # Ghi nhận là không tìm thấy
            else:
                 print(f"    ℹ️ (GĐ3) Không tìm thấy, giữ lại kết quả từ GĐ1 cho trường: '{field}'")

        await asyncio.sleep(0.5) 

    print("\n\n✅ Quá trình trích xuất 3 giai đoạn hoàn tất!")

    # --- CUỐI CÙNG: CẤU TRÚC LẠI DỮ LIỆU ---
    # Bạn cần tự định nghĩa hàm này để sắp xếp `final_result` phẳng thành JSON lồng nhau theo `mapping`
    if template_id == "template4":
        return structure_data_for_loan_assessment_report(final_result, mapping)
        
    return final_result