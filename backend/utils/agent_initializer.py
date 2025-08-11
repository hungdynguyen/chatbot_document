import asyncio
from typing import Dict, List, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import uuid
# Import các hàm chức năng từ các module của bạn
from .embedding_handler import embed_files_to_qdrant
from .rag_client import query_rag_flow
from .extractor import extract_information_from_docs

# --- ĐỊNH NGHĨA SCHEMA (INPUT) CHO TỪNG TOOL ---

class IngestSchema(BaseModel):
    file_ids: List[str] = Field(description="Danh sách các ID của file đã upload cần xử lý.")

class RagQuerySchema(BaseModel):
    question: str = Field(description="Câu hỏi của người dùng.")
    collection_name: str = Field(description="Tên của collection Qdrant chứa dữ liệu cho session này.")

class ExtractionSchema(BaseModel):
    prompt: str = Field(description="Yêu cầu trích xuất của người dùng, ví dụ: 'trích xuất báo cáo thẩm định'")
    file_ids: List[str] = Field(description="Danh sách ID của các file cần trích xuất.")
    collection_name: str = Field(description="Tên collection Qdrant cho session này.")
    template_id: str = Field(description="ID của template cần trích xuất, ví dụ 'template4'.")

# --- ĐỊNH NGHĨA CÁC LỚP TOOL THEO CHUẨN MỚI ---

class IngestDocumentsTool(BaseTool):
    """
    Công cụ để xử lý và nạp các file đã upload vào cơ sở dữ liệu vector. 
    Chạy công cụ này ĐẦU TIÊN sau khi người dùng upload file.
    """
    name: str = "ingest_documents"
    description: str = "Processes and ingests uploaded files into a vector database. Run this tool FIRST after the user uploads files."
    args_schema: Type[BaseModel] = IngestSchema

    def _run(self, *args, **kwargs):
        raise NotImplementedError("IngestDocumentsTool không hỗ trợ chạy đồng bộ (sync).")

    async def _arun(self, file_ids: List[str]) -> Dict[str, Any]:
        print(f"Tool: Ingesting files {file_ids}")
        try:
            collection_name = await embed_files_to_qdrant(file_ids)
            return {
                "status": "success", 
                "collection_name": collection_name, 
                "message": f"Successfully processed {len(file_ids)} files. Collection '{collection_name}' is ready. You can now ask questions."
            }
        except Exception as e:
            print(f"Error during ingestion: {e}")
            return {"status": "error", "message": f"An error occurred during file processing: {str(e)}"}

class RagQueryTool(BaseTool):
    """Answers user questions based on the ingested documents."""
    name: str = "rag_query"
    description: str = "Answers user questions based on the ingested documents."
    args_schema: Type[BaseModel] = RagQuerySchema

    def _run(self, question: str, collection_name: str) -> Dict[str, Any]:
        print(f"Tool: Querying RAG with question '{question}' on collection '{collection_name}'")
        try:
            answer = query_rag_flow(question, collection_name)
            return {"answer": answer}
        except Exception as e:
            print(f"Error during RAG query: {e}")
            return {"answer": f"An error occurred while searching for an answer: {str(e)}"}
    
    async def _arun(self, question: str, collection_name: str) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._run, question, collection_name)

class StructuredExtractionTool(BaseTool):
    """Extracts structured information from documents based on a predefined template."""
    name: str = "structured_extraction"
    description: str = "Extracts structured information from documents based on a predefined template."
    args_schema: Type[BaseModel] = ExtractionSchema

    def _run(self, *args, **kwargs):
        raise NotImplementedError("StructuredExtractionTool không hỗ trợ chạy đồng bộ (sync).")

    async def _arun(self, prompt: str, file_ids: List[str], collection_name: str, template_id: str) -> Dict[str, Any]:
        print(f"Tool: Extracting info with prompt '{prompt}' from collection '{collection_name}' using template '{template_id}'")
        try:
            extracted_data = await extract_information_from_docs(prompt, file_ids, collection_name, template_id)
            return {"extracted_data": extracted_data, "message": "Structured information extraction complete."}
        except Exception as e:
            print(f"Error during extraction: {e}")
            return {"extracted_data": None, "message": f"An error occurred during extraction: {str(e)}"}

# --- SINGLETON INITIALIZER ---

_tools = None

def _initialize():
    """Initializes tools, ensuring it only runs once."""
    global _tools
    if _tools is None:
        print("🔧 Initializing agent tools...")
        _tools = [
            IngestDocumentsTool(),
            RagQueryTool(),
            StructuredExtractionTool(),
        ]
        print(f"✅ Agent tools initialized: {len(_tools)} tools available.")

def get_tools() -> List[BaseTool]:
    """Returns the list of initialized tools."""
    if _tools is None:
        _initialize()
    return _tools

# Initialize on import
_initialize()