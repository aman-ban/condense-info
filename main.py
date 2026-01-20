import streamlit as st
from google import genai
from fpdf import FPDF
from io import BytesIO
from gtts import gTTS
import pypdf


# --- 1. API & MODEL CONFIGURATION ---
def configure_api():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key not found in Streamlit Secrets.")
        st.stop()
    return genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

client = configure_api()

# --- 2. SESSION STATE INITIALIZATION ---
if 'text_input' not in st.session_state:
    st.session_state.text_input = ""
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0
if "last_uploaded_file" not in st.session_state:
    st.session_state["last_uploaded_file"] = None


# --- 3. HELPER FUNCTIONS ---
def clear_text():
    st.session_state["main_text_area"] = ""
    st.session_state["last_uploaded_file"] = None
    st.session_state.uploader_key += 1


def create_pdf(text):
    pdf = FPDF()
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    clean_text = (
        text.replace("**", "")
        .replace("#", "")
        .replace("•", "-")
        .replace("—", "-")
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )

    clean_text = "\n".join(line.strip() for line in clean_text.splitlines())
    safe_text = clean_text.encode("latin-1", "replace").decode("latin-1")
    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    for line in safe_text.split("\n"):
        pdf.set_x(pdf.l_margin)
        if line.strip() == "":
            pdf.ln(8)
        else:
            pdf.multi_cell(page_width, 8, line)

    output = pdf.output(dest="S")
    return bytes(output) if isinstance(output, bytearray) else output.encode("latin-1")


def build_bias_prompt(text):
    try:
        base_instructions = st.secrets["BIAS_PROMPT"]
    except:
        return f"Analyze this text for bias: {text}"

    return f"{base_instructions}\n\n{text}"


# --- 4. UI LAYOUT ---
st.set_page_config(page_title="Condense", page_icon="📝", layout="centered")

st.title("Condense.info")
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: white !important; color: black !important; }
    .stTextArea textarea { background-color: #ffffff !important; color: #000000 !important; border: 1px solid #d1d5db !important; }
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 { color: black !important; }
    label, .stFileUploader label { color: black !important; }
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

languages = {
    "English": ("en", "English"),
    "Spanish": ("es", "Spanish"),
    "French": ("fr", "French"),
    "German": ("de", "German"),
    "Italian": ("it", "Italian"),
    "Portuguese": ("pt", "Portuguese"),
}

selected_lang_name = st.selectbox("Output Language:", options=list(languages.keys()))
lang_code, lang_name = languages[selected_lang_name]

# --- 7. SUMMARIZE & CLEAR BUTTONS ---
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    summarize_btn = st.button("Summarize Now", use_container_width=True, type="primary")

with col2:
    detect_bias_btn = st.button("Detect Bias", use_container_width=True)

with col3:
    st.button("Clear All", on_click=clear_text, use_container_width=True)

# --- 8. PROCESSING LOGIC ---
if summarize_btn:
    text_to_process = user_input.strip()

    if not text_to_process:
        st.warning("Please upload a file or paste some text first.")
    else:
        with st.spinner(f"Generating Brief..."):
            try:
                if "SUMMARY_PROMPT" not in st.secrets:
                    st.error("SUMMARY_PROMPT missing from secrets.toml")
                    st.stop()

                base_prompt = st.secrets["SUMMARY_PROMPT"]

                final_prompt = (
                    f"{base_prompt}\n"
                    f"IMPORTANT: Provide the entire response in {lang_name}.\n\n"
                    f"TEXT:\n{text_to_process}"
                )

                try:
                    response = client.models.generate_content(
                        model='gemini-flash-latest',
                        contents=final_prompt
                    )
                except Exception as quota_error:
                    if "quota" in str(quota_error).lower() or "resource" in str(quota_error).lower():
                        response = client.models.generate_content(
                            model='gemini-2.5-flash-lite',
                            contents=final_prompt
                        )
                    else:
                        raise quota_error

                if not response.text:
                    st.error("The AI returned an empty response.")
                else:
                    summary = response.text
                    st.divider()
                    st.subheader(f"Your {selected_lang_name} Summary")
                    st.markdown(summary)

                    # Audio Logic
                    try:
                        with st.status(f"Generating audio...", expanded=False):
                            speech_text = summary.replace("*", "").replace("#", "").replace("\n", " ")[:4500]
                            tts_lang = "pt-br" if lang_code == "pt" else lang_code
                            tts = gTTS(text=speech_text, lang=tts_lang, slow=False)
                            audio_fp = BytesIO()
                            tts.write_to_fp(audio_fp)
                            audio_fp.seek(0)
                            st.audio(audio_fp.read(), format="audio/mpeg")
                    except Exception as tts_error:
                        st.info(f"Audio error: {tts_error}")

                    # PDF Logic
                    try:
                        pdf_data = create_pdf(summary)
                        st.download_button(
                            label=f"📄 Save {selected_lang_name} PDF",
                            data=pdf_data,
                            file_name=f"summary_{lang_code}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as pdf_error:
                        st.warning(f"Summary created, but PDF failed: {pdf_error}")

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

if detect_bias_btn:
    text_to_process = user_input.strip()
    if not text_to_process:
        st.warning("Please upload or paste an article first.")
    else:
        with st.spinner("Analyzing article for bias..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=build_bias_prompt(text_to_process)
                )
                st.divider()
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Bias detection failed: {e}")