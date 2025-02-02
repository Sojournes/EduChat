# 📚 EduChat - AI Study Companion

EduChat is an AI-powered study assistant designed to help students with exam preparation and textbook comprehension. It uses advanced AI models to generate structured study materials, practice questions, and relevant learning resources.

## Image

![image](https://github.com/user-attachments/assets/4abfd36d-7eba-47f6-b5f3-df0ce022bfbe)

## 🚀 Features

### 1. **Textbook Summarization & Question Generation**
- Upload a textbook PDF to extract chapters.
- Generate structured chapter summaries, key concepts, formulas, and practice questions.
- Ask AI-powered questions and receive detailed answers.

### 2. **Exam-Specific Study Guide & Resources**
- Enter an exam name to generate relevant study topics.
- Get a comprehensive study guide with key concepts, formulas, and practice exercises.
- Discover additional learning materials including YouTube videos and recommended books.

## 🛠️ Tech Stack
- **Frontend**: Streamlit
- **AI Models**: Anthropic Claude
- **PDF Processing**: PyPDF2, pdfplumber
- **Search & External Resources**: Serper API
- **Environment Management**: dotenv

## 📥 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/educhat-ai.git
   cd educhat-ai
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On macOS/Linux
   venv\Scripts\activate      # On Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Rename `.env.example` to `.env` and add your API keys:
     ```plaintext
     ANTHROPIC_API_KEY=your_anthropic_api_key
     SERPER_API_KEY=your_serper_api_key
     ```

## ▶️ Usage

1. **Run the application**
   ```bash
   streamlit run app.py
   ```
2. **Upload a textbook PDF** to generate summaries and practice questions.
3. **Enter an exam name** to generate relevant study topics and learning resources.

## 📌 Contributing
We welcome contributions! To contribute:
- Fork this repository.
- Create a new branch.
- Commit your changes and open a pull request.

## 📧 Contact
For questions or feedback, reach out via diwakersehgal16@gmail.com.

---
Built with ❤️ using Anthropic Claude, Streamlit, and Serper API.

