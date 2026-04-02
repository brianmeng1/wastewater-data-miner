"""
California Wastewater Contaminant Research
Streamlit interface for searching, fetching, and exploring scientific literature
on wastewater contaminants in California.

Usage: streamlit run app/streamlit_app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd

from config import get_llm, SPRINGER_API_KEY
from scraping.query_generation import generate_search_queries
from scraping.crossref_search import fetch_articles
from scraping.springer_search import fetch_springer_articles

st.set_page_config(
    page_title="California Wastewater Contaminant Database",
    page_icon="💧",
    layout="wide",
)

st.title("California Wastewater Contaminant Research")
st.markdown(
    "This database allows researchers to explore scientific literature "
    "on wastewater contaminants in California."
)

# Search filters
all_words = st.text_input("With all of the words")
exact_phrase = st.text_input("With the exact phrase")
at_least_one_word = st.text_input("With at least one of the words")
without_words = st.text_input("Without the words")
title_contains = st.text_input("Where the title contains")
author_editor = st.text_input("Where the author/editor is")
start_year = st.text_input("Start year", value="2000")
end_year = st.text_input("End year", value="2024")
extra_considerations = st.text_area(
    "Extra considerations (optional)",
    placeholder="Add any additional information for your search.",
)

if st.button("Search"):
    if not all_words:
        st.warning("Please enter search terms.")
    else:
        try:
            llm = get_llm()
        except Exception as e:
            st.error(f"Failed to initialize LLM: {e}")
            st.stop()

        # Generate queries
        st.write("### Generating search queries...")
        queries = generate_search_queries(llm, all_words, use_filters=True)

        st.write("### Generated Search Queries:")
        for i, query in enumerate(queries, 1):
            st.write(f"{i}. {query}")

        # CrossRef results
        st.write("### Fetching Articles from CrossRef...")
        df = fetch_articles(queries, start_year, end_year)

        if len(df) > 0:
            st.write(f"### Found {len(df)} Articles:")
            st.dataframe(df)
            csv_data = df.to_csv(index=False)
            st.download_button("Download Results as CSV", csv_data, "results.csv", "text/csv")
        else:
            st.write("No articles found from CrossRef.")

        # Springer results
        st.write("### Fetching Articles from Springer API...")
        try:
            springer_articles = fetch_springer_articles(
                all_words, exact_phrase, at_least_one_word, without_words,
                title_contains, author_editor, start_year, end_year,
                api_key=SPRINGER_API_KEY,
            )

            if springer_articles:
                for article in springer_articles:
                    title = article.get("title", "No title")
                    link = article.get("url", [{}])[0].get("value", "#")
                    st.write(f"**{title}**")
                    st.markdown(f"[Read Article]({link})", unsafe_allow_html=True)
                    st.write("---")
            else:
                st.write("No articles found from Springer.")
        except Exception as e:
            st.error(f"Error fetching from Springer: {e}")

        st.write(
            "**Note:** Articles are dynamically fetched based on your search query."
        )
