import ollama
from ollama import chat
from ollama import ChatResponse
import requests
import re
import argparse
from pdf_extract import pdf_pipeline
from build_models import generate_base_models, generate_paper_models, isModelLoaded

parser = argparse.ArgumentParser(description="MultiAgent paper review")
parser.add_argument("url", type=str, help="Path to the Conference CFP")
parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
args = parser.parse_args()

paper = pdf_pipeline(args.pdf_path)
keys = list(paper.keys())[1:-1]  # Skip the first and last keys
paper_content = {key: paper[key] for key in keys}
generate_base_models(args.url)
generate_paper_models(paper_content)
print(ollama.list().models)

def consultWiki(question):
    print(f"Searching Wikipedia for: {question}")
    url = f"https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": question,
        "srlimit": 1,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "query" in data and "search" in data["query"] and len(data["query"]["search"]) > 0:
            top_result = data["query"]["search"][0]
            title = top_result["title"]
            snippet = re.sub(r'<[^>]*>', '', top_result["snippet"])
            page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            return f"**{title}**\n{snippet}\n{page_url}"
        else:
            return "No results found on Wikipedia."
    else:
        return "Failed to fetch data from Wikipedia."
    
def consultAgent(agent, question):
    # print("Consulting agent", agent, "with question", question)
    if not isModelLoaded(agent):
        print(f"Model {agent} not found")
        return
    response: ChatResponse = chat(model=agent, messages=[
        {
            'role': 'user',
            'content': question,
        },
    ])
    return response.message.content

def consultDeskReviewer(abstract):
    desk_review = consultAgent('deskreviewer', abstract)
    print(desk_review)
    return 'accept' in desk_review.lower()

def consultReviewer1(abstract):
    review = consultAgent('reviewer1', abstract)
    print(review)
    return review.split(' ')[0]

def consultReviewer2(abstract):
    review = consultAgent('reviewer2', abstract)
    print(review)
    return review.split(' ')[0]

def consultReviewer3(abstract):
    review = consultAgent('reviewer3', abstract)
    print(review)
    return review.split(' ')[0]

def consultQuestioner(text):
    return consultAgent('questioner', text)

available_models = [model.model for model in ollama.list().models]

available_functions = {
    'consultWiki': consultWiki,
    'consultDeskReviewer': consultDeskReviewer,
    'consultReviewer1': consultReviewer1,
    'consultReviewer2': consultReviewer2,
    'consultReviewer3': consultReviewer3,
    'consultQuestioner': consultQuestioner,
}

print(consultDeskReviewer(paper['Abstract']))
print(consultReviewer1(paper['Abstract']))
print(consultReviewer2(paper['Abstract']))
print(consultReviewer3(paper['Abstract']))
print(consultQuestioner(paper['Abstract']))
