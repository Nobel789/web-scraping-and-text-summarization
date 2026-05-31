import streamlit as st
import requests
from bs4 import BeautifulSoup
import PyPDF2
import docx
import io
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def summarize_text(text, per=0.3):
    try:
        if not text or len(text.split()) < 10:
            return text # text is too short to summarize

        doc = nlp(text)

        # Calculate word frequencies
        word_frequencies = {}
        for word in doc:
            if word.text.lower() not in list(STOP_WORDS) and word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1

        # Normalize frequencies
        max_frequency = max(word_frequencies.values())
        for word in word_frequencies.keys():
            word_frequencies[word] = word_frequencies[word] / max_frequency

        # Calculate sentence scores
        sentence_tokens = [sent for sent in doc.sents]
        sentence_scores = {}
        for sent in sentence_tokens:
            for word in sent:
                if word.text.lower() in word_frequencies.keys():
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word.text.lower()]
                    else:
                        sentence_scores[sent] += word_frequencies[word.text.lower()]

        # Select top sentences
        select_length = int(len(sentence_tokens) * per)
        if select_length == 0:
            select_length = 1

        summary_sentences = nlargest(select_length, sentence_scores, key=sentence_scores.get)
        final_summary = [word.text for word in summary_sentences]
        summary = ' '.join(final_summary)

        return summary
    except Exception as e:
        return f"Error summarizing text: {e}"

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error extracting text from DOCX: {e}"

def extract_text_from_txt(file):
    try:
        return file.getvalue().decode("utf-8")
    except Exception as e:
        return f"Error extracting text from TXT: {e}"

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract text from paragraphs
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])

        # If no paragraphs, try getting all text
        if not text.strip():
            text = soup.get_text(separator=' ', strip=True)

        return text
    except Exception as e:
        return f"Error extracting text from URL: {e}"

def main():
    st.set_page_config(page_title="Text Summarizer", page_icon="📝")
    st.title("Web Scraping & Text Summarization App")

    st.markdown("""
    This app allows you to extract text from a web link or uploaded files (PDF, Word, Text)
    and summarize the content using NLP.
    """)

    input_source = st.radio(
        "Select Input Source",
        ("Web Link", "Upload File")
    )

    text_to_summarize = ""

    summary_ratio = st.slider("Summary Ratio", min_value=0.1, max_value=0.9, value=0.3, step=0.1)

    if input_source == "Web Link":
        url = st.text_input("Enter the URL:")
        if st.button("Extract & Summarize"):
            if url:
                with st.spinner("Extracting and summarizing..."):
                    text_to_summarize = extract_text_from_url(url)
                    if text_to_summarize and not text_to_summarize.startswith("Error"):
                        st.subheader("Extracted Text")
                        st.text_area("", text_to_summarize, height=200)

                        summary = summarize_text(text_to_summarize, per=summary_ratio)
                        if summary and not summary.startswith("Error"):
                            st.subheader("Summary")
                            st.success(summary)
                        else:
                            st.error(summary)
                    else:
                        st.error(text_to_summarize)
            else:
                st.warning("Please enter a URL.")

    elif input_source == "Upload File":
        uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])
        if uploaded_file is not None:
            if st.button("Extract & Summarize"):
                with st.spinner("Extracting and summarizing..."):
                    if uploaded_file.type == "text/plain":
                        text_to_summarize = extract_text_from_txt(uploaded_file)
                    elif uploaded_file.type == "application/pdf":
                        text_to_summarize = extract_text_from_pdf(uploaded_file)
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        text_to_summarize = extract_text_from_docx(uploaded_file)

                    if text_to_summarize and not text_to_summarize.startswith("Error"):
                        st.subheader("Extracted Text")
                        st.text_area("", text_to_summarize, height=200)

                        summary = summarize_text(text_to_summarize, per=summary_ratio)
                        if summary and not summary.startswith("Error"):
                            st.subheader("Summary")
                            st.success(summary)
                        else:
                            st.error(summary)
                    else:
                        st.error(text_to_summarize)

if __name__ == "__main__":
    main()
