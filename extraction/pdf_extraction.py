"""
PDF Extraction
Extracts text from PDF documents using PyPDFLoader, then queries an LLM
to extract structured contaminant data (location, sampling time, contaminant
name, concentration, analytical method, etc.).
"""

import os
from langchain.document_loaders import PyPDFLoader


def extract_text_from_pdf(file_path):
    """
    Extract full text from a PDF file using PyPDFLoader.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Concatenated text from all pages, or empty string on failure
    """
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        full_text = "\n".join(page.page_content for page in pages)
        print(f"Extracted {len(full_text)} characters from {len(pages)} pages")
        return full_text
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return ""


def generate_extraction_prompt(user_query, full_text):
    """
    Build a prompt for the LLM to extract structured data from paper text.
    
    Args:
        user_query: What information to extract (e.g., contaminant names and concentrations)
        full_text: Full text of the paper
    
    Returns:
        Formatted prompt string
    """
    return f"""You are an expert assistant tasked with analyzing scientific papers and 
providing detailed insights. Your goal is to answer the following user query as 
comprehensively as possible, using the content of the provided paper:

### User Query
{user_query}

### Content of the Paper
{full_text}

### Instructions:
1. Extract and include all relevant information from the paper.
2. If the paper contains tables or numerical data related to the query, 
   present them in a structured format.
3. If the information is not available in the paper, clearly state that.
4. Be precise with numerical values, units, and methodological details.
5. Cite specific sections or tables when referencing data.
"""


def query_llm(llm, prompt):
    """
    Send an extraction prompt to the LLM and return the response.
    
    Args:
        llm: LangChain LLM instance
        prompt: Extraction prompt string
    
    Returns:
        LLM response text
    """
    messages = [
        ("system", "You are an assistant extracting structured data from scientific papers."),
        ("user", prompt),
    ]
    response = llm.invoke(messages)
    return response.content


def extract_contaminant_data(llm, pdf_path, fields=None):
    """
    End-to-end extraction: load PDF → build prompt → query LLM → return structured data.
    
    Args:
        llm: LangChain LLM instance
        pdf_path: Path to PDF file
        fields: List of fields to extract (defaults to standard contaminant fields)
    
    Returns:
        LLM response with extracted data
    """
    if fields is None:
        fields = [
            "WWTP location",
            "time of sampling",
            "influent or effluent measurement",
            "sample type",
            "analytical method",
            "contaminant name",
            "concentration value",
            "unit of measure",
        ]
    
    full_text = extract_text_from_pdf(pdf_path)
    if not full_text:
        return "Failed to extract text from PDF."
    
    query = f"Extract the following fields from this paper: {', '.join(fields)}"
    prompt = generate_extraction_prompt(query, full_text)
    
    return query_llm(llm, prompt)


# Example queries for demonstration:
DEMO_PROMPTS = [
    "I want to find information on the WWTP location, time of sampling, "
    "if the measurement was influent or effluent, sample type, analytical method, "
    "contaminant name, concentration value, unit of measure",
    "I want to find information on water contaminant names and concentration levels",
    "What treatment processes are described and what are their removal efficiencies?",
]
