from fastapi import FastAPI, File, UploadFile, Form
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

app = FastAPI(
    title="Text Summarizer API",
    description="API for extracting text from a web link or uploaded files (PDF, Word, Text) and summarizing the content using NLP.",
    version="1.0.0"
)

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

def extract_text_from_pdf(file_content):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

def extract_text_from_docx(file_content):
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error extracting text from DOCX: {e}"

def extract_text_from_txt(file_content):
    try:
        return file_content.decode("utf-8")
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


@app.post("/summarize-url")
async def api_summarize_url(url: str = Form(...), summary_ratio: float = Form(0.3)):
    text = extract_text_from_url(url)
    if text.startswith("Error"):
        return {"error": text}

    summary = summarize_text(text, per=summary_ratio)
    if summary.startswith("Error"):
        return {"error": summary}

    return {
        "extracted_text": text,
        "summary": summary
    }

@app.post("/summarize-file")
async def api_summarize_file(file: UploadFile = File(...), summary_ratio: float = Form(0.3)):
    content = await file.read()

    text = ""
    if file.filename.endswith(".txt"):
        text = extract_text_from_txt(content)
    elif file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(content)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(content)
    else:
        return {"error": "Unsupported file format. Please upload .txt, .pdf, or .docx files."}

    if text.startswith("Error"):
        return {"error": text}

    summary = summarize_text(text, per=summary_ratio)
    if summary.startswith("Error"):
        return {"error": summary}

    return {
        "filename": file.filename,
        "extracted_text": text,
        "summary": summary
    }
