import os
from pathlib import Path
import subprocess
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile
# Check for LibreOffice availability (Linux alternative)
def check_libreoffice():
    try:
        result = subprocess.run(['libreoffice', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

LIBREOFFICE_AVAILABLE = check_libreoffice()
if not LIBREOFFICE_AVAILABLE:
    print("LibreOffice not found. Install with: sudo apt-get install libreoffice")

# For Excel to PDF conversion
try:
    EXCEL_PDF_AVAILABLE = True
except ImportError:
    EXCEL_PDF_AVAILABLE = False
    print("Required packages not available. Install with: pip install openpyxl pandas reportlab")

def convert_word_to_pdf(word_file_path, output_pdf_path=None):
    """
    Convert Word document to PDF using LibreOffice (Linux compatible)
    """
    if not LIBREOFFICE_AVAILABLE:
        print("LibreOffice is required for Word to PDF conversion on Linux")
        return False
    
    try:
        word_file_path = Path(word_file_path)
        if output_pdf_path is None:
            output_pdf_path = word_file_path.with_suffix('.pdf')
        else:
            output_pdf_path = Path(output_pdf_path)
        
        # Use LibreOffice headless mode for conversion
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(output_pdf_path.parent),
            str(word_file_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # LibreOffice creates PDF with same name as input file
            generated_pdf = output_pdf_path.parent / f"{word_file_path.stem}.pdf"
            if generated_pdf != output_pdf_path and generated_pdf.exists():
                generated_pdf.rename(output_pdf_path)
            
            print(f"Successfully converted {word_file_path} to {output_pdf_path}")
            return True
        else:
            print(f"LibreOffice conversion failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("LibreOffice conversion timed out")
        return False
    except Exception as e:
        print(f"Error converting Word to PDF: {e}")
        return False

def convert_excel_to_pdf(excel_file_path, output_pdf_path=None):
    """
    Convert Excel file to PDF maintaining table structure
    """
    if not EXCEL_PDF_AVAILABLE:
        print("Required packages not available for Excel to PDF conversion")
        return False
    
    try:
        if output_pdf_path is None:
            output_pdf_path = str(Path(excel_file_path).with_suffix('.pdf'))
        
        # Read Excel file
        df = pd.read_excel(excel_file_path, sheet_name=None)  # Read all sheets
        
        # Create PDF document
        doc = SimpleDocTemplate(output_pdf_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        for sheet_name, sheet_df in df.items():
            # Add sheet title
            title = Paragraph(f"<b>{sheet_name}</b>", styles['Heading1'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Convert dataframe to table data
            table_data = [list(sheet_df.columns)]  # Headers
            for row in sheet_df.values:
                table_data.append([str(cell) if pd.notna(cell) else '' for cell in row])
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(elements)
        print(f"Successfully converted {excel_file_path} to {output_pdf_path}")
        return True
    except Exception as e:
        print(f"Error converting Excel to PDF: {e}")
        return False

def convert_file_to_pdf(file_path, output_pdf_path=None):
    """
    Auto-detect file type and convert to PDF
    """
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    if file_extension in ['.docx', '.doc']:
        return convert_word_to_pdf(file_path, output_pdf_path)
    elif file_extension in ['.xlsx', '.xls']:
        return convert_excel_to_pdf(file_path, output_pdf_path)
    else:
        print(f"Unsupported file format: {file_extension}")
        return False
