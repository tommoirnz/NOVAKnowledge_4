import re
from document_reader import read_document
from tools.download_tools import download_file

def summarise_document_from_source(source):

    print("[TOOL] summarise_document_from_source called")

    if not re.match(r"https?://", source):
        return "Error: Please provide a valid document URL"

    # Fix arXiv abs → pdf
    if "arxiv.org/abs/" in source:
        arxiv_id = source.split("/")[-1]
        source = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    path = download_file(source)

    text = read_document(path)
    text = text[:20000]

    return text  # return RAW TEXT