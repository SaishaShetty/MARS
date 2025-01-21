import argparse
import re
from PyPDF2 import PdfReader

def parse_pdf_to_text(pdf_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"  # Add newline between pages
        return text
    except Exception as e:
        return f"Error parsing PDF: {e}"

def clean_text(text):
    """Clean the extracted text by fixing common PDF extraction issues."""
    # Remove extra spaces in all-caps headers
    text = re.sub(r'([A-Z])\s+([A-Z][a-z])', r'\1\2', text)
    
    # Ensure Roman numerals start on new lines
    text = re.sub(r'([^I-Z])((?:IX|IV|V?I{1,3}|I[XV]|X{1,3}|VI{1,3})\.)', r'\1\n\2', text)
    
    # Ensure proper spacing after Roman numerals
    text = re.sub(r'([IVX]+)\.\s*([A-Z])', r'\1. \2', text)
    
    return text

def split_text_into_sections(text):
    """
    Split the text into sections based on common research paper headers.
    Returns a list of (header, content) tuples to preserve order and handle duplicate headers.
    """
    # Simpler pattern that matches what we see in the output
    section_pattern = r"""
        (?:^|\n)                   # Start of string or newline
        (?:                        # Start of non-capturing group
            (?:[IVX]+\.)\s*       # Roman numerals followed by a dot
            [A-Z][A-Za-z\s]*      # Section title
            |
            (?:Abstract|ABSTRACT|ACKNOWLEDGMENTS|REFERENCES)  # Special sections
        )
    """
    
    # Find all section headers with their positions
    headers = []
    for match in re.finditer(section_pattern, text, re.VERBOSE | re.MULTILINE):
        header_text = match.group().strip()
        
        # Skip if this appears to be a reference citation
        if "et al." in header_text.lower() or re.search(r'\[\d+\]', header_text):
            continue
            
        # Skip if header contains "TABLE"
        if "TABLE" in header_text:
            continue
            
        headers.append((match.start(), header_text))
    
    # Add end position
    headers.append((len(text), "END"))
    
    # Extract sections with their content
    sections = []
    references_content = ""
    found_references = False
    
    for i in range(len(headers) - 1):
        start_pos = headers[i][0]
        end_pos = headers[i + 1][0]
        header = headers[i][1]
        content = text[start_pos:end_pos].strip()
        
        if found_references:
            # Append all content after REFERENCES to references_content
            references_content += "\n" + content
            continue
            
        if header == "REFERENCES":
            found_references = True
            references_content = content
            sections.append((header, references_content))
            continue
            
        # Only add non-empty sections
        if content and not content.isspace():
            # Handle content with TABLE
            if i > 0 and "TABLE" in content:
                # Append this content to the previous section
                prev_header, prev_content = sections[-1]
                sections[-1] = (prev_header, prev_content + "\n" + content)
            else:
                sections.append((header, content))
    
    # If we found references and collected additional content, update the references section
    if found_references:
        for i in range(len(sections)):
            if sections[i][0] == "REFERENCES":
                sections[i] = ("REFERENCES", references_content)
                sections = sections[:i+1]  # Remove any sections after REFERENCES
                break
    
    return sections

def main():
    parser = argparse.ArgumentParser(description="Parse a PDF file, extract text, and split by sections.")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    parser.add_argument("--output", "-o", type=str, help="Output file path (optional)")
    parser.add_argument("--preview-length", "-p", type=int, default=500,
                       help="Number of characters to preview for each section (default: 500)")
    
    args = parser.parse_args()
    
    # Parse PDF to text
    pdf_text = parse_pdf_to_text(args.pdf_path)
    if pdf_text.startswith("Error"):
        print(pdf_text)
        return
    
    # # Save raw text for debugging
    with open('raw_pdf_text.txt', 'w', encoding='utf-8') as f:
        f.write(pdf_text)
        
    # Clean the text
    pdf_text = clean_text(pdf_text)
    
    # # Save cleaned text for debugging
    with open('cleaned_pdf_text.txt', 'w', encoding='utf-8') as f:
        f.write(pdf_text)
    
    # Split text into sections
    sections = split_text_into_sections(pdf_text)
    
    if not sections:
        print("WARNING: No sections were extracted!")
        return
    
    # Prepare output
    output = []
    for header, content in sections:
        output.append(f"\n{'='*80}\n{header}\n{'='*80}\n")
        if args.preview_length > 0:
            preview = content[:args.preview_length]
            output.append(f"{content}")
        else:
            output.append(content)
    
    # Output results
    output_text = "\n".join(output)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
    else:
        print(output_text)

def pdf_pipeline(pdf_path):
    # Parse PDF to text
    pdf_text = parse_pdf_to_text(pdf_path)
    if pdf_text.startswith("Error"):
        print(pdf_text)
        return
    
    # Clean the text
    pdf_text = clean_text(pdf_text)
    
    # Split text into sections
    sections = split_text_into_sections(pdf_text)
    
    if not sections:
        print("WARNING: No sections were extracted!")
        return
    
    # Prepare output dictionary
    output_dict = {}
    for header, content in sections:
        output_dict[header] = content
    
    return output_dict

if __name__ == "__main__":
    main()
