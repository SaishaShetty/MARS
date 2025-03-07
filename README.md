# MARS: Multi-Agent Review System for Academic Papers

### Overview
The MARS project is designed to automate the evaluation of research papers by leveraging multiple AI agents. These agents provide feedback on different sections of a research paper, including relevance, quality, grammar, and open-ended questions. The project utilizes the Ollama framework for model interactions and PyPDF2 for PDF processing.

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

Also, make sure you have the base `mistral`, `llama3.2`, `qwen2.5` and `deepseek-r1` models downloaded from the Ollama framework.
You can download them by:
```bash
ollama run <model_name>
```
where `<model_name>` is the name of the model you want to download.

### Usage
#### Run
Firstly, we run the file that gives questions that could be useful to improve the paper by the questioner.
To test this system, use the following command:

- `<cfp_url>`: URL to the Conference Call for Papers (CFP).
- `<json_path>`: Path to the json file of the research paper (Sectioned).
Alternatively, you can provide the path to a .pdf file to extract the text and sections. However, the text extraction may not be perfect.
- `<answer_question>`: If you want to answer the questions that the questioner has asked using the sections of the paper, this is an optional argument to run the second half of the paper review system.

#### Example
```bash
python MARS.py https://www.example.com/cfp example_paper.json
```
Once the processing is complete, it is saved as a "feedback_collab_answer.json". This file contains the feedback for each section of the paper and the answers to the questions asked by the questioner.

The schema for a paper that can be processed by the pipeline can be found in the `paper.schema.json` file.

### Outputs

1. **Console Output**:
   - Displays the feedback for each section.

2. **Feedback JSON File**:
   - Saves detailed feedback for each section with the answers from the questioner in `feedback_collab_with_answers.json` file.

#### Sample Feedback Format
```json
{
  "DeskReviewer": {
      "Review": "Accept - Relevant to the conference topics.",
      "Accept": true,
  }, 
  "Abstract": {
    "Reviwers": {
      "Reviewer1": "Weak Accept - Good quality but could improve clarity.",
      "Reviewer2": "Reject - Needs more data to support claims.",
      "Reviewer3": "Weak Accept - Add more details to methodology.",
      "Reviewer4": "Accept - Relevant to the conference topics."
    },
    "Questioner": "What are the limitations of this study?",
    "Grammar Check": "Accept - No grammar issues found.",
    "Novelty Check": "Reject - Lacks novelty in the approach.",
    "Fact Check": "Accept - No factual errors found.",
    "Final Summary": "Weak Accept - Good quality but could improve clarity."
  },
  "Introduction": {
    ...
  },
  "Answers" : {
    "What are the limitations of this study?": {
      "Abstract": "The limitations of this study include the small sample size and lack of diversity in the participants.",
      "Introduction": "The study was limited by the lack of access to detailed data on the participants' medical history."
      ...
    }
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
- **`MARS.py`**: Main script to run the paper review system.
- **`requirements.txt`**: Lists all dependencies for the project.
- **`dataset_results/`**: Contains results of 10 research papers.
- **`human_reviews/`**:Contains list of 10 research paper's human reviews.
- **`util/`**: Contains utility scripts for various tasks.
  - **`__init__.py`**: Initializes the utility package.
  - **`extract_cfp.py`**: Extracts topics from CFP.
  - **`extract_keywords.py`**: Extracts keywords from text.
  - **`reviewer.py`**: Defines reviewer classes and functions.
  - **`scholar.py`**: Searches for academic papers.
  - **`review_collab.py`**: Reviewers communicate with each other and provide feedback and summary. Also has a PDF parser.
  - **`multiagent.py`**: Contains the main class for the multi-agent system.
  - **`build_models.py`**: Builds the models for the agents.
- **`results/`**: Contains the results of the paper review system.
  - **`csv/`**: Contains the CSV files of the results.
      - **`ablation_results.csv`**: Contains the ablation results of the paper review system.
      - **`section_language_scores.csv`**: Contains the language scores of the sections of the paper.
      - **`summarizer_language_scores.csv`**: Contains the language scores of the summarizer.
  - **`plots/`**: Contains the plots of the results.
      - **`plotter.py`**: Plots the scores from the metric scores.
      - **`plots.ipynb`**: Jupyter notebook to plot the scores.
  - **`scripts/`**: Contains the scripts for the evaluation of the paper review system.
      - **`ablation.py`**: Contains the ablation script for the paper review system.
      - **`eval_scores.py`**: Contains the language evaluation script of the paper review system (BLEU,ROUGE-L,METEOR).
      - **`conditional_probabilities.py`**: Contains the probability calculation script of the paper review system.
      - **`accept_reject_calc.py`**: Contains the script to calculate the accept and reject scores of the paper review system.
