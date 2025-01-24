import ollama
from ollama import chat
from ollama import ChatResponse
import requests
import re
import argparse
import json
from PyPDF2 import PdfReader
from build_models import generate_base_models, generate_paper_models, isModelLoaded


# PDF extraction function
def pdf_pipeline(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        content = {}
        for page in reader.pages:
            text = page.extract_text()
            if text:
                if "Abstract" in text:
                    content["Abstract"] = text.split("Abstract")[1].split("\n")[0]
        return content
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return {}


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


def collect_feedback(content):
    feedback = {}
    feedback["DeskReviewer"] = consultAgent(
        "deskreviewer",
        f"Evaluate this abstract for relevance to the conference topics. Respond with [Accept] or [Reject] and provide reasoning: {content}",
    )
    feedback["Reviewer1"] = consultAgent(
        "reviewer1",
        f"Review this abstract's quality. Provide an [Accept], [Weak Accept], [Weak Reject], or [Reject] decision and reasoning: {content}",
    )
    feedback["Reviewer2"] = consultAgent(
        "reviewer2",
        f"Provide feedback on the strengths and weaknesses of this abstract. Include an [Accept], [Weak Accept], [Weak Reject], or [Reject] decision: {content}",
    )
    feedback["Reviewer3"] = consultAgent(
        "reviewer3",
        f"Provide constructive feedback on this abstract. Respond with [Accept], [Weak Accept], [Weak Reject], or [Reject], followed by reasoning and suggestions: {content}",
    )
    feedback["Questioner"] = consultAgent(
          "questioner",
          f"Ask open-ended, non-leading questions about the following content. Focus on the paper's content, not its authors, presentation, reviewers, or the conference: {content}",
      )
    feedback["Grammar"] = consultAgent(
        "grammar",
        f"Check the abstract for grammar issues. Respond with [Accept] if the grammar is correct or [Reject] if there are errors, and provide corrections: {content}",
    )
    return feedback


# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MultiAgent paper review")
    parser.add_argument("url", type=str, help="Path to the Conference CFP")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    args = parser.parse_args()

    paper = pdf_pipeline(args.pdf_path)
    if not paper:
        print("Error: No content extracted from the PDF.")
        exit(1)

    abstract_content = paper.get("Abstract", "No Abstract Found")
    if abstract_content == "No Abstract Found":
        print("Error: Abstract not found in the paper.")
        exit(1)

    generate_base_models(args.url)
    generate_paper_models({"Abstract": abstract_content})
    print("Available models:", [model.model for model in ollama.list().models])

    feedback = collect_feedback(abstract_content)
    print("\nCollected Feedback:")
    for reviewer, comments in feedback.items():
        print(f"- {reviewer}: {comments}")

    # Save feedback to JSON file
    with open("feedback.json", "w") as f:
        json.dump(feedback, f, indent=4)
    print("\nFeedback saved to feedback.json")
