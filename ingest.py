import os

os.environ["HF_HUB_DISABLE_XET"] = "1"               # normal download (xet hangs on Windows)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = Path(__file__).parent
PDF_PATH = BASE_DIR / "data" / "hotel_info.pdf"
CHROMA_DIR = BASE_DIR / "chroma_db"
MODELS_DIR = BASE_DIR / "models"
COLLECTION_NAME = "hotel_info"


def get_embeddings():
    # Free local model; the same one must be used for building and searching
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5", cache_dir=str(MODELS_DIR))


def build_vectorstore(embeddings=None):
    """Load PDF -> split into chunks -> embed -> store in Chroma."""
    embeddings = embeddings or get_embeddings()
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)  # avoid storing chunks twice

    docs = PyPDFLoader(str(PDF_PATH)).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
    )


def load_vectorstore(embeddings=None):
    """Load the saved database, or build it if it does not exist yet."""
    embeddings = embeddings or get_embeddings()
    if not CHROMA_DIR.exists():
        return build_vectorstore(embeddings)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )


if __name__ == "__main__":
    vectorstore = build_vectorstore()
    print(f"Done! Stored {vectorstore._collection.count()} chunks in {CHROMA_DIR}")