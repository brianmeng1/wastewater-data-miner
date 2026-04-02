# Wastewater Contaminant Data Miner

Natural language powered data extraction and database generation pipeline for wastewater contaminant literature. Built as part of the UC Berkeley CDSS Discovery Program, Fall 2024.

## Overview

There is no existing approach that can systematically evaluate the risk of de facto wastewater reuse at the national scale, given that there is no routine monitoring of many biological and chemical contaminants discharged with wastewater. This project harnesses the power of language models to scrape and compile data on wastewater contaminants from the vast body of existing literature, building a structured database that can support predictive modeling of contaminant loading.

## Architecture

```
├── config.py                      # Centralized API key management (env variables)
├── scraping/
│   ├── query_generation.py        # LLM-powered boolean search query generation
│   ├── crossref_search.py         # CrossRef API article metadata fetching
│   ├── springer_search.py         # Springer Nature API + Scrapy spider
│   └── doi_scraper.py             # Multi-format fallback web scraping via Selenium
├── extraction/
│   ├── pdf_extraction.py          # LangChain PDF text extraction + LLM entity extraction
│   └── image_extraction.py        # Byaldi + Llama 3.2 Vision multimodal figure analysis
├── storage/
│   ├── vector_db.py               # FAISS vector database for RAG-style document retrieval
│   └── firebase_storage.py        # Firebase cloud storage integration
├── app/
│   └── streamlit_app.py           # User-facing search and exploration interface
└── poster.pdf                     # CDSS Discovery Program presentation poster
```

## Pipeline

1. **Literature Discovery** — User provides a natural language topic. The LLM generates diverse boolean search queries, which are executed against CrossRef and Springer Nature APIs to retrieve article metadata and DOIs.

2. **Document Acquisition** — PDFs are downloaded via DOI links using Selenium. A Scrapy spider crawls Springer for direct PDF URLs. Failed downloads fall back to HTML scraping.

3. **Content Extraction** — Three extraction strategies handle different document formats:
   - **PDF text extraction** via PyPDFLoader with LLM-powered entity tagging (WWTP location, contaminant name, concentration, analytical method, etc.)
   - **HTML scraping** with multi-pattern fallback (tries `pXXXX`, `paraXXXX`, `sparaXXX`, and raw `<span>` elements across publisher formats)
   - **Multimodal extraction** using Byaldi (ColQwen2) for image extraction and Llama 3.2 90B Vision for figure/table summarization

4. **Storage & Retrieval** — Document summaries are embedded using sentence-transformers and indexed in a FAISS vector database for similarity-based retrieval. Raw data is stored in Firebase.

5. **Interface** — A Streamlit application provides researchers with search, filtering, and CSV export capabilities.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in API keys in .env
streamlit run app/streamlit_app.py
```

  ## Acknowledgements

- Dan Wang, California State Water Resources Control Board
- Zwea Htet
- UC Berkeley CDSS Discovery Program


