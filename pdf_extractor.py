"""
PDF Text Extraction Module
Extracts text content from PDF resumes
"""

import PyPDF2
import re
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from all pages
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        # Clean up the text
        text = clean_extracted_text(text)
        return text
    
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {str(e)}")
        return ""


def clean_extracted_text(text):
    """
    Clean extracted text from PDF
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep important ones
    text = re.sub(r'[^\w\s\+\#\-\.\,\(\)]', ' ', text)
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    return text.strip()


def extract_from_multiple_pdfs(pdf_folder):
    """
    Extract text from multiple PDF files in a folder
    
    Args:
        pdf_folder: Path to folder containing PDF files
        
    Returns:
        Dictionary with filename as key and extracted text as value
    """
    pdf_folder = Path(pdf_folder)
    resumes = {}
    
    for pdf_file in pdf_folder.glob("*.pdf"):
        text = extract_text_from_pdf(pdf_file)
        if text:
            resumes[pdf_file.name] = text
    
    return resumes


if __name__ == "__main__":
    # Test the extraction
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        text = extract_text_from_pdf(pdf_path)
        print(f"Extracted text from {pdf_path}:")
        print("-" * 50)
        print(text[:500])  # Print first 500 characters
    else:
        print("Usage: python pdf_extractor.py <path_to_pdf>")
