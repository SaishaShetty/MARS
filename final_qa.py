import json
import re
from ollama import chat
from ollama import ChatResponse
from build_models import isModelLoaded

def consultAgent(agent, question):
    print(f"Attempting to consult agent: '{agent}' with question: '{question}'")
    if not agent or agent.isspace():
        print(f"Invalid model name: '{agent}'")
        return
    if not isModelLoaded(agent):
        print(f"Model {agent} not found")
        return
    try:
        response: ChatResponse = chat(model=agent, messages=[
            {
                'role': 'user',
                'content': question,
            },
        ])
        cleaned_content = re.sub(r'<think>.*?</think>', '', response.message.content, flags=re.DOTALL)
        return cleaned_content.strip()
    except Exception as e:
        print(f"Error consulting agent '{agent}': {str(e)}")
        return None

# Load paper-specific models
print("Content of paper_specific_models.txt:")
with open('paper_specific_models.txt', 'r') as f:
    paper_specific_models = [line.strip() for line in f if line.strip()]
print("Paper-specific models:", paper_specific_models)

# Load feedback data
with open('feedback_collab.json', 'r') as f:
    feedback = json.load(f)
print("\nStructure of feedback_collab.json:")
print(json.dumps(list(feedback.keys()), indent=2))

# Initialize Answers if not present
if 'Answers' not in feedback:
    feedback['Answers'] = {}

# Process each section
for section_name, section_data in feedback['Section Reviews'].items():
    if section_name in feedback['Answers']:
        print(f"\nSkipping already processed section: {section_name}")
        continue  # Skip sections that are already processed

    print(f"\nProcessing section: {section_name}")
    questions = section_data.get('Questioner', '').split('?')
    feedback['Answers'][section_name] = {}

    for question in questions:
        question = question.strip() + '?'
        if not question or question == '?':
            continue

        print(f"Processing question: {question}")
        feedback['Answers'][section_name][question] = {}

        for model in paper_specific_models:
            if section_name == model:
                continue

            answer = consultAgent(model, "Answer the following question with respect to your system message (what you know). If you have no answer, say 'No answer'.\n" + question)
            print(answer)
            feedback['Answers'][section_name][question][model] = answer

    # Checkpoint: Save after processing each section
    with open('feedback_collab_with_answers.json', 'w') as f:
        json.dump(feedback, f, indent=4)

    print(f"Checkpoint saved after processing section: {section_name}")

print("\nFinal answers have been saved to feedback_collab_with_answers.json")
