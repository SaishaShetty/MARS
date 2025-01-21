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

def generate_models(url):
    models = {
        "reviewer1": reviewer_messages[0],
        "reviewer2": reviewer_messages[1],
        "reviewer3": reviewer_messages[2],
        "deskreviewer": gen_desk_review_message(url)
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
