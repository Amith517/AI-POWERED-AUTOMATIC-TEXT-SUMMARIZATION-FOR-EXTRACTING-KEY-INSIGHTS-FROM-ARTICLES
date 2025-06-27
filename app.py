import streamlit as st
from helper import get_summary, spacy_rander, fetch_news, fetch_news_links

st.set_page_config(
    page_title="Data Analysis Web App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/everydaycodings/Text-Summarization-using-NLP',
        'Report a bug': "https://github.com/everydaycodings/Text-Summarization-using-NLP/issues/new",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

st.sidebar.title("Text Summarization Web App")

option = ["News Summary and Headlines", "Custom Text Summarization"]
choice = st.sidebar.selectbox("Select of your choice", options=option)

if choice == "Custom Text Summarization":
    st.sidebar.markdown("Copy Sample Article if you want to test the web app. [[article source](https://edition.cnn.com/2022/02/14/us/new-mexico-albuquerque-stabbings/index.html)]")
    #st.sidebar.code(open("presentation/sample.txt", "r").read())
    st.sidebar.write("Welcome to the News Summarization App!")
    st.title("Welcome to {}".format(choice))

    col1, col2 = st.columns(2)

    with col1:
        text = st.text_area(label="Enter Your Text or story", height=350, placeholder="Enter Your Text or story or your article it can be of any length")
        
    if st.button("Get Summary and Headline"):
        summary = get_summary(text)

        try:
            with col2:
                st.write("Text Summary (Summary length: {})".format(len(summary)))
                st.code(summary)
                st.write("Text Headline")
                st.code("Feature Comming Soon")

            spacy_rander(summary)

            spacy_rander(text, text="Yes")
            
        except NameError:
            pass

if choice == "News Summary and Headlines":
    st.title("Article's Summary")

    search_query = st.text_input("", placeholder="Enter the topic you want to search")
    st.write(" ")

    # Fetch news links, titles, and thumbnails using updated function
    links, titles, thumbnails = fetch_news_links(search_query)

    if links:  # If there are news links found
        fetch_news_data = fetch_news(links)  # Fetch the articles content for each link
        
        # Divide the layout into two columns for better presentation
        col1, col2 = st.columns(2)

        with col1:
            for i in range(len(links)):
                if (i % 2) == 0:
                    if thumbnails[i]:
                        st.image(thumbnails[i], width=200)
                    st.write(titles[i])
                    with st.expander("Read The Summary"):
                        st.write(get_summary(fetch_news_data[i]))
                    st.markdown("[**Read Full Article**]({})".format(links[i]), unsafe_allow_html=True)
                    st.write(" ")
        
        with col2:
            for i in range(len(links)):
                if (i % 2) != 0:
                    if thumbnails[i]:
                        st.image(thumbnails[i], width=200)
                    st.write(titles[i])
                    with st.expander("Read The Summary"):
                        st.write(get_summary(fetch_news_data[i]))
                    st.markdown("[**Read Full Article**]({})".format(links[i]), unsafe_allow_html=True)
                    st.write(" ")
    
    else:
        st.info(f"No result found for '{search_query}'. Please try using popular keywords or a different search query.")
