import streamlit as st
from google import genai
import os
from fpdf import FPDF
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash')

# --- Simple Usage Limiter ---
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0

MAX_FREE_SUMMARIES = 5


def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S')


# --- UI ---
st.title("Condense AI")

if st.session_state.usage_count > MAX_FREE_SUMMARIES:
    st.error(f"You've reached your limit of {MAX_FREE_SUMMARIES} summaries for this session.")
else:
    remaining = MAX_FREE_SUMMARIES - st.session_state.usage_count
    st.caption(f"Free summaries remaining: {remaining}")

    user_input = st.text_area("Paste document text:", height=300)

    if st.button("Summarize"):
        if user_input:
            with st.spinner("Thinking..."):
                try:
                    response = model.generate_content(
                        f"Provide a comprehensive summary with headers for the following text:\n\n{user_input}"
                    )

                    st.session_state.usage_count += 1
                    summary_text = response.text

                    st.subheader("Summary")
                    st.markdown(summary_text)

                    # PDF Download
                    pdf_data = create_pdf(summary_text)
                    st.download_button(
                        label="Download PDF",
                        data=pdf_data,
                        file_name="summary.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"An error occurred: {e}")