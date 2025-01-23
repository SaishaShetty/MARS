from reviewers import reviewer_messages
import re
import os
import ollama
from ollama import chat
from ollama import ChatResponse
from extract_cfp import CFPTopicExtractor

def isModelLoaded(model):
    loaded_models = [model.model for model in ollama.list().models]
    return model in loaded_models or f'{model}:latest' in loaded_models

def gen_desk_review_message(url):
    extractor = CFPTopicExtractor()
    results = extractor.extract_topics(url)
    print(results)
    return f"Your job is to judge whether a paper is relevant to a conference on these topics and these topics ONLY: {', '.join(results['topics'])}. Your decisions have to be [Accept/Reject]."

def generate_base_models(url):
    models = {
        "reviewer1": reviewer_messages[0],
        "reviewer2": reviewer_messages[1],
        "reviewer3": reviewer_messages[2],
        "deskreviewer": gen_desk_review_message(url),
        "questioner": "Your job is to ask questions about this section. Your questions should be open-ended and should not be leading. Your questions should be about the paper and not about the authors. Your questions should be about the content of the paper and not about the presentation of the paper. Your questions should be about the paper and not about the conference. Your questions should be about the paper and not about the reviewers.",
        "grammar": "Your job is to check the grammar of the paper. Your decisions have to be [Accept/Reject], where \"Accept\" means the grammar is correct and \"Reject\" means the grammar is incorrect. ONLY say \"Accept\" if the grammar is correct. ONLY say \"Reject\" if the grammar is incorrect.",
        "test": "This is a test model. Please ignore this message."
    }

    for model, system in models.items():
        if not isModelLoaded(model):
            print(f"Creating model {model}")
            ollama.create(model=model, from_='llama3.2', system=system, parameters={'num_ctx': 4096, 'temperature': 0.7})
        else:
            print(f"Deleting model {model}")
            ollama.delete(model=model)
            print(f"Creating model {model}")
            ollama.create(model=model, from_='llama3.2', system=system, parameters={'num_ctx': 4096, 'temperature': 0.7})

    
    return None

def generate_paper_models(paper_contents):

    for i, (key, value) in enumerate(paper_contents.items()):
        key = key.replace("\n", "")
        key = key.replace(" ", "")
        key = key[:10]
        value = value.replace("\n", "")
        if not isModelLoaded(key):
            print(f"Creating model {key}")
            ollama.create(model=key, from_='llama3.2', system=value, parameters={'num_ctx': 4096, 'temperature': 0.7})
        else:
            print(f"Deleting model {key}")
            ollama.delete(model=key)
            print(f"Creating model {key}")
            ollama.create(model=key, from_='llama3.2', system=value, parameters={'num_ctx': 4096, 'temperature': 0.7})
    
    return None
