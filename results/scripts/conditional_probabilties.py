import os
import json
import glob
import re
import itertools
from collections import defaultdict

def extract_decision(review_obj):
    """
    Try to extract a decision ("Accept" or "Reject") from a review object.
    This function checks for a boolean field 'Accept' first, then looks into text.
    """
    if isinstance(review_obj, dict):
        if "Accept" in review_obj:
            value = review_obj["Accept"]
            if isinstance(value, bool):
                return "Accept" if value else "Reject"
            elif isinstance(value, str):
                if "accept" in value.lower():
                    return "Accept"
                elif "reject" in value.lower():
                    return "Reject"
        for key, text in review_obj.items():
            if isinstance(text, str):
                match = re.search(r'(Final Decision|Decision)[:\s]+(Accept|Reject)', text, re.IGNORECASE)
                if match:
                    return match.group(2).capitalize()
                match = re.search(r'\b(accept|reject)\b', text, re.IGNORECASE)
                if match:
                    return match.group(1).capitalize()
    elif isinstance(review_obj, str):
        match = re.search(r'\b(accept|reject)\b', review_obj, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()
    return None

def process_json_file(file_path, cond_counts, total_counts, pair_counts):
    """
    Process one JSON file:
      - Iterate through each section in "Section Reviews"
      - Extract reviewer decisions (from both top-level keys and nested "Reviewers")
      - Update counts for pairwise conditional probability calculations.
    """
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing {file_path}: {e}")
            return

    if "Section Reviews" not in data:
        return

    section_reviews = data["Section Reviews"]
    for section, review_data in section_reviews.items():
        decisions = {}
        # First, check for nested "Reviewers"
        if isinstance(review_data, dict) and "Reviewers" in review_data:
            for reviewer, rev_obj in review_data["Reviewers"].items():
                decision = extract_decision(rev_obj)
                if decision:
                    decisions[reviewer] = decision

        # Also look at other keys that might represent individual reviewer entries.
        if isinstance(review_data, dict):
            for key, value in review_data.items():
                if key in {"Reviewers", "Review", "Test", "Grammar Check", "Novelty Check", "Fact Check", "Questioner", "Final Summary"}:
                    continue
                decision = extract_decision(value)
                if decision:
                    decisions[key] = decision

        # If we have at least 2 reviewers, update our pairwise counts.
        reviewers = list(decisions.keys())
        if len(reviewers) < 2:
            continue
        
        for i in range(len(reviewers)):
            rev_i = reviewers[i]
            decision_i = decisions[rev_i]
            total_counts[rev_i][decision_i] += 1
            for j in range(len(reviewers)):
                if i == j:
                    continue
                rev_j = reviewers[j]
                decision_j = decisions[rev_j]
                cond_counts[rev_i][decision_i][rev_j][decision_j] += 1
                pair_counts[(rev_i, rev_j)] += 1

def compute_multi_condition_probabilities(directory):
    """
    For each section in each JSON file, generate every possible condition (i.e. a nonempty subset
    of reviewers with their decisions) and then, for every target reviewer (one not in the condition),
    record the target’s decision when the condition holds.
    
    This structure maps:
      condition (frozenset of (reviewer, decision)) ->
            target reviewer -> {decision: count}
    """
    multi_cond_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    multi_cond_totals = defaultdict(lambda: defaultdict(int))

    for file_path in glob.glob(os.path.join(directory, "*.json")):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing {file_path}: {e}")
            continue

        if "Section Reviews" not in data:
            continue

        section_reviews = data["Section Reviews"]
        for section, review_data in section_reviews.items():
            decisions = {}
            if isinstance(review_data, dict) and "Reviewers" in review_data:
                for reviewer, rev_obj in review_data["Reviewers"].items():
                    decision = extract_decision(rev_obj)
                    if decision:
                        decisions[reviewer] = decision
            if isinstance(review_data, dict):
                for key, value in review_data.items():
                    if key in {"Reviewers", "Review", "Test", "Grammar Check", "Novelty Check", "Fact Check", "Questioner", "Final Summary"}:
                        continue
                    decision = extract_decision(value)
                    if decision:
                        decisions[key] = decision

            reviewers = list(decisions.keys())
            # Only consider sections with at least 2 reviewers.
            if len(reviewers) < 2:
                continue

            # Generate all nonempty subsets of reviewers that could serve as the condition.
            # We only consider subsets that are not the entire set (so there is at least one target reviewer).
            for r in range(1, len(reviewers)):
                for subset in itertools.combinations(reviewers, r):
                    # Build a frozenset for the condition: each element is (reviewer, decision)
                    condition = frozenset((rev, decisions[rev]) for rev in subset)
                    # For each reviewer not in the condition, record the target's decision.
                    for target in set(reviewers) - set(subset):
                        target_decision = decisions[target]
                        multi_cond_counts[condition][target][target_decision] += 1
                        multi_cond_totals[condition][target] += 1

    # Print the full probability space for multi-reviewer conditions.
    print("Conditional probabilities given multiple reviewer conditions:")
    for condition, target_dict in multi_cond_counts.items():
        condition_str = ", ".join(f"{rev}={dec}" for rev, dec in sorted(condition))
        print(f"Condition: {condition_str}")
        for target, decision_counts in target_dict.items():
            total = multi_cond_totals[condition][target]
            print(f"  For target reviewer '{target}':")
            for decision, count in decision_counts.items():
                probability = count / total if total > 0 else 0
                print(f"    {decision}: {probability:.2f} ({count}/{total})")
        print()

def main(directory):
    # Pairwise counts (existing functionality)
    cond_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    total_counts = defaultdict(lambda: defaultdict(int))
    pair_counts = defaultdict(int)

    for file in glob.glob(os.path.join(directory, "*.json")):
        process_json_file(file, cond_counts, total_counts, pair_counts)

    # Print pairwise conditional probabilities.
    for rev_i in cond_counts:
        for decision_i in cond_counts[rev_i]:
            for rev_j in cond_counts[rev_i][decision_i]:
                counts = cond_counts[rev_i][decision_i][rev_j]
                total_for_pair = sum(counts.values())
                if total_for_pair == 0:
                    continue
                print(f"Conditional probabilities for reviewer '{rev_j}' given '{rev_i}' = {decision_i}:")
                for decision_j, count in counts.items():
                    probability = count / total_for_pair
                    print(f"  {decision_j}: {probability:.2f} ({count}/{total_for_pair})")
                print()

    print("Overall decision counts per reviewer:")
    for rev, counts in total_counts.items():
        print(f"  {rev}: {dict(counts)}")

    # Now compute and print the full probability space
    print("\nExploring the full probability space with multi-reviewer conditions:")
    compute_multi_condition_probabilities(directory)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory_with_json_files>")
        exit(1)
    main(sys.argv[1])
