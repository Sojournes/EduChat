import os
import streamlit as st
from dotenv import load_dotenv
import anthropic
import re
import requests

# Load environment variables
load_dotenv('.env.example')

# Streamlit page config
st.set_page_config(page_title="EduChat - AI Study Companion", page_icon="📚", layout="wide")

# Title and description
st.title("📚 EduChat - AI Study Companion")
st.markdown("Enter your exam name and generate topics dynamically.")

# Initialize APIs
api_key = os.environ.get("ANTHROPIC_API_KEY")
serper_api_key = os.environ.get("SERPER_API_KEY")

if not api_key:
    st.error("Anthropic API key is missing. Please set the ANTHROPIC_API_KEY in your environment variables.")
    st.stop()

if not serper_api_key:
    st.error("Serper API key is missing. Please set the SERPER_API_KEY in your environment variables.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# Function to dynamically generate topics using Claude (Anthropic)
def get_topics_for_exam(exam_name):
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.3,
            system="Respond in short and clear sentences.",
            messages=[{
                "role": "user",
                "content": f"Can you generate a list of study topics for the {exam_name} exam?"
            }]
        )

        # Extract and process response
        topics_response = message.content
        if isinstance(topics_response, list):
            topics_response = "\n".join([block.text for block in topics_response])

        if isinstance(topics_response, str):
            topics = [line.strip() for line in topics_response.split('\n') if line.strip() and not line.startswith("Sure")]
            topics = [line for line in topics if not re.match(r'^\d+\.|\*|•', line)]
            return topics if topics else ["General Knowledge", "Problem Solving", "Critical Thinking"]
        else:
            st.error(f"Unexpected response format: {type(topics_response)}")
            return []
    except Exception as e:
        st.error(f"Error fetching topics: {str(e)}")
        return []

# Function to fetch search results using Serper API
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

# Function to generate study content using Anthropic Claude
def generate_study_content(exam, topic):
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1500,
            temperature=0.5,
            system="Generate a structured study guide in markdown format.",
            messages=[{
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
            }]
        )

        # Extract response
        study_guide = message.content
        if isinstance(study_guide, list):
            study_guide = "\n".join([block.text for block in study_guide])

        return study_guide if isinstance(study_guide, str) else "No study guide generated."
    except Exception as e:
        st.error(f"Error generating study content: {str(e)}")
        return "An error occurred while generating the study guide."

# Main content area
# Fetch and display resources
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
st.markdown("Built with Anthropic Claude, Serper, and Streamlit.")