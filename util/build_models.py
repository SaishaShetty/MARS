from util.reviewer import reviewer_messages
import re
import os
import ollama
from ollama import chat
from ollama import ChatResponse
from util.extract_cfp import CFPTopicExtractor
from util.scholar import search_arxiv_papers
from util.extract_keywords import extract_keywords

def isModelLoaded(model):
    loaded_models = [model.model for model in ollama.list().models]
    return model in loaded_models or f'{model}:latest' in loaded_models

def gen_desk_review_message(url):
    extractor = CFPTopicExtractor()
    results = extractor.extract_topics(url)
    return f"Your job is to judge whether a paper is relevant to a conference on these topics and these topics ONLY: {', '.join(results['topics'])}. Your decisions have to be [Accept/Reject]."

def gen_novelty_model(paper_contents):
    keywords = extract_keywords(paper_contents, num_keywords=10)
    keywords = ' '.join(keywords)
    relevant_papers = search_arxiv_papers(keywords, max_results=5)
    for paper in relevant_papers:
        paper['title'] = re.sub(r'\W+', ' ', paper['title'])
        paper['summary'] = re.sub(r'\W+', ' ', paper['summary'])
    return ' '.join([paper['title'] for paper in relevant_papers]), ' '.join([paper['summary'] for paper in relevant_papers])

def generate_base_models(url, paper_contents):
    models = {
        "deskreviewer": gen_desk_review_message(url),
        "reviewer1": reviewer_messages[0],
        "reviewer2": reviewer_messages[1],
        "reviewer3": reviewer_messages[2],
        "questioner": "Your job is to ask questions about this section. Your questions should be open-ended and should not be leading. Your questions should be about the paper and not about the authors. Your questions should be about the content of the paper and not about the presentation of the paper. Your questions should be about the paper and not about the conference. Your questions should be about the paper and not about the reviewers.",
        "grammar": "Your job is to check the grammar of the paper. Your decisions have to be [Accept/Reject], where \"Accept\" means the grammar is correct and \"Reject\" means the grammar is incorrect. ONLY say \"Accept\" if the grammar is correct. ONLY say \"Reject\" if the grammar is incorrect.",
        "test": "This is a test model. Please ignore this message.",
        "novelty": f"Your job is to judge whether a paper is novel. Your decisions have to be [Accept/Reject], where \"Accept\" means the paper is novel and \"Reject\" means the paper is not novel. Say \"Accept\" if the paper is novel. Say \"Reject\" if the paper is not novel. Use all the information in the prompt to make your decision and tell why you chose what you chose.", 
        "factchecker": "You are a fact checker. Respond with [Accept] if the facts are correct or [Reject] if there are inaccuracies, followed by specific corrections. You should use Wikipedia as a reference. If you are satisfied with the facts, respond with [Accept]. If you find inaccuracies, respond with [Reject] and provide corrections. You do NOT have to always ASK WIKIPEDIA. Also, give your own take on the facts.",
        # "grammar": "You are a grammar checker. Review the section for grammar issues. Respond with [Accept] if the grammar is correct or [Reject] if there are issues, followed by specific corrections.",
    }

    for model, system in models.items():
        if not isModelLoaded(model):
            print(f"Creating model {model}")
            ollama.create(model=model, from_="llama3.2", system=system, parameters={"num_ctx": 4096, "temperature": 0.7})
        else:
            print(f"Recreating model {model}")
            ollama.delete(model=model)
            ollama.create(model=model, from_="llama3.2", system=system, parameters={"num_ctx": 4096, "temperature": 0.7})

    return gen_novelty_model(paper_contents)

def generate_paper_models(paper_contents):
    paper_keys = []
    for key, value in paper_contents:
        key = key.replace("\n", "").replace(" ", "")[:10]
        if not isModelLoaded(key):
            print(f"Creating model {key}")
            paper_keys.append(key)
            ollama.create(model=key, from_="llama3.2", system=value, parameters={"num_ctx": 4096, "temperature": 0.7})
        else:
            print(f"Recreating model {key}")
            ollama.delete(model=key)
            paper_keys.append(key)
            ollama.create(model=key, from_="llama3.2", system=value, parameters={"num_ctx": 4096, "temperature": 0.7})
    return paper_keys