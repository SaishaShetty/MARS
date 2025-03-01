import os
import json
import glob
import re
from collections import defaultdict


DECISION_SCORES = {
    "Accept": 100, 
    "Reject": 0      
}

SECTION_WEIGHT = 1 

def extract_decision(review_obj):
    """
    Extracts 'Accept' or 'Reject' decision from a review object.
    If "Accept" is **not found**, defaults to "Reject".
    """
    if isinstance(review_obj, dict):
        if "Accept" in review_obj:
            value = review_obj["Accept"]
            if isinstance(value, bool):
                return "Accept" if value else "Reject"

        for key, text in review_obj.items():
            if isinstance(text, str):
                match = re.search(r'\b(accept|reject)\b', text, re.IGNORECASE)
                if match:
                    return match.group(1).capitalize()

    elif isinstance(review_obj, str):
        match = re.search(r'\b(accept|reject)\b', review_obj, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()

    return "Reject"  

def extract_score(review_obj):
    """Extracts a numerical score (0-100) based on Accept/Reject or numeric values."""

    if isinstance(review_obj, dict) and "Reviewers" in review_obj:
        reviewer_scores = []
        
        for reviewer, review in review_obj["Reviewers"].items():
            decision = extract_decision(review)  
            reviewer_scores.append(DECISION_SCORES.get(decision, 0))  
        
        if reviewer_scores:
            return sum(reviewer_scores) / len(reviewer_scores)  
    

    if isinstance(review_obj, dict):
        for key, value in review_obj.items():
            if isinstance(value, (int, float)) and 0 <= value <= 100:
                return value  

    decision = extract_decision(review_obj)
    return DECISION_SCORES.get(decision, 0)

def determine_verdict(score):
    """Determines the final verdict based on average section score."""
    if score >= 85:
        return "Accept"
    elif 70 <= score < 85:
        return "Minor Revisions"
    elif 50 <= score < 70:
        return "Major Revisions"
    else:
        return "Reject"

def process_json_file(file_path, paper_decisions):
    """Processes a JSON file, extracts section scores, and computes final average-based verdict."""
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing {file_path}: {e}")
            return

    if "Section Reviews" not in data:
        return

    section_reviews = data["Section Reviews"]
    section_scores = {}  
    weighted_total = 0
    num_sections = 0  

    calculations = []  # For debugging

    for section, review_data in section_reviews.items():  
        score = extract_score(review_data) 
        section_scores[section] = score  

        weighted_total += score * SECTION_WEIGHT
        num_sections += 1
        calculations.append(f"{score} × {SECTION_WEIGHT} = {score:.2f}")  

    final_score = weighted_total / num_sections if num_sections > 0 else 0

    final_paper_verdict = determine_verdict(final_score)
    print(f"\nDEBUG: Processing file: {file_path}")
    for section, score in section_scores.items():
        print(f"  Section '{section}': Score = {score:.2f}")
    print(f"  Weighted Contributions: {' + '.join(calculations)}")
    print(f"  **Final Score: {final_score:.2f}**")
    print(f"  **Final Verdict: {final_paper_verdict}**\n")


    paper_decisions[file_path] = {
        "Section Scores": section_scores,
        "Final Score": final_score,
        "Final Decision": final_paper_verdict
    }

def main(directory):
    paper_decisions = {}

    for file in glob.glob(os.path.join(directory, "*.json")):
        process_json_file(file, paper_decisions)

    print("\nFinal Decisions for Each Paper:\n")
    for file_path, result in paper_decisions.items():
        print(f"File: {os.path.basename(file_path)}")
        for section, score in result["Section Scores"].items():
            print(f"  Section '{section}': Score = {score:.2f}")
        print(f"  **Final Score: {result['Final Score']:.2f}**")
        print(f"  **Final Verdict: {result['Final Decision']}**\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python process_reviews.py <directory_with_json_files>")
        exit(1)
    main(sys.argv[1])
