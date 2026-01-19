📝 Condense.info
Condense.info is a minimalist, high-contrast AI summarization tool designed for accessibility and ease of use. It helps users quickly digest long documents, articles, or pasted text by converting them into clear, jargon-free bullet points and headers.

✨ Features
Drag-and-Drop: Upload PDF or TXT files directly to extract text automatically.

Simple UI: Designed with high contrast (Black on White) to ensure readability for all users, regardless of device settings.

Printable Results: One-click "Save as PDF" to keep a copy of your summary or print it for offline reading.

Privacy-First: Summaries are generated on the fly and not stored permanently on our servers.

Clear All: A single-click reset to start fresh with a new document.

🚀 How It Works
Condense utilizes the Google Gemini 1.5 Flash model to process text. The application logic is built with Streamlit, ensuring a responsive experience on both desktop and mobile devices.

🛠️ Installation & Local Setup
If you want to run this project locally on your machine:

Clone the repository:

Bash

git clone https://github.com/your-username/condense.info.git
cd condense.info
Create and activate a virtual environment:

Bash

python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate  # Windows
Install dependencies:

Bash

pip install -r requirements.txt
Set up your API Key: Create a .env file in the root directory and add your Google API Key:

Plaintext

GOOGLE_API_KEY=your_actual_key_here
Run the app:

Bash

streamlit run main.py
📦 Requirements
streamlit: The web interface framework.

google-genai: To connect with the Gemini AI model.

pypdf: For extracting text from uploaded PDF files.

fpdf2: For generating the downloadable summary PDFs.

python-dotenv: For managing local environment variables.

🎨 Accessibility Focus
This app forces a Light Theme (base="light") via .streamlit/config.toml to prevent "halation" effects and ensure maximum contrast for users with visual impairments or those viewing the site in bright conditions.