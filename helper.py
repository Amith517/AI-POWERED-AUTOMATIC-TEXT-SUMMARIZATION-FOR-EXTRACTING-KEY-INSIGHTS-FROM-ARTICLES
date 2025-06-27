import random
from spacy.lang.en.stop_words import STOP_WORDS
import spacy
from string import punctuation
from heapq import nlargest
import spacy_streamlit
import requests
import json
from bs4 import BeautifulSoup
import configparser
import streamlit as st

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Load stopwords and punctuation
stopwords = list(STOP_WORDS)
punctuation = punctuation + "\n"

# Load the API key from config
config = configparser.ConfigParser()
config.read("config.ini")
news_api_key = config["API"]["news_api"]
print("Loaded API Key:", news_api_key)


def spacy_rander(summary, text=None):
    summ = nlp(summary)
    if text == "Yes":
        rend = spacy_streamlit.visualize_ner(summ, labels=nlp.get_pipe("ner").labels, title="Full Article Visualization", show_table=False, key=random.randint(0, 100))
    else:
        rend = spacy_streamlit.visualize_ner(summ, labels=nlp.get_pipe("ner").labels, title="Summary Visualization", show_table=False, key=random.randint(0, 100))
    return rend

def word_frequency(doc):
    word_frequencies = {}
    for word in doc:
        if word.text.lower() not in stopwords:
            if word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1
    return word_frequencies

def sentence_score(sentence_tokens, word_frequencies):
    sentence_score = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_score.keys():
                    sentence_score[sent] = word_frequencies[word.text.lower()]
                else:
                    sentence_score[sent] += word_frequencies[word.text.lower()]
    return sentence_score

@st.cache_data
def fetch_news_links(search_query):
    url = f"https://newsapi.org/v2/everything?q={search_query}&apiKey={news_api_key}"
    response = requests.get(url)
    data = response.json()
    print("Status Code:", response.status_code)
    print("Raw Response:", response.text)
    print("API Response:", data)

    if data.get('status') == 'ok' and 'articles' in data:
        links, titles, thumbnails = [], [], []

        for article in data["articles"]:
            link = article.get('url', '')
            title = article.get('title', '')
            thumbnail = article.get('urlToImage', '')

            links.append(link)
            titles.append(title)
            thumbnails.append(thumbnail)

        return links, titles, thumbnails
    else:
        print("Error: No articles found or invalid response.")
        return [], [], []

@st.cache_data
def fetch_news(link_list):
    news_list = []

    for news_reqUrl in link_list:
        headersList = {
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0"
        }

        try:
            news_response = requests.get(news_reqUrl, headers=headersList, timeout=10)
            soup = BeautifulSoup(news_response.content, features="html.parser")

            # Try to get BBC-specific blocks first
            news = []
            bbc_blocks = soup.find_all("div", {"data-component": "text-block"})
            for block in bbc_blocks:
                p_tag = block.find("p")
                if p_tag is not None:
                    news.append(p_tag.get_text())

            # Fallback: extract all <p> tags if nothing found
            if not news:
                for p in soup.find_all("p"):
                    if p.get_text().strip():
                        news.append(p.get_text())

            if not news:
                news.append("Could not extract article content.")

            joinnews = " ".join(news)
            print(f"\n--- Article Content from {news_reqUrl} ---\n{joinnews[:500]}...\n--- End of Preview ---\n")

            news_list.append(joinnews)

        except Exception as e:
            error_message = f"Error fetching article: {str(e)}"
            print(error_message)
            news_list.append(error_message)

    return news_list


def get_summary(text):
    if not text or len(text.strip()) < 50:
        return "Text too short to summarize."

    doc = nlp(text)
    word_frequencies = word_frequency(doc)

    # Normalize word frequencies
    max_freq = max(word_frequencies.values(), default=1)
    for word in word_frequencies.keys():
        word_frequencies[word] = word_frequencies[word] / max_freq

    sentence_tokens = [sent for sent in doc.sents]
    sentence_scores = sentence_score(sentence_tokens, word_frequencies)

    select_length = max(1, int(len(sentence_tokens) * 0.10))  # At least 1 sentence
    summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)
    summary = [sent.text for sent in summary]
    summary = " ".join(summary)

    return summary
