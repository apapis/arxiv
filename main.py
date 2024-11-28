from langfuse.decorators import observe
from langfuse.openai import openai
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os

load_dotenv()
ARTICLE_URL = os.getenv("DATA_URL")
QUESTIONS_URL = os.getenv("API_URL")
MAX_CHUNK_LENGTH = 6000

def combine_sections(sections, max_length):
    combined = []
    current_chunk = ""
    
    for section in sections:
        if len(current_chunk) + len(section) + 1 <= max_length:
            current_chunk += section + "\n"
        else:
            if current_chunk:
                combined.append(current_chunk)
            current_chunk = section + "\n"
    
    if current_chunk:
        combined.append(current_chunk)
    
    return combined

@observe(name="fetch_article")
def fetch_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        body = soup.find('body')
        sections = body.find_all(['h2', 'p'])
        
        text_sections = []
        current_section = []
        
        for element in sections:
            if element.name == 'h2':
                if current_section:
                    text_sections.append('\n'.join(current_section))
                current_section = [element.get_text().strip()]
            else:
                current_section.append(element.get_text().strip())
        
        if current_section:
            text_sections.append('\n'.join(current_section))

        optimized_sections = combine_sections(text_sections, MAX_CHUNK_LENGTH)
        
        images = []
        for img in soup.find_all('img'):
            images.append({
                'src': img['src'],
                'caption': img.find_next('figcaption').text if img.find_next('figcaption') else None
            })

        audio = []
        for audio_tag in soup.find_all('audio'):
            source = audio_tag.find('source')
            if source and source['src']:
                audio.append(source['src'])

        return {
            'text_sections': optimized_sections,
            'images': images,
            'audio': audio
        }
    except Exception as e:
        print(f"Error: {e}")
        return ""

@observe(name="fetch_questions")
def fetch_questions(url):
    try:
        response = requests.get(url)
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return ""

@observe(name="summarize_text_chunk")
def summarize_chunk(chunk, questions):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Stwórz zwięzłe streszczenie poniższego fragmentu tekstu, zwracając szczególną uwagę na informacje, które mogą być istotne do odpowiedzi na pytania."},
                {"role": "user", "content": f"Pytania do rozważenia:\n{questions}\n\nFragment tekstu:\n{chunk}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in chunk summary: {e}")
        return ""

@observe(name="analyze_arxiv_text")
def analyze_article_text(article_data, questions):
    summaries = []
    
    for section in article_data['text_sections']:
        if len(section.strip()) > 0:
            summary = summarize_chunk(section, questions)
            if summary:
                summaries.append(summary)
    
    try:
        full_summary = "\n\n".join(summaries)
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """Przeanalizuj dokładnie wszystkie streszczenia i znajdź w nich konkretne informacje odpowiadające na pytania. 
                Nie odpowiadaj 'brak informacji' jeśli informacja znajduje się w którejkolwiek części streszczeń.
                Zwróć szczególną uwagę na szczegóły, które mogą początkowo wydawać się nieistotne.
                Odpowiedzi muszą być w formacie JSON: {'ID-pytania-01': 'znaleziona odpowiedź', 'ID-pytania-02': 'znaleziona odpowiedź'}.
                Każda odpowiedź powinna zawierać konkretną informację znalezioną w streszczeniach."""},
                {"role": "user", "content": f"Pytania:\n{questions}\n\nPrzeanalizuj poniższe streszczenia i znajdź odpowiedzi:\n{full_summary}"}
            ]
        )
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("Raw response:", response.choices[0].message.content)
            return {}
    except Exception as e:
        print(f"Error in analysis: {e}")
        return {}

def main():
    article = fetch_article_content(ARTICLE_URL)
    questions = fetch_questions(QUESTIONS_URL)
    answers = analyze_article_text(article, questions)
    print(answers)

if __name__ == "__main__":
    main()