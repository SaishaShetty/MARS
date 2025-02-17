import os
import ollama
import requests
import re
import argparse
import json
from bs4 import BeautifulSoup
from util.review_collab import parse_pdf_to_text, clean_text, extract_section, split_text_into_sections
from build_models import generate_base_models, generate_paper_models
from util.review_collab import extract_section, reviewer_agent, summarizer 
from multiagent import consultGrammar as consult_grammar, consultNovelty as consult_novelty, consultFactChecker as fact_checker, consultWiki as consult_wikipedia, consultQuestioner as consult_question, consultTest as consult_test  
from util.reviewer import assigned_reviewers

# ---- SUPER FANCY ADDITIONS ----
# Import an advanced summarization pipeline and sentiment analyzer
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# ------------------------------

MODELS = ["mistral", "llama3.2", "qwen2.5", "deepseek-r1"]
CHECKPOINT_FILE = "feedback_collab.json"

parser = argparse.ArgumentParser(description="MultiAgent Paper Review with Collaboration")
parser.add_argument("url", type=str, help="Path to the Conference CFP")
parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
parser.add_argument("section_name", type=str, help="Optional: specific paper section for review", nargs='?', default='')
args = parser.parse_args()

# Parse and clean the PDF text.
if args.pdf_path.endswith(".pdf"):
    pdf_text = parse_pdf_to_text(args.pdf_path)
    cleaned_text = clean_text(pdf_text)
    sections = split_text_into_sections(cleaned_text)
else:
    sections = []
    with open(args.pdf_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Check if the JSON file contains an "input" key with "sections"
    if "input" in data and "sections" in data["input"]:
        for section in data["input"]["sections"]:
            sections.append((section["heading"], section["text"]))

print("\nAvailable Sections in the Paper:")
for section in sections:
    print(f"- {section[0]}")

# Load previously processed sections from the checkpoint file, if available.
if os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, "r", encoding='utf-8') as f:
        checkpoint_data = json.load(f)
        all_section_reviews = checkpoint_data.get("Section Reviews", {})
    processed_sections = set(all_section_reviews.keys())
    print(f"\nFound checkpoint. Processed sections: {', '.join(processed_sections) if processed_sections else 'None'}")
else:
    all_section_reviews = {}
    processed_sections = set()

# Determine which sections to process.
if args.section_name:
    # If a specific section is provided, process it only if not already done.
    if args.section_name in processed_sections:
        print(f"\nSection '{args.section_name}' is already processed. Exiting.")
        exit(0)
    sections_to_process = [args.section_name]
else:
    # Process all sections that haven't been processed yet.
    sections_to_process = [section[0] for section in sections if section[0] not in processed_sections]

if not sections_to_process:
    print("\nNo new sections to process. Exiting.")
    exit(0)

# Function for checkpointing current progress to JSON.
def checkpoint_progress(sections, reviews, filename=CHECKPOINT_FILE):
    feedback = {
        "Available Sections": [section[0] for section in sections],
        "Section Reviews": reviews
    }
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(feedback, f, indent=4, ensure_ascii=False)
    print(f"\nCheckpoint saved to {filename}.")

paper_specific_models = generate_paper_models(sections)

for section_name in sections_to_process:
    print(f"\n\nProcessing section: {section_name}")
    
    if args.pdf_path.endswith(".pdf"):
        section_text = extract_section(args.pdf_path, section_name)
    else:
        section_text = next(section[1] for section in sections if section[0] == section_name)
    print("\n🔍 **Extracted Section:**")
    print(section_text[:1000])
    # if "no" in section_text.lower():
    #     print(section_text.lower())
    #     print(f"Section '{section_name}' not found or error occurred.")
    #     continue

    similar_paper_data = generate_base_models(args.url, section_text)
   
    print(f"\n📢 **Reviewers Begin Discussion for {section_name}:**\n")
    review_outputs = {}
    for model in MODELS:
        review_outputs[model] = reviewer_agent(assigned_reviewers[0], section_text, model)
        print(f"🗣️ **{assigned_reviewers[0].name} ({model})**: {review_outputs[model]}\n")

    # ---- SUPER FANCY META-REVIEW AGGREGATION ----
    def fancy_aggregate_reviews(review_list):
        """
        Use sentiment analysis to weight reviews and then generate a weighted aggregated summary using a transformer summarizer.
        Reviews with stronger (absolute) compound sentiment scores will be given more weight.
        """
        analyzer = SentimentIntensityAnalyzer()
        sentiments = [analyzer.polarity_scores(review) for review in review_list]
        weights = [abs(s['compound']) for s in sentiments]
        total = sum(weights) + 1e-6  # avoid division by zero
        normalized_weights = [w / total for w in weights]

        weighted_text = ""
        for review, weight in zip(review_list, normalized_weights):
            repeat_count = max(1, int(weight * 10))  # scale factor: adjust as needed
            weighted_text += (" " + review) * repeat_count

        summarizer_model = pipeline("summarization", model="facebook/bart-large-cnn")
        summary = summarizer_model(weighted_text, max_length=150, min_length=40, do_sample=False)
        return summary[0]['summary_text']

    aggregated_review = fancy_aggregate_reviews(list(review_outputs.values()))
    print("\n**Super Fancy Aggregated Meta-Review:**")
    print(aggregated_review)
    # ---- END SUPER FANCY AGGREGATION ----

    # Optional Human-in-the-Loop check if conflicts are detected.
    if any("conflict" in review.lower() for review in review_outputs.values()):
        print("\n**Potential conflict detected in reviews. Human oversight required.**")
        override = input("Do you want to override the aggregated review? (y/n): ")
        if override.lower() == 'y':
            aggregated_review = input("Enter your revised aggregated review: ")
            print("\nHuman revised aggregated review recorded.")
        else:
            print("\nProceeding with automated aggregated review.")

    # Continue with other consultations.
    # wiki_info = consult_wikipedia(section_text)
    grammar_feedback = consult_grammar(section_text)
    novelty_feedback = consult_novelty(section_text)
    fact_check_feedback = fact_checker(section_text)
    question_feedback = consult_question(section_text)
    test_feedback = consult_test(section_text)
    final_summary = summarizer(section_text, aggregated_review)

    # Store all feedback for this section.
    all_section_reviews[section_name] = {
        "Test": test_feedback,
        "Reviewers": review_outputs,
        # "Wikipedia Information": wiki_info,
        "Grammar Check": grammar_feedback,
        "Novelty Check": novelty_feedback,
        "Fact Check": fact_check_feedback,
        "Questioner": question_feedback,
        "Final Summary": aggregated_review + "\n" + final_summary
    }

    print(f"\n**Results for section: {section_name}**")
    # print("\n**Wikipedia Information:**")
    # print(wiki_info)
    print("\n**Grammar Check Feedback:**")
    print(grammar_feedback)
    print("\n**Novelty Check Feedback:**")
    print(novelty_feedback)
    print("\n**Fact-Check Feedback:**")
    print(fact_check_feedback)
    print("\n**Final Summary and Decision:**")
    print(final_summary)
    
    # ---- CHECKPOINTING: Save current progress to JSON after each section ----
    checkpoint_progress(sections, all_section_reviews)

print("\nAll new sections processed. Final checkpoint saved.")

with open('paper_specific_models.txt', 'w') as f:
    for key in paper_specific_models:
        f.write("%s\n" % key)