import os
import glob
import json
import pandas as pd
import docx
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
from typing import List, Optional
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentParser:
    """
    A unified document parser for various file formats:
    - Excel (.xlsx, .xls)
    - PDF (.pdf)
    - Word (.docx, .doc)
    - Text (.txt)
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the document parser with configurable chunking parameters.
        
        Args:
            chunk_size: Maximum size of text chunks
            chunk_overlap: Overlap between consecutive chunks
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def parse_file(self, file_path: str) -> List[Document]:
        """
        Parse a file and return a list of Document objects.
        Automatically detects file type and uses appropriate parser.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            List of Document objects
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension in ['.xlsx', '.xls']:
            return self.parse_excel(file_path)
        elif file_extension == '.pdf':
            return self.parse_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return self.parse_word(file_path)
        elif file_extension == '.txt':
            return self.parse_text(file_path)
        else:
            print(f"Unsupported file type: {file_extension}")
            return []
    
    def parse_directory(self, directory_path: str, output_dir: Optional[str] = None) -> dict:
        """
        Parse all supported files in a directory and save results to JSON files.
        
        Args:
            directory_path: Path to the directory containing files to parse
            output_dir: Directory to save the output JSON files (optional)
            
        Returns:
            Dictionary with counts of parsed documents by file type
        """
        directory_path = Path(directory_path)
        
        # Define output directory
        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = directory_path / "output"
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find files by extension
        excel_files = list(directory_path.glob("*.xlsx")) + list(directory_path.glob("*.xls"))
        pdf_files = list(directory_path.glob("*.pdf"))
        word_files = list(directory_path.glob("*.docx")) + list(directory_path.glob("*.doc"))
        text_files = list(directory_path.glob("*.txt"))
        
        # Print summary of files found
        print(f"Found {len(excel_files)} Excel files, {len(pdf_files)} PDF files, "
              f"{len(word_files)} Word files, and {len(text_files)} text files.")
        
        # Dictionary to store counts
        results = {
            "excel": 0,
            "pdf": 0,
            "word": 0,
            "text": 0
        }
        
        # Process Excel files
        if excel_files:
            all_excel_documents = []
            for file_path in excel_files:
                print(f"Parsing Excel file: {file_path}")
                documents = self.parse_excel(file_path)
                all_excel_documents.extend(documents)
                print(f"Parsed {len(documents)} documents from {file_path}")
            
            # Save Excel results
            if all_excel_documents:
                excel_output = output_dir / "excel_documents_parsed.json"
                with excel_output.open("w", encoding="utf-8") as f:
                    json.dump([{"page_content": doc.page_content, "metadata": doc.metadata} 
                              for doc in all_excel_documents], f, ensure_ascii=False, indent=4)
                results["excel"] = len(all_excel_documents)
        
        # Process PDF files
        if pdf_files:
            all_pdf_documents = []
            for file_path in pdf_files:
                print(f"Parsing PDF file: {file_path}")
                documents = self.parse_pdf(file_path)
                all_pdf_documents.extend(documents)
                print(f"Parsed {len(documents)} documents from {file_path}")
            
            # Save PDF results
            if all_pdf_documents:
                pdf_output = output_dir / "pdf_documents_parsed.json"
                with pdf_output.open("w", encoding="utf-8") as f:
                    json.dump([{"page_content": doc.page_content, "metadata": doc.metadata} 
                              for doc in all_pdf_documents], f, ensure_ascii=False, indent=4)
                results["pdf"] = len(all_pdf_documents)
        
        # Process Word files
        if word_files:
            all_word_documents = []
            for file_path in word_files:
                print(f"Parsing Word file: {file_path}")
                documents = self.parse_word(file_path)
                all_word_documents.extend(documents)
                print(f"Parsed {len(documents)} documents from {file_path}")
            
            # Save Word results
            if all_word_documents:
                word_output = output_dir / "word_documents_parsed.json"
                with word_output.open("w", encoding="utf-8") as f:
                    json.dump([{"page_content": doc.page_content, "metadata": doc.metadata} 
                              for doc in all_word_documents], f, ensure_ascii=False, indent=4)
                results["word"] = len(all_word_documents)
        
        # Process Text files
        if text_files:
            all_text_documents = []
            for file_path in text_files:
                print(f"Parsing text file: {file_path}")
                documents = self.parse_text(file_path)
                all_text_documents.extend(documents)
                print(f"Parsed {len(documents)} documents from {file_path}")
            
            # Save Text results
            if all_text_documents:
                text_output = output_dir / "text_documents_parsed.json"
                with text_output.open("w", encoding="utf-8") as f:
                    json.dump([{"page_content": doc.page_content, "metadata": doc.metadata} 
                              for doc in all_text_documents], f, ensure_ascii=False, indent=4)
                results["text"] = len(all_text_documents)
        
        # Save combined results
        all_documents = []
        for file_type in ["excel", "pdf", "word", "text"]:
            input_file = output_dir / f"{file_type}_documents_parsed.json"
            if input_file.exists():
                with input_file.open("r", encoding="utf-8") as f:
                    all_documents.extend(json.load(f))
        
        if all_documents:
            combined_output = output_dir / "all_documents_parsed.json"
            with combined_output.open("w", encoding="utf-8") as f:
                json.dump(all_documents, f, ensure_ascii=False, indent=4)
        
        print(f"Total documents created: {sum(results.values())}")
        return results
    
    def parse_excel(self, file_path: Path) -> List[Document]:
        """
        Parse Excel file một cách tối ưu, biến mỗi hàng của mỗi bảng thành một Document riêng biệt
        với metadata chi tiết.
        """
        documents = []
        
        try:
            # Sử dụng ExcelFile để có thể truy cập các sheet hiệu quả
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # --- Xử lý cho sheet rỗng ---
                if df.empty:
                    continue
                    
                # --- Logic để xác định các bảng riêng biệt trong một sheet ---
                df['is_empty'] = df.isnull().all(axis=1)
                df['table_id'] = df['is_empty'].cumsum()
                
                tables = df.groupby('table_id')
                
                for table_id, table_df in tables:
                    # Bỏ các dòng trống đã dùng làm dấu phân cách
                    table_df = table_df.dropna(how='all').reset_index(drop=True)
                    table_df = table_df.drop(columns=['is_empty', 'table_id'], errors='ignore')

                    if table_df.empty:
                        continue
                    
                    headers = table_df.columns.tolist()

                    for index, row in table_df.iterrows():
                        row_texts = [
                            f"{str(col_name).strip()}: {str(row[col_name]).strip()}"
                            for col_name in headers if pd.notna(row[col_name])
                        ]
                        
                        if not row_texts:
                            continue
                            
                        page_content = " | ".join(row_texts)
                        
                        metadata = {
                            "source": str(file_path),
                            "file_type": "excel",
                            "sheet_name": sheet_name,
                            "table_id": f"table_{table_id}",
                            "row_index_in_table": index
                        }
                        
                        documents.append(Document(
                            page_content=page_content,
                            metadata=metadata
                        ))

        except Exception as e:
            print(f"Error parsing Excel file (optimized) {file_path}: {e}")
                
        return documents
    
    def parse_pdf(self, file_path: Path) -> List[Document]:
        """
        Optimized PDF parser: extracts tables row-by-row and text paragraph-by-paragraph.
        Includes OCR fallback.
        """
        documents = []
        
        # --- Method 1: Direct text and table extraction ---
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # 1. Extract tables first
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        # Giả định hàng đầu tiên là header
                        headers = [h.strip() if h else f"col_{i}" for i, h in enumerate(table[0])]
                        for row_idx, row in enumerate(table[1:], start=1):
                            row_texts = [
                                f"{headers[i]}: {str(cell).strip()}"
                                for i, cell in enumerate(row) if cell and str(cell).strip()
                            ]
                            if not row_texts: continue
                            
                            page_content = " | ".join(row_texts)
                            metadata = {
                                "source": str(file_path), "file_type": "pdf", "page_num": page_num,
                                "content_type": "table_row", "table_id": table_idx, 
                                "row_index_in_table": row_idx, "extraction_method": "text"
                            }
                            documents.append(Document(page_content=page_content, metadata=metadata))

                    # 2. Extract text and chunk it
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_chunks = self.text_splitter.split_text(page_text)
                        for chunk in text_chunks:
                            metadata = {
                                "source": str(file_path), "file_type": "pdf", "page_num": page_num,
                                "content_type": "paragraph", "extraction_method": "text"
                            }
                            documents.append(Document(page_content=chunk, metadata=metadata))
                            
        except Exception as e:
            print(f"Error during direct PDF parsing for {file_path}: {e}")

        # --- Method 2: OCR Fallback if direct extraction yields little content ---
        if not documents or len("".join(d.page_content for d in documents)) < 100:
            print(f"PDF {file_path} has little text, trying OCR...")
            try:
                images = convert_from_path(file_path, dpi=300)
                for page_num, image in enumerate(images, start=1):
                    ocr_text = pytesseract.image_to_string(image, lang='vie+eng')
                    if ocr_text and ocr_text.strip():
                        text_chunks = self.text_splitter.split_text(ocr_text)
                        for chunk in text_chunks:
                            metadata = {
                                "source": str(file_path), "file_type": "pdf", "page_num": page_num,
                                "content_type": "paragraph", "extraction_method": "ocr"
                            }
                            documents.append(Document(page_content=chunk, metadata=metadata))
            except Exception as e:
                print(f"Error during OCR PDF parsing for {file_path}: {e}")

        return documents
    
    def parse_word(self, file_path: Path) -> List[Document]:
        """
        Optimized Word parser: extracts tables row-by-row and text paragraph-by-paragraph.
        """
        documents = []
        try:
            doc = docx.Document(file_path)

            # 1. Extract tables first
            for table_idx, table in enumerate(doc.tables):
                if not table.rows:
                    continue
                
                # Assume the first row is the header
                headers = [cell.text.strip() for cell in table.rows[0].cells]
                
                # Iterate over data rows
                for row_idx, row in enumerate(table.rows[1:], start=1):
                    row_texts = []
                    for i, cell in enumerate(row.cells):
                        cell_text = cell.text.strip()
                        if cell_text:
                            # Use header if available, otherwise use column index
                            header = headers[i] if i < len(headers) else f"col_{i}"
                            row_texts.append(f"{header}: {cell_text}")
                    
                    if not row_texts: continue

                    page_content = " | ".join(row_texts)
                    metadata = {
                        "source": str(file_path),
                        "file_type": "word",
                        "content_type": "table_row",
                        "table_id": table_idx,
                        "row_index_in_table": row_idx
                    }
                    documents.append(Document(page_content=page_content, metadata=metadata))
            
            # 2. Extract and chunk paragraph text
            # The doc.paragraphs object intelligently excludes text within tables.
            full_text = "\n\n".join(
                para.text.strip() for para in doc.paragraphs if para.text.strip()
            )
            
            if full_text:
                text_chunks = self.text_splitter.split_text(full_text)
                for chunk in text_chunks:
                    metadata = {
                        "source": str(file_path),
                        "file_type": "word",
                        "content_type": "paragraph"
                    }
                    documents.append(Document(page_content=chunk, metadata=metadata))

        except Exception as e:
            print(f"Error parsing Word file (optimized) {file_path}: {e}")

        return documents
    
    def parse_text(self, file_path: Path) -> List[Document]:
        """
        Optimized Text parser: reads the entire file and splits it into manageable
        text chunks using the class's text_splitter.
        """
        documents = []
        content = ""
        encoding_used = "utf-8"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"UTF-8 decoding failed for {file_path}. Trying latin-1.")
            encoding_used = "latin-1"
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading text file {file_path} with latin-1: {e}")
                return []
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return []

        if content.strip():
            text_chunks = self.text_splitter.split_text(content)
            for i, chunk in enumerate(text_chunks):
                metadata = {
                    "source": str(file_path),
                    "file_type": "text",
                    "content_type": "text_chunk",
                    "chunk_id": i,
                    "encoding": encoding_used
                }
                documents.append(Document(page_content=chunk, metadata=metadata))
        
        return documents


# Example usage
if __name__ == "__main__":
    # Initialize parser
    parser = DocumentParser()
    
    # Example 1: Parse a single file
    # file_path = "/path/to/document.pdf"
    # documents = parser.parse_file(file_path)
    # print(f"Parsed {len(documents)} documents from {file_path}")
    
    # Example 2: Parse all supported files in a directory
    data_dir = "/mnt/d/Techcombank_/chatbot_document/data/data_real"
    output_dir = "/mnt/d/Techcombank_/chatbot_document/data/output"
    results = parser.parse_directory(data_dir, output_dir)
    
    print("\nParsing Summary:")
    print(f"Excel documents: {results['excel']}")
    print(f"PDF documents: {results['pdf']}")
    print(f"Word documents: {results['word']}")
    print(f"Text documents: {results['text']}")
    print(f"Total documents: {sum(results.values())}")