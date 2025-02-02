import os
import re
import tempfile
import streamlit as st
from dotenv import load_dotenv
import anthropic
import pdfplumber
import PyPDF2

# Load environment variables
load_dotenv('.env.example')

# Streamlit page config
st.set_page_config(page_title="EduChat - AI Study Companion", page_icon="📚", layout="wide")

# Title and description
st.title("📚 EduChat - AI Study Companion")
st.markdown("Upload a textbook PDF to generate chapter summaries and questions.")

# Initialize Anthropic client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    st.error("Anthropic API key is missing. Please set the ANTHROPIC_API_KEY in your environment variables.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

def extract_chapters_from_pdf(pdf_path):
    """Extract chapters from PDF using outline/bookmarks or TOC parsing"""
    chapters = []
    
    # Try to extract from PDF outline first
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        if len(pdf.outline) > 0:
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
            if "table of contents" in text.lower():
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
    """Extract text from specific pages of a PDF"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page, end_page):
            if page_num < len(pdf.pages):
                text += pdf.pages[page_num].extract_text() + "\n\n"
    return text

def generate_rag_content(chapter_text):
    """Generate summary and questions using Claude 3 with RAG"""
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.3,
            system="You are a helpful study assistant. Analyze the provided textbook chapter and generate:",
            messages=[{
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
            }]
        )
        
        # Convert response content to string
        if isinstance(message.content, list):
            content = "\n".join([block.text for block in message.content])
        else:
            content = str(message.content)
            
        # Split content into summary and questions
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

def generate_answer(question, context):
    """Generate answer to user question using Claude 3"""
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.3,
            system="Answer the question based on the provided textbook content. Be concise and accurate.",
            messages=[{
                "role": "user",
                "content": f"Textbook content:\n{context[:150000]}\n\nQuestion: {question}\nAnswer:"
            }]
        )
        if isinstance(message.content, list):
            return "\n".join([block.text for block in message.content])
        return str(message.content)
    except Exception as e:
        return f"Error generating answer: {str(e)}"

# Sidebar for PDF upload
with st.sidebar:
    st.header("Upload Textbook")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        
        chapters = extract_chapters_from_pdf(tmp_path)
        if chapters:
            selected_chapter = st.selectbox(
                "Select Chapter",
                [f"{chap['title']} (pp. {chap['start_page']+1}-{chap['end_page']})" for chap in chapters]
            )
            generate_button = st.button("Generate Chapter Guide")
        else:
            st.warning("No chapters detected in PDF. Using full document.")
            selected_chapter = None
            generate_button = False

# ... (keep all previous code the same until the main content area section)

# Main content area
if uploaded_file:
    if 'chapter_data' not in st.session_state:
        st.session_state.chapter_data = {}

    if generate_button and selected_chapter:
        # Find selected chapter details
        chap_index = [i for i, chap in enumerate(chapters) 
                    if selected_chapter.startswith(chap['title'])][0]
        chapter = chapters[chap_index]
        
        with st.spinner(f"Processing Chapter {chap_index+1}: {chapter['title']}..."):
            # Extract chapter text
            chapter_text = extract_chapter_text(
                tmp_path, 
                chapter['start_page'], 
                chapter['end_page']
            )
            
            # Generate RAG content
            summary_content, questions_content = generate_rag_content(chapter_text)
            
            if summary_content and questions_content:
                # Store in session state
                st.session_state.chapter_data = {
                    'summary': summary_content,
                    'questions': questions_content,
                    'text': chapter_text,
                    'title': chapter['title']
                }

# Display content if available in session state
if "chapter_data" in st.session_state and st.session_state.chapter_data:
    # Create tabs for content display
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
    st.subheader("Ask Questions About the Chapter")
    user_question = st.text_input("Enter your question here:", key="user_question")
    
    if user_question:
        with st.spinner("Generating answer..."):
            answer = generate_answer(user_question, st.session_state.chapter_data['text'])
            st.markdown("**Answer:**")
            st.markdown(answer)

# Footer
st.markdown("---")
st.markdown("Built with Anthropic Claude and Streamlit")
