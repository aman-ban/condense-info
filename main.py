import streamlit as st
import google.generativeai as genai
import os
from fpdf import FPDF

# --- API Configuration (Cloud + Local Friendly) ---
# This looks for the key in Streamlit Secrets first, then falls back to your local environment
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
    except ImportError:
        api_key = None

if not api_key:
    st.error("API Key not found. Please add it to Streamlit Secrets or a .env file.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- UI Configuration ---
st.set_page_config(page_title="Condense", page_icon="📝", layout="centered")

# Professional, minimalist CSS
st.markdown("""
    <style>
    /* Main background and font */
    .stApp { background-color: #ffffff; font-family: 'Inter', sans-serif; }

    /* Input area styling */
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        font-size: 16px;
        line-height: 1.6;
    }

    /* Button styling: Professional Blue */
    .stButton button {
        background-color: #1a73e8;
        color: white;
        border-radius: 6px;
        padding: 0.6rem 2rem;
        font-size: 18px;
        font-weight: 500;
        border: none;
        transition: background-color 0.2s;
    }
    .stButton button:hover { background-color: #1557b0; color: white; }

    /* Hide Streamlit branding for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    # Essential for older users: clear, readable text
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S')


# --- App Layout ---
st.title("Condense")
st.markdown("##### Paste any long text below to get a clear, simple summary.")

# Single, large input field
user_input = st.text_area(
    label="Text to summarize",
    placeholder="Right-click here and select 'Paste'...",
    height=350,
    label_visibility="collapsed"
)

# Professional "Summarize" button
if st.button("Summarize Now"):
    if not user_input.strip():
        st.warning("Please paste some text first.")
    else:
        with st.spinner("Processing... please wait a moment."):
            try:
                # Prompt optimized for clarity and older readers
                prompt = (
                    "Summarize the following text using simple, clear language. "
                    "Use bullet points and bold headers. Avoid jargon."
                    f"\n\nTEXT:\n{user_input}"
                )

                response = model.generate_content(prompt)
                summary = response.text

                # Display Results
                st.divider()
                st.subheader("Your Summary")
                st.markdown(summary)

                # Download Option
                pdf_bytes = create_pdf(summary)
                st.download_button(
                    label="📄 Save as PDF (to Print or Read)",
                    data=pdf_bytes,
                    file_name="summary.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error("Something went wrong. Please try again in a moment.")