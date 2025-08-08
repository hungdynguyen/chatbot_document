import os
import json
import pandas as pd
import time
import traceback
from datetime import datetime
from typing import List, Dict, Optional

from datasets import Dataset
from ragas import evaluate
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import (
    faithfulness,
    context_recall,
    context_precision,
    answer_correctness,
    SemanticSimilarity,
    AnswerSimilarity
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.outputs import LLMResult
from pydantic import SecretStr
from utils.api_key_manager import ApiKeyManager
# Tắt các cảnh báo không cần thiết từ huggingface_hub
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

def is_meaningful_item(item: str) -> bool:
    """
    Kiểm tra một item (chuỗi) trong list ground_truths có mang ý nghĩa hay không.
    Trả về False nếu:
    - Chuỗi là rỗng hoặc chỉ chứa khoảng trắng.
    - Chuỗi là "null".
    - Chuỗi là một JSON object mà tất cả các giá trị đều là null.
    """
    # Kiểm tra cơ bản
    if not item or not item.strip() or item.strip().lower() == 'null':
        return False
    
    # Cố gắng phân tích chuỗi như một JSON
    try:
        data = json.loads(item)
        # Nếu là một dictionary
        if isinstance(data, dict):
            # Nếu dict rỗng hoặc tất cả các giá trị là None, nó không có ý nghĩa
            if not data or all(value is None for value in data.values()):
                return False
        # Nếu là một list
        if isinstance(data, list):
            # Nếu list rỗng hoặc tất cả các giá trị là None, nó không có ý nghĩa
            if not data or all(value is None for value in data):
                return False
    except (json.JSONDecodeError, TypeError):
        # Nếu không phải là JSON hợp lệ, nó là một chuỗi văn bản bình thường.
        # Vì đã qua các bước kiểm tra rỗng/null ở trên, ta coi nó có ý nghĩa.
        pass
        
    return True

def is_valid_ground_truths_list(gt_list: list) -> bool:
    """
    Kiểm tra toàn bộ list ground_truths.
    Nó chỉ hợp lệ nếu chứa ít nhất MỘT item có ý nghĩa.
    """
    if not isinstance(gt_list, list) or not gt_list:
        return False
    return any(is_meaningful_item(item) for item in gt_list)


class RetryingChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    api_manager: ApiKeyManager
    
    def _handle_quota_error(self, error: Exception):
        error_message = str(error).lower()
        is_quota_error = "429" in error_message or "quota" in error_message or "resource_exhausted" in error_message
        if is_quota_error:
            print("  ⚠️ Lỗi Quota được phát hiện.", force=True)
            self.api_manager.switch_to_next_key()
            
            # Cập nhật API key
            old_key = self.google_api_key
            self.google_api_key = self.api_manager.get_current_key()
            print(f"  🔧 Đã chuyển từ key cũ sang key mới", force=True)
            
            # QUAN TRỌNG: Tạo lại client với API key mới
            self._recreate_client()
            
        raise error

    def _recreate_client(self):
        """Tạo lại client với API key mới"""
        try:
            from langchain_google_genai._common import get_client_info
            from langchain_google_genai import _genai_extension as genaix
            
            google_api_key = None
            if not self.credentials:
                if isinstance(self.google_api_key, SecretStr):
                    google_api_key = self.google_api_key.get_secret_value()
                else:
                    google_api_key = self.google_api_key
            
            # Tạo lại sync client
            self.client = genaix.build_generative_service(
                credentials=self.credentials,
                api_key=google_api_key,
                client_info=get_client_info(f"ChatGoogleGenerativeAI:{self.model}"),
                client_options=self.client_options,
                transport=self.transport,
            )
            
            # Reset async client để nó được tạo lại khi cần
            self.async_client_running = None
            
            print("  ✅ Đã tạo lại client với API key mới", force=True)
        except Exception as e:
            print(f"  ❌ Lỗi khi tạo lại client: {e}", force=True)

    def _generate(self, *args, **kwargs) -> LLMResult:
        try: 
            return super()._generate(*args, **kwargs)
        except Exception as e: 
            self._handle_quota_error(e)

    async def _agenerate(self, *args, **kwargs) -> LLMResult:
        try: 
            return await super()._agenerate(*args, **kwargs)
        except Exception as e: 
            self._handle_quota_error(e)
    
class RagasEvaluator:
    """
    Một class chuyên dụng để thực hiện đánh giá RAGAS,
    dễ dàng tích hợp vào Jupyter Notebook.
    """
    def __init__(self, list_of_api_keys: list):
        print("🚀 Khởi tạo RagasEvaluator (có Retry & Key Switching)...", force=True)
        if not list_of_api_keys:
            raise ValueError("Cần cung cấp danh sách Google API Key.")
            
        self.api_manager = ApiKeyManager(list_of_api_keys)
        self.api_call_delay_seconds = 8.0
        self.llm_based_metrics = ['faithfulness', 'context_precision', 'context_recall', 'answer_correctness']
        self.embedding_based_metrics = ['semantic_similarity']
        
        # 1. Khởi tạo LLM (Generator & Critic)
        llm_instance = RetryingChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=self.api_manager.get_current_key(), 
            api_manager=self.api_manager, 
            temperature=0.0,
            max_retries=2,
        )
        self.llm = LangchainLLMWrapper(llm_instance)
        
        # 2. Khởi tạo Embeddings
        self.embeddings = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(
                model_name="jinaai/jina-embeddings-v3",
                model_kwargs={"device": "cpu", "trust_remote_code": True}
            )
        )
        print("LLM và Embeddings đã sẵn sàng.", force=True)

        # 3. Định nghĩa các metrics
        self.faithfulness_metric = faithfulness
        self.context_precision_metric = context_precision
        self.context_recall_metric = context_recall
        answer_similarity = AnswerSimilarity(embeddings=self.embeddings)
        self.answer_correctness_metric = answer_correctness
        self.answer_correctness_metric.answer_similarity = answer_similarity
        
        # Non-LLM metrics
        self.semantic_sim_metric = SemanticSimilarity()
        
        # Tất cả metrics
        self.metrics = [
            self.faithfulness_metric,           # Mức độ câu trả lời bám sát context
            self.context_precision_metric,      # Mức độ các context được lấy ra là cần thiết
            self.context_recall_metric,         # Mức độ các context cần thiết đã được lấy ra
            self.answer_correctness_metric,     # Độ chính xác về mặt fact/semantic của câu trả lời
            self.semantic_sim_metric,           # Độ tương đồng ngữ nghĩa
        ]
        
        # Gán llm và embeddings cho các metrics cần thiết
        for metric in self.metrics:
            if hasattr(metric, 'llm'):
                metric.llm = self.llm
            if hasattr(metric, 'embeddings'):
                metric.embeddings = self.embeddings
                
        print(f"📋 Đã định nghĩa {len(self.metrics)} metrics: {[m.name for m in self.metrics]}")

        # 4. Thư mục lưu kết quả
        self.reports_dir = "evaluation_reports"
        os.makedirs(self.reports_dir, exist_ok=True)
        print(f"Đã tạo thư mục báo cáo: {self.reports_dir}")

    def load_base_dataset(self, filepath: str) -> List[Dict]:
        """Tải dataset cơ sở (question, ground_truth) từ file JSON."""
        print(f"Đang tải base dataset từ: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Tải thành công {len(data)} mẫu.")
            return data
        except Exception as e:
            print(f"Lỗi khi tải base dataset: {e}")
            return []

    def prepare_evaluation_dataset(self, base_data: List[Dict], generated_data: List[Dict]) -> Optional[Dataset]:
        """
        Kết hợp base_data và generated_data để tạo dataset hoàn chỉnh cho RAGAS.
        (Phiên bản sửa lỗi và cải tiến)
        """
        print("Đang chuẩn bị dataset để đánh giá...")
        if not base_data or not generated_data:
            print("Dữ liệu cơ sở hoặc dữ liệu được sinh ra bị rỗng.")
            return None

        base_df = pd.DataFrame(base_data)
        generated_df = pd.DataFrame(generated_data)
        
        if 'query' in generated_df.columns:
            generated_df = generated_df.rename(columns={'query': 'question'})

        eval_df = pd.merge(base_df, generated_df, on='question', how='inner')

        if eval_df.empty:
            print("Sau khi join, DataFrame rỗng. Kiểm tra lại các câu hỏi.")
            return None
        
        eval_df = eval_df.rename(columns={'ground_truth': 'ground_truths'})
        
        # 2. Xử lý cột 'ground_truths' một cách an toàn
        def format_ground_truth(x):
            if x is None:
                return []
            if isinstance(x, list):
                return [str(item) for item in x if item not in [None, "", "null"]]
            if isinstance(x, dict):
                return [json.dumps(x, ensure_ascii=False)]
            return [str(x)]

        eval_df['ground_truths'] = eval_df['ground_truths'].apply(format_ground_truth)

        # 3. Xử lý cột 'contexts' để đảm bảo nó luôn là List[str]
        def format_contexts(x):
            if not isinstance(x, list):
                return []
            return [str(item) for item in x]

        eval_df['contexts'] = eval_df['contexts'].apply(format_contexts)
        print(f"Đã chuẩn hóa cột 'contexts' với kiểu dữ liệu: {type(eval_df['contexts'].iloc[0])}")
        

        print(f"Đã tạo thành công dataset với {len(eval_df)} mẫu để đánh giá.")
        
        # Thêm bước kiểm tra kiểu dữ liệu để chắc chắn
        if not eval_df.empty:
            first_context_type = type(eval_df.iloc[0]['contexts'])
            print(f"Kiểu dữ liệu của cột 'contexts' đã được xác nhận là: {first_context_type}")
            if first_context_type is not list:
                print("CẢNH BÁO: Kiểu dữ liệu của 'contexts' vẫn không phải là list!")

        # Bước 4: Loại bỏ dòng chứa null trong các cột cần thiết
        required_cols = ['answer', 'ground_truths', 'contexts']
        eval_df = eval_df.dropna(subset=required_cols)

        # Và đảm bảo ground_truths không rỗng và contexts không rỗng
        eval_df = eval_df[eval_df['contexts'].apply(lambda x: isinstance(x, list) and len(x) > 0)]
        eval_df = eval_df[eval_df["ground_truths"].apply(is_valid_ground_truths_list)]
        print(f"Sau khi loại bỏ null/empty, còn {len(eval_df)} mẫu.")

        # Thêm cột reference (cần cho một số metrics)
        if 'reference' not in eval_df.columns:
            # Sử dụng ground_truths[0] làm reference
            eval_df['reference'] = eval_df['ground_truths'].apply(lambda x: x[0] if x and len(x) > 0 else "")
            print("Đã thêm cột 'reference' từ ground_truths.")

        # Tiếp tục trả về dataset
        return Dataset.from_pandas(eval_df)

    def validate_dataset_schema(self, dataset: Dataset) -> bool:
        """Kiểm tra schema của dataset có đủ các cột cần thiết không."""
        required_columns = ['question', 'answer', 'contexts', 'ground_truths','reference']
        
        missing_required = [col for col in required_columns if col not in dataset.column_names]
        if missing_required:
            print(f"Dataset thiếu các cột bắt buộc: {missing_required}")
            return False
        
        print(f"Dataset schema hợp lệ. Columns: {dataset.column_names}")
        return True

    def run_evaluation(self, dataset: Dataset) -> Optional[pd.DataFrame]:
        """Thực thi việc đánh giá RAGAS trên dataset đã chuẩn bị - đánh giá từng dòng một."""
        if not dataset:
            print("❌ Dataset rỗng, không thể đánh giá.")
            return None
        
        # Validate dataset schema
        if not self.validate_dataset_schema(dataset):
            print("❌ Dataset schema không hợp lệ.")
            return None
        
        total_rows = len(dataset)
        
        print(f"\n🔬 Bắt đầu đánh giá RAGAS trên {total_rows} mẫu với {len(self.metrics)} metrics...")
        print(f"📋 Metrics: {[m.name for m in self.metrics]}")
        
        try:
            # Lặp qua từng dòng của dataset và đánh giá từng metric một cách tuần tự
            all_results = []
            
            for i, row in enumerate(dataset):
                print(f"\n--- 🔄 Đang đánh giá dòng {i+1}/{total_rows} ---")
                # In ra question và answer thông tin dòng
                print(f"   Q: {row['question'][:100]}...")
                print(f"   A: {row['answer'][:100]}...")
                
                row_scores = {}
                
                # Tạo SingleTurnSample cho dòng hiện tại
                try:
                    sample = SingleTurnSample(
                        user_input=row['question'],
                        response=row['answer'],
                        retrieved_contexts=row['contexts'],
                        reference=row.get('reference', row['ground_truths'][0] if row['ground_truths'] else "")
                    )
                except Exception as e:
                    print(f"    ❌ Lỗi tạo SingleTurnSample cho dòng {i+1}: {e}")
                    continue
                
                # Đánh giá từng metric một cách tuần tự sử dụng single_turn_score
                for j, metric in enumerate(self.metrics):
                    try:
                        print(f"    🔄 Metric {j+1}/{len(self.metrics)}: {metric.name}")
                        
                        # Gọi single_turn_score để đánh giá metric này cho sample này
                        score = metric.single_turn_score(sample)
                        
                        # Lưu kết quả với tên cột phù hợp
                        metric_name = metric.name
                        
                        row_scores[metric_name] = float(score) if score is not None else 0.0
                        
                        print(f"{metric.name}: {score}")
                        
                        # Delay giữa các metric để tránh rate limit
                        if metric.name in self.llm_based_metrics:
                            print(f"Chờ {self.api_call_delay_seconds}s để tránh rate limit...")
                            time.sleep(self.api_call_delay_seconds)
                        else:
                            time.sleep(0.5)  # Delay ngắn cho non-LLM metrics
                            
                    except Exception as e:
                        print(f"Lỗi đánh giá {metric.name} cho dòng {i+1}: {e}")
                        metric_name = metric.name
                        row_scores[metric_name] = 0.0
                        continue
                
                # Thêm kết quả của dòng này vào danh sách
                row_df = pd.DataFrame([row_scores])
                all_results.append(row_df)
                print(f"Đánh giá dòng {i+1} hoàn tất.")
                
                # Chỉ chờ giữa các dòng nếu có sử dụng LLM metrics
                has_llm_metrics = any(metric.name in self.llm_based_metrics for metric in self.metrics)
                
                if has_llm_metrics and i < total_rows - 1:
                    print(f"Chờ {self.api_call_delay_seconds}s trước khi xử lý dòng tiếp theo...")
                    time.sleep(self.api_call_delay_seconds)
                elif not has_llm_metrics:
                    time.sleep(1.0)  
            
            # Tổng hợp tất cả kết quả
            print("\n---Tất cả các dòng đã được đánh giá. Tổng hợp kết quả... ---")
            if not all_results:
                print("Không có kết quả nào để tổng hợp.")
                return None
            
            # Ghép tất cả các DataFrame kết quả lại thành một
            result_df = pd.concat(all_results, ignore_index=True)
            print(f"Kết quả có {len(result_df)} dòng và {len(result_df.columns)} cột metrics.")
            return result_df

        except Exception as e:
            print(f"Lỗi nghiêm trọng trong quá trình đánh giá: {e}")
            traceback.print_exc()
            return None

    def save_report(self, scores_df: pd.DataFrame, output_dir: Optional[str] = None, filename: Optional[str] = None) -> Optional[str]:
        """Lưu báo cáo kết quả đánh giá ra file Excel."""
        if scores_df is None or scores_df.empty:
            print("Không có dữ liệu để lưu báo cáo.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Xử lý thư mục output
        if output_dir is None:
            output_dir = self.reports_dir
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(output_dir, exist_ok=True)
        print(f"Đã đảm bảo thư mục tồn tại: {output_dir}")
        
        # Xử lý tên file
        if filename is None:
            filename = f"ragas_report_{timestamp}.xlsx"
        
        filepath = os.path.join(output_dir, filename)
        
        # Tính điểm trung bình cho các cột metric
        metric_names = [m.name for m in self.metrics]
        # Map tên metrics để khớp với tên cột trong DataFrame
        mapped_names = []
        for name in metric_names:
            mapped_names.append(name)
        
        # Lấy các cột metric từ df chi tiết, đảm bảo chúng tồn tại
        existing_metric_cols = [col for col in mapped_names if col in scores_df.columns]
        print(f"Tìm thấy {len(existing_metric_cols)} metrics trong kết quả: {existing_metric_cols}")
        
        if existing_metric_cols:
            # Tính điểm trung bình cho từng metric
            avg_scores = {}
            for col in existing_metric_cols:
                # Chuyển đổi sang numeric và tính mean, bỏ qua các giá trị không phải số
                mean_score = pd.to_numeric(scores_df[col], errors='coerce').dropna().mean()
                avg_scores[col] = float(mean_score) if pd.notna(mean_score) else 0.0
            
            # Chuyển thành DataFrame
            avg_scores_df = pd.DataFrame(list(avg_scores.items()), columns=['metric', 'average_score'])
        else:
            print("⚠️ Không tìm thấy cột metric nào trong DataFrame.")
            avg_scores_df = pd.DataFrame({"metric": ["no_metrics"], "average_score": [0.0]})
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Sheet 1: Tổng quan điểm số
                avg_scores_df.to_excel(writer, sheet_name='Summary_Scores', index=False)
                
                # Sheet 2: Chi tiết từng dòng
                scores_df.to_excel(writer, sheet_name='Detailed_Results', index=False)
                
                # Sheet 3: Metadata
                metadata_df = pd.DataFrame({
                    "Property": ["Total Metrics", "Sample Count", "Generated At", "Metrics List", "Evaluation Method"],
                    "Value": [
                        len(self.metrics), 
                        len(scores_df), 
                        datetime.now().isoformat(),
                        ", ".join([m.name for m in self.metrics]),
                        "Single Turn Score (Row by Row)"
                    ]
                })
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
            print(f"Báo cáo đã được lưu tại: {filepath}")
            print("Điểm số trung bình:")
            for _, row in avg_scores_df.iterrows():
                try:
                    print(f"   {row['metric']}: {row['average_score']:.4f}")
                except Exception as format_error:
                    print(f"   {row['metric']}: {row['average_score']}")
            
            return filepath
        except Exception as e:
            print(f"Lỗi khi lưu báo cáo: {e}")
            traceback.print_exc()
            return None

