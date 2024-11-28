from langfuse.decorators import observe
from langfuse.openai import openai
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os
import base64

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
        
        for img in soup.find_all('img'):
            caption = img.find_next('figcaption').text if img.find_next('figcaption') else None
            image_data = {
                'src': img['src'],
                'caption': caption
            }
            
            img_description = analyze_single_image(image_data)
            if img_description:
                new_p = soup.new_tag("p")
                new_p.string = f"[OPIS OBRAZKA: {img_description}]"
                img.replace_with(new_p)

        for audio_tag in soup.find_all('audio'):
            source = audio_tag.find('source')
            if source and source['src']:
                audio_transcript = analyze_single_audio(source['src'])
                if audio_transcript:
                    new_p = soup.new_tag("p")
                    new_p.string = f"[TRANSKRYPCJA AUDIO: {audio_transcript}]"
                    audio_tag.replace_with(new_p)
        
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
        
        return {
            'text_sections': optimized_sections
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

def encode_image(image_url):
    response = requests.get(image_url)
    return base64.b64encode(response.content).decode('utf-8')

@observe(name="analyze_single_image")
def analyze_single_image(image):
    try:
        base_url = "https://centrala.ag3nts.org/dane/"
        full_image_url = base_url + image['src']
        base64_image = encode_image(full_image_url)
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Szczegółowo opisz co widzisz na tym obrazku. Podpis obrazka to: " + (image['caption'] or 'brak podpisu')
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        
        print(f"Successfully analyzed image: {full_image_url}")
        return response.choices[0].message.content
    except Exception as img_e:
        print(f"Error processing image {image['src']}: {img_e}")
        return ""

@observe(name="analyze_single_audio")
def analyze_single_audio(audio_url):
    try:
        base_url = "https://centrala.ag3nts.org/dane/"
        full_audio_url = base_url + audio_url
        response = requests.get(full_audio_url)
        
        # Zapisujemy tymczasowo plik audio
        temp_file_path = "temp_audio.mp3"
        with open(temp_file_path, "wb") as f:
            f.write(response.content)
        
        # Otwieramy plik i wysyłamy do transkrypcji
        with open(temp_file_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pl"
            )
        
        # Usuwamy tymczasowy plik
        os.remove(temp_file_path)
        
        print(f"Successfully transcribed audio: {full_audio_url}")
        return transcript.text
    except Exception as audio_e:
        print(f"Error processing audio {audio_url}: {audio_e}")
        return ""
    
@observe(name="analyze_arxiv_text")
def analyze_article_text(article_data, questions):
    summaries = []
    
    # Analiza tekstu
    for section in article_data['text_sections']:
        if len(section.strip()) > 0:
            summary = summarize_chunk(section, questions)
            if summary:
                summaries.append(summary)
    
    try:
        full_summary = "\n\n".join(summaries)
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
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
    print(json.dumps(answers, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    main()