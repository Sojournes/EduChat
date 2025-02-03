# 📚 EduChat - AI Study Companion  

EduChat is an AI-powered study assistant designed to help students with **exam preparation** and **textbook comprehension**. It leverages AI models to generate structured study materials, practice questions, and relevant learning resources.  

## 📸 Screenshots  

![image](https://github.com/user-attachments/assets/bda7067a-cf42-4bfb-9a68-9c5d3ea7c4af)![image](https://github.com/user-attachments/assets/4abfd36d-7eba-47f6-b5f3-df0ce022bfbe)  

## 🚀 Features  

### **1️⃣ Book Chat - AI-Powered Textbook Learning**  
- **Upload a textbook PDF** to extract chapters.  
- **Generate structured chapter summaries**, key concepts, formulas, and practice questions.  
- **Ask AI-powered questions** and receive contextual answers using **ChromaDB for retrieval**.  

### **2️⃣ Exam Content Generator - Dynamic Study Guides**  
- **Enter an exam name** to generate relevant study topics using AI.  
- **Receive a structured study guide** with key concepts, formulas, example problems, and study tips.  
- **Discover additional resources** with curated **YouTube videos and books** via **Serper API**.  

## 🛠️ Tech Stack  

- **Frontend**: Streamlit  
- **AI Models**: OpenAI (via BoltIoT)  
- **Database**: ChromaDB (for document retrieval and AI-powered search)  
- **PDF Processing**: PyPDF2, pdfplumber  
- **Search & External Resources**: Serper API  
- **Environment Management**: dotenv  

## 📥 Installation  

1. **Clone the repository:**  
   ```bash
   git clone https://github.com/your-username/educhat-ai.git
   cd educhat-ai
   ```
2. **Create a virtual environment and activate it:**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # On macOS/Linux  
   venv\Scripts\activate      # On Windows  
   ```  
3. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```  
4. **Set up environment variables:**  
   - Create a `.env` file in the root directory and add your API keys:  
     ```plaintext
     OPENAI_API_KEY=your_openai_api_key
     SERPER_API_KEY=your_serper_api_key
     ```  

## ▶️ Usage  

1. **Run the application:**  
   ```bash
   streamlit run EduChat.py
   ```  
2. **Upload a textbook PDF** to generate summaries and practice questions.  
3. **Enter an exam name** to generate relevant study topics and learning resources.  

## 📌 Contributing  

We welcome contributions! To contribute:  
- Fork this repository.  
- Create a new branch.  
- Commit your changes and open a pull request.  

## 📧 Contact  

For questions or feedback, reach out via **diwakersehgal16@gmail.com**.  

---  

Built with ❤️ using **OpenAI (via BoltIoT), ChromaDB, Streamlit, and Serper API**.  
```
