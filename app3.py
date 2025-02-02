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

# In your app3.py (main dashboard):
with col1:
    if st.button("Go to Exam Content Generator"):
        st.switch_page("app.py")  # Now in pages directory

with col2:
    if st.button("Go to Book Chat"):
        st.switch_page("app2.py")  # Now in pages directory

# Footer
st.markdown("---")
st.markdown("Built with Streamlit")