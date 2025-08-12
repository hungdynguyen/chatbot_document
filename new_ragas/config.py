import os
# API KEYS
DELAY_BETWEEN_CALLS = 0
DEEPSEEK_API_KEY = ""
GOOGLE_API_KEY = "AIzaSyCm7HiIOyph1ZJY0Vf4aqYreZ_iUc3tz3w"
LIST_GOOGLE_API_KEYS = [ "AIzaSyAWtCSrLhJDZGF1ArOSS0o7Iy_zMG42810",
                    "AIzaSyCaKzwEjW0XxJAuZ9XdzI6rHkifHkA0eNY",
                    "AIzaSyBH8O5IfqYrJ5wtWnmUC21IfMjzJCrTm3I",
                    "AIzaSyDtBIjTSfbvuEsobNwjtdyi9gVpDrCaWPM",
                    "AIzaSyAD_58r3fQhcTOE6qQS1YlR3iJ_ZnGKy10",
                    "AIzaSyCtAz9maZ9usoxEHhhFocHW07WM4IbgOXo",
                    "AIzaSyCI8QGQrVUgr_FrFLttDs0fP4VyJyPXoec",
                    "AIzaSyBPglAFlDOf97drnNAplHIIsjgvsfzezsI",
                    "AIzaSyDNosIJZjXd2tzm7_VKxK5uFTBmoPuHXkc"]
# --- CẤU HÌNH QDRANT & EMBEDDING ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "child_chunks_eval_notebook" 

#Cau hinh Re-ranker model
RERANKER_MODEL_NAME = 'BAAI/bge-reranker-large'
RERANKER_DEVICE = "cpu"  

# Cấu hình model embedding
EMBEDDING_MODEL_NAME = "jinaai/jina-embeddings-v3"
EMBEDDING_DEVICE = "cpu" 


HEADERS = {"Content-Type": "application/json; charset=utf-8"}
