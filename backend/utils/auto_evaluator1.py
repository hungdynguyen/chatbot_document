import os
import json
import pandas as pd
import time
from datetime import datetime
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from deepdiff import DeepDiff
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, List, Optional, Tuple

# Import thêm các thư viện cho metrics mới
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from difflib import SequenceMatcher
import re
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge import Rouge
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class AutoEvaluator:
    """
    Auto-evaluation class để tự động đánh giá kết quả trích xuất
    mỗi lần có request từ backend.
    """
    
    def __init__(self):
        # Cấu hình
        self.google_api_key = "AIzaSyAD_58r3fQhcTOE6qQS1YlR3iJ_ZnGKy10"
        self.qdrant_host = "localhost"
        self.qdrant_port = 6333
        self.embedding_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        
        # Khởi tạo clients
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        self.embedding_model = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        self.gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite", 
            google_api_key=self.google_api_key, 
            temperature=0
        )
        
        # Thêm model cho semantic similarity
        self.similarity_model = SentenceTransformer(self.embedding_model_name)
        
        # Rouge evaluator cho traditional NLP metrics
        self.rouge = Rouge()
        
        # Thư mục lưu kết quả
        self.evaluation_dir = "evaluation_results"
        self.reports_dir = os.path.join(self.evaluation_dir, "auto_reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Ground truth paths
        self.ground_truth_paths = {
            "template4": r"/home/locmt/Techcombank_/chatbot_document/backend/schemas/template4.json"
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
    
    def calculate_exact_match(self, ground_truth_json: Dict, extracted_json: Dict) -> float:
        """Tính toán Exact Match - tỷ lệ các field khớp hoàn toàn."""
        total_fields = 0
        exact_matches = 0
        
        def compare_fields(gt_node, ext_node, path=""):
            nonlocal total_fields, exact_matches
            
            if isinstance(gt_node, dict) and isinstance(ext_node, dict):
                for key, gt_value in gt_node.items():
                    total_fields += 1
                    ext_value = ext_node.get(key)
                    
                    if isinstance(gt_value, dict) and isinstance(ext_value, dict):
                        compare_fields(gt_value, ext_value, f"{path}.{key}" if path else key)
                    elif gt_value == ext_value:
                        exact_matches += 1
            elif gt_node == ext_node:
                exact_matches += 1
                
        compare_fields(ground_truth_json, extracted_json)
        return (exact_matches / total_fields * 100) if total_fields > 0 else 0
    
    def calculate_semantic_similarity(self, ground_truth_json: Dict, extracted_json: Dict) -> float:
        """Tính toán Semantic Similarity bằng sentence embeddings."""
        gt_text = self._flatten_to_text(ground_truth_json)
        ext_text = self._flatten_to_text(extracted_json)
        
        if not gt_text.strip() or not ext_text.strip():
            return 0.0
            
        # Tạo embeddings
        gt_embedding = self.similarity_model.encode([gt_text])
        ext_embedding = self.similarity_model.encode([ext_text])
        
        # Tính cosine similarity
        similarity = cosine_similarity(gt_embedding, ext_embedding)[0][0]
        return float(similarity * 100)  # Chuyển về phần trăm
    
    def calculate_string_similarity(self, ground_truth_json: Dict, extracted_json: Dict) -> Dict[str, float]:
        """Tính toán Non-LLM String Similarity với nhiều metrics."""
        gt_text = self._flatten_to_text(ground_truth_json)
        ext_text = self._flatten_to_text(extracted_json)
        
        if not gt_text.strip() or not ext_text.strip():
            return {
                "jaccard_similarity": 0.0,
                "cosine_similarity": 0.0, 
                "sequence_matcher": 0.0,
                "levenshtein_ratio": 0.0
            }
        
        # Jaccard Similarity
        gt_words = set(gt_text.lower().split())
        ext_words = set(ext_text.lower().split())
        jaccard = len(gt_words & ext_words) / len(gt_words | ext_words) if gt_words | ext_words else 0
        
        # Sequence Matcher
        sequence_ratio = SequenceMatcher(None, gt_text.lower(), ext_text.lower()).ratio()
        
        # Levenshtein ratio (using difflib)
        levenshtein_ratio = SequenceMatcher(None, gt_text, ext_text).ratio()
        
        return {
            "jaccard_similarity": jaccard * 100,
            "sequence_matcher": sequence_ratio * 100, 
            "levenshtein_ratio": levenshtein_ratio * 100
        }
    
    def calculate_traditional_nlp_metrics(self, ground_truth_json: Dict, extracted_json: Dict) -> Dict[str, float]:
        """Tính toán Traditional NLP Metrics (BLEU, ROUGE)."""
        gt_text = self._flatten_to_text(ground_truth_json)
        ext_text = self._flatten_to_text(extracted_json)
        
        if not gt_text.strip() or not ext_text.strip():
            return {
                "bleu_score": 0.0,
                "rouge_1_f": 0.0,
                "rouge_2_f": 0.0,
                "rouge_l_f": 0.0
            }
        
        # BLEU Score
        try:
            gt_tokens = gt_text.lower().split()
            ext_tokens = ext_text.lower().split()
            smoothie = SmoothingFunction().method4
            bleu = sentence_bleu([gt_tokens], ext_tokens, smoothing_function=smoothie)
        except:
            bleu = 0.0
        
        # ROUGE Scores
        try:
            rouge_scores = self.rouge.get_scores(ext_text, gt_text)[0]
            rouge_1_f = rouge_scores['rouge-1']['f']
            rouge_2_f = rouge_scores['rouge-2']['f'] 
            rouge_l_f = rouge_scores['rouge-l']['f']
        except:
            rouge_1_f = rouge_2_f = rouge_l_f = 0.0
        
        return {
            "bleu_score": bleu * 100,
            "rouge_1_f": rouge_1_f * 100,
            "rouge_2_f": rouge_2_f * 100,
            "rouge_l_f": rouge_l_f * 100
        }
    
    def calculate_factual_correctness(self, ground_truth_json: Dict, extracted_json: Dict) -> float:
        """
        Tính toán Factual Correctness - đo lường độ chính xác về mặt thông tin thực tế.
        Đây là một implementation đơn giản, có thể cải thiện bằng NER hoặc fact-checking models.
        """
        # Trích xuất các fact quan trọng (numbers, dates, names, etc.)
        gt_facts = self._extract_facts(ground_truth_json)
        ext_facts = self._extract_facts(extracted_json)
        
        if not gt_facts:
            return 100.0  # Nếu không có facts để so sánh
            
        correct_facts = 0
        for fact in gt_facts:
            if fact in ext_facts:
                correct_facts += 1
                
        return (correct_facts / len(gt_facts)) * 100
    
    def _flatten_to_text(self, data: Dict) -> str:
        """Chuyển JSON thành text để so sánh."""
        def extract_text(obj):
            if isinstance(obj, dict):
                return " ".join([extract_text(v) for v in obj.values()])
            elif isinstance(obj, list):
                return " ".join([extract_text(item) for item in obj])
            else:
                return str(obj) if obj is not None else ""
        
        return extract_text(data)
    
    def _extract_facts(self, data: Dict) -> List[str]:
        """Trích xuất các facts quan trọng từ JSON (numbers, dates, names)."""
        facts = []
        text = self._flatten_to_text(data)
        
        # Trích xuất numbers
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        facts.extend(numbers)
        
        # Trích xuất dates (simple patterns)
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}', text)
        facts.extend(dates)
        
        # Trích xuất capitalized words (potential names/entities)
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        facts.extend(words)
        
        return list(set(facts))  # Remove duplicates
    
    def generate_ragas_dataset(self, ground_truth_json: Dict, extracted_json: Dict, collection_name: str) -> Dataset:
        """Tạo dataset cho Ragas từ ground truth và kết quả trích xuất."""
        print("🔄 Generating Ragas dataset...")
        ragas_data = {"question": [], "answer": [], "contexts": [], "ground_truths": [], "reference": []}
        
        def flatten_and_ask(node, path=""):
            for key, value in node.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, dict):
                    flatten_and_ask(value, current_path)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    print(f"📝 Added list item: {current_path}")
                    question = f"Hãy cung cấp thông tin chi tiết về: {current_path}"
                    ground_truth_answer = json.dumps(value, ensure_ascii=False)
                    extracted_answer_obj = extracted_json
                    for p in current_path.split('.'): 
                        if isinstance(extracted_answer_obj, dict):
                            extracted_answer_obj = extracted_answer_obj.get(p, {})
                        else:
                            extracted_answer_obj = {}
                    extracted_answer = json.dumps(extracted_answer_obj, ensure_ascii=False)
                    contexts = self.retrieve_contexts(question, collection_name)

                    if contexts and len(contexts) > 0:
                        ragas_data["question"].append(question)
                        ragas_data["answer"].append(extracted_answer)
                        ragas_data["contexts"].append(contexts)
                        ragas_data["ground_truths"].append([ground_truth_answer])
                        ragas_data["reference"].append(ground_truth_answer)
                elif value is not None and str(value).strip():
                    print(f"📝 Added field: {current_path}")
                    print(f"    Question: {f'Thông tin về {current_path} là gì?'[:50]}...")
                    question = f"Thông tin về '{current_path}' là gì?"
                    ground_truth_answer = str(value)
                    print(f"    GT Answer: {ground_truth_answer[:50]}...")
                    
                    extracted_answer_obj = extracted_json
                    try:
                        for p in current_path.split('.'): 
                            if isinstance(extracted_answer_obj, dict):
                                extracted_answer_obj = extracted_answer_obj.get(p, "")
                            else:
                                extracted_answer_obj = ""
                                break
                    except:
                        extracted_answer_obj = ""

                    extracted_answer = str(extracted_answer_obj) if extracted_answer_obj else "Không có thông tin"
                    print(f"    Ext Answer: {extracted_answer[:50]}...")
                    contexts = self.retrieve_contexts(question, collection_name)
                    print(f"    Contexts: {len(contexts)} items")

                    if contexts and len(contexts) > 0 and extracted_answer.strip():
                        ragas_data["question"].append(question)
                        ragas_data["answer"].append(extracted_answer)
                        ragas_data["contexts"].append(contexts)
                        ragas_data["ground_truths"].append([ground_truth_answer])
                        ragas_data["reference"].append(ground_truth_answer)

        flatten_and_ask(ground_truth_json)
        
        dataset = Dataset.from_dict(ragas_data)
        print(f"📊 Generated Ragas dataset with {len(dataset)} samples")
        print(f"📊 Data keys: {list(ragas_data.keys())}")
        print(f"📊 Sample counts - Q:{len(ragas_data['question'])}, A:{len(ragas_data['answer'])}, C:{len(ragas_data['contexts'])}, GT:{len(ragas_data['ground_truths'])}")
        
        if len(dataset) > 0:
            sample = dataset[0]
            print(f"📊 Dataset info - Total samples: {len(dataset)}")
            print(f"📝 Sample keys: {list(sample.keys())}")
            print(f"📝 Sample question: {sample['question'][:50]}...")
            print(f"📝 Sample answer: {sample['answer'][:50]}...")
            print(f"📝 Sample contexts count: {len(sample['contexts'])}")
            print(f"📝 Sample ground_truths count: {len(sample['ground_truths'])}")
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
            contexts = [hit.payload.get("page_content", "") for hit in hits if hit.payload.get("page_content")]
            return contexts[:5] if contexts else []
        except Exception as e:
            print(f"Lỗi khi truy xuất ngữ cảnh từ Qdrant: {e}")
            return []
    
    def run_ragas_evaluation(self, ragas_dataset: Dataset, max_samples: int = 5, run_full_metrics: bool = False) -> Dict:
        """
        Chạy đánh giá Ragas với giới hạn số lượng mẫu.
        
        Args:
            ragas_dataset: Dataset để đánh giá
            max_samples: Số lượng mẫu tối đa
            run_full_metrics: Có chạy toàn bộ metrics không
        """
        if len(ragas_dataset) == 0:
            print("⚠️ Ragas dataset is empty!")
            return {
                "faithfulness": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "answer_relevancy": 0.0,
            }
        
        # Giới hạn số lượng mẫu để tránh timeout
        limited_dataset = ragas_dataset.select(range(min(len(ragas_dataset), max_samples)))
        print(f"📊 Limited dataset size: {len(limited_dataset)}")
        
        try:
            # Chọn metrics dựa trên cấu hình
            if run_full_metrics:
                metrics = [faithfulness, answer_relevancy, context_recall, context_precision]
                print(f"🔍 Chạy Ragas evaluation với TOÀN BỘ 4 metrics cho {len(limited_dataset)} mẫu...")
            else:
                metrics = [faithfulness, answer_relevancy]
                print(f"🔍 Chạy Ragas evaluation với 2 metrics CƠ BẢN cho {len(limited_dataset)} mẫu...")
            
            print("🚀 Starting Ragas evaluation...")
            result = evaluate(
                limited_dataset,
                metrics=metrics,
                llm=self.gemini_llm,
                embeddings=self.embedding_model,
                raise_exceptions=False
            )
            
            print("✅ Ragas evaluation completed, converting to pandas...")
            df = result.to_pandas()
            print(f"📊 DataFrame columns: {list(df.columns)}")
            print(f"📊 DataFrame shape: {df.shape}")
            
            # Debug: Print some values
            for col in df.columns:
                if col in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']:
                    values = df[col].dropna()
                    print(f"📊 {col}: mean={values.mean():.4f}, values={values.tolist()[:3]}")
            
            scores = {}
            
            # Tính faithfulness
            if "faithfulness" in df.columns:
                faithfulness_values = df["faithfulness"].dropna()
                scores["faithfulness"] = float(faithfulness_values.mean()) if len(faithfulness_values) > 0 else 0.0
            else:
                scores["faithfulness"] = 0.0
            
            # Tính answer_relevancy
            if "answer_relevancy" in df.columns:
                relevancy_values = df["answer_relevancy"].dropna()
                scores["answer_relevancy"] = float(relevancy_values.mean()) if len(relevancy_values) > 0 else 0.0
            else:
                scores["answer_relevancy"] = 0.0
            
            # Thêm metrics bổ sung nếu chạy full
            if run_full_metrics:
                if "context_precision" in df.columns:
                    precision_values = df["context_precision"].dropna()
                    scores["context_precision"] = float(precision_values.mean()) if len(precision_values) > 0 else 0.0
                else:
                    scores["context_precision"] = 0.0
                    
                if "context_recall" in df.columns:
                    recall_values = df["context_recall"].dropna()
                    scores["context_recall"] = float(recall_values.mean()) if len(recall_values) > 0 else 0.0
                else:
                    scores["context_recall"] = 0.0
            else:
                scores["context_precision"] = 0.0  # Không chạy
                scores["context_recall"] = 0.0     # Không chạy
            
            print(f"🎯 Final Ragas scores: {scores}")
            return scores
            
        except Exception as e:
            print(f"❌ Lỗi khi chạy Ragas: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return {
                "faithfulness": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "answer_relevancy": 0.0,
            }
    
    def calculate_all_metrics(self, ground_truth_json: Dict, extracted_json: Dict) -> Dict:
        """Tính toán tất cả các metrics mới."""
        print("🔢 Tính toán các metrics...")
        
        # Exact Match
        exact_match = self.calculate_exact_match(ground_truth_json, extracted_json)
        print(f"   - Exact Match: {exact_match:.2f}%")
        
        # Semantic Similarity
        semantic_similarity = self.calculate_semantic_similarity(ground_truth_json, extracted_json)
        print(f"   - Semantic Similarity: {semantic_similarity:.2f}%")
        
        # Factual Correctness
        factual_correctness = self.calculate_factual_correctness(ground_truth_json, extracted_json)
        print(f"   - Factual Correctness: {factual_correctness:.2f}%")
        
        # String Similarity metrics
        string_similarities = self.calculate_string_similarity(ground_truth_json, extracted_json)
        print(f"   - String Similarities: Jaccard={string_similarities['jaccard_similarity']:.2f}%")
        
        # Traditional NLP metrics
        nlp_metrics = self.calculate_traditional_nlp_metrics(ground_truth_json, extracted_json)
        print(f"   - NLP Metrics: BLEU={nlp_metrics['bleu_score']:.2f}%, ROUGE-L={nlp_metrics['rouge_l_f']:.2f}%")
        
        return {
            "exact_match": exact_match,
            "semantic_similarity": semantic_similarity, 
            "factual_correctness": factual_correctness,
            **string_similarities,
            **nlp_metrics
        }
    
    def save_auto_evaluation_results(self, all_metrics: Dict, latency: float, ragas_scores: Dict, 
                                    extracted_json: Dict, ground_truth_json: Dict, 
                                    template_id: str, file_ids: List[str], run_full_metrics: bool = False) -> str:
        """Lưu kết quả auto evaluation với tất cả metrics."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"auto_eval_{template_id}_{timestamp}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Summary metrics - bao gồm tất cả metrics mới
                hallucination_rate = 1.0 - ragas_scores.get('faithfulness', 0)
                
                # Tạo danh sách metrics tùy theo cấu hình
                metrics_list = [
                    "End-to-End Latency (s)",
                    "--- Extraction Metrics ---",
                    "Exact Match (%)",
                    "Semantic Similarity (%)",
                    "Factual Correctness (%)",
                    "--- String Similarity ---",
                    "Jaccard Similarity (%)",
                    "Sequence Matcher (%)",
                    "Levenshtein Ratio (%)",
                    "--- Traditional NLP ---",
                    "BLEU Score (%)",
                    "ROUGE-1 F1 (%)",
                    "ROUGE-2 F1 (%)",
                    "ROUGE-L F1 (%)",
                    "--- Ragas Metrics ---",
                    "Faithfulness",
                    "Answer Relevancy",
                    "Hallucination Rate (%)"
                ]
                scores_list = [
                    f"{latency:.2f}",
                    "--------------------------",
                    f"{all_metrics.get('exact_match', 0):.2f}",
                    f"{all_metrics.get('semantic_similarity', 0):.2f}",
                    f"{all_metrics.get('factual_correctness', 0):.2f}",
                    "--------------------------",
                    f"{all_metrics.get('jaccard_similarity', 0):.2f}",
                    f"{all_metrics.get('sequence_matcher', 0):.2f}",
                    f"{all_metrics.get('levenshtein_ratio', 0):.2f}",
                    "--------------------------",
                    f"{all_metrics.get('bleu_score', 0):.2f}",
                    f"{all_metrics.get('rouge_1_f', 0):.2f}",
                    f"{all_metrics.get('rouge_2_f', 0):.2f}",
                    f"{all_metrics.get('rouge_l_f', 0):.2f}",
                    "--------------------------",
                    f"{ragas_scores.get('faithfulness', 0):.4f}",
                    f"{ragas_scores.get('answer_relevancy', 0):.4f}",
                    f"{hallucination_rate:.2%}"
                ]
                
                # Thêm metrics Ragas bổ sung nếu chạy full
                if run_full_metrics:
                    metrics_list.extend([
                        "Context Precision",
                        "Context Recall"
                    ])
                    scores_list.extend([
                        f"{ragas_scores.get('context_precision', 0):.4f}",
                        f"{ragas_scores.get('context_recall', 0):.4f}"
                    ])
                
                summary_data = {
                    "Metric": metrics_list,
                    "Score": scores_list,
                    "Timestamp": [timestamp] * len(metrics_list),
                    "Template": [template_id] * len(metrics_list),
                    "Files": [", ".join(file_ids)] * len(metrics_list)
                }
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Comprehensive_Metrics', index=False)
                
                # Sheet 2: Detailed breakdown của từng loại metric
                breakdown_data = {
                    "Metric Category": [
                        "Extraction Quality", "Extraction Quality", "Extraction Quality",
                        "String Similarity", "String Similarity", "String Similarity", 
                        "Traditional NLP", "Traditional NLP", "Traditional NLP", "Traditional NLP",
                        "Ragas LLM-based", "Ragas LLM-based", "Ragas LLM-based", "Ragas LLM-based"
                    ],
                    "Metric Name": [
                        "Exact Match", "Semantic Similarity", "Factual Correctness",
                        "Jaccard Similarity", "Sequence Matcher", "Levenshtein Ratio",
                        "BLEU Score", "ROUGE-1 F1", "ROUGE-2 F1", "ROUGE-L F1",
                        "Faithfulness", "Answer Relevancy", "Context Precision", "Context Recall"
                    ],
                    "Score": [
                        all_metrics.get('exact_match', 0),
                        all_metrics.get('semantic_similarity', 0),
                        all_metrics.get('factual_correctness', 0),
                        all_metrics.get('jaccard_similarity', 0),
                        all_metrics.get('sequence_matcher', 0),
                        all_metrics.get('levenshtein_ratio', 0),
                        all_metrics.get('bleu_score', 0),
                        all_metrics.get('rouge_1_f', 0),
                        all_metrics.get('rouge_2_f', 0),
                        all_metrics.get('rouge_l_f', 0),
                        ragas_scores.get('faithfulness', 0) * 100,  # Chuyển về %
                        ragas_scores.get('answer_relevancy', 0) * 100,
                        ragas_scores.get('context_precision', 0) * 100,
                        ragas_scores.get('context_recall', 0) * 100
                    ]
                }
                
                df_breakdown = pd.DataFrame(breakdown_data)
                df_breakdown.to_excel(writer, sheet_name='Metrics_Breakdown', index=False)
            
            print(f"📊 Comprehensive evaluation kết quả đã được lưu: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Lỗi khi lưu comprehensive evaluation: {e}")
            return ""
    
    def auto_evaluate(self, extracted_data: Dict, template_id: str, collection_name: str, 
                     file_ids: List[str], latency: float, run_full_metrics: bool = False) -> Optional[Dict]:
        """
        Hàm chính để auto-evaluate kết quả trích xuất với tất cả metrics mới.
        
        Args:
            extracted_data: Dữ liệu đã trích xuất
            template_id: ID template được sử dụng
            collection_name: Tên collection Qdrant
            file_ids: Danh sách file IDs
            latency: Thời gian xử lý (giây)
            run_full_metrics: Có chạy toàn bộ metrics không
            
        Returns:
            Dict chứa kết quả evaluation hoặc None nếu không có ground truth
        """
        print(f"🎯 Bắt đầu comprehensive auto-evaluation cho template: {template_id}")
        
        # Tải ground truth
        ground_truth_json = self.load_ground_truth(template_id)
        if not ground_truth_json:
            print(f"⚠️ Bỏ qua auto-evaluation: không có ground truth cho {template_id}")
            return None
        
        try:
            # Tính toán tất cả metrics mới
            all_metrics = self.calculate_all_metrics(ground_truth_json, extracted_data)
            
            # Tạo Ragas dataset (nhỏ để nhanh)
            ragas_dataset = self.generate_ragas_dataset(ground_truth_json, extracted_data, collection_name)
            
            # Chạy Ragas evaluation với cấu hình metrics
            ragas_scores = self.run_ragas_evaluation(ragas_dataset, max_samples=40, run_full_metrics=run_full_metrics)
            
            # Lưu kết quả với tất cả metrics
            report_path = self.save_auto_evaluation_results(
                all_metrics=all_metrics,
                latency=latency,
                ragas_scores=ragas_scores,
                extracted_json=extracted_data,
                ground_truth_json=ground_truth_json,
                template_id=template_id,
                file_ids=file_ids,
                run_full_metrics=run_full_metrics
            )
            
            # Trả về kết quả với tất cả metrics
            evaluation_result = {
                # Core metrics
                "latency": latency,
                "exact_match": all_metrics.get('exact_match', 0),
                "semantic_similarity": all_metrics.get('semantic_similarity', 0),
                "factual_correctness": all_metrics.get('factual_correctness', 0),
                
                # String similarity metrics
                "jaccard_similarity": all_metrics.get('jaccard_similarity', 0),
                "sequence_matcher": all_metrics.get('sequence_matcher', 0),
                "levenshtein_ratio": all_metrics.get('levenshtein_ratio', 0),
                
                # Traditional NLP metrics
                "bleu_score": all_metrics.get('bleu_score', 0),
                "rouge_1_f": all_metrics.get('rouge_1_f', 0),
                "rouge_2_f": all_metrics.get('rouge_2_f', 0),
                "rouge_l_f": all_metrics.get('rouge_l_f', 0),
                
                # Ragas metrics
                "faithfulness": ragas_scores.get('faithfulness', 0),
                "answer_relevancy": ragas_scores.get('answer_relevancy', 0),
                "hallucination_rate": 1.0 - ragas_scores.get('faithfulness', 0),
                
                # Meta info
                "report_path": report_path,
                "evaluated_at": datetime.now().isoformat(),
                "metrics_used": "full" if run_full_metrics else "basic"
            }
            
            # Thêm Ragas metrics bổ sung nếu chạy full
            if run_full_metrics:
                evaluation_result.update({
                    "context_precision": ragas_scores.get('context_precision', 0),
                    "context_recall": ragas_scores.get('context_recall', 0)
                })
            
            print(f"✅ Comprehensive auto-evaluation hoàn tất!")
            print(f"   - Exact Match: {all_metrics.get('exact_match', 0):.2f}%")
            print(f"   - Semantic Similarity: {all_metrics.get('semantic_similarity', 0):.2f}%")
            print(f"   - Factual Correctness: {all_metrics.get('factual_correctness', 0):.2f}%")
            print(f"   - Faithfulness: {ragas_scores.get('faithfulness', 0):.3f}")
            print(f"   - Answer Relevancy: {ragas_scores.get('answer_relevancy', 0):.3f}")
            if run_full_metrics:
                print(f"   - Context Precision: {ragas_scores.get('context_precision', 0):.3f}")
                print(f"   - Context Recall: {ragas_scores.get('context_recall', 0):.3f}")
            
            return evaluation_result
            
        except Exception as e:
            print(f"❌ Lỗi trong quá trình comprehensive auto-evaluation: {e}")
            return None

# Singleton instance
auto_evaluator = AutoEvaluator()
