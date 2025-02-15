import ollama
import requests
import re
import argparse
from util.pdf_extract import pdf_pipeline
from build_models import generate_base_models, generate_paper_models, isModelLoaded

def consultAgent(agent, question):
    """Consult an AI agent and return the response."""
    if not isModelLoaded(agent):
        print(f"Model {agent} not found")
        return None
    
    response = ollama.chat(model=agent, messages=[{'role': 'user', 'content': question}])
    return response['message']['content']

def get_paper_review_results(url, pdf_path):
    """Run the full paper review process using AI models."""
    # Extract paper content from PDF
    print(f"Extracting content from {pdf_path}...")
    paper = pdf_pipeline(pdf_path)

    if not paper or 'Abstract' not in paper:
        print(f"Error: No content extracted from {pdf_path}")
        return

    abstract = paper['Abstract']
    keys = list(paper.keys())[1:-1]  # Skip first and last keys
    paper_content = {key: paper[key] for key in keys}

    # Generate AI models
    print("Generating models...")
    generate_base_models(url, abstract)
    generate_paper_models(paper_content)

    print("Running AI reviews...\n")
    
    # Consult various reviewers
    desk_review = consultAgent('deskreviewer', abstract)
    reviewer1 = consultAgent('reviewer1', abstract)
    reviewer2 = consultAgent('reviewer2', abstract)
    reviewer3 = consultAgent('reviewer3', abstract)
    questioner = consultAgent('questioner', abstract)
    grammar = consultAgent('grammar', abstract)
    novelty = consultAgent('novelty', abstract)

    # Display results
    print("\n=== Paper Review Results ===")
    print(f"📌 **Desk Reviewer Decision**: {desk_review}")
    print(f"👨‍⚖️ **Reviewer 1**: {reviewer1}")
    print(f"👩‍⚖️ **Reviewer 2**: {reviewer2}")
    print(f"🧑‍⚖️ **Reviewer 3**: {reviewer3}")
    print(f"❓ **Questioner Suggestions**: {questioner}")
    print(f"📝 **Grammar Check**: {grammar}")
    print(f"🆕 **Novelty Check**: {novelty}")
    
    return {
        "Desk Reviewer": desk_review,
        "Reviewer 1": reviewer1,
        "Reviewer 2": reviewer2,
        "Reviewer 3": reviewer3,
        "Questioner": questioner,
        "Grammar Check": grammar,
        "Novelty Check": novelty
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI Paper Review")
    parser.add_argument("url", type=str, help="URL of the conference CFP")
    parser.add_argument("pdf_path", type=str, help="Path to the paper PDF")
    args = parser.parse_args()

    results = get_paper_review_results(args.url, args.pdf_path)
