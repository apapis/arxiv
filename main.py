import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
ARTICLE_URL = os.getenv("DATA_URL")
QUESTIONS_URL = os.getenv("API_URL")

def fetch_article_content(url):
    try:
        response = requests.get(url)
        print("\nRaw article response:")
        print(response.text)
        return response.text
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
    analyze_content(article, questions)

if __name__ == "__main__":
    main()