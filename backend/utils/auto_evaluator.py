import os
import json
import pandas as pd
import time
import asyncio # Cần cho async sleep
from datetime import datetime
from datasets import Dataset
from ragas import evaluate
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult
from typing import Any, Dict, List, Optional

# Import các RAG metrics (LLM-based)
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
    answer_correctness,
)

# Import các metric cổ điển dưới dạng Class
from ragas.metrics import (
    BleuScore,
    RougeScore,
    ExactMatch
)


# Lớp Wrapper để thêm độ trễ giữa các lần gọi API
class RateLimitedLLM:
    """
    Một lớp vỏ (wrapper) bao quanh một đối tượng BaseChatModel của LangChain
    để thêm một khoảng thời gian chờ cố định trước mỗi lần gọi API,
    giúp tránh lỗi rate limit.
    """
    def __init__(self, llm: BaseChatModel, delay_seconds: float = 1.0):
        self._llm = llm
        self._delay = delay_seconds
        print(f"✅ RateLimiter được kích hoạt cho LLM với độ trễ {self._delay} giây/request.")

    async def ainvoke(self, *args, **kwargs) -> ChatResult:
        """Thực hiện sleep rồi gọi ainvoke của LLM gốc."""
        await asyncio.sleep(self._delay)
        return await self._llm.ainvoke(*args, **kwargs)

    def invoke(self, *args, **kwargs) -> ChatResult:
        """Thực hiện sleep rồi gọi invoke của LLM gốc."""
        time.sleep(self._delay)
        return self._llm.invoke(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Chuyển tiếp tất cả các truy cập thuộc tính khác đến LLM gốc."""
        return getattr(self._llm, name)


class AutoEvaluator:
    """
    Class Auto-evaluation được thiết kế lại để tự động đánh giá kết quả,
    tận dụng tối đa framework Ragas cho tất cả các loại metric.
    """

    def __init__(self):
        # Cấu hình
        self.google_api_key = "AIzaSyAD_58r3fQhcTOE6qQS1YlR3iJ_ZnGKy10"
        self.qdrant_host = "localhost"
        self.qdrant_port = 6333
        self.embedding_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.api_call_delay_seconds = 1.0 # <-- Cấu hình độ trễ ở đây (ví dụ: 1 giây)

        # Khởi tạo clients
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        self.embedding_model = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        
        # Khởi tạo LLM gốc
        gemini_llm_base = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=self.google_api_key,
            temperature=0
        )
        
        # Bọc LLM gốc bằng RateLimitedLLM
        self.gemini_llm = RateLimitedLLM(
            llm=gemini_llm_base, 
            delay_seconds=self.api_call_delay_seconds
        )

        # Thư mục lưu kết quả
        self.evaluation_dir = "evaluation_results"
        self.reports_dir = os.path.join(self.evaluation_dir, "auto_reports")
        os.makedirs(self.reports_dir, exist_ok=True)

        # Ground truth paths
        self.ground_truth_paths = {
            "template4": r"/home/locmt/Techcombank_/chatbot_document/backend/schemas/ground_truth_template4.json"
        }

    def load_ground_truth(self, template_id: str) -> Optional[Dict]:
        """Tải ground truth cho template."""
        try:
            ground_truth_path = self.ground_truth_paths.get(template_id)
            if not ground_truth_path or not os.path.exists(ground_truth_path):
                print(f"⚠️ Không tìm thấy ground truth cho template: {template_id}")
                return None
            with open(ground_truth_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Lỗi khi tải ground truth: {e}")
            return None

    def generate_ragas_dataset(self, ground_truth_json: Dict, extracted_json: Dict, collection_name: str) -> Dataset:
        """
        Tạo dataset cho Ragas từ ground truth và kết quả trích xuất.
        Mỗi hàng trong dataset tương ứng với một trường thông tin cần đánh giá.
        """
        print("🔄 Generating Ragas dataset...")
        ragas_data = {"question": [], "answer": [], "contexts": [], "reference": []}

        def flatten_and_build(gt_node, ext_node, path=""):
            if not isinstance(gt_node, dict):
                return

            for key, gt_value in gt_node.items():
                current_path = f"{path}.{key}" if path else key
                ext_value = ext_node.get(key) if isinstance(ext_node, dict) else None

                if isinstance(gt_value, dict):
                    flatten_and_build(gt_value, ext_value, current_path)
                elif gt_value is not None and str(gt_value).strip() != "":
                    question = f"Trích xuất thông tin cho trường '{current_path}'."
                    ground_truth_answer = json.dumps(gt_value, ensure_ascii=False) if isinstance(gt_value, list) else str(gt_value)
                    extracted_answer = json.dumps(ext_value, ensure_ascii=False) if isinstance(ext_value, list) else str(ext_value if ext_value is not None else "")
                    
                    if extracted_answer.strip() and extracted_answer != '""' and extracted_answer != '[]':
                        contexts = self.retrieve_contexts(question, collection_name)
                        if contexts:
                            ragas_data["question"].append(question)
                            ragas_data["answer"].append(extracted_answer)
                            ragas_data["contexts"].append(contexts)
                            ragas_data["reference"].append(ground_truth_answer)

        flatten_and_build(ground_truth_json, extracted_json)

        if not ragas_data["question"]:
            print("⚠️ Không thể tạo Ragas dataset. Có thể do không trích xuất được trường nào hoặc không tìm thấy context.")
            return Dataset.from_dict({"question": [], "answer": [], "contexts": [], "reference": []})

        dataset = Dataset.from_dict(ragas_data)
        print(f"📊 Đã tạo Ragas dataset với {len(dataset)} mẫu.")
        return dataset

    def retrieve_contexts(self, question: str, collection_name: str) -> List[str]:
        """Truy xuất ngữ cảnh từ Qdrant."""
        try:
            query_vector = self.embedding_model.embed_query(question)
            hits = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=5
            )
            return [hit.payload.get("page_content", "") for hit in hits if hit.payload.get("page_content")]
        except Exception as e:
            print(f"❌ Lỗi khi truy xuất ngữ cảnh từ Qdrant: {e}")
            return []

    def save_evaluation_report(self, scores: Dict, latency: float, template_id: str, file_ids: List[str], dataset_size: int) -> str:
        """Lưu báo cáo đánh giá toàn diện vào file Excel."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"auto_eval_{template_id}_{timestamp}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)

        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Sheet 1: Tổng quan
                hallucination_rate = 1.0 - scores.get('faithfulness', 0)
                
                summary_data = {
                    "Metric Category": [
                        "Hiệu năng",
                        "---",
                        "Chất lượng RAG (LLM-based)", "Chất lượng RAG (LLM-based)", "Chất lượng RAG (LLM-based)", 
                        "Chất lượng RAG (LLM-based)", "Chất lượng RAG (LLM-based)",
                        "---",
                        "Chất lượng trích xuất (LLM-based)",
                        "---",
                        "Chất lượng trích xuất (Classical)", "Chất lượng trích xuất (Classical)", "Chất lượng trích xuất (Classical)",
                    ],
                    "Metric Name": [
                        "End-to-End Latency (s)",
                        "---",
                        "Faithfulness", "Answer Relevancy", "Context Precision", "Context Recall", "Hallucination Rate (%)",
                        "---",
                        "Answer Correctness (Semantic & Factual)",
                        "---",
                        "Exact Match", "BLEU Score", "ROUGE-L Score",
                    ],
                    "Score": [
                        f"{latency:.2f}",
                        "---",
                        f"{scores.get('faithfulness', 0):.4f}", f"{scores.get('answer_relevancy', 0):.4f}", 
                        f"{scores.get('context_precision', 0):.4f}", f"{scores.get('context_recall', 0):.4f}", f"{hallucination_rate:.2%}",
                        "---",
                        f"{scores.get('answer_correctness', 0):.4f}",
                        "---",
                        f"{scores.get('exact_match', 0):.4f}", f"{scores.get('bleu_score', 0):.4f}", f"{scores.get('rouge_L', 0):.4f}",
                    ]
                }
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Evaluation_Summary', index=False)

                # Sheet 2: Chi tiết
                info_data = {
                    "Thông tin": ["Thời gian", "Template ID", "File IDs", "Số mẫu đánh giá", "Độ trễ API (s)"],
                    "Giá trị": [timestamp, template_id, ", ".join(file_ids), dataset_size, self.api_call_delay_seconds]
                }
                df_info = pd.DataFrame(info_data)
                df_info.to_excel(writer, sheet_name='Run_Info', index=False)

            print(f"📊 Báo cáo đánh giá đã được lưu: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Lỗi khi lưu báo cáo: {e}")
            return ""

    def auto_evaluate(self, extracted_data: Dict, template_id: str, collection_name: str,
                     file_ids: List[str], latency: float, run_full_metrics: bool = True) -> Optional[Dict]:
        """
        Hàm chính để auto-evaluate kết quả trích xuất bằng Ragas.
        """
        print(f"🎯 Bắt đầu auto-evaluation toàn diện cho template: {template_id}...")

        # 1. Tải ground truth
        ground_truth_json = self.load_ground_truth(template_id)
        if not ground_truth_json:
            print(f"⚠️ Bỏ qua auto-evaluation: không có ground truth cho {template_id}")
            return None

        try:
            # 2. Tạo dataset cho Ragas
            dataset = self.generate_ragas_dataset(ground_truth_json, extracted_data, collection_name)
            if len(dataset) == 0:
                print("⚠️ Dataset rỗng, không thể thực hiện đánh giá.")
                return None
            
            # 3. Định nghĩa các metrics sẽ sử dụng
            extraction_metrics = [
                answer_correctness,
                ExactMatch(),
                BleuScore(),
                RougeScore(rouge_type="rougeL")
            ]
            rag_metrics = [faithfulness, answer_relevancy]
            if run_full_metrics:
                rag_metrics.extend([context_precision, context_recall])
            all_metrics = rag_metrics + extraction_metrics
            
            # 4. Chạy đánh giá - Ragas sẽ tự động sử dụng LLM đã được bọc rate-limit
            print(f"🚀 Chạy đánh giá Ragas với {len(all_metrics)} metrics trên {len(dataset)} mẫu...")
            # Ước tính thời gian chạy
            llm_calls_approx = len(dataset) * sum(1 for m in all_metrics if hasattr(m, 'llm'))
            estimated_time = llm_calls_approx * self.api_call_delay_seconds
            print(f"   ... Ước tính có ~{llm_calls_approx} lệnh gọi LLM. Thời gian chờ dự kiến: ~{estimated_time:.0f} giây.")

            result = evaluate(
                dataset,
                metrics=all_metrics,
                llm=self.gemini_llm, # <-- Truyền vào đối tượng LLM đã được bọc
                embeddings=self.embedding_model,
                raise_exceptions=False
            )
            print("✅ Đánh giá Ragas hoàn tất.")
            
            # 5. Xử lý và tổng hợp kết quả
            df = result.to_pandas()
            scores = {}
            for metric in all_metrics:
                metric_name = metric.name
                if metric_name in df.columns:
                    mean_score = df[metric_name].dropna().mean()
                    scores[metric_name] = float(mean_score) if pd.notna(mean_score) else 0.0
                else:
                    scores[metric_name] = 0.0

            # 6. Lưu báo cáo
            report_path = self.save_evaluation_report(
                scores=scores,
                latency=latency,
                template_id=template_id,
                file_ids=file_ids,
                dataset_size=len(dataset)
            )
            
            # 7. Chuẩn bị kết quả cuối cùng để trả về
            final_result = {
                **scores,
                "hallucination_rate": 1.0 - scores.get('faithfulness', 0),
                "latency": latency,
                "report_path": report_path,
                "evaluated_at": datetime.now().isoformat(),
                "metrics_used": "full" if run_full_metrics else "basic+extraction",
                "dataset_size": len(dataset)
            }
            
            print("\n--- KẾT QUẢ ĐÁNH GIÁ TỔNG QUAN ---")
            for key, value in final_result.items():
                if isinstance(value, float):
                    print(f"   - {key:<20}: {value:.4f}")
            print("-------------------------------------\n")
            
            return final_result

        except Exception as e:
            import traceback
            print(f"❌ Lỗi nghiêm trọng trong quá trình auto-evaluation: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return None

# Singleton instance
auto_evaluator = AutoEvaluator()