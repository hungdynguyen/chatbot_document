from typing import Dict, List, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

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

    def _run(self, *args, **kwargs):
        raise NotImplementedError("StructuredExtractionTool không hỗ trợ chạy đồng bộ (sync).")

    async def _arun(self, prompt: str, file_ids: List[str], collection_name: str, template_id: str) -> Dict[str, Any]:
        print(f"Tool: Extracting info with prompt '{prompt}' from collection '{collection_name}' using template '{template_id}'")
        try:
            # Import here to avoid circular import
            from .extractor import extract_information_from_docs
            extracted_data = await extract_information_from_docs(prompt, file_ids, collection_name, template_id)
            return {"extracted_data": extracted_data, "message": "Structured information extraction complete."}
        except Exception as e:
            print(f"Error during extraction: {e}")
            return {"extracted_data": None, "message": f"An error occurred during extraction: {str(e)}"}