import json
from ollama import chat
from ollama import ChatResponse
from build_models import isModelLoaded

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

with open('paper_specific_models.txt', 'r') as f:
    paper_specific_models = f.read().splitlines()

with open('feedback_new.json', 'r') as f:
    feedback = json.load(f)

feedback['Answers'] = {}

for i in feedback['Questions']:
    questions = feedback['Questions'][i].split('?')
    print(questions)
    model_name = i
    feedback['Answers'][model_name] = {}
    for j in range(len(questions)):
        questions[j] = questions[j].strip()
        print(questions[j])
        if questions[j] == '':
            continue
        feedback['Answers'][model_name][questions[j]] = {}
        for models in paper_specific_models:
            if model_name==models:
                continue
            else:
                answer = consultAgent(models, "Answer the following question with respect to your system message (what you know). If you have no answer, say 'No answer'.\n" + questions[j])
                print(answer)
                feedback['Answers'][model_name][questions[j]][models] = answer

with open('feedback_new.json', 'w') as f:
    json.dump(feedback, f, indent=4)
