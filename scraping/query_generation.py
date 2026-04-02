"""
Search Query Generation
Uses LLMs to generate diverse boolean search queries from a user topic,
optimized for academic literature databases (Springer, CrossRef).
"""

import re
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


QUERY_TEMPLATE = """
You are a literature research assistant. Based on the user prompt "{user_prompt}", 
generate five different search queries using logical operators (AND, OR, NOT) and 
synonyms to broaden the search.

Each query should:
1. Include keywords related to the main topic.
2. Use synonyms or alternative words for broader coverage.
3. Group similar terms using parentheses to create logical groupings.
4. Be well-formatted and appropriate for input into the Springer database.
5. Use AND for required terms, OR for alternatives, and NOT for exclusions.
6. Include the word California.

Make sure each query is short, general, and straightforward.
Your response should only contain the generated queries with no redundant comments.
Return only the formatted search queries as a numbered list.
"""

FILTERED_TEMPLATE = """
You are a literature research assistant. Based on the user prompt "{user_prompt}", 
generate five different search queries for scientific literature.

Each query should use different synonyms for the key terms.
Do not use AND or OR, just natural language sentences.
Return the queries as a numbered list (1 to 5).
Always start with the word California.
Make sure each query is short, general, and straightforward.
Your response should only contain the generated queries.
"""


def generate_search_queries(llm, topic, use_filters=False):
    """
    Generate search queries from a natural language topic.
    
    Args:
        llm: LangChain LLM instance
        topic: User's search topic string
        use_filters: If True, uses natural language queries; if False, uses boolean operators
    
    Returns:
        List of search query strings
    """
    template = FILTERED_TEMPLATE if use_filters else QUERY_TEMPLATE
    prompt = PromptTemplate(input_variables=["user_prompt"], template=template)
    chain = LLMChain(llm=llm, prompt=prompt)
    
    result = chain.run(topic)
    
    # Clean numbered list formatting
    cleaned = re.sub(r'^\d+\.\s*', '', result, flags=re.MULTILINE)
    queries = [q.strip() for q in cleaned.split('\n') if q.strip()]
    
    return queries
