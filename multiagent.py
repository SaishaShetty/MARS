import ollama
from ollama import chat
from ollama import ChatResponse
import requests
import re
import argparse
from util.pdf_extract import pdf_pipeline
from build_models import generate_base_models, generate_paper_models, isModelLoaded
import json
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description="MultiAgent paper review")
parser.add_argument("url", type=str, help="Path to the Conference CFP")
parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
args = parser.parse_args()

paper = pdf_pipeline(args.pdf_path)
if 'Abstract' in paper.keys():
    keys = list(paper.keys())[1:-1] # Skip the first and last keys
    similar_paper_data = generate_base_models(args.url, paper['Abstract'])
else:
    keys = list(paper.keys())
    similar_paper_data = generate_base_models(args.url, paper[keys[0]])
paper_content = {key: paper[key] for key in keys}
paper_specific_models = generate_paper_models(paper_content)
print(paper_specific_models)
with open('paper_specific_models.txt', 'w') as f:
    for model in paper_specific_models:
        f.write(model + '\n')
print(ollama.list().models)

def isModelLoaded(model):
    loaded_models = [model.model for model in ollama.list().models]
    return model in loaded_models or f"{model}:latest" in loaded_models

if not paper_content:
    print("Error: No content extracted from the PDF.")
    exit(1)

def consultWiki(question):
    print(f"Searching Wikipedia for: {question}")
    
    search_url = "https://en.wikipedia.org/w/api.php"
    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": question,
        "srlimit": 1,
    }

    response = requests.get(search_url, params=search_params)
    if response.status_code == 200:
        data = response.json()
        search_results = data.get("query", {}).get("search", [])

        if search_results:
            top_result = search_results[0]["title"]
            page_url = f"https://en.wikipedia.org/wiki/{top_result.replace(' ', '_')}"
            print(f"Fetching full content from: {page_url}")

            # Fetch the full page HTML
            html_url = f"https://en.wikipedia.org/api/rest_v1/page/html/{top_result.replace(' ', '_')}"
            html_response = requests.get(html_url)

            if html_response.status_code == 200:
                soup = BeautifulSoup(html_response.text, "html.parser")

                # Extract all paragraphs from the page
                paragraphs = [p.get_text() for p in soup.find_all("p") if p.get_text()]
                full_text = " ".join(paragraphs)

                # Summarize (basic extractive approach)
                summary = " ".join(full_text.split(". ")[:5])  # First 5 sentences

                return f"**{top_result}**\n{summary}...\n[Read more]({page_url})"
    
    return "No results found on Wikipedia. Try using simpler keywords."
    
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
    return 'accept' in desk_review.lower(), desk_review

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

def consultPaperSpecificModels(model, question):
    return consultAgent(model, question)

def consultQuestioner(text):
    return consultAgent('questioner', text)

def consultGrammar(text):
    return consultAgent('grammar', text)

def consultTest(text):
    return consultAgent('test', text)

def consultNovelty(text):
    return consultAgent('novelty', text)

def consultFactChecker(text):
    tool_config = {
        "name": "consultWiki",
        "type": "function",
        "function": {
            "name": "consultWiki",
            "description": "Consult Wikipedia to check facts",
            "parameters": {
                "type": "object",
                "required": ["question"],
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask Wikipedia"
                    }
                }
            }
        }
    }
    
    retries = 3  # Set a max retry limit
    query = text

    response = chat(model='factchecker', messages=[{'role': 'user', 'content': "Do you need more facts? Only say yes or no. \n " + query}])
    if 'yes' in response.message.content.lower():
        
        for attempt in range(retries):
            response = chat(model='factchecker', messages=[{'role': 'user', 'content': query}], tools=[tool_config])
            
            print("Attempt number", attempt + 1)

            if response.message.tool_calls:
                for tool in response.message.tool_calls:
                    if function_to_call := available_functions.get(tool.function.name):
                        try:
                            print("Asking " + tool.function.name + ": " + tool.function.arguments['question'])
                        except:
                            pass
                        output = function_to_call(**tool.function.arguments)
                        
                        if output and output != "No results found on Wikipedia. Try using simpler keywords.":
                            # new_query = "Question: \n" + query + " " + "Answer: \n" + output
                            # print("new_query", new_query)
                            # consultFactChecker(new_query)
                            return output
                        
                        print("Refining query...")
                        query = " ".join(re.findall(r'\b[A-Za-z0-9-]+\b', text)[:10]) # more specific query

        print("Could not retrieve relevant information from Wikipedia after multiple attempts.")
        return None
    else:
        response = chat(model='factchecker', messages=[{'role': 'user', 'content': "Do you accept the claims? Say 'Accept' if yes and 'Reject' if no. \n " + query}])
        return response.message.content

available_models = [model.model for model in ollama.list().models]

available_functions = {
    'consultWiki': consultWiki,
    'consultDeskReviewer': consultDeskReviewer,
    'consultReviewer1': consultReviewer1,
    'consultReviewer2': consultReviewer2,
    'consultReviewer3': consultReviewer3,
    'consultQuestioner': consultQuestioner,
    'consultGrammar': consultGrammar,
    'consultTest': consultTest,
    'consultNovelty': consultNovelty,
    'consultFactChecker': consultFactChecker,
}

# Consult all agents
feedback = {}

feedback['DeskReviewer'] = {}
desk_review = consultDeskReviewer(paper[list(paper.keys())[0]])
feedback['DeskReviewer'] = {
    'Accept': desk_review[0],
    'Feedback': desk_review[1]
}

feedback['Questions'] = {}
feedback['Grammar'] = {}
feedback['Novelty'] = {}
feedback['FactChecker'] = {}

for i in paper_content:
    feedback['Questions'][i.split()[0]] = consultQuestioner(paper_content[i])
    
    grammar_feedback = consultGrammar(paper_content[i])
    feedback['Grammar'][i.split()[0]] = {
        'Accept': 'accept' in grammar_feedback.lower(),
        'Feedback': grammar_feedback
    }
    
    feedback['Novelty'][i.split()[0]] = {}
    feedback['Novelty'][i.split()[0]]['Feedback'] = consultNovelty(
        "Paper Info:\n" + paper_content[i] + "\n" +
        "arXiv Similar Papers:\n" + similar_paper_data[0] + "\n" +
        "arXiv Similar Papers Summary:\n" + similar_paper_data[1]
    )
    feedback['Novelty'][i.split()[0]]['Accept'] = 'accept' in feedback['Novelty'][i.split()[0]]['Feedback'].lower()
    
    feedback['FactChecker'][i.split()[0]] = {}
    fact_check_feedback = consultFactChecker(paper_content[i])
    fact_check_feedback = consultFactChecker(
        "Text:\n" + paper_content[i] + "\nFacts:\n" + str(fact_check_feedback)
    )
    feedback['FactChecker'][i.split()[0]]['Feedback'] = fact_check_feedback
    feedback['FactChecker'][i.split()[0]]['Accept'] = 'accept' in fact_check_feedback.lower()


# feedback['Answers'] = {}

# for i in feedback['Questions']:
#     questions = feedback['Questions'][i].split('?')
#     model_name = i
#     feedback['Answers'][model_name] = {}
#     for j in range(len(questions)):
#         questions[j] = questions[j].strip()
#         feedback['Answers'][model_name][models] = []
#         for models in paper_specific_models:
#             if model_name==models:
#                 continue
#             else:
#                 answer = consultPaperSpecificModels(models, "Answer the following question with respect to your system message (what you know). If you have no answer, say 'No answer'.\n" + questions[j])
#                 feedback['Answers'][model_name][models].append({
#                     'Question': questions[j],
#                     'Answer': answer
#                 })


# for i in paper_content:
#     feedback['Reviewer1'] = {}
#     feedback['Reviewer1'][i] = consultReviewer1(paper_content[i])
#     feedback['Reviewer2'] = {}
#     feedback['Reviewer2'][i] = consultReviewer2(paper_content[i])
#     feedback['Reviewer3'] = {}
#     feedback['Reviewer3'][i] = consultReviewer3(paper_content[i])


# write feedback to file
with open('feedback_new.json', 'w') as f:
    json.dump(feedback, f, indent=4)

# print(consultDeskReviewer(paper['Abstract']))
# print("QUESTION", consultQuestioner(paper['Abstract']))
# print("GRAMMAR", consultGrammar(paper['Abstract']))
# print(consultNovelty(paper['Abstract']))
