# help.py
import asyncio
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import random
import spacy
import requests
import configparser
from bs4 import BeautifulSoup
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest
import spacy_streamlit
import torch
from transformers import PegasusForConditionalGeneration, PegasusTokenizer, pipeline
import streamlit as st

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")
stopwords = list(STOP_WORDS)
punctuation += "\n"

# Load the API key from config
config = configparser.ConfigParser()
config.read("config.ini")
news_api_key = config["API"]["news_api"]

@st.cache_resource
def load_pegasus_pipeline():
    model_name = "google/pegasus-cnn_dailymail"
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    model = PegasusForConditionalGeneration.from_pretrained(model_name)
    return pipeline("summarization", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)

pegasus_pipeline = load_pegasus_pipeline()

def get_summary_pegasus(text):
    if not text or len(text.strip()) < 50:
        return "Text too short to summarize."

    text = text.strip().replace("\n", " ")

    # Tokenizer & model from pipeline
    tokenizer = pegasus_pipeline.tokenizer

    # Tokenize the input first
    tokens = tokenizer.encode(text, truncation=True, max_length=1024, return_tensors="pt")

    try:
        summary_ids = pegasus_pipeline.model.generate(
            tokens.to(pegasus_pipeline.model.device),
            max_length=200,
            min_length=50,
            do_sample=False,
            early_stopping=True
        )
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summary = summary.replace('<n>', ' ').strip()
        return summary

    except Exception as e:
        return f"Error summarizing: {str(e)}"



def word_frequency(doc):
    word_frequencies = {}
    for word in doc:
        if word.text.lower() not in stopwords and word.text.lower() not in punctuation:
            word_frequencies[word.text.lower()] = word_frequencies.get(word.text.lower(), 0) + 1
    return word_frequencies

def sentence_score(sentence_tokens, word_frequencies):
    sentence_score = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies:
                sentence_score[sent] = sentence_score.get(sent, 0) + word_frequencies[word.text.lower()]
    return sentence_score

def get_summary_spacy(text):
    if not text or len(text.strip()) < 50:
        return "Text too short to summarize."
    doc = nlp(text)
    word_frequencies = word_frequency(doc)
    max_freq = max(word_frequencies.values(), default=1)
    for word in word_frequencies:
        word_frequencies[word] /= max_freq
    sentence_tokens = [sent for sent in doc.sents]
    sentence_scores = sentence_score(sentence_tokens, word_frequencies)
    select_length = max(1, int(len(sentence_tokens) * 0.10))
    summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)
    return " ".join([sent.text for sent in summary])

def spacy_rander(summary, text=None):
    doc = nlp(summary)
    title = "Full Article Visualization" if text == "Yes" else "Summary Visualization"
    spacy_streamlit.visualize_ner(doc, labels=nlp.get_pipe("ner").labels, title=title, show_table=False, key=random.randint(0, 100))

@st.cache_data(ttl=600)
def fetch_news_links(search_query):
    url = f"https://newsapi.org/v2/everything?q={search_query}&apiKey={news_api_key}"
    response = requests.get(url)
    data = response.json()
    if data.get('status') == 'ok' and 'articles' in data:
        links, titles, thumbnails = [], [], []
        for article in data["articles"]:
            links.append(article.get('url', ''))
            titles.append(article.get('title', ''))
            thumbnails.append(article.get('urlToImage', ''))
        return links, titles, thumbnails
    return [], [], []

@st.cache_data(ttl=600)
def fetch_news(link_list):
    news_list = []
    for url in link_list:
        headers = {"Accept": "*/*", "User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            news = []
            bbc_blocks = soup.find_all("div", {"data-component": "text-block"})
            for block in bbc_blocks:
                p = block.find("p")
                if p:
                    news.append(p.get_text())
            if not news:
                for p in soup.find_all("p"):
                    if p.get_text().strip():
                        news.append(p.get_text())
            news_list.append(" ".join(news) if news else "Could not extract article content.")
        except Exception as e:
            news_list.append(f"Error fetching article: {str(e)}")
    return news_list
