import os
import streamlit as st
from dotenv import load_dotenv
import re
import requests
import openai

# Load environment variables
load_dotenv('.env')

# Streamlit page config
st.set_page_config(page_title="ExamChat - AI Study Companion", page_icon="📚", layout="wide")

# Title and description
st.title("1 📚 Content Generator")
st.markdown("Enter your exam name and generate topics dynamically.")

# Initialize APIs
openai.api_key = os.environ['OPENAI_API_KEY']
serper_api_key = os.environ.get("SERPER_API_KEY")

if not serper_api_key:
    st.error("Serper API key is missing. Please set the SERPER_API_KEY in your environment variables.")
    st.stop()

# Function to dynamically generate topics using OpenAI
def get_topics_for_exam(exam_name):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Respond in short and clear sentences."
                },
                {
                    "role": "user",
                    "content": f"Can you generate a list of study topics for the {exam_name} exam?"
                }
            ]
        )

        # Use dictionary key access based on the observed response structure
        topics_response = response['choices'][0]['message']['content']
        topics = [line.strip() for line in topics_response.split('\n') if line.strip()]
        return topics if topics else ["General Knowledge", "Problem Solving", "Critical Thinking"]
        
    except Exception as e:
        st.error(f"Error fetching topics: {str(e)}")
        return []

# Function to fetch search results including YouTube links and books
def fetch_serper_results(query):
    url = "https://google.serper.dev/search"
    search_queries = [
        f"{query} site:youtube.com",  # Search specifically for YouTube links
        f"{query} books OR textbook OR recommended readings"  # Search for books
    ]
    
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }

    results = {"youtube": [], "books": []}

    for idx, search_query in enumerate(search_queries):
        payload = {"q": search_query, "gl": "us", "hl": "en"}
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if "organic" in data:
                for result in data["organic"][:5]:  # Get top 5 results for each query
                    if idx == 0:
                        results["youtube"].append((result["title"], result["link"]))
                    else:
                        results["books"].append((result["title"], result["link"]))
        else:
            st.error(f"Error fetching search results: {response.status_code}")

    return results

# Sidebar for Exam and Topic Selection
with st.sidebar:
    st.header("Enter Exam Name")
    selected_exam = st.text_input("Enter your exam name", value="SAT")
    
    if selected_exam:
        topics = get_topics_for_exam(selected_exam)
        selected_topic = st.selectbox("Choose a topic", topics)
        generate_button = st.button("Generate Study Content")
    else:
        st.warning("Please enter an exam name.")
        generate_button = False

# Function to generate study content using OpenAI
def generate_study_content(exam, topic):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Generate a structured study guide in markdown format."
                },
                {
                    "role": "user",
                    "content": f"""
Create a comprehensive study guide for the {topic} section of the {exam} exam.
The guide should include:
- Key concepts and explanations
- Important formulas or rules
- Example problems with solutions
- Study tips and common mistakes to avoid
- Suggested practice exercises

Format the response using markdown with clear section headings.
                    """
                }
            ]
        )

        # Use dictionary key access based on the observed response structure
        return response['choices'][0]['message']['content']
        
    except Exception as e:
        st.error(f"Error generating study content: {str(e)}")
        return "An error occurred while generating the study guide."

# Main content area
if generate_button:
    with st.spinner('Generating study content... Please wait.'):
        result = generate_study_content(selected_exam, selected_topic)
        
        st.markdown("### Study Guide")
        st.markdown(result)

        st.download_button(
            label="Download Study Guide",
            data=result,
            file_name=f"{selected_exam}_{selected_topic}.md",
            mime="text/markdown"
        )

        # Fetch additional resources including YouTube and Books
        st.markdown("### Additional Resources")
        search_query = f"{selected_exam} {selected_topic} study resources"
        serper_results = fetch_serper_results(search_query)

        # Display YouTube Links
        if serper_results["youtube"]:
            st.markdown("#### 📺 YouTube Videos")
            for title, link in serper_results["youtube"]:
                st.markdown(f"- [{title}]({link})")

        # Display Books
        if serper_results["books"]:
            st.markdown("#### 📚 Books & Textbooks")
            for title, link in serper_results["books"]:
                st.markdown(f"- [{title}]({link})")

        if not serper_results["youtube"] and not serper_results["books"]:
            st.warning("No relevant YouTube videos or books found.")

# Footer
st.markdown("---")
st.markdown("Built with OpenAI, Serper, and Streamlit.")
