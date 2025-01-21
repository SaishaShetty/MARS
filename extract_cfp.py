import requests
from bs4 import BeautifulSoup
import re

class CFPTopicExtractor:
    def __init__(self):
        # Keywords that indicate administrative content to exclude
        self.exclude_keywords = [
            'chair', 'deadline', 'notification', 'period', 'committee',
            'abstract', 'submission', 'date', 'pm', 'am', 'aoe'
        ]

    def is_valid_topic(self, text):
        """Check if a text segment is likely a valid topic."""
        text_lower = text.lower()
        
        # Exclude if contains administrative keywords
        if any(keyword in text_lower for keyword in self.exclude_keywords):
            return False
            
        # Exclude if it's just a date
        if re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text):
            return False
            
        # Exclude if it's just a time
        if re.search(r'\d{1,2}:\d{2}', text):
            return False
            
        # Must have substantial content (at least 3 words)
        words = text.split()
        return len(words) >= 3

    def clean_topic(self, topic):
        """Clean and format a topic string."""
        # Remove leading/trailing punctuation and whitespace
        topic = re.sub(r'^[-•*\s]+|[-•*\s]+$', '', topic)
        
        # Remove repeated whitespace
        topic = ' '.join(topic.split())
        
        return topic

    def extract_topics(self, url):
        """Extract and clean topics from the URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            topics = set()  # Use set to avoid duplicates
            
            # Find the largest list in the document (usually contains topics)
            lists = soup.find_all(['ul', 'ol'])
            if lists:
                largest_list = max(lists, key=lambda x: len(x.find_all('li')))
                for item in largest_list.find_all('li'):
                    topic = self.clean_topic(item.get_text())
                    if self.is_valid_topic(topic):
                        topics.add(topic)
            
            # Convert to sorted list and remove duplicates
            return {
                "success": True,
                "topics": sorted(list(topics))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def format_topics(topics):
    """Format topics for display."""
    print("Technical Areas of Interest:")
    print("===========================")
    for topic in topics:
        print(f"• {topic}")

def main():
    extractor = CFPTopicExtractor()
    url = "https://www.iscaconf.org/isca2025/submit/papers.php"
    
    results = extractor.extract_topics(url)
    
    if results.get("success"):
        format_topics(results["topics"])
    else:
        print(f"Error: {results.get('error')}")

if __name__ == "__main__":
    main()