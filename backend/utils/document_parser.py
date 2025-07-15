# backend/utils/document_parser.py

import os
import pandas as pd
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import docx
from pptx import Presentation
from langchain.schema import Document

class DocumentParser:
    """
    Unified document parser for Excel, PDF, Word, PowerPoint files
    """
    
    def __init__(self):
        self.supported_extensions = {
            '.xlsx', '.xls', '.csv',  # Excel
            '.pdf',                   # PDF
            '.docx', '.doc',          # Word
            '.pptx', '.ppt',          # PowerPoint
            '.txt'                    # Text
        }
    
    def parse_file(self, file_path: str) -> List[Document]:
        """
        Parse file based on extension and return LangChain Documents
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {extension}")
        
        try:
            if extension in ['.xlsx', '.xls', '.csv']:
                return self._parse_excel(file_path)
            elif extension == '.pdf':
                return self._parse_pdf(file_path)
            elif extension in ['.docx', '.doc']:
                return self._parse_word(file_path)
            elif extension in ['.pptx', '.ppt']:
                return self._parse_powerpoint(file_path)
            elif extension == '.txt':
                return self._parse_text(file_path)
            else:
                raise ValueError(f"Handler not implemented for {extension}")
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
    
    def _parse_excel(self, file_path: Path) -> List[Document]:
        """Parse Excel files"""
        documents = []
        
        try:
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
                sheet_name = "CSV"
            else:
                # Read all sheets
                excel_file = pd.ExcelFile(file_path)
                all_data = []
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Convert DataFrame to text
                    text_content = f"=== SHEET: {sheet_name} ===\n"
                    
                    # Add headers
                    text_content += "Columns: " + ", ".join(df.columns.tolist()) + "\n\n"
                    
                    # Add data rows
                    for index, row in df.iterrows():
                        row_text = []
                        for col, value in row.items():
                            if pd.notna(value):
                                row_text.append(f"{col}: {value}")
                        text_content += " | ".join(row_text) + "\n"
                    
                    documents.append(Document(
                        page_content=text_content,
                        metadata={
                            "source": str(file_path),
                            "file_type": "excel",
                            "sheet_name": sheet_name,
                            "rows": len(df),
                            "columns": len(df.columns)
                        }
                    ))
                    
        except Exception as e:
            print(f"Error parsing Excel file {file_path}: {e}")
            
        return documents
    
    def _parse_pdf(self, file_path: Path) -> List[Document]:
        """Parse PDF files with OCR fallback"""
        documents = []
        
        try:
            # Method 1: Try text extraction first
            text_content = self._extract_pdf_text(file_path)
            
            # If no text found, use OCR
            if len(text_content.strip()) < 100:
                print(f"PDF {file_path} has little text, trying OCR...")
                text_content = self._extract_pdf_ocr(file_path)
            
            if text_content.strip():
                documents.append(Document(
                    page_content=text_content,
                    metadata={
                        "source": str(file_path),
                        "file_type": "pdf",
                        "extraction_method": "text" if len(text_content) > 100 else "ocr"
                    }
                ))
                
        except Exception as e:
            print(f"Error parsing PDF file {file_path}: {e}")
            
        return documents
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF using pdfplumber"""
        text_content = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n=== PAGE {page_num + 1} ===\n"
                        text_content += page_text + "\n"
                        
                    # Also extract tables
                    tables = page.extract_tables()
                    for table_num, table in enumerate(tables):
                        text_content += f"\n--- TABLE {table_num + 1} ---\n"
                        for row in table:
                            if row:
                                text_content += " | ".join([cell or "" for cell in row]) + "\n"
                                
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            
        return text_content
    
    def _extract_pdf_ocr(self, file_path: Path) -> str:
        """Extract text from PDF using OCR"""
        text_content = ""
        
        try:
            # Convert PDF to images
            pages = convert_from_path(file_path, dpi=300)
            
            for page_num, page in enumerate(pages):
                print(f"OCR processing page {page_num + 1}...")
                
                # Perform OCR
                ocr_text = pytesseract.image_to_string(
                    page, 
                    lang='vie+eng',  # Vietnamese + English
                    config='--psm 6'
                )
                
                if ocr_text.strip():
                    text_content += f"\n=== PAGE {page_num + 1} (OCR) ===\n"
                    text_content += ocr_text + "\n"
                    
        except Exception as e:
            print(f"Error performing OCR on PDF: {e}")
            
        return text_content
    
    def _parse_word(self, file_path: Path) -> List[Document]:
        """Parse Word documents"""
        documents = []
        
        try:
            doc = docx.Document(file_path)
            text_content = ""
            
            # Extract paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    text_content += para.text + "\n"
            
            # Extract tables
            for table_num, table in enumerate(doc.tables):
                text_content += f"\n--- TABLE {table_num + 1} ---\n"
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        row_text.append(cell.text.strip())
                    text_content += " | ".join(row_text) + "\n"
            
            documents.append(Document(
                page_content=text_content,
                metadata={
                    "source": str(file_path),
                    "file_type": "word",
                    "paragraphs": len(doc.paragraphs),
                    "tables": len(doc.tables)
                }
            ))
            
        except Exception as e:
            print(f"Error parsing Word file {file_path}: {e}")
            
        return documents
    
    def _parse_powerpoint(self, file_path: Path) -> List[Document]:
        """Parse PowerPoint presentations"""
        documents = []
        
        try:
            prs = Presentation(file_path)
            text_content = ""
            
            for slide_num, slide in enumerate(prs.slides):
                text_content += f"\n=== SLIDE {slide_num + 1} ===\n"
                
                # Extract text from shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text_content += shape.text + "\n"
                    
                    # Extract text from tables
                    if shape.has_table:
                        text_content += "\n--- TABLE ---\n"
                        table = shape.table
                        for row in table.rows:
                            row_text = []
                            for cell in row.cells:
                                row_text.append(cell.text.strip())
                            text_content += " | ".join(row_text) + "\n"
            
            documents.append(Document(
                page_content=text_content,
                metadata={
                    "source": str(file_path),
                    "file_type": "powerpoint",
                    "slides": len(prs.slides)
                }
            ))
            
        except Exception as e:
            print(f"Error parsing PowerPoint file {file_path}: {e}")
            
        return documents
    
    def _parse_text(self, file_path: Path) -> List[Document]:
        """Parse text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return [Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "file_type": "text"
                }
            )]
        except UnicodeDecodeError:
            # Try different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            return [Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "file_type": "text",
                    "encoding": "latin-1"
                }
            )]
