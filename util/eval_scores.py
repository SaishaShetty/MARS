import json
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def compute_rouge_l(reference, generated):
    """
    Compute a simple ROUGE-L score based on longest common subsequence (LCS).
    """
    ref_words = reference.split()
    gen_words = generated.split()
    
    def lcs(X, Y):
        m, n = len(X), len(Y)
        L = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            for j in range(n + 1):
                if i == 0 or j == 0:
                    L[i][j] = 0
                elif X[i - 1] == Y[j - 1]:
                    L[i][j] = L[i - 1][j - 1] + 1
                else:
                    L[i][j] = max(L[i - 1][j], L[i][j - 1])
        
        return L[m][n]

    lcs_length = lcs(ref_words, gen_words)
    recall = lcs_length / len(ref_words) if ref_words else 0
    precision = lcs_length / len(gen_words) if gen_words else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return f1_score

# Load JSON files
file1_path = "/Users/saishashetty/Desktop/litai/dataset_results/TwoLayerReLURisk_6doXHqwMayf.json"
file2_path = "/Users/saishashetty/Desktop/litai/human_reviews/TwoLayerReLURisk_6doXHqwMayf.json"

with open(file1_path, "r") as f1, open(file2_path, "r") as f2:
    data1 = json.load(f1)
    data2 = json.load(f2)

# Extract reviewer comments from first file
section_reviews = []
if "Section Reviews" in data1:
    for section, content in data1["Section Reviews"].items():
        if isinstance(content, dict) and "Reviewers" in content:
            combined_review = " ".join(content["Reviewers"].values())
            section_reviews.append((section, combined_review))

# Extract corresponding output comments from second file
reviewer_comments = []
if "output" in data2:
    for review_group in data2["output"]:
        combined_review = " ".join(review_group)
        reviewer_comments.append(combined_review)

# Ensure lists are properly aligned by similarity
vectorizer = TfidfVectorizer()
all_texts = [s[1] for s in section_reviews] + reviewer_comments
X = vectorizer.fit_transform(all_texts)
similarity_matrix = cosine_similarity(X)

# Find best matches based on similarity
best_matches = []
for i in range(len(section_reviews)):
    section_idx = i
    review_idx = len(section_reviews) + similarity_matrix[i, len(section_reviews):].argmax()
    best_matches.append((section_reviews[section_idx][0], section_reviews[section_idx][1], reviewer_comments[review_idx - len(section_reviews)]))

# Compute BLEU, ROUGE-L, and METEOR scores
smoothing = SmoothingFunction().method1
bleu_scores, rouge_l_scores, meteor_scores = [], [], []

for section, ref, gen in best_matches:
    bleu_score = sentence_bleu([ref.split()], gen.split(), smoothing_function=smoothing)
    rouge_l_score = compute_rouge_l(ref, gen)
    meteor = meteor_score([ref.split()], gen.split())  # Fix: Tokenize input
    
    bleu_scores.append(bleu_score)
    rouge_l_scores.append(rouge_l_score)
    meteor_scores.append(meteor)

# Compute overall BLEU, ROUGE-L, and METEOR scores
average_bleu = sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0
average_rouge_l = sum(rouge_l_scores) / len(rouge_l_scores) if rouge_l_scores else 0
average_meteor = sum(meteor_scores) / len(meteor_scores) if meteor_scores else 0

# Store results in DataFrame
results_df = pd.DataFrame({
    "Section": [s[0] for s in best_matches],
    "Reference Text": [s[1] for s in best_matches],
    "Generated Text": [s[2] for s in best_matches],
    "BLEU Score": bleu_scores,
    "ROUGE-L Score": rouge_l_scores,
    "METEOR Score": meteor_scores
})

# Save individual results to CSV
results_df.to_csv("evaluation_results.csv", index=False)

# Save overall scores to a separate CSV file and append if exists
overall_scores_file = "overall_scores.csv"
overall_scores_df = pd.DataFrame({
    "File Name": [file2_path],
    "Overall BLEU Score": [average_bleu],
    "Overall ROUGE-L Score": [average_rouge_l],
    "Overall METEOR Score": [average_meteor]
})

if os.path.exists(overall_scores_file):
    existing_df = pd.read_csv(overall_scores_file)
    overall_scores_df = pd.concat([existing_df, overall_scores_df], ignore_index=True)

overall_scores_df.to_csv(overall_scores_file, index=False)

# Print top results
print(results_df.head())

# Print overall scores
print(f"Overall BLEU Score: {average_bleu:.4f}")
print(f"Overall ROUGE-L Score: {average_rouge_l:.4f}")
print(f"Overall METEOR Score: {average_meteor:.4f}")
