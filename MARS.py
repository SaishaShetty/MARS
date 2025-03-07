import os
import json
import re
import time
import argparse
import requests
import ollama
from bs4 import BeautifulSoup
from ollama import chat, ChatResponse
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from util.review_collab import (
    parse_pdf_to_text, clean_text, extract_section,
    split_text_into_sections, reviewer_agent, summarizer
)
from util.build_models import generate_base_models, generate_paper_models
from util.multiagent import (
    consultGrammar as consult_grammar,
    consultNovelty as consult_novelty,
    consultFactChecker as fact_checker,
    consultQuestioner as consult_question,
    consultTest as consult_test,
    consultDeskReviewer as consult_desk_reviewer
)
from util.reviewer import assigned_reviewers
from util.build_models import isModelLoaded

# Constants
MODELS = ["mistral", "llama3.2", "qwen2.5", "deepseek-r1"]
CHECKPOINT_FILE = "feedback_collab.json"
ANSWER_FILE = "feedback_collab_with_answers.json"
MODEL_LIST_FILE = "paper_specific_models.txt"

# Argument Parser
parser = argparse.ArgumentParser(description="MultiAgent Paper Review with Optional Q&A")
parser.add_argument("url", type=str, help="Path to the Conference CFP")
parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
parser.add_argument("section_name", type=str, nargs='?', default='', help="Optional: specific paper section for review")
parser.add_argument("--answer-questions", action="store_true", help="Enable answering questions in the second stage")
args = parser.parse_args()

# ---- Stage 1: Review Paper Sections ----

# Parse and clean the PDF text
if args.pdf_path.endswith(".pdf"):
    pdf_text = parse_pdf_to_text(args.pdf_path)
    cleaned_text = clean_text(pdf_text)
    sections = split_text_into_sections(cleaned_text)
else:
    sections = []
    with open(args.pdf_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "input" in data and "sections" in data["input"]:
        sections = [(s["heading"], s["text"]) for s in data["input"]["sections"]]

print("\nAvailable Sections in the Paper:")
for section in sections:
    print(f"- {section[0]}")

# Load checkpoint if available
if os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint_data = json.load(f)
        all_section_reviews = checkpoint_data.get("Section Reviews", {})
    processed_sections = set(all_section_reviews.keys())
    print(f"\nFound checkpoint. Processed sections: {', '.join(processed_sections) if processed_sections else 'None'}")
else:
    all_section_reviews = {}
    processed_sections = set()

# Determine sections to process
if args.section_name:
    if args.section_name in processed_sections:
        print(f"\nSection '{args.section_name}' is already processed. Exiting.")
        exit(0)
    sections_to_process = [args.section_name]
else:
    sections_to_process = [s[0] for s in sections if s[0] not in processed_sections]

if not sections_to_process:
    print("\nNo new sections to process. Exiting.")
    exit(0)

# Checkpointing function
def checkpoint_progress():
    feedback = {
        "Available Sections": [s[0] for s in sections],
        "Section Reviews": all_section_reviews
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(feedback, f, indent=4, ensure_ascii=False)
    print(f"\nCheckpoint saved to {CHECKPOINT_FILE}.")

# Generate paper-specific models
paper_specific_models = generate_paper_models(sections)

start_time = time.time()
for section_name in sections_to_process:
    print(f"\n\nProcessing section: {section_name}")
    
    section_text = extract_section(args.pdf_path, section_name) if args.pdf_path.endswith(".pdf") else next(s[1] for s in sections if s[0] == section_name)
    
    print("\n🔍 **Extracted Section:**")
    print(section_text[:1000])

    similar_paper_data = generate_base_models(args.url, section_text)
   
    print(f"\n📢 **Reviewers Begin Discussion for {section_name}:**\n")
    review_outputs = {model: reviewer_agent(assigned_reviewers[0], section_text, model) for model in MODELS}

    def fancy_aggregate_reviews(review_list):
        analyzer = SentimentIntensityAnalyzer()
        sentiments = [analyzer.polarity_scores(r) for r in review_list]
        weights = [abs(s['compound']) for s in sentiments]
        total = sum(weights) + 1e-6
        normalized_weights = [w / total for w in weights]

        weighted_text = " ".join([r * max(1, int(w * 10)) for r, w in zip(review_list, normalized_weights)])

        summarizer_model = pipeline("summarization", model="facebook/bart-large-cnn")
        summary = summarizer_model(weighted_text, max_length=150, min_length=40, do_sample=False)
        return summary[0]['summary_text']

    aggregated_review = fancy_aggregate_reviews(list(review_outputs.values()))
    final_summary = summarizer(section_text, aggregated_review)

    if "DeskReviewer" not in all_section_reviews:
        desk_review = consult_desk_reviewer(sections[0][1])
        all_section_reviews["DeskReviewer"] = {"Review": desk_review[1], "Accept": desk_review[0]}

    all_section_reviews[section_name] = {
        "Test": consult_test(section_text),
        "Reviewers": review_outputs,
        "Grammar Check": consult_grammar(section_text),
        "Novelty Check": consult_novelty(section_text),
        "Fact Check": fact_checker(section_text),
        "Questioner": consult_question(section_text),
        "Final Summary": aggregated_review + "\n" + final_summary
    }

    checkpoint_progress()

print("\nAll new sections processed. Final checkpoint saved.")
print(f"\nTotal time taken: {time.time() - start_time:.2f} seconds")

with open(MODEL_LIST_FILE, "w") as f:
    for key in paper_specific_models:
        f.write(f"{key}\n")

# ---- Stage 2: Answering Questions (Optional) ----

if args.answer_questions:
    print("\nStarting Question-Answering Stage...")

    with open(MODEL_LIST_FILE, "r") as f:
        paper_specific_models = [line.strip() for line in f if line.strip()]

    with open(CHECKPOINT_FILE, "r") as f:
        feedback = json.load(f)

    if "Answers" not in feedback:
        feedback["Answers"] = {}

    start_time = time.time()
    for section_name, section_data in feedback["Section Reviews"].items():
        if section_name in feedback["Answers"]:
            print(f"\nSkipping already processed section: {section_name}")
            continue

        print(f"\nProcessing section: {section_name}")
        questions = section_data.get("Questioner", "").split("?")
        feedback["Answers"][section_name] = {}

        for question in questions:
            question = question.strip() + "?"
            if question == "?":
                continue

            print(f"Processing question: {question}")
            feedback["Answers"][section_name][question] = {}

            for model in paper_specific_models:
                if section_name == model:
                    continue
                answer = chat(model=model, messages=[{"role": "user", "content": question}]).message.content.strip()
                feedback["Answers"][section_name][question][model] = answer

        with open(ANSWER_FILE, "w") as f:
            json.dump(feedback, f, indent=4)

    print(f"\nAll questions answered in {time.time() - start_time:.2f} seconds")
    print(f"Final answers saved to {ANSWER_FILE}")
