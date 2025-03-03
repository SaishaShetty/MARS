import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the CSV file
file_path = "./util/sum_scores.csv"  # Change this to your actual file path
df = pd.read_csv(file_path)

# Rename columns for easier handling
df.columns = ["File Name", "BLEU", "ROUGE-L", "METEOR"]

# Summary statistics
print(df.describe())

# Pairplot to visualize correlations
sns.pairplot(df[["BLEU", "ROUGE-L", "METEOR"]], kind="reg")
plt.suptitle("Pairplot of BLEU, ROUGE-L, and METEOR Scores", y=1.02)
plt.show()

# Correlation heatmap
plt.figure(figsize=(6, 4))
sns.heatmap(df[["BLEU", "ROUGE-L", "METEOR"]].corr(), annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Heatmap of Scores")
plt.show()

# Distribution plots
plt.figure(figsize=(12, 4))
for i, metric in enumerate(["BLEU", "ROUGE-L", "METEOR"]):
    plt.subplot(1, 3, i + 1)
    sns.histplot(df[metric], bins=10, kde=True)
    plt.title(f"Distribution of {metric} Scores")
plt.tight_layout()
plt.show()
