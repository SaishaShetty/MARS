import ollama
import requests
import re
import argparse
import json
from bs4 import BeautifulSoup
from util.review_collab import parse_pdf_to_text, clean_text, extract_section, split_text_into_sections
from build_models import generate_base_models, generate_paper_models
from util.review_collab import extract_section, reviewer_agent, summarizer
from util.reviewer import assigned_reviewers

MODELS = ["mistral", "llama", "qwen"]

parser = argparse.ArgumentParser(description="MultiAgent Paper Review with Collaboration")
parser.add_argument("url", type=str, help="Path to the Conference CFP")
parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
parser.add_argument("section_name", type=str, help="Paper section for review")
args = parser.parse_args()

pdf_text = parse_pdf_to_text(args.pdf_path)
cleaned_text = clean_text(pdf_text)
sections = split_text_into_sections(cleaned_text)

print("\nAvailable Sections in the Paper:")
for section in sections:
    print(f"- {section[0]}")

section_text = extract_section(args.pdf_path, args.section_name)
if "no" in section_text.lower():
    print(section_text)

similar_paper_data = generate_base_models(args.url, section_text)

# Run Multi-Agent Review Collaboration
print("\n📢 **Reviewers Begin Discussion:**\n")
review_outputs = {}
for model in MODELS:
    review_outputs[model] = reviewer_agent(assigned_reviewers[0], section_text)
    print(f"🗣️ **{assigned_reviewers[0].name} ({model})**: {review_outputs[model]}\n")

final_summary = summarizer(section_text, "\n".join(review_outputs.values()))

feedback = {
    "Available Sections": [section[0] for section in sections],
    "Reviewers": review_outputs,
    "Final Summary": final_summary
}

with open("feedback_collab.json", "w") as f:
    json.dump(feedback, f, indent=4)

print("\n**Final Summary and Decision:**")
print(final_summary)
