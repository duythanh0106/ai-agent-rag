from langchain_core.documents import Document
from typing import List
from docx import Document as DocxDocument
from docx.table import Table
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph
import os

def table_to_markdown(table_data: List[List]) -> str:
    """Convert table data to Markdown format"""
    if not table_data or len(table_data) < 2:
        return ""
    
    markdown = []
    
    headers = table_data[0]
    markdown.append("| " + " | ".join(str(cell) if cell else "" for cell in headers) + " |")
    markdown.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for row in table_data[1:]:
        padded_row = row + [""] * (len(headers) - len(row))
        markdown.append("| " + " | ".join(str(cell) if cell else "" for cell in padded_row[:len(headers)]) + " |")
    
    return "\n".join(markdown)

def extract_docx_table(table: Table) -> str:
    """Extract table from DOCX and convert to Markdown"""
    try:
        table_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            table_data.append(row_data)
        
        if len(table_data) >= 2:
            return table_to_markdown(table_data)
        return ""
    except Exception as e:
        print(f"      ⚠️ DOCX table extraction error: {e}")
        return ""

def extract_content_from_docx(file_path: str) -> List[Document]:
    """Extract text and tables from DOCX file"""
    documents = []
    filename = os.path.basename(file_path)
    
    try:
        doc = DocxDocument(file_path)
        
        # Extract content in order (paragraphs and tables)
        content_parts = []
        current_section = []
        section_num = 0
        table_count = 0
        
        print(f"  📄 Processing DOCX structure...")
        
        # Iterate through document elements in order
        for element in doc.element.body:
            if isinstance(element, CT_P):  # Paragraph
                paragraph = Paragraph(element, doc)
                text = paragraph.text.strip()
                
                if text:
                    current_section.append(text)
            
            elif isinstance(element, CT_Tbl):  # Table
                table = Table(element, doc)
                
                # Save accumulated text before table
                if current_section:
                    section_text = "\n\n".join(current_section)
                    if section_text:
                        content_parts.append({
                            'type': 'text',
                            'content': section_text,
                            'section': section_num
                        })
                        section_num += 1
                    current_section = []
                
                # Extract table
                markdown_table = extract_docx_table(table)
                if markdown_table:
                    table_count += 1
                    content_parts.append({
                        'type': 'table',
                        'content': f"\n**Bảng {table_count}:**\n{markdown_table}\n",
                        'section': section_num
                    })
                    section_num += 1
        
        # Add remaining text
        if current_section:
            section_text = "\n\n".join(current_section)
            if section_text:
                content_parts.append({
                    'type': 'text',
                    'content': section_text,
                    'section': section_num
                })
        
        # Create documents from content parts
        total_sections = len(content_parts)
        
        for i, part in enumerate(content_parts):
            has_table = part['type'] == 'table'
            
            doc_obj = Document(
                page_content=part['content'],
                metadata={
                    "source": filename,
                    "page": i,  # Use section number as "page"
                    "total_pages": total_sections,
                    "type": "docx_table" if has_table else "docx_text",
                    "has_table": has_table,
                    "file_type": "docx"
                }
            )
            documents.append(doc_obj)
        
        print(f"  ✅ Extracted {len(documents)} sections")
        print(f"  📊 Tables found: {table_count}")
        
        return documents
        
    except Exception as e:
        print(f"    ❌ DOCX extraction error: {e}")
        return []