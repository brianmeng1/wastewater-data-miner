"""
CrossRef API Search
Fetches academic article metadata (title, DOI, authors, publication date, abstract)
from the CrossRef API based on search queries.
"""

import requests
import pandas as pd


CROSSREF_API_URL = "https://api.crossref.org/works"


def fetch_articles(queries, start_year="2000", end_year="2024", rows_per_query=10,
                   contact_email="your_email@example.com"):
    """
    Fetch article metadata from CrossRef for a list of search queries.
    
    Args:
        queries: List of search query strings
        start_year: Filter start year
        end_year: Filter end year
        rows_per_query: Max results per query
        contact_email: Contact email for polite API usage
    
    Returns:
        DataFrame with columns: Query, Title, DOI, Authors, Publication Date, URL, Abstract
    """
    articles = []
    
    for query in queries:
        params = {
            "query": query,
            "filter": f"from-pub-date:{start_year}-01-01,until-pub-date:{end_year}-12-31",
            "rows": rows_per_query,
            "mailto": contact_email,
        }
        
        try:
            response = requests.get(CROSSREF_API_URL, params=params, timeout=30)
            if response.status_code != 200:
                print(f"CrossRef API error for query '{query}': {response.status_code}")
                continue
            
            data = response.json()
            for item in data["message"]["items"]:
                title = item.get("title", ["No title available"])[0]
                doi = item.get("DOI", "No DOI available")
                
                authors = item.get("author", [])
                author_names = [
                    f"{a.get('given', '')} {a.get('family', '')}".strip()
                    for a in authors
                ]
                
                pub_date = (
                    item.get("published-print", {}).get("date-parts", [[None]])[0][0]
                    or item.get("published-online", {}).get("date-parts", [[None]])[0][0]
                    or "No date available"
                )
                
                abstract = item.get("abstract", "Not available")
                if abstract != "Not available":
                    abstract = (abstract.replace("<jats:p>", "")
                                .replace("</jats:p>", "")
                                .replace("<jats:title>", "")
                                .replace("</jats:title>", ""))
                
                articles.append({
                    "Query": query,
                    "Title": title,
                    "DOI": doi,
                    "Authors": "; ".join(author_names) if author_names else "Not available",
                    "Publication Date": pub_date,
                    "URL": f"https://doi.org/{doi}" if doi != "No DOI available" else "No URL",
                    "Abstract": abstract,
                })
        except Exception as e:
            print(f"Error fetching CrossRef results for '{query}': {e}")
    
    df = pd.DataFrame(articles)
    if len(df) > 0:
        df = df.drop_duplicates(subset="DOI")
    
    print(f"Fetched {len(df)} unique articles from CrossRef")
    return df
