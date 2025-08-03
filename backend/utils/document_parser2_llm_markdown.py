import os
import json
import time
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional
import google.generativeai as genai
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import warnings
from config import GOOGLE_API_KEY

# Imports for conversion (tích hợp từ file_converter.py)
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

warnings.filterwarnings("ignore", category=UserWarning, module='unstructured')

class DocumentParser:
    """
    Document Parser với conversion support nâng cao cho Gemini.
    Tích hợp file_converter để hỗ trợ nhiều format conversion.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # Rate limiting settings
        self.last_api_call = 0
        self.min_delay_between_calls = 4.0
        self.max_retries = 3
        self.base_retry_delay = 5.0
        
        # API Setup
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY không được tìm thấy trong config.py")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        
        try:
            self.llm_client = genai.GenerativeModel('gemini-2.0-flash')
            print("✅ Gemini client (gemini-2.0-flash) for parsing đã sẵn sàng.")
        except Exception as e:
            print(f"⚠️ Fallback to gemini-1.5-flash: {e}")
            self.llm_client = genai.GenerativeModel('gemini-1.5-flash')
        
        # Supported file types cho direct processing
        self.supported_direct_types = {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
        self.convertible_types = {".docx", ".doc", ".xlsx", ".xls"}
        
        # Check system capabilities
        self.libreoffice_available = self._check_libreoffice()
        self.excel_pdf_available = self._check_excel_pdf_libs()
        
        print(f"🔧 System capabilities:")
        print(f"   - LibreOffice: {'✅' if self.libreoffice_available else '❌'}")
        print(f"   - Excel-to-PDF: {'✅' if self.excel_pdf_available else '❌'}")

    def _check_libreoffice(self) -> bool:
        """Check if LibreOffice is available for document conversion."""
        try:
            result = subprocess.run(['libreoffice', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_excel_pdf_libs(self) -> bool:
        """Check if required libraries for Excel-to-PDF conversion are available."""
        try:
            import pandas as pd
            from reportlab.lib.pagesizes import A4
            return True
        except ImportError:
            return False

    def _convert_to_supported_format(self, file_path: Path) -> Path:
        """
        Convert unsupported files to supported format using enhanced converters.
        """
        file_extension = file_path.suffix.lower()
        
        if file_extension in [".docx", ".doc"]:
            return self._convert_word_to_pdf_enhanced(file_path)
        elif file_extension in [".xlsx", ".xls"]:
            return self._convert_excel_to_pdf_enhanced(file_path)
        else:
            raise ValueError(f"Conversion not supported for {file_extension}")

    def _convert_word_to_pdf_enhanced(self, word_path: Path) -> Path:
        """
        Enhanced Word to PDF conversion with LibreOffice support.
        """
        print(f"🔄 Converting Word to PDF: {word_path.name}")
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            pdf_path = Path(tmp_file.name)
        
        # Method 1: Try LibreOffice (preferred for Linux)
        if self.libreoffice_available:
            try:
                cmd = [
                    'libreoffice',
                    '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', str(pdf_path.parent),
                    str(word_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # LibreOffice creates PDF with same name as input file
                    generated_pdf = pdf_path.parent / f"{word_path.stem}.pdf"
                    if generated_pdf.exists():
                        if generated_pdf != pdf_path:
                            generated_pdf.rename(pdf_path)
                        print(f"✅ LibreOffice conversion successful: {pdf_path}")
                        return pdf_path
                    
            except subprocess.TimeoutExpired:
                print("⚠️ LibreOffice conversion timed out")
            except Exception as e:
                print(f"⚠️ LibreOffice conversion failed: {e}")
        
        # Method 2: Fallback to text extraction
        print("🔄 Falling back to text extraction...")
        return self._extract_docx_text_to_temp_file(word_path)

    def _convert_excel_to_pdf_enhanced(self, excel_path: Path) -> Path:
        """
        Enhanced Excel to PDF conversion maintaining table structure.
        """
        print(f"🔄 Converting Excel to PDF: {excel_path.name}")
        
        if self.excel_pdf_available:
            try:
                # Create temporary PDF file
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                    pdf_path = Path(tmp_file.name)
                
                # Read Excel file
                df_dict = pd.read_excel(excel_path, sheet_name=None)  # Read all sheets
                
                # Create PDF document
                doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()
                
                for sheet_name, sheet_df in df_dict.items():
                    # Add sheet title
                    title = Paragraph(f"<b>{sheet_name}</b>", styles['Heading1'])
                    elements.append(title)
                    elements.append(Spacer(1, 12))
                    
                    # Convert dataframe to table data
                    if not sheet_df.empty:
                        table_data = [list(sheet_df.columns)]  # Headers
                        for row in sheet_df.values:
                            table_data.append([str(cell) if pd.notna(cell) else '' for cell in row])
                        
                        # Create table with styling
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        elements.append(table)
                        elements.append(Spacer(1, 20))
                
                # Build PDF
                doc.build(elements)
                print(f"✅ Excel-to-PDF conversion successful: {pdf_path}")
                return pdf_path
                
            except Exception as e:
                print(f"⚠️ Excel-to-PDF conversion failed: {e}")
        
        # Fallback to text extraction
        print("🔄 Falling back to text extraction...")
        return self._extract_xlsx_text_to_temp_file(excel_path)

    def _extract_docx_text_to_temp_file(self, docx_path: Path) -> Path:
        """
        Extract text from DOCX and save to temporary text file.
        """
        print(f"🔄 Extracting text from DOCX: {docx_path.name}")
        
        try:
            from docx import Document as DocxDocument
            
            doc = DocxDocument(docx_path)
            full_text = []
            
            # Extract paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            # Extract tables
            for table in doc.tables:
                table_text = []
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        table_text.append(row_text)
                if table_text:
                    full_text.extend(table_text)
                    full_text.append("")  # Empty line after table
            
            # Save to temporary text file
            with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write('\n'.join(full_text))
                temp_path = Path(tmp_file.name)
            
            print(f"✅ Extracted to text file: {temp_path}")
            return temp_path
            
        except Exception as e:
            print(f"❌ Text extraction failed: {e}")
            raise

    def _extract_xlsx_text_to_temp_file(self, xlsx_path: Path) -> Path:
        """
        Extract data from XLSX and save to temporary text file.
        """
        print(f"🔄 Extracting data from XLSX: {xlsx_path.name}")
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(xlsx_path)
            full_text = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                if not df.empty:
                    full_text.append(f"=== SHEET: {sheet_name} ===")
                    
                    # Convert to markdown-style table
                    headers = " | ".join(str(col) for col in df.columns)
                    separator = " | ".join("---" for _ in df.columns)
                    full_text.append(headers)
                    full_text.append(separator)
                    
                    for _, row in df.iterrows():
                        row_text = " | ".join(str(cell) if pd.notna(cell) else "" for cell in row)
                        full_text.append(row_text)
                    
                    full_text.append("")  # Empty line between sheets
            
            # Save to temporary text file
            with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write('\n'.join(full_text))
                temp_path = Path(tmp_file.name)
            
            print(f"✅ Extracted to text file: {temp_path}")
            return temp_path
            
        except Exception as e:
            print(f"❌ XLSX extraction failed: {e}")
            raise

    def _apply_rate_limit(self):
        """Apply rate limiting to avoid quota exceeded errors."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_delay_between_calls:
            delay = self.min_delay_between_calls - time_since_last_call
            print(f"⏳ Rate limiting: Đợi {delay:.1f} giây...")
            time.sleep(delay)
        
        self.last_api_call = time.time()

    def _parse_with_llm_with_retry(self, file_path: Path) -> str:
        """
        Parse file với enhanced conversion support và retry logic.
        """
        original_path = file_path
        temp_file_created = False
        
        # Check if conversion is needed
        if file_path.suffix.lower() not in self.supported_direct_types:
            if file_path.suffix.lower() in self.convertible_types:
                print(f"📋 File type {file_path.suffix} không được Gemini hỗ trợ trực tiếp. Đang convert...")
                try:
                    file_path = self._convert_to_supported_format(file_path)
                    temp_file_created = True
                except Exception as conv_error:
                    print(f"❌ Conversion failed: {conv_error}")
                    return ""
            else:
                print(f"❌ File type {file_path.suffix} không được hỗ trợ.")
                return ""

        print(f"🧠 Bắt đầu parsing bằng LLM cho file: {original_path.name}...")
        
        uploaded_file = None
        
        try:
            for attempt in range(self.max_retries):
                try:
                    # Rate limiting
                    self._apply_rate_limit()
                    
                    # Upload file
                    if not uploaded_file:
                        uploaded_file = genai.upload_file(path=str(file_path), display_name=original_path.name)
                    
                    # Wait for processing
                    max_wait_time = 60
                    wait_time = 0
                    while uploaded_file.state.name == "PROCESSING" and wait_time < max_wait_time:
                        time.sleep(2)
                        wait_time += 2
                        uploaded_file = genai.get_file(uploaded_file.name)
                    
                    if uploaded_file.state.name == "FAILED":
                        print(f"❌ File upload failed: {uploaded_file.state}")
                        return ""
                    
                    # Generate content
                    self._apply_rate_limit()
                    
                    prompt = """
Phân tích file được cung cấp và chuyển đổi TOÀN BỘ nội dung thành Markdown.

YÊU CẦU:
1. Bảo toàn 100% nội dung: văn bản, số liệu, bảng
2. Chuyển bảng thành định dạng Markdown table
3. Giữ nguyên cấu trúc: tiêu đề, danh sách
4. Không tóm tắt, không thêm comment
5. Chỉ trả về Markdown content

Trả về nội dung Markdown:
"""

                    response = self.llm_client.generate_content([uploaded_file, prompt])
                    print(f"✅ LLM đã parse thành công file: {original_path.name}")
                    return response.text

                except Exception as e:
                    error_message = str(e)
                    
                    if "429" in error_message or "quota" in error_message.lower():
                        retry_delay = self.base_retry_delay * (2 ** attempt)
                        print(f"  ⚠️ Gặp lỗi Rate Limit. Đang thử lại sau {retry_delay} giây... (Lần {attempt + 1}/{self.max_retries})")
                        time.sleep(retry_delay)
                        continue
                    elif "mimeType" in error_message or "not supported" in error_message:
                        print(f"❌ Lỗi MIME type không được hỗ trợ: {e}")
                        break
                    elif "503" in error_message or "Service Unavailable" in error_message:
                        retry_delay = self.base_retry_delay * (2 ** attempt)
                        print(f"  ⚠️ Gemini service unavailable. Đang thử lại sau {retry_delay} giây... (Lần {attempt + 1}/{self.max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"❌ Lỗi khác khi parsing: {e}")
                        break
            
            print(f"  ❌ Đã thử lại {self.max_retries} lần nhưng vẫn gặp lỗi. Bỏ cuộc.")
            return ""
            
        finally:
            # Cleanup
            if uploaded_file:
                try:
                    genai.delete_file(uploaded_file.name)
                    print(f"🧹 Đã cleanup uploaded file: {original_path.name}")
                except:
                    pass
            
            # Remove temporary file if created
            if temp_file_created and file_path.exists():
                try:
                    os.unlink(file_path)
                    print(f"🧹 Đã xóa file tạm: {file_path}")
                except:
                    pass

    def parse_file(self, file_path: str) -> List[Document]:
        """
        Parse file với enhanced conversion support.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ File không tồn tại: {file_path}")
            return []
        
        # Parse với LLM
        full_markdown_content = self._parse_with_llm_with_retry(file_path)
        
        if not full_markdown_content or not full_markdown_content.strip():
            print(f"⚠️ LLM không trả về nội dung nào cho file {file_path.name}. Trả về danh sách rỗng.")
            return []
            
        # Chunking
        print(f"🔪 Bắt đầu chunking nội dung Markdown (độ dài: {len(full_markdown_content)} chars)...")
        
        chunks = self.text_splitter.create_documents([full_markdown_content])
        
        # Add metadata
        for chunk in chunks:
            chunk.metadata = {
                "source": str(file_path),
                "basename": file_path.name,
                "file_type": file_path.suffix.lower(),
                "content_type": "llm_parsed_markdown_chunk",
                "parser_method": "gemini_enhanced"
            }
            
        print(f"✅ Hoàn tất! Tạo ra {len(chunks)} documents từ file {file_path.name}.")
        return chunks

    def convert_file_to_pdf(self, file_path: str, output_pdf_path: Optional[str] = None) -> Optional[str]:
        """
        Public method to convert files to PDF format.
        
        Args:
            file_path: Path to input file
            output_pdf_path: Optional output path for PDF
            
        Returns:
            Path to converted PDF file or None if conversion failed
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.convertible_types:
            print(f"❌ Conversion không được hỗ trợ cho file type: {file_extension}")
            return None
        
        try:
            if output_pdf_path:
                output_path = Path(output_pdf_path)
            else:
                output_path = file_path.with_suffix('.pdf')
            
            if file_extension in ['.docx', '.doc']:
                converted_path = self._convert_word_to_pdf_enhanced(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                converted_path = self._convert_excel_to_pdf_enhanced(file_path)
            else:
                return None
            
            # Move converted file to desired location if different
            if converted_path != output_path:
                converted_path.rename(output_path)
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            return None