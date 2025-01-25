import arxiv

def search_arxiv_papers(query, max_results=5):
    """
    Search and fetch papers from arXiv based on a query.

    Args:
        query (str): The search query (e.g., "superconductors gem5").
        max_results (int): The maximum number of results to retrieve.

    Returns:
        list: A list of dictionaries containing paper details.
    """
    # Create an arXiv client
    client = arxiv.Client()

    # Define the search
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        # Uncomment if sorting is needed
        # sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    # Fetch results and format them
    papers = []
    for result in client.results(search):
        papers.append({
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "published": result.published,
            "summary": result.summary,
            "pdf_url": result.pdf_url,
        })
    return papers

# Example usage
if __name__ == "__main__":
    query = "superconductors gem5"
    max_results = 5
    papers = search_arxiv_papers(query, max_results)
    
    for paper in papers:
        print(f"Title: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"Published: {paper['published']}")
        print(f"Summary: {paper['summary']}")
        print(f"PDF URL: {paper['pdf_url']}")
        print("=" * 80)
