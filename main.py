import streamlit as st
from google import genai
import os
from fpdf import FPDF
from io import BytesIO


# --- 1. API & MODEL CONFIGURATION ---
def configure_api():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GOOGLE_API_KEY")
        except ImportError:
            api_key = None

    if not api_key:
        st.error("API Key not found.")
        st.stop()

    return genai.Client(api_key=api_key)

client = configure_api()

# --- 2. SESSION STATE INITIALIZATION ---
if 'text_input' not in st.session_state:
    st.session_state.text_input = ""
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0


# --- 3. HELPER FUNCTIONS ---
def clear_text():
    st.session_state["main_text_area"] = ""
    st.session_state.uploader_key += 1

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    clean_text = text.encode('latin-1', 'replace').decode('latin-1')

    pdf.multi_cell(0, 10, txt=clean_text)

    pdf_output = pdf.output(dest='S')

    if isinstance(pdf_output, str):
        return BytesIO(pdf_output.encode('latin-1'))
    return BytesIO(pdf_output)


# --- 4. UI LAYOUT ---
st.set_page_config(page_title="Condense", page_icon="📝", layout="centered")

st.title("Condense.info")
st.markdown("""
    <style>
    /* Force high contrast for the whole app */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: white !important;
        color: black !important;
    }
    /* Force the text area specifically */
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #d1d5db !important;
    }
    /* Ensure all markdown (summary text) is black */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {
        color: black !important;
    }
    /* Ensure labels for buttons and uploaders are black */
    label, .stFileUploader label {
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. FILE UPLOADER LOGIC ---
uploaded_file = st.file_uploader(
    "Upload a document (PDF or Text)",
    type=['pdf', 'txt'],
    key=f"file_uploader_{st.session_state.uploader_key}"
)

if uploaded_file:

    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_uploaded_file") != file_id:
        with st.spinner("Extracting text from file..."):
            try:
                if uploaded_file.type == "application/pdf":
                    import pypdf

                    reader = pypdf.PdfReader(uploaded_file)
                    pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                    extracted_content = "\n\n".join(pages)
                else:
                    extracted_content = uploaded_file.read().decode("utf-8")


                st.session_state["main_text_area"] = extracted_content

                st.session_state["last_uploaded_file"] = file_id

                st.rerun()

            except Exception as e:
                st.error(f"Could not read this file: {e}")

# --- 6. TEXT INPUT AREA ---
user_input = st.text_area(
    "Content to summarize:",
    height=300,
    placeholder="Paste your text here or drop a file above...",
    key="main_text_area"
)

# --- 7. SUMMARIZE & CLEAR BUTTONS ---
col1, col2 = st.columns([1, 1])

with col1:
    summarize_btn = st.button("Summarize Now", use_container_width=True, type="primary")

with col2:
    st.button("Clear All", on_click=clear_text, use_container_width=True)

# --- 8. PROCESSING LOGIC ---
if summarize_btn:
    text_to_process = user_input.strip()

    if not text_to_process:
        st.warning("Please upload a file or paste some text first.")
    else:
        with st.spinner("Condensing your information..."):
            try:

                prompt = (
                    "Summarize the following text clearly for a general audience. "
                    "Use bold headers and bullet points. Avoid complex jargon.\n\n"
                    f"TEXT:\n{text_to_process}"
                )


                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )

                if not response.text:
                    st.error("The AI returned an empty response. Try slightly different text.")
                else:
                    summary = response.text


                    st.divider()
                    st.subheader("Your Summary")
                    st.markdown(summary)


                    try:

                        pdf_buffer = create_pdf(summary)

                        st.download_button(
                            label="📄 Save as PDF (to Print or Read)",
                            data=pdf_buffer.getvalue(),
                            file_name="summary.pdf",
                            mime="application/pdf",
                        )
                    except Exception as pdf_error:
                        st.warning(f"Summary created, but PDF failed: {pdf_error}")

            except Exception as e:

                st.error(f"Something went wrong: {str(e)}")