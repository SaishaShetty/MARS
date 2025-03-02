import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge import Rouge
import json

def calculate_bleu_scores(reference_reviews, generated_reviews):
    """
    Calculates BLEU scores for LLM-generated reviews compared to actual reference reviews.
    
    :param reference_reviews: List of actual reviews (list of strings)
    :param generated_reviews: List of LLM-generated reviews (list of strings)
    :return: List of BLEU scores for each generated review
    """
    bleu_scores = []
    smoothie = SmoothingFunction().method1  
    
    for ref, gen in zip(reference_reviews, generated_reviews):
        reference_tokens = [ref.split()]
        generated_tokens = gen.split()
        bleu_score = sentence_bleu(reference_tokens, generated_tokens, smoothing_function=smoothie)
        bleu_scores.append(bleu_score)
    
    return bleu_scores

def calculate_rouge_scores(reference_reviews, generated_reviews):
    """
    Calculates ROUGE scores for LLM-generated reviews compared to actual reference reviews.
    
    :param reference_reviews: List of actual reviews (list of strings)
    :param generated_reviews: List of LLM-generated reviews (list of strings)
    :return: Dictionary of ROUGE scores
    """
    rouge = Rouge()
    scores = []
    
    for ref, gen in zip(reference_reviews, generated_reviews):
        score = rouge.get_scores(gen, ref)[0] 
        scores.append(score)
    
    return scores

# Load JSON files
with open('actual_reviews.json', 'r') as f:
    actual_reviews_data = json.load(f)

with open('generated_reviews.json', 'r') as f:
    generated_reviews_data = json.load(f)

# Extract reviews from JSON assuming structure {"reviews": ["review1", "review2", ...]}
actual_reviews = actual_reviews_data["reviews"]
generated_reviews = generated_reviews_data["reviews"]

bleu_results = calculate_bleu_scores(actual_reviews, generated_reviews)
rouge_results = calculate_rouge_scores(actual_reviews, generated_reviews)

results = {
    "bleu_scores": bleu_results,
    "rouge_scores": rouge_results
}

with open('evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=4)

for i, (bleu, rouge) in enumerate(zip(bleu_results, rouge_results)):
    print(f"Review {i+1} BLEU Score: {bleu:.4f}")
    print(f"Review {i+1} ROUGE Scores: {rouge}")