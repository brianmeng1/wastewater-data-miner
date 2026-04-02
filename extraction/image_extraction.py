"""
Multimodal Image Extraction
Uses Byaldi (ColQwen2) for image extraction from PDFs and Llama 3.2 Vision
(via Groq) to generate text descriptions and numerical summaries of figures.
"""

import os
import base64
from pathlib import Path

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from byaldi import RAGMultiModalModel
    import pdfplumber
    BYALDI_AVAILABLE = True
except ImportError:
    BYALDI_AVAILABLE = False


def extract_images_from_pdf(pdf_path, output_folder="extracted_images"):
    """
    Extract images and text from a PDF using Byaldi and pdfplumber.
    
    Args:
        pdf_path: Path to PDF file
        output_folder: Directory to save extracted images
    
    Returns:
        Tuple of (extracted_text, image_paths)
    """
    if not BYALDI_AVAILABLE:
        raise ImportError("byaldi and pdfplumber are required: pip install byaldi pdfplumber")
    
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)
    
    # Extract text with pdfplumber
    extracted_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n"
    
    # Extract images with Byaldi
    print("Running Byaldi multimodal indexing...")
    model = RAGMultiModalModel.from_pretrained("vidore/colqwen2-v0.1", device="cpu")
    
    image_paths = []
    try:
        results = model.index(pdf_path, index_name="temp_index", overwrite=True)
        for i, result in enumerate(results):
            if hasattr(result, "image"):
                img_path = output_path / f"figure_{i+1}.png"
                result.image.save(str(img_path))
                image_paths.append(str(img_path))
    except Exception as e:
        print(f"Byaldi extraction error: {e}")
    
    print(f"Extracted {len(extracted_text)} chars text, {len(image_paths)} images")
    return extracted_text, image_paths


def summarize_image(image_path, groq_api_key=None):
    """
    Generate a detailed summary of an image using Llama 3.2 Vision via Groq.
    
    Args:
        image_path: Path to the image file
        groq_api_key: Groq API key (from env if not provided)
    
    Returns:
        Text summary of the image content
    """
    if not GROQ_AVAILABLE:
        raise ImportError("groq is required: pip install groq")
    
    if groq_api_key is None:
        groq_api_key = os.getenv("GROQ_API_KEY", "")
    
    client = Groq(api_key=groq_api_key)
    
    # Encode image as base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    response = client.chat.completions.create(
        model="llama-3.2-90b-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"},
                },
                {
                    "type": "text",
                    "text": (
                        "Provide a detailed summary of this scientific figure. "
                        "Focus on numerical data, trends, units, and key findings. "
                        "If it contains a table, extract all values."
                    ),
                },
            ],
        }],
    )
    
    return response.choices[0].message.content


def process_pdf_multimodal(pdf_path, groq_api_key=None):
    """
    End-to-end multimodal extraction: extract images from PDF, then summarize
    each figure using Llama Vision.
    
    Args:
        pdf_path: Path to PDF file
        groq_api_key: Groq API key
    
    Returns:
        Dict with 'text', 'images', and 'summaries' keys
    """
    text, image_paths = extract_images_from_pdf(pdf_path)
    
    summaries = {}
    for img_path in image_paths:
        try:
            summary = summarize_image(img_path, groq_api_key)
            summaries[img_path] = summary
            print(f"Summarized: {img_path}")
        except Exception as e:
            summaries[img_path] = f"Error: {e}"
            print(f"Failed to summarize {img_path}: {e}")
    
    return {"text": text, "images": image_paths, "summaries": summaries}
