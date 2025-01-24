import ollama
from ollama import chat
from ollama import ChatResponse
import requests
import re
import argparse
import json
from build_models import generate_base_models, generate_paper_models, isModelLoaded
from pdf_test import pdf_pipeline  

def consultAgent(agent, question):
    if not isModelLoaded(agent):
        print(f"Model {agent} not found. Skipping...")
        return "Model not found"
    try:
        response: ChatResponse = chat(model=agent, messages=[
            {"role": "user", "content": question}
        ])
        return response.message.content.strip()
    except Exception as e:
        print(f"Error consulting {agent}: {e}")
        return f"Error: {e}"


def collect_feedback(content, section_name):
    """Collect feedback for a given section."""
    feedback = {}
    feedback["DeskReviewer"] = consultAgent(
        "deskreviewer",
        f"Evaluate this {section_name} for relevance to the conference topics. Respond with [Accept] or [Reject] and provide reasoning: {content}",
    )
    feedback["Reviewer1"] = consultAgent(
        "reviewer1",
        f"Review the quality of this {section_name}. Provide an [Accept], [Weak Accept], [Weak Reject], or [Reject] decision and reasoning: {content}",
    )
    feedback["Reviewer2"] = consultAgent(
        "reviewer2",
        f"Provide feedback on the strengths and weaknesses of this {section_name}. Include an [Accept], [Weak Accept], [Weak Reject], or [Reject] decision: {content}",
    )
    feedback["Reviewer3"] = consultAgent(
        "reviewer3",
        f"Provide constructive feedback on this {section_name}. Respond with [Accept], [Weak Accept], [Weak Reject], or [Reject], followed by reasoning and suggestions: {content}",
    )
    feedback["Questioner"] = consultAgent(
        "questioner",
        f"Ask open-ended, non-leading questions about the following {section_name}. Focus on the paper's content, not its authors, presentation, reviewers, or the conference: {content}",
    )
    feedback["Grammar"] = consultAgent(
        "grammar",
        f"Check the {section_name} for grammar issues. Respond with [Accept] if the grammar is correct or [Reject] if there are errors, and provide corrections: {content}",
    )
    return feedback


# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MultiAgent paper review")
    parser.add_argument("url", type=str, help="Path to the Conference CFP")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    args = parser.parse_args()

    # Extract sections from the PDF
    paper_sections = pdf_pipeline(args.pdf_path)
    if not paper_sections:
        print("Error: No content extracted from the PDF.")
        exit(1)
    generate_base_models(args.url)
    generate_paper_models(paper_sections)
    print("Available models:", [model.model for model in ollama.list().models])


    all_feedback = {}
    for section_name, content in paper_sections.items():
        print(f"\nCollecting feedback for section: {section_name}")
        feedback = collect_feedback(content, section_name)
        all_feedback[section_name] = feedback


    print("\nCollected Feedback:")
    for section, feedback in all_feedback.items():
        print(f"\nFeedback for {section}:")
        for reviewer, comments in feedback.items():
            print(f"- {reviewer}: {comments}")

    with open("feedback.json", "w") as f:
        json.dump(all_feedback, f, indent=4)
    print("\nFeedback saved to feedback.json")
