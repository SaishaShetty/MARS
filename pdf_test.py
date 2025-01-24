import re
from PyPDF2 import PdfReader


def parse_pdf_to_text(pdf_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"  # Add newline between pages
        return text.strip()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""


def split_text_into_sections(text):
    """
    Split text into sections based on common section headings.
    Returns a dictionary of {section: content}.
    """
    # Define patterns for common section headings
    section_patterns = [
        r"\bAbstract\b",
        r"\bIntroduction\b",
        r"\bMethods?\b",
        r"\bResults?\b",
        r"\bDiscussion\b",
        r"\bConclusion\b",
        r"\bReferences\b",
    ]
    section_regex = "|".join(section_patterns)

    # Find all section headers
    matches = list(re.finditer(section_regex, text, re.IGNORECASE))

    if not matches:
        print("No recognizable sections found.")
        return {}

    sections = {}
    for i, match in enumerate(matches):
        # Get the section header
        section_title = match.group(0).strip()

        # Get the content between this header and the next
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_content = text[start:end].strip()

        sections[section_title] = section_content

    return sections


def pdf_pipeline(pdf_path):
    """
    Full pipeline to extract and split text from a PDF.
    Returns a dictionary of sections.
    """
    # Extract raw text
    text = parse_pdf_to_text(pdf_path)
    if not text:
        return {}

    # Split into sections
    sections = split_text_into_sections(text)
    return sections


if __name__ == "__main__":
    # Example usage
    pdf_path = "path_to_your_pdf.pdf"
    sections = pdf_pipeline(pdf_path)

    if sections:
        print("\nExtracted Sections:\n")
        for section, content in sections.items():
            print(f"=== {section} ===")
            print(content[:500])  # Show first 500 characters of each section
            print("\n")
    else:
        print("No sections extracted from the PDF.")
