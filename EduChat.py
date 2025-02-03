import streamlit as st

# Streamlit page config
st.set_page_config(
    page_title="EduChat Dashboard",
    page_icon="📚",
    layout="centered"
)

# Title and description
st.title("📚 EduChat Dashboard")
st.markdown("Welcome to EduChat! Choose your study companion:")

# Create columns for better layout
col1, col2 = st.columns(2)

with col1:
    if st.button("Go to Exam Content Generator"):
        st.switch_page("pages/1_📚_Content_Generator.py")

with col2:
    if st.button("Go to Book Chat"):
        st.switch_page("pages/2_📖_Book_Chat.py")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit")