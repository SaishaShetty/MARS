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

MODELS = ["mistral", "llama", "qwen"]

parser = argparse.ArgumentParser(description="MultiAgent Paper Review with Collaboration")
parser.add_argument("url", type=str, help="Path to the Conference CFP")
parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
parser.add_argument("section_name", type=str, help="Paper section for review (optional - reviews all if not specified)", nargs='?', default='')

args = parser.parse_args()

pdf_text = parse_pdf_to_text(args.pdf_path)
cleaned_text = clean_text(pdf_text)
sections = split_text_into_sections(cleaned_text)

print("\nAvailable Sections in the Paper:")
for section in sections:
    print(f"- {section[0]}")

all_section_reviews = {}
sections_to_process = [args.section_name] if args.section_name else [section[0] for section in sections]
for section_name in sections_to_process:
    print(f"\n\nProcessing section: {section_name}")
    
    section_text = extract_section(args.pdf_path, section_name)
    if "no" in section_text.lower():
        print(f"Section '{section_name}' not found or error occurred.")
        continue

    similar_paper_data = generate_base_models(args.url, section_text)
   
    print(f"\n📢 **Reviewers Begin Discussion for {section_name}:**\n")
    review_outputs = {}
    for model in MODELS:
        review_outputs[model] = reviewer_agent(assigned_reviewers[0], section_text)
        print(f"🗣️ **{assigned_reviewers[0].name} ({model})**: {review_outputs[model]}\n")

    wiki_info = consult_wikipedia(section_text)
    grammar_feedback = consult_grammar(section_text)
    novelty_feedback = consult_novelty(section_text)
    fact_check_feedback = fact_checker(section_text)
    question_feedback = consult_question(section_text)
    test_feedback = consult_test(section_text)
    final_summary = summarizer(section_text, "\n".join(review_outputs.values()))

    # Store all feedback for this section
    all_section_reviews[section_name] = {
        "Test": test_feedback,
        "Reviewers": review_outputs,
        "Wikipedia Information": wiki_info,
        "Grammar Check": grammar_feedback,
        "Novelty Check": novelty_feedback,
        "Fact Check": fact_check_feedback,
        "Questioner": question_feedback,
        "Final Summary": final_summary
    }

    print(f"\n**Results for section: {section_name}**")
    print("\n**Wikipedia Information:**")
    print(wiki_info)
    print("\n**Grammar Check Feedback:**")
    print(grammar_feedback)
    print("\n**Novelty Check Feedback:**")
    print(novelty_feedback)
    print("\n**Fact-Check Feedback:**")
    print(fact_check_feedback)
    print("\n**Final Summary and Decision:**")
    print(final_summary)

feedback = {
    "Available Sections": [section[0] for section in sections],
    "Section Reviews": all_section_reviews
}

with open("feedback_collab.json", "w", encoding='utf-8') as f:
    json.dump(feedback, f, indent=4, ensure_ascii=False)

print("\nAll reviews have been saved to feedback_collab.json")