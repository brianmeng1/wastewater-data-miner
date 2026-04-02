"""
Vector Database
Builds a FAISS index from document embeddings for similarity-based retrieval.
Uses sentence-transformers to embed document summaries, enabling RAG-style
queries against the collected literature.
"""

import os
import csv
import numpy as np

try:
    import fitz  # PyMuPDF
    import faiss
    from sentence_transformers import SentenceTransformer
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False


class DocumentVectorDB:
    """FAISS-backed vector database for academic paper retrieval."""
    
    def __init__(self, embedding_model_name="all-MiniLM-L6-v2"):
        if not DEPS_AVAILABLE:
            raise ImportError("faiss-cpu, sentence-transformers, and PyMuPDF required")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.index = None
        self.metadata = []
        self.embeddings = []
    
    def read_pdf(self, file_path, max_pages=10):
        """Extract text from the first N pages of a PDF."""
        text = ""
        with fitz.open(file_path) as doc:
            for page_num in range(min(max_pages, len(doc))):
                text += doc[page_num].get_text()
        return text
    
    def index_directory(self, pdf_directory, llm=None):
        """
        Index all PDFs in a directory by extracting text, generating metadata
        summaries, and building FAISS embeddings.
        
        Args:
            pdf_directory: Path to directory containing PDF files
            llm: Optional LangChain LLM for generating metadata summaries
        """
        for pdf_file in os.listdir(pdf_directory):
            if not pdf_file.endswith(".pdf"):
                continue
            
            file_path = os.path.join(pdf_directory, pdf_file)
            pdf_text = self.read_pdf(file_path)
            
            if not pdf_text.strip():
                print(f"Skipping empty PDF: {pdf_file}")
                continue
            
            # Generate summary (use first 500 chars if no LLM)
            if llm:
                try:
                    response = llm.invoke(
                        f"Summarize this scientific paper in 2-3 sentences:\n\n{pdf_text[:3000]}"
                    )
                    summary = response.content
                except Exception:
                    summary = pdf_text[:500]
            else:
                summary = pdf_text[:500]
            
            # Generate embeddings
            text_embedding = self.embedding_model.encode(pdf_text[:2000])
            summary_embedding = self.embedding_model.encode(summary)
            
            self.embeddings.append(summary_embedding)
            self.metadata.append({
                "filename": pdf_file,
                "summary": summary,
                "text_embedding": text_embedding.tolist(),
                "summary_embedding": summary_embedding.tolist(),
            })
            
            print(f"Indexed: {pdf_file}")
        
        # Build FAISS index
        if self.embeddings:
            embeddings_np = np.array(self.embeddings).astype("float32")
            self.index = faiss.IndexFlatL2(embeddings_np.shape[1])
            self.index.add(embeddings_np)
            print(f"\nBuilt FAISS index with {len(self.metadata)} documents")
    
    def search(self, query, k=5):
        """
        Search for the most relevant documents given a natural language query.
        
        Args:
            query: Search query string
            k: Number of results to return
        
        Returns:
            List of (metadata_dict, distance) tuples
        """
        if self.index is None:
            raise ValueError("Index not built. Call index_directory() first.")
        
        query_embedding = self.embedding_model.encode(query).reshape(1, -1).astype("float32")
        distances, indices = self.index.search(query_embedding, min(k, len(self.metadata)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                results.append((self.metadata[idx], float(dist)))
        
        return results
    
    def save_metadata(self, output_path="pdf_metadata_embeddings.csv"):
        """Save metadata and embeddings to CSV."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "summary"])
            for meta in self.metadata:
                writer.writerow([meta["filename"], meta["summary"]])
        print(f"Metadata saved to {output_path}")
