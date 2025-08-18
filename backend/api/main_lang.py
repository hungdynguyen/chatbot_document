import os
import asyncio
import re
from typing import Dict, List, Any, TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
import operator
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
import uuid
import time
import traceback
# Import from your project
from config import GOOGLE_API_KEY, UPLOAD_DIRECTORY, origins, TOGETHER_API_KEY, DEEPSEEK_API_KEY
from utils.agent_initializer import get_tools

# --- 1. SETUP FASTAPI APP ---
app = FastAPI(title="LangGraph Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, you can use wildcard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DEFINE LANGGRAPH AGENT ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    collection_name: Optional[str]
    file_ids: List[str]

# Initialize tools and LLM
tools = get_tools()
tool_node = ToolNode(tools)

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
llm_with_tools = llm.bind_tools(tools)

# Node definitions

async def ingest_node(state: AgentState):
    print("--- Node: INGEST (Bắt buộc) ---")
    file_ids = state['file_ids']
    
    ingest_tool = next((t for t in tools if t.name == "ingest_documents"), None)
    if not ingest_tool:
        raise ValueError("Không tìm thấy IngestDocumentsTool.")

    tool_input = {"file_ids": file_ids}
    result = await ingest_tool.arun(tool_input)
    
    collection_name = result.get("collection_name")
    user_message = result.get("message", "Lỗi trong quá trình nạp dữ liệu.")
    
    print(f"--- Hoàn tất Ingestion. Collection: {collection_name} ---")
    return {
        "collection_name": collection_name,
        "messages": [AIMessage(content=user_message)]
    }
    
# def agent_node(state: AgentState):
#     print("--- Node: AGENT (Hỏi-đáp) ---")
    
#     collection_name = state.get('collection_name')
#     if not collection_name:
#         return {"messages": [AIMessage(content="Lỗi: Chưa có dữ liệu nào được nạp.")]}
    
#     formatted_history = ""
#     for msg in state['messages']:
#         if isinstance(msg, SystemMessage):
#             continue
#         if isinstance(msg, HumanMessage):
#             formatted_history += f"Người dùng: {msg.content}\n"
#         elif isinstance(msg, AIMessage):
#             # Kiểm tra xem tin nhắn AI có tool_calls không
#             if msg.tool_calls:
#                 tool_info = json.dumps(msg.tool_calls, ensure_ascii=False)
#                 formatted_history += f"AI (quyết định gọi tool): {tool_info}\n"
#             else:
#                 formatted_history += f"AI: {msg.content}\n"
#         elif isinstance(msg, ToolMessage):
#             formatted_history += f"Kết quả Tool ({msg.tool_call_id}): {msg.content}\n"

#     # 2. Tạo một prompt cuối cùng, rõ ràng và đầy đủ
#     # Prompt này ra lệnh cho LLM phải sử dụng collection_name được cung cấp.
#     final_prompt_for_decision = f"""Bạn là một trợ lý AI có khả năng sử dụng các công cụ.

#         QUY TẮC BẮT BUỘC: Khi bạn cần sử dụng bất kỳ công cụ nào yêu cầu "collection_name", bạn PHẢI sử dụng giá trị sau: "{collection_name}"

#         Dựa vào lịch sử trò chuyện dưới đây, hãy quyết định bước tiếp theo.
#         - Nếu bạn có đủ thông tin, hãy trả lời trực tiếp câu hỏi cuối cùng của người dùng.
#         - Nếu không, hãy gọi công cụ cần thiết với các tham số chính xác (bao gồm cả "collection_name" đã được cung cấp).

#         --- LỊCH SỬ TRÒ CHUYỆN ---
#                 {formatted_history}
#                 ---

#         Hãy hành động.
#         """
#     response = llm_with_tools.invoke([HumanMessage(content=final_prompt_for_decision)])
#     return {"messages": [response]}


def agent_node(state: AgentState):
    print("--- Node: AGENT (Hỏi-đáp) ---")
    
    collection_name = state.get('collection_name')
    if not collection_name:
        return {"messages": [AIMessage(content="Lỗi: Chưa có dữ liệu nào được nạp.")]}
    
    formatted_history = ""
    for msg in state['messages']:
        if isinstance(msg, SystemMessage):
            continue
        if isinstance(msg, HumanMessage):
            formatted_history += f"Người dùng: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            # Kiểm tra xem tin nhắn AI có tool_calls không
            if msg.tool_calls:
                tool_info = json.dumps(msg.tool_calls, ensure_ascii=False)
                formatted_history += f"AI (quyết định gọi tool): {tool_info}\n"
            else:
                formatted_history += f"AI: {msg.content}\n"
        elif isinstance(msg, ToolMessage):
            formatted_history += f"Kết quả Tool ({msg.tool_call_id}): {msg.content}\n"

    # Tạo prompt rõ ràng hơn về việc sử dụng rag_query
    final_prompt_for_decision = f"""Bạn là một trợ lý AI chuyên nghiệp.

        HƯỚNG DẪN: Dựa vào lịch sử trò chuyện, hãy quyết định hành động tiếp theo.

        QUY TẮC TUYỆT ĐỐI:
        1.  Nếu tin nhắn cuối cùng trong lịch sử là một "Kết quả Tool", nhiệm vụ duy nhất của bạn là trình bày lại kết quả đó một cách trực tiếp và ngắn gọn cho người dùng.
            - Ví dụ: Nếu Kết quả Tool là "CÔNG TY CỔ PHẦN MẶT DỰNG CAG", bạn PHẢI trả lời chính xác "CÔNG TY CỔ PHẦN MẶT DỰNG CAG".
            - TUYỆT ĐỐI KHÔNG thêm các câu hội thoại như "Tôi đã tìm thấy thông tin", "Tôi hiểu rồi", hoặc "Bạn có câu hỏi nào khác không?".
        2.  Nếu bạn chưa có đủ thông tin, hãy gọi công cụ `rag_query` với `collection_name` là "{collection_name}".
        3.  KHÔNG trả lời câu hỏi về tài liệu mà không sử dụng công cụ.

        --- LỊCH SỬ TRÒ CHUYỆN ---
        {formatted_history}
        ---

        Bây giờ, hãy thực hiện hành động của bạn.
        """
    response = llm_with_tools.invoke([HumanMessage(content=final_prompt_for_decision)])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    print("--- Node: ROUTER ---")
    messages = state["messages"]
    last_message = messages[-1]
    
    # Kiểm tra số lượng vòng lặp
    tool_messages_count = sum(1 for msg in messages if isinstance(msg, ToolMessage))
    if tool_messages_count >= 50:  # Giới hạn số lần gọi tool
        print("Decision: Đã đạt giới hạn gọi tool, kết thúc")
        return "end"
    
    # Kiểm tra tool calls - cải thiện detection
    has_tool_call = False
    
    # Kiểm tra thuộc tính tool_calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        has_tool_call = True
        tool_names = [call['name'] for call in last_message.tool_calls]
        print(f"Decision: Call tool(s): {tool_names}")
    
    # Kiểm tra additional_kwargs nếu tool_calls không được tìm thấy
    elif hasattr(last_message, 'additional_kwargs') and last_message.additional_kwargs.get('tool_calls'):
        has_tool_call = True
        tool_names = [call['name'] for call in last_message.additional_kwargs['tool_calls']]
        print(f"Decision: Call tool(s): {tool_names}")
    
    # Kiểm tra nội dung tin nhắn AI cho các từ khóa liên quan đến tool
    elif isinstance(last_message, AIMessage) and any(keyword in last_message.content.lower() for keyword in ['rag_query', 'truy vấn tài liệu', 'cần sử dụng công cụ']):
        print(f"Decision: Message indicates tool use intent but lacks proper tool_calls.")
        # Fix: Properly structure the tool call with 'args' key
        if not hasattr(last_message, 'tool_calls'):
            last_message.tool_calls = []
        
        # Add a properly formatted tool call
        last_message.tool_calls.append({
            "name": "rag_query", 
            "args": {  # This key must exist
                "question": "Câu hỏi từ người dùng",
                "collection_name": state.get("collection_name", "")
            }
        })
        has_tool_call = True
    
    if has_tool_call:
        return "action"
    else:
        print("Decision: End")
        return "end"

# def should_continue(state: AgentState) -> str:
#     print("--- Node: ROUTER ---")
#     last_message = state["messages"][-1]
    
#     # Kiểm tra số lượng vòng lặp
#     tool_messages_count = sum(1 for msg in state["messages"] if isinstance(msg, ToolMessage))
#     if tool_messages_count >= 50:  # Giới hạn số lần gọi tool
#         print("Decision: Đã đạt giới hạn gọi tool, kết thúc")
#         return "end"
    
#     # Kiểm tra tool calls
#     if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
#         tool_names = [call['name'] for call in last_message.tool_calls]
#         print(f"Decision: Call tool(s): {tool_names}")
#         return "action"
#     else:
#         print("Decision: End")
#         return "end"


def entry_router(state: AgentState) -> str:
    print("--- Node: ENTRY ROUTER ---")
    if state.get("collection_name"):
        print("  Decision: Collection đã tồn tại, chuyển đến agent.")
        return "agent"
    else:
        print("  Decision: Chưa có collection, chuyển đến ingest.")
        return "ingest"

# Build graph
workflow = StateGraph(AgentState)

workflow.add_node("ingest", ingest_node)
workflow.add_node("agent", agent_node)
workflow.add_node("action", tool_node)

workflow.set_conditional_entry_point(
    entry_router,
    {
        "ingest": "ingest",
        "agent": "agent",
    }
)

workflow.add_edge("ingest", "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "action": "action",
        "end": END,
    }
)
workflow.add_edge("action", "agent")

langgraph_app = workflow.compile()

# Store active sessions
active_sessions: Dict[str, Dict] = {}

# --- 3. API ENDPOINTS ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    file_ids: Optional[List[str]] = None
    collection_name: Optional[str] = None
@app.post("/chat_rag")
async def chat_rag(request: ChatRequest):
    """
    Endpoint for chat with RAG functionality
    """
    session_id = request.session_id 
    is_new_session = not session_id or session_id not in active_sessions
    
    if is_new_session:
        # Tạo session ID mới, duy nhất
        session_id = f"session_{uuid.uuid4().hex}"
        print(f"🚀 Creating new session: {session_id}")
        # LOGIC QUAN TRỌNG ĐỂ TEST WORKFLOW CỦA BẠN
        if request.collection_name:
            print(f"  -> Using pre-existing collection from extraction: {request.collection_name}")
            if not request.file_ids:
                 raise HTTPException(status_code=400, detail="file_ids are required for context, even with an existing collection.")
            # Tạo state ban đầu cho phiên mới
            current_state = {
                "messages": [
                    SystemMessage(content="Bạn là một trợ lý tài liệu thông minh."),
                ],
                "file_ids": request.file_ids,
                "collection_name": request.collection_name,  # Bắt đầu với None để entry_router đưa vào ingest
            }    
        else:
            # KỊCH BẢN 2: Bắt đầu một phiên chat RAG bình thường
            print("  -> Standard new session, will perform ingestion.")
            if not request.file_ids:
                raise HTTPException(status_code=400, detail="No 'file_ids' provided for a new session.")
            
            # Tạo state với collection_name là None để kích hoạt 'ingest'
            current_state = {
                "messages": [SystemMessage(content="Bạn là một trợ lý tài liệu thông minh.")],
                "file_ids": request.file_ids,
                "collection_name": None, # SẼ KÍCH HOẠT INGEST
            }
    else:
        # Nếu là phiên đã tồn tại, lấy state từ bộ nhớ
        print(f"🔄 Continuing session: {session_id}")
        current_state = active_sessions[session_id]

    # Thêm tin nhắn mới của người dùng vào state
    current_state["messages"].append(HumanMessage(content=request.message))
    
    try:
        # Chạy graph với state hiện tại
        final_state = await langgraph_app.ainvoke(current_state, config={"recursion_limit": 10})
        
        # Cập nhật state mới nhất vào bộ nhớ
        active_sessions[session_id] = final_state
        
        # Trích xuất câu trả lời cuối cùng từ AI một cách an toàn
        answer = "Xin lỗi, tôi chưa thể tìm ra câu trả lời."
        for msg in reversed(final_state['messages']):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                answer = msg.content
                break
        
        # Chuẩn bị dữ liệu trả về cho front-end
        response_data = {
            "answer": answer,
            "session_id": session_id,
            "collection_name": final_state.get("collection_name")
        }
            
        return response_data
    except Exception as e:
        print(f"Error in chat_rag for session {session_id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    """
    Handle file uploads
    """
    try:
        upload_dir = Path(UPLOAD_DIRECTORY)
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        return {
            "filename": file.filename, 
            "content_type": file.content_type, 
            "file_id": file.filename
        }
    except Exception as e:
        print(f"Error in upload_file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_prompt")
async def process_prompt(request: Request):
    """
    Process extraction prompts with improved response format
    """
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        file_ids = data.get("file_ids", [])
        template_id = data.get("template_id", "template4")
        
        if not prompt or not file_ids:
            raise HTTPException(status_code=400, detail="Missing prompt or file_ids")
        
        # Tạo ID duy nhất cho phiên làm việc này
        unique_session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        print(f"🆔 Phiên trích xuất mới: {unique_session_id}")
        
        start_time = time.time()
        
        # First ingest documents if needed
        ingest_tool = next((t for t in tools if t.name == "ingest_documents"), None)
        ingest_result = await ingest_tool.arun({"file_ids": file_ids})
        collection_name = ingest_result.get("collection_name")
        
        if not collection_name:
            raise HTTPException(status_code=500, detail="Failed to ingest documents")
        
        
        # QUAN TRỌNG: Giới hạn thời gian chạy extraction để tránh vòng lặp vô tận
        extraction_tool = next((t for t in tools if t.name == "structured_extraction"), None)
        
        # Tạo task với timeout
        extraction_task = asyncio.create_task(extraction_tool.arun({
            "prompt": prompt,
            "file_ids": file_ids,
            "collection_name": collection_name,
            "template_id": template_id
        }))
        
        try:
            # Set timeout 5 phút
            extraction_result = await asyncio.wait_for(extraction_task, timeout=1000)
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Extraction timed out after 1000 seconds - possible infinite loop detected"
            }
        
        # Lấy extracted_data từ kết quả
        extracted_data = extraction_result.get("extracted_data", {})
        
        # Đảm bảo extracted_data là một đối tượng JSON hợp lệ
        if not isinstance(extracted_data, dict):
            print("⚠️ extracted_data không phải dict! Chuyển đổi sang dict rỗng")
            extracted_data = {}
            
        # In ra cấu trúc JSON để debug
        print("\n🔍 CẤU TRÚC CUỐI CÙNG CỦA DỮ LIỆU:")
        print("-"*50)
        import pprint
        pprint.pprint({k: type(v).__name__ for k, v in extracted_data.items()})
        print("-"*50)
        
        # Đảm bảo có đủ các trường chính của template4
        if template_id == "template4":
            expected_keys = ["thongTinChung", "thongTinKhachHang", "hoatDongKinhDoanh", "thongTinNganh"]
            for key in expected_keys:
                if key not in extracted_data:
                    extracted_data[key] = {}
        
        # Tính latency
        end_time = time.time()
        latency = end_time - start_time
        
        # Format response giống như main.py để đảm bảo tính tương thích
        response_data = {
            "summary": "Quá trình trích xuất thông tin đã hoàn tất.",
            "extracted_data": extracted_data,
            "prompt": prompt,
            "file_ids": file_ids,
            "collection_name": collection_name,
            "processing_time": latency,
            "status": "success",
            "message": f"Extracted data successfully",
            "session_id": unique_session_id,
        }
        
        # Lưu JSON kết quả để debug
        try:
            debug_dir = os.path.join(os.path.dirname(__file__), "..", "debug_output")
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, f"api_response_{unique_session_id}.json")
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Đã lưu API response để debug tại: {debug_file}")
        except Exception as debug_err:
            print(f"⚠️ Không thể lưu file debug API: {debug_err}")
        
        return response_data
    except Exception as e:
        print(f"Error in process_prompt: {e}")
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        
        # Trả về lỗi chi tiết để dễ debug
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n{traceback_str}")

@app.post("/clear_rag_session")
async def clear_rag_session(request: Request):
    """
    Clear a RAG session
    """
    try:
        data = await request.json()
        session_id = data.get("session_id", "default")
        
        if session_id in active_sessions:
            del active_sessions[session_id]
            
        return {"status": "success", "message": f"Session {session_id} cleared"}
    except Exception as e:
        print(f"Error in clear_rag_session: {e}")
        return {"status": "success", "message": "Session cleared (error handled)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


