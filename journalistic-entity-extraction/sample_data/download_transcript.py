import os
import requests
from bs4 import BeautifulSoup

def get_full_transcript(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve the page.")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    transcript = []

    for tr in soup.find_all('tr'):
        short_transcript = tr.find('p', class_='short_transcript')
        if short_transcript:
            # Add the short transcript text
            transcript_text = short_transcript.get_text(separator=' ', strip=True)
        else:
            transcript_text = ""

        # Check for hidden full transcript text
        hidden_text = tr.find('span', class_='hidden-full-transcript-text')
        if hidden_text:
            transcript_text += ' ' + hidden_text.get_text(separator=' ', strip=True)
        
        # Only add non-empty transcript text
        if transcript_text.strip():
            transcript.append(transcript_text)
    
    return ' '.join(transcript)

# URL of the page to scrape
url = "https://www.c-span.org/video/?535773-6/house-debate-federal-disaster-tax-relief-bill&action=getTranscript&transcriptType=cc&service-url=%2Fcommon%2Fservices%2FprogramSpeakers.php&progid=463179&appearance-filter=&personSkip=0&ccSkip=0&transcriptSpeaker=&transcriptQuery=#"
transcript = get_full_transcript(url)

if transcript:
    output_directory = "journalistic-entity-extraction/sample_data"
    os.makedirs(output_directory, exist_ok=True)
    output_file_path = os.path.join(output_directory, "full_transcript.txt")
    
    with open(output_file_path, "w") as f:
        f.write(transcript)
    
    print(f"Transcript downloaded successfully and saved to {output_file_path}.")
else:
    print("Failed to retrieve transcript.")
