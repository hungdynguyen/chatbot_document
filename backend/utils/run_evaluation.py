import os
import json
import requests
import pandas as pd
import time
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from deepdiff import DeepDiff
from datetime import datetime
# --- 1. CẤU HÌNH ---
BACKEND_URL = "http://localhost:8000"
DOCS_DIRECTORY = "/home/locmt/Techcombank_/chatbot_document/data/data_real" 
GROUND_TRUTH_PATH = "/home/locmt/Techcombank_/chatbot_document/backend/schemas/ground_truth_template4.json" 

# Thư mục lưu trữ kết quả evaluation
BASE_EVALUATION_DIR = "/home/locmt/Techcombank_/chatbot_document/evaluation_results"
REPORTS_DIR = os.path.join(BASE_EVALUATION_DIR, "reports")
RAW_DATA_DIR = os.path.join(BASE_EVALUATION_DIR, "raw_data")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(RAW_DATA_DIR, exist_ok=True)

SOURCE_FILES_FOR_TEST = [
    "call-rp.xlsx",
    "DN HMTD CAG 2024 (1).docx",
    "MB01-HD.SPDN_43 - Hỗ Trợ Phân Nhóm Khách Hàng (1).xlsx",
    "SO-SÁNH-DN-CÙNG-NGÀNH.docx",
    # "DKKD lan 8 ngay 12.04.2023.pdf" # Thêm file này nếu có
]

# Cấu hình Ragas (khớp với embedding_handler.py)
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


# --- 2. CÁC HÀM TÍNH TOÁN METRICS ---

def calculate_extraction_accuracy(ground_truth_json, extracted_json):
    """
    Sử dụng DeepDiff để so sánh 2 JSON và tính toán độ chính xác.
    Metric quan trọng nhất của bạn.
    """
    diff = DeepDiff(ground_truth_json, extracted_json, ignore_order=True, verbose_level=0)
    
    total_fields = 0
    correct_fields = 0

    def count_fields(d):
        count = 0
        for k, v in d.items():
            if isinstance(v, dict):
                count += count_fields(v)
            elif isinstance(v, list):
                # Coi mỗi item trong list là 1 field
                count += len(v) if v else 1 
            else:
                count += 1
        return count

    total_fields = count_fields(ground_truth_json)
    
    # Số trường bị sai là tổng số thay đổi, thêm, bớt
    errors = len(diff.get('values_changed', {})) + \
             len(diff.get('dictionary_item_added', {})) + \
             len(diff.get('dictionary_item_removed', {}))
    
    correct_fields = total_fields - errors
    accuracy = (correct_fields / total_fields) * 100 if total_fields > 0 else 0
    
    return accuracy, diff

def generate_ragas_dataset(ground_truth_json, extracted_json, collection_name):
    """
    Tạo dataset cho Ragas từ ground truth và kết quả trích xuất.
    """
    ragas_data = {"question": [], "answer": [], "contexts": [], "ground_truths": []}
    
    # Helper function để duyệt qua JSON lồng nhau
    def flatten_and_ask(node, path=""):
        for key, value in node.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                flatten_and_ask(value, current_path)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                 # Xử lý cho bảng (ví dụ banLanhDao)
                 question = f"Hãy cung cấp thông tin chi tiết về: {current_path}"
                 ground_truth_answer = json.dumps(value, ensure_ascii=False)
                 extracted_answer_obj = extracted_json
                 for p in current_path.split('.'): extracted_answer_obj = extracted_answer_obj.get(p, {})
                 extracted_answer = json.dumps(extracted_answer_obj, ensure_ascii=False)
                 contexts = retrieve_contexts(question, collection_name)

                 ragas_data["question"].append(question)
                 ragas_data["answer"].append(extracted_answer)
                 ragas_data["contexts"].append(contexts)
                 ragas_data["ground_truths"].append([ground_truth_answer])
            elif value is not None:
                question = f"Thông tin về '{current_path}' là gì?"
                ground_truth_answer = str(value)
                
                extracted_answer_obj = extracted_json
                try:
                    for p in current_path.split('.'): extracted_answer_obj = extracted_answer_obj.get(p, "")
                except:
                    extracted_answer_obj = ""

                extracted_answer = str(extracted_answer_obj)
                contexts = retrieve_contexts(question, collection_name)

                ragas_data["question"].append(question)
                ragas_data["answer"].append(extracted_answer)
                ragas_data["contexts"].append(contexts)
                ragas_data["ground_truths"].append([ground_truth_answer])

    flatten_and_ask(ground_truth_json)
    return Dataset.from_dict(ragas_data)

def retrieve_contexts(question, collection_name):
    """Truy xuất ngữ cảnh từ Qdrant (cần cho Ragas)."""
    try:
        query_vector = embedding_model.embed_query(question)
        hits = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=10 # Phải khớp với Number of Results trong Langflow
        )
        return [hit.payload["page_content"] for hit in hits]
    except Exception as e:
        print(f"Lỗi khi truy xuất ngữ cảnh từ Qdrant: {e}")
        return []
    

def save_evaluation_results(accuracy, latency, ragas_scores, diff_details, extracted_json, ground_truth_json):
    """Lưu kết quả evaluation vào file Excel với timestamp."""
    
    # Tạo timestamp cho tên file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_report_{timestamp}.xlsx"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    # Chuẩn bị dữ liệu cho các sheet
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        
        # Sheet 1: Summary Metrics
        hallucination_rate = 1.0 - ragas_scores.get('faithfulness', 0)
        summary_data = {
            "Metric": [
                "Extraction Accuracy (%)",
                "End-to-End Latency (s)",
                "Faithfulness",
                "Context Precision", 
                "Context Recall",
                "Answer Relevancy",
                "Hallucination Rate (%)"
            ],
            "Score": [
                f"{accuracy:.2f}",
                f"{latency:.2f}",
                f"{ragas_scores.get('faithfulness', 0):.4f}",
                f"{ragas_scores.get('context_precision', 0):.4f}",
                f"{ragas_scores.get('context_recall', 0):.4f}",
                f"{ragas_scores.get('answer_relevancy', 0):.4f}",
                f"{hallucination_rate:.2%}"
            ],
            "Timestamp": [timestamp] * 7,
            "Template": ["template4"] * 7
        }
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: Detailed Comparison
        comparison_data = []
        
        def flatten_json_for_comparison(gt_node, ext_node, path=""):
            """Flatten JSON để so sánh chi tiết từng field."""
            for key, gt_value in gt_node.items():
                current_path = f"{path}.{key}" if path else key
                ext_value = ext_node.get(key, "") if isinstance(ext_node, dict) else ""
                
                if isinstance(gt_value, dict) and isinstance(ext_value, dict):
                    flatten_json_for_comparison(gt_value, ext_value, current_path)
                elif isinstance(gt_value, list):
                    comparison_data.append({
                        "Field": current_path,
                        "Ground Truth": json.dumps(gt_value, ensure_ascii=False),
                        "Extracted": json.dumps(ext_value, ensure_ascii=False),
                        "Match": "✓" if gt_value == ext_value else "✗",
                        "Type": "List"
                    })
                else:
                    comparison_data.append({
                        "Field": current_path,
                        "Ground Truth": str(gt_value),
                        "Extracted": str(ext_value),
                        "Match": "✓" if str(gt_value) == str(ext_value) else "✗",
                        "Type": type(gt_value).__name__
                    })
        
        flatten_json_for_comparison(ground_truth_json, extracted_json)
        
        if comparison_data:
            df_comparison = pd.DataFrame(comparison_data)
            df_comparison.to_excel(writer, sheet_name='Field_Comparison', index=False)
        
        # Sheet 3: Diff Details (nếu có)
        if diff_details:
            diff_data = []
            
            # Values changed
            if 'values_changed' in diff_details:
                for path, change in diff_details['values_changed'].items():
                    diff_data.append({
                        "Type": "Value Changed",
                        "Path": path,
                        "Old Value": str(change.get('old_value', '')),
                        "New Value": str(change.get('new_value', ''))
                    })
            
            # Items added
            if 'dictionary_item_added' in diff_details:
                for path in diff_details['dictionary_item_added']:
                    diff_data.append({
                        "Type": "Item Added",
                        "Path": str(path),
                        "Old Value": "N/A",
                        "New Value": "Added"
                    })
            
            # Items removed
            if 'dictionary_item_removed' in diff_details:
                for path in diff_details['dictionary_item_removed']:
                    diff_data.append({
                        "Type": "Item Removed", 
                        "Path": str(path),
                        "Old Value": "Removed",
                        "New Value": "N/A"
                    })
            
            if diff_data:
                df_diff = pd.DataFrame(diff_data)
                df_diff.to_excel(writer, sheet_name='Diff_Details', index=False)
        
        # Sheet 4: Raw Data
        raw_data = {
            "Ground Truth JSON": [json.dumps(ground_truth_json, ensure_ascii=False, indent=2)],
            "Extracted JSON": [json.dumps(extracted_json, ensure_ascii=False, indent=2)],
            "Evaluation Time": [timestamp],
            "Files Used": [", ".join(SOURCE_FILES_FOR_TEST)]
        }
        
        df_raw = pd.DataFrame(raw_data)
        df_raw.to_excel(writer, sheet_name='Raw_Data', index=False)
    
    print(f"📊 Kết quả evaluation đã được lưu: {filepath}")
    return filepath

# --- 3. HÀM CHÍNH ĐIỀU PHỐI ---

def run_full_evaluation():
    """Hàm chính điều phối toàn bộ quy trình đánh giá."""
    
    # --- GIAI ĐOẠN 1: CHUẨN BỊ ---
    print("--- Giai đoạn 1: Chuẩn bị môi trường ---")
    
    # 1.1 Tải ground truth
    with open(GROUND_TRUTH_PATH, 'r', encoding='utf-8') as f:
        ground_truth_json = json.load(f)
        
    # 1.2 Upload các file cần thiết
    print("Uploading source files...")
    file_id_map = {}
    for filename in SOURCE_FILES_FOR_TEST:
        filepath = os.path.join(DOCS_DIRECTORY, filename)
        if os.path.exists(filepath):
            file_id = requests.post(f"{BACKEND_URL}/upload_file", files={"file": open(filepath, "rb")}).json()["file_id"]
            file_id_map[filename] = file_id
        else:
            print(f"⚠️ File not found: {filepath}")

    # --- GIAI ĐOẠN 2: CHẠY HỆ THỐNG VÀ ĐO LƯỜNG ---
    print("\n--- Giai đoạn 2: Chạy trích xuất và đo lường Latency ---")
    
    payload = {
        "prompt": "Trích xuất thông tin theo mẫu Báo cáo thẩm định.",
        "file_ids": list(file_id_map.values()),
        "template_id": "template4"
    }
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/process_prompt", json=payload, timeout=300)
    end_time = time.time()
    
    if response.status_code != 200:
        print(f"❌ Lỗi API nghiêm trọng: {response.text}")
        return

    extracted_result = response.json()
    extracted_json = extracted_result["extracted_data"]
    collection_name = extracted_result["collection_name"]
    
    # Metric: End-to-End Latency
    latency = end_time - start_time
    print(f"✅ Trích xuất hoàn tất. Collection được sử dụng: {collection_name}")
    print(f"⏱️ End-to-End Latency: {latency:.2f} giây")

    # --- GIAI ĐOẠN 3: TÍNH TOÁN METRICS ---
    print("\n--- Giai đoạn 3: Tính toán các metrics ---")

    # Metric: Extraction Accuracy
    accuracy, diff = calculate_extraction_accuracy(ground_truth_json, extracted_json)
    print(f"🎯 Extraction Accuracy: {accuracy:.2f}%")
        
    # Chuẩn bị dataset cho Ragas
    ragas_dataset = generate_ragas_dataset(ground_truth_json, extracted_json, collection_name)
    
    # Đánh giá bằng Ragas
    print("\n   -> Đang chạy đánh giá Ragas (có thể mất vài phút)...")
    ragas_result = evaluate(
        ragas_dataset,
        metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
    )
    
    # --- GIAI ĐOẠN 4: HIỂN THỊ KẾT QUẢ TỔNG HỢP ---
    print("\n--- BẢNG ĐIỀU KHIỂN ĐÁNH GIÁ ---")
    
    ragas_scores = ragas_result.scores
    hallucination_rate = 1.0 - ragas_scores.get('faithfulness', 0)
    
    summary = {
        "Metric": [
            "Extraction Accuracy (%)",
            "End-to-End Latency (s)",
            "--- Ragas Core Metrics ---",
            "Faithfulness",
            "Context Precision",
            "Context Recall",
            "Answer Relevancy",
            "--- Reliability Metrics ---",
            "Hallucination Rate (%)"
        ],
        "Score": [
            f"{accuracy:.2f}",
            f"{latency:.2f}",
            "--------------------------",
            f"{ragas_scores.get('faithfulness', 'N/A'):.4f}",
            f"{ragas_scores.get('context_precision', 'N/A'):.4f}",
            f"{ragas_scores.get('context_recall', 'N/A'):.4f}",
            f"{ragas_scores.get('answer_relevancy', 'N/A'):.4f}",
            "--------------------------",
            f"{hallucination_rate:.2%}"
        ]
    }
    
    df_summary = pd.DataFrame(summary)
    print(df_summary.to_string(index=False))
    
    # --- GIAI ĐOẠN 5: LUU KẾT QUẢ VÀO EXCEL ---
    print("\n--- Giai đoạn 5: Lưu kết quả vào Excel ---")
    excel_filepath = save_evaluation_results(
        accuracy=accuracy,
        latency=latency, 
        ragas_scores=ragas_scores,
        diff_details=diff,
        extracted_json=extracted_json,
        ground_truth_json=ground_truth_json
    )

    # --- GIAI ĐOẠN 6: DỌN DẸP ---
    requests.post(f"{BACKEND_URL}/clear_rag_session", json={"collection_name": collection_name})
    print(f"\n✅ Đã dọn dẹp collection: {collection_name}")


if __name__ == "__main__":
    run_full_evaluation()