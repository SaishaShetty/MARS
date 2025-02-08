import ollama
import argparse
from PyPDF2 import PdfReader
import re
from reviewer import assigned_reviewers  

def parse_pdf_to_text(pdf_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except Exception as e:
        return f"Error parsing PDF: {e}"

def clean_text(text):
    """Cleans extracted text by fixing spacing issues and formatting errors."""
    text = re.sub(r'([A-Z])\s+([A-Z][a-z])', r'\1\2', text)  
    text = re.sub(r'([^I-Z])((?:IX|IV|V?I{1,3}|I[XV]|X{1,3}|VI{1,3})\.)', r'\1\n\2', text)  
    text = re.sub(r'([IVX]+)\.\s*([A-Z])', r'\1. \2', text)  
    return text

def split_text_into_sections(text):
    """Splits text into sections based on research paper headers."""
    section_pattern = r"""
        (?:^|\n)                   
        (?:
            (?:[IVX]+\.)\s*       
            [A-Z][A-Za-z\s]*      
            |
            (?:Abstract|ABSTRACT|ACKNOWLEDGMENTS|REFERENCES)  
        )
    """
    headers = []
    for match in re.finditer(section_pattern, text, re.VERBOSE | re.MULTILINE):
        header_text = match.group().strip()
        if "et al." in header_text.lower() or re.search(r'\[\d+\]', header_text) or "TABLE" in header_text:
            continue
        headers.append((match.start(), header_text))

    headers.append((len(text), "END"))
    sections = []

    for i in range(len(headers) - 1):
        start_pos, header = headers[i]
        end_pos = headers[i + 1][0]
        content = text[start_pos:end_pos].strip()
        if content and not content.isspace():
            sections.append((header, content))

    return sections

def extract_section(pdf_path, section_name):
    """Extracts a section based on approximate name matching."""
    pdf_text = parse_pdf_to_text(pdf_path)
    if pdf_text.startswith("Error"):
        return pdf_text

    pdf_text = clean_text(pdf_text)
    sections = split_text_into_sections(pdf_text)

    for header, content in sections:
        if section_name.lower() in header.lower():
            return content

    return f"Section '{section_name}' not found. Try a different section."

reviewer_messages = []
for reviewer in assigned_reviewers:
    message = f"""
    You are {reviewer.name}, assigned to review this paper. 
    You are {reviewer.experience_level} reviewer with {reviewer.knowledge_level} expertise.
    Your feedback tone is {reviewer.tone}.
    You have no conflict of interest.
    Your decisions may include: [Strong Accept, Accept, Weak Accept, Weak Reject, Strong Reject].
    At the end of your review, provide a final decision based on your critique.
    """
    reviewer_messages.append(message)

def reviewer_agent(reviewer, section_text, previous_feedback=None):
    """LLM agent that reviews a section based on assigned reviewer attributes and provides a decision."""
    prompt = f"""
    {reviewer_messages[assigned_reviewers.index(reviewer)]}
    
    The section for review:
    "{section_text}"
    
    {f"Previous discussion so far: {previous_feedback}" if previous_feedback else ""}
    
    Respond in a conversational manner, directly addressing previous comments if any.
    If you agree with a previous reviewer, elaborate on why.
    If you disagree, provide justification and alternative suggestions.
    
    🔹 **At the end of your review, explicitly state your final decision (Strong Accept, Accept, Weak Accept, Weak Reject, Strong Reject).**
    """
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

def summarizer(section_text, reviews):
    """Summarizes the discussion into a structured summary with a final decision."""
    prompt = f"""Summarize the discussion among three reviewers about the following research paper section.
    
    Section: "{section_text}"

    Reviews:
    {reviews}

    Format the summary as if recording minutes of a meeting. Highlight agreements, disagreements, and key takeaways.
    
    🔹 **At the end, determine the final decision based on the majority vote (Strong Accept, Accept, Weak Accept, Weak Reject, Strong Reject).**
    """
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

def main():
    parser = argparse.ArgumentParser(description="Extract and discuss a specific section of a research paper.")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    parser.add_argument("section_name", type=str, help="Name of the section to extract and discuss")

    args = parser.parse_args()
    section_text = extract_section(args.pdf_path, args.section_name)
    if "no" in section_text:
        print(section_text)
        return

    print("\n🔍 **Extracted Section:**")
    print(section_text[:1000]) 

    print("\n📢 **Reviewers Begin Discussion:**\n")
    
    review1_output = reviewer_agent(assigned_reviewers[0], section_text)
    print(f"🗣️ **{assigned_reviewers[0].name} ({assigned_reviewers[0].experience_level} - {assigned_reviewers[0].knowledge_level})**: {review1_output}\n")
    
    review2_output = reviewer_agent(assigned_reviewers[1], section_text, review1_output)
    print(f"🗣️ **{assigned_reviewers[1].name} ({assigned_reviewers[1].experience_level} - {assigned_reviewers[1].knowledge_level})**: {review2_output}\n")
    
    review3_output = reviewer_agent(assigned_reviewers[2], section_text, f"{review1_output}\n{review2_output}")
    print(f"🗣️ **{assigned_reviewers[2].name} ({assigned_reviewers[2].experience_level} - {assigned_reviewers[2].knowledge_level})**: {review3_output}\n")

    final_summary = summarizer(section_text, f"{review1_output}\n{review2_output}\n{review3_output}")
    
    print("\n**Final Summary and Decision:**")
    print(final_summary)

if __name__ == "__main__":
    main()
