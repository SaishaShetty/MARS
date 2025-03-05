# LitAI - MultiAgent Paper Review

### Overview
The MultiAgent Paper Review project is designed to automate the evaluation of research papers by leveraging multiple AI agents. These agents provide feedback on different sections of a research paper, including relevance, quality, grammar, and open-ended questions. The project utilizes the Ollama framework for model interactions and PyPDF2 for PDF processing.

### Features
1. **Dynamic Section Feedback**: Provides detailed feedback for each section of a paper.
2. **Multiple Review Agents**: Includes reviewers for grammar, relevance, and content quality.
3. **Customizable Prompts**: Adapts prompts for different sections dynamically.
4. **JSON Feedback Output**: Saves structured feedback in a JSON file for further use.
5. **Integration with Ollama**: Uses AI models for natural language processing tasks.

### Installation
#### Prerequisites
- Python 3.8 or higher
- `pip` for managing Python packages

#### Install Dependencies
Run the following command to install the required Python libraries:
```bash
pip install -r requirements.txt
```

### Usage
#### Run
Firstly, we run the file that gives questions that could be useful to improve the paper by the questioner.
To test this system, use the following command:

- `<cfp_url>`: URL to the Conference Call for Papers (CFP).
- `<json_path>`: Path to the json file of the research paper (Sectioned).

#### Example
```bash
python final.py https://www.example.com/cfp example_paper.json
```
Once the file is saved as a "feedback_collab.json". 
Run the final_qa.py to get answers from the questioner that can help the authors improve the paper.

#### Example
```bash
python final_qa.py feedback_collab.json
```
### Outputs

1. **Console Output**:
   - Displays the feedback for each section.

2. **Feedback JSON File**:
   - Saves detailed feedback for each section with the answers from the questioner in `feedback_collab_with_answers.json` file.

#### Sample Feedback Format
```json
{
  "Abstract": {
    "DeskReviewer": "Accept - Relevant to the conference topics.",
    "Reviewer1": "Weak Accept - Good quality but could improve clarity.",
    "Reviewer2": "Reject - Needs more data to support claims.",
    "Reviewer3": "Weak Accept - Add more details to methodology.",
    "Questioner": "What are the limitations of this study?",
    "Grammar": "Accept - No grammar issues found."
  },
  "Introduction": {
    ...
  }
}
```
### How It Works
1. **PDF Parsing**:
   - Extracts sections such as Abstract, Introduction, Methods, Results, etc.

2. **Model Generation**:
   - Creates AI models dynamically based on the content and CFP URL.

3. **Feedback Collection**:
   - Each agent reviews a specific section and provides feedback.

4. **Feedback Storage**:
   - Saves the feedback in a structured JSON format.

## Project Structure
- **`test.py`**: Entry point for testing the paper review system.
- **`final.py`** Integrates review_colab with other components.
- **`final_qa.py`**: Answers questions provided in each section and store it in another file.
- **`pdf_test.py`**: Handles PDF parsing and section extraction.
- **`build_models.py`**: Manages AI model creation and interaction.
- **`requirements.txt`**: Lists all dependencies for the project.
- **`feedback_files/`**:Contains list of feedback json files.
- **`human_reviews/`**:Contains list of 10 research paper human reviews.
- **`util/`**: Contains utility scripts for various tasks.
  - **`extract_cfp.py`**: Extracts topics from CFP.
  - **`extract_keywords.py`**: Extracts keywords from text.
  - **`pdf_extract.py`**: Extracts text from PDF files.
  - **`reviewers.py`**: Defines reviewer classes and functions.
  - **`scholar.py`**: Searches for academic papers.
  - **`reviewer.py`**: Defines reviewer classes and functions.
  - **`review_collab.py`**: Reviewers communicate with each other and provide feedback and summary.
  - **`eval_scores.py`**: The evaluation scores (BLEU,ROUGE,METEOR) between LLM generated responses with the human reviews.
  - **`prob_scores.py`**: A mathematical evaluation of weighted probability scores of the LLM generated accepts and rejects for each section in the paper.
  - **`ablation.py`**: ....
  - **`plotter.py`**: Plots the scores from the metric scores.
