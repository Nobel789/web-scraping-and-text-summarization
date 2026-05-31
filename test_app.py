import pytest
import io
from unittest.mock import patch, MagicMock
from app import extract_text_from_url, extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt, summarize_text
import docx
import PyPDF2

def test_extract_text_from_txt():
    # Mock uploaded file for text
    mock_file = MagicMock()
    mock_file.getvalue.return_value = b"Hello world! This is a test."

    text = extract_text_from_txt(mock_file)
    assert text == "Hello world! This is a test."

def test_summarize_text():
    # A short text shouldn't be summarized, or handles it well
    short_text = "This is short."
    assert summarize_text(short_text) == short_text

    # A longer text
    long_text = "This is the first sentence. This is the second sentence. The third sentence is also here. The fourth sentence adds length. The fifth sentence completes it. This paragraph provides some context. Here is another sentence." * 3
    summary = summarize_text(long_text, per=0.3)
    assert len(summary) > 0

@patch('app.requests.get')
def test_extract_text_from_url(mock_get):
    # Mock response
    mock_response = MagicMock()
    mock_response.content = b"<html><body><p>Test paragraph 1</p><p>Test paragraph 2</p></body></html>"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    text = extract_text_from_url("http://example.com")
    assert "Test paragraph 1" in text
    assert "Test paragraph 2" in text

def test_extract_text_from_docx():
    # Create a real docx in memory
    doc = docx.Document()
    doc.add_paragraph("First paragraph.")
    doc.add_paragraph("Second paragraph.")

    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    text = extract_text_from_docx(file_stream)
    assert "First paragraph." in text
    assert "Second paragraph." in text

def test_extract_text_from_pdf():
    # It's hard to dynamically create a PDF, so we mock PyPDF2.PdfReader
    with patch('app.PyPDF2.PdfReader') as MockPdfReader:
        mock_reader_instance = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "This is a PDF test."
        mock_reader_instance.pages = [mock_page]
        MockPdfReader.return_value = mock_reader_instance

        # We can pass any dummy object since it's mocked
        text = extract_text_from_pdf(MagicMock())
        assert "This is a PDF test." in text
