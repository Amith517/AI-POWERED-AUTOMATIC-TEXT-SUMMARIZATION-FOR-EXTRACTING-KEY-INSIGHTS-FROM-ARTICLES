
import streamlit as st

st.set_page_config(
    page_title="Text Summarization Web App",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/everydaycodings/Text-Summarization-using-NLP',
        'Report a bug': "https://github.com/everydaycodings/Text-Summarization-using-NLP/issues/new",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

from help import (
    get_summary_pegasus,
    get_summary_spacy,
    spacy_rander,
    fetch_news,
    fetch_news_links
)

st.sidebar.title("Text Summarization Web App")
choice = st.sidebar.selectbox("Select Option", ["News Summary", "Custom Text Summarization"])

if choice == "Custom Text Summarization":
    st.title("Custom Text Summarization")
    st.sidebar.markdown("Try a sample article: [CNN Stabbing Article](https://edition.cnn.com/2022/02/14/us/new-mexico-albuquerque-stabbings/index.html)")

    col1, col2 = st.columns(2)

    with col1:
        text = st.text_area("Enter Your Text or Article", height=350, placeholder="Paste or write your article here...")
        summarization_method = st.radio("Choose summarization method", ["Abstractive", "Extractive"])

    if st.button("Get Summary"):
        if text.strip():
            with st.spinner("Generating summary..."):
                summary = get_summary_pegasus(text) if summarization_method == "Abstractive" else get_summary_spacy(text)
            with col2:
                st.text_area("Summary", summary, height=250)
            spacy_rander(summary)
            spacy_rander(text, text="Yes")
        else:
            st.warning("Please enter some text.")

elif choice == "News Summary":
    st.title("News Article Summarizer")
    search_query = st.text_input("Search News", placeholder="Enter a topic to search for news...")

    if search_query != st.session_state.get('previous_search', ''):
        st.session_state.clear()
    st.session_state['previous_search'] = search_query

    if search_query:
        links, titles, thumbnails = fetch_news_links(search_query)
        if links:
            articles = fetch_news(links)
            col1, col2 = st.columns(2)

            for i in range(len(links)):
                if i >= len(articles):
                    continue  # Skip if article not fetched properly

                with (col1 if i % 2 == 0 else col2):
                    if thumbnails[i]:
                        st.image(thumbnails[i], width=250)
                    st.subheader(titles[i])

                    summary_key = f"summary_{i}"
                    method_key = f"method_{i}"
                    default_method = st.session_state.get(method_key, "Abstractive")

                    method = st.radio(
                        "Choose summarization method",
                        ("Abstractive", "Extractive"),
                        key=method_key,
                        index=0 if default_method == "Abstractive" else 1
                    )

                    if method != st.session_state.get(f"{method_key}_last"):
                        st.session_state.pop(summary_key, None)
                        st.session_state[f"{method_key}_last"] = method

                    if summary_key not in st.session_state:
                        with st.spinner("Summarizing..."):
                            try:
                                summary = get_summary_pegasus(articles[i]) if method == "Abstractive" else get_summary_spacy(articles[i])
                            except Exception as e:
                                summary = f"Error during summarization: {e}"
                            st.session_state[summary_key] = summary

                    with st.expander("Read The Summary"):
                        st.write(st.session_state[summary_key])

                    st.markdown(f"[**Read Full Article**]({links[i]})", unsafe_allow_html=True)
        else:
            st.info(f"No results found for '{search_query}'. Try a different keyword.")
    else:
        st.info("Please enter a topic to begin searching news articles.")
