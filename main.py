import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import os

load_dotenv()
ARTICLE_URL = os.getenv("DATA_URL")
QUESTIONS_URL = os.getenv("API_URL")

def fetch_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        text_content = soup.get_text()

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
            'text': text_content,
            'images': images,
            'audio': audio
        }
    except Exception as e:
        print(f"Error: {e}")
        return ""

def fetch_questions(url):
    try:
        response = requests.get(url)
        print("\nRaw questions response:")
        print(response.text)
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return ""

def analyze_content(article, questions):
    print("\nArticle content:")
    print(article)
    print("\nQuestions content:")
    print(questions)
    return {}

def main():
    article = fetch_article_content(ARTICLE_URL)
    questions = fetch_questions(QUESTIONS_URL)
    print("Article structure:")
    print(json.dumps(article, indent=4, ensure_ascii=False))
    print("\nQuestions:")
    print(questions)

if __name__ == "__main__":
    main()