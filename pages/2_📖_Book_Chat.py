import os
import re
import hashlib
import tempfile
import streamlit as st
from dotenv import load_dotenv
import pdfplumber
import PyPDF2
import chromadb
from chromadb.utils import embedding_functions
from boltiotai import openai  # Using the BoltIoT wrapper

# Load environment variables
load_dotenv('.env.example')

# Streamlit page config
st.set_page_config(page_title="BookChat - AI Study Companion", page_icon="📚", layout="wide")

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="educhat_db")

# Set the OpenAI API key for BoltIoT
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    st.error("OpenAI API key is missing. Please set the OPENAI_API_KEY in your environment variables.")
    st.stop()

def split_text_into_chunks(text, chunk_size=1000):
    """Split text into manageable chunks preserving paragraph structure."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_length = len(para.split())
        if current_length + para_length > chunk_size:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_length = para_length
        else:
            current_chunk.append(para)
            current_length += para_length

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    return chunks

def extract_chapters_from_pdf(pdf_path):
    """Extract chapters from PDF using outline/bookmarks or TOC parsing."""
    chapters = []
    
    # Try to extract from PDF outline first
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        if hasattr(pdf, 'outline') and len(pdf.outline) > 0:
            for item in pdf.outline:
                if isinstance(item, dict):
                    title = item.get('/Title', 'Untitled')
                    page_num = pdf.get_destination_page_number(item)
                    chapters.append({
                        'title': title,
                        'start_page': page_num,
                        'end_page': None  # Will be filled later
                    })
            if chapters:
                # Calculate end pages
                for i in range(len(chapters)):
                    if i < len(chapters) - 1:
                        chapters[i]['end_page'] = chapters[i+1]['start_page']
                    else:
                        chapters[i]['end_page'] = len(pdf.pages)
                return chapters
    
    # Fallback to TOC parsing if outline is empty
    toc_pattern = r'(?i)(chapter\s+\d+|section\s+\d+|[ivx]+)\s+(.+?)\s+(\d+)'
    with pdfplumber.open(pdf_path) as pdf:
        toc_text = ""
        # Check first 10 pages for TOC
        for page in pdf.pages[:10]:
            text = page.extract_text()
            if text and "table of contents" in text.lower():
                toc_text += text + "\n"
        
        matches = re.findall(toc_pattern, toc_text)
        for match in matches:
            chapters.append({
                'title': match[1].strip(),
                'start_page': int(match[2]) - 1,  # Convert to 0-based index
                'end_page': None
            })
        
        # Calculate end pages for TOC chapters
        if chapters:
            for i in range(len(chapters)):
                if i < len(chapters) - 1:
                    chapters[i]['end_page'] = chapters[i+1]['start_page']
                else:
                    chapters[i]['end_page'] = len(pdf.pages)
    
    return chapters

def extract_chapter_text(pdf_path, start_page, end_page):
    """Extract text from specific pages of a PDF."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page, end_page):
            if page_num < len(pdf.pages):
                page_text = pdf.pages[page_num].extract_text()
                if page_text:
                    text += page_text + "\n\n"
    return text

def generate_rag_content(chapter_text):
    """Generate summary and questions using OpenAI with RAG."""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful study assistant. Analyze the provided textbook chapter and generate:"
                },
                {
                    "role": "user",
                    "content": f"""
Textbook chapter content:
{chapter_text[:150000]}  # Truncate to avoid token limits

Please generate the following sections with clear headings:
1. ## Chapter Summary - Structured chapter summary (markdown)
2. ## Key Concepts - Bullet points of key definitions
3. ## Formulas/Theorems - Important formulas/theorems
4. ## Practice Questions - 10 varied-format questions with answers

Maintain clear section headings and proper formatting.
                    """
                }
            ]
        )
        
        content = response['choices'][0]['message']['content']
        
        # Split content into summary and questions if possible
        if "## Practice Questions" in content:
            summary_part, questions_part = content.split("## Practice Questions", 1)
            questions_part = "## Practice Questions" + questions_part
        else:
            summary_part = content
            questions_part = "## Practice Questions\nNo questions generated."
        
        return summary_part, questions_part
        
    except Exception as e:
        st.error(f"Error generating content: {str(e)}")
        return None, None

def generate_answer(question, chroma_collection):
    """Generate answer using RAG with ChromaDB retrieval and OpenAI."""
    try:
        # Retrieve relevant chunks
        results = chroma_collection.query(
            query_texts=[question],
            n_results=5
        )
        
        # Format context with citations
        context = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            context.append(
                f"Chapter: {meta['chapter']}\n"
                f"Pages: {meta['start_page']}-{meta['end_page']}\n"
                f"Content: {doc}\n"
            )
        context_str = "\n\n".join(context)
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an academic assistant. Answer questions using only the provided context. "
                        "Always cite sources using chapter and page numbers. If unsure, say 'I don't know'."
                    )
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context_str}\n\nQuestion: {question}\nAnswer:"
                }
            ]
        )
        
        return response['choices'][0]['message']['content']
        
    except Exception as e:
        return f"Error generating answer: {str(e)}"

# Streamlit UI
st.title("2 📖 Book Chat")
st.markdown("Upload a textbook PDF to generate chapter summaries and questions.")

# Sidebar for PDF upload
with st.sidebar:
    st.header("Upload Textbook")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        
        chapters = extract_chapters_from_pdf(tmp_path)
        if chapters:
            # Create unique collection based on file hash
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
            collection_name = f"textbook_{file_hash}"
            chroma_collection = chroma_client.get_or_create_collection(name=collection_name)
            
            with st.spinner("Indexing textbook content..."):
                for chapter in chapters:
                    chapter_text = extract_chapter_text(
                        tmp_path, 
                        chapter['start_page'], 
                        chapter['end_page']
                    )
                    chunks = split_text_into_chunks(chapter_text)
                    
                    # Generate metadata for each chunk
                    ids = [f"{chapter['title']}_chunk_{i}" for i in range(len(chunks))]
                    metadatas = [{
                        "chapter": chapter['title'],
                        "start_page": chapter['start_page'] + 1,  # 1-based page numbers
                        "end_page": chapter['end_page']
                    } for _ in chunks]
                    
                    chroma_collection.add(
                        documents=chunks,
                        metadatas=metadatas,
                        ids=ids
                    )
            
            selected_chapter = st.selectbox(
                "Select Chapter",
                [f"{chap['title']} (pp. {chap['start_page']+1}-{chap['end_page']})" for chap in chapters]
            )
            generate_button = st.button("Generate Chapter Guide")
        else:
            st.warning("No chapters detected in PDF. Using full document.")
            selected_chapter = None
            generate_button = False

# Maintain session state for chapter data
if uploaded_file and 'chapter_data' not in st.session_state:
    st.session_state.chapter_data = {}

if uploaded_file and selected_chapter and generate_button:
    chap_index = [i for i, chap in enumerate(chapters) 
                  if selected_chapter.startswith(chap['title'])][0]
    chapter = chapters[chap_index]
    
    with st.spinner(f"Processing Chapter {chap_index+1}: {chapter['title']}..."):
        chapter_text = extract_chapter_text(
            tmp_path, 
            chapter['start_page'], 
            chapter['end_page']
        )
        summary_content, questions_content = generate_rag_content(chapter_text)
        
        if summary_content and questions_content:
            st.session_state.chapter_data = {
                'summary': summary_content,
                'questions': questions_content,
                'title': chapter['title']
            }

# Display content
if "chapter_data" in st.session_state and st.session_state.chapter_data:
    tab1, tab2 = st.tabs(["Study Guide", "Practice Questions"])
    
    with tab1:
        st.markdown(st.session_state.chapter_data['summary'])
        st.download_button(
            label="Download Study Guide",
            data=st.session_state.chapter_data['summary'],
            file_name=f"{st.session_state.chapter_data['title']}_Study_Guide.md",
            mime="text/markdown"
        )
    
    with tab2:
        st.markdown(st.session_state.chapter_data['questions'])
        st.download_button(
            label="Download Practice Questions",
            data=st.session_state.chapter_data['questions'],
            file_name=f"{st.session_state.chapter_data['title']}_Practice_Questions.md",
            mime="text/markdown"
        )

    # Question answering section
    st.divider()
    st.subheader("Ask Questions About the Textbook")
    user_question = st.text_input("Enter your question here:", key="user_question")
    
    if user_question:
        with st.spinner("Searching textbook..."):
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
            collection_name = f"textbook_{file_hash}"
            chroma_collection = chroma_client.get_collection(collection_name)
            answer = generate_answer(user_question, chroma_collection)
            st.markdown("**Answer:**")
            st.markdown(answer)

# Footer
st.markdown("---")
st.markdown("Built with OpenAI (via BoltIoT) and Streamlit | Enhanced with RAG using ChromaDB")
