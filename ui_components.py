import streamlit as st
from streamlit import session_state as _state
import pypdfium2 as pdfium

from prompts import get_system_prompt_with_site_text, get_system_prompt_only_conversation


def display_initial_ui():
    # Display file uploader and position description input
    _state["file_uploaded"] = st.sidebar.file_uploader("Choose a file", ['pdf'], key=_state["file_uploader_key"])
    _state["position_text"] = st.sidebar.text_input('Position description (optional). Press enter after pasting the text.')
    if _state["position_text"] != "":
        st.sidebar.markdown("Position description uploaded")

    if _state["file_uploaded"] is None:
        """Displays initial UI components like the title and instructions."""
        st.title("Welcome to the LLM Interviewer")
        st.subheader("""To start, upload your CV. You can also paste a job description text to make the interviewer aware of the specific position.""")
        st.write("We know your CV and conversation are private, and we are not saving anything on our servers.")


def process_uploaded_file(uploaded_file):
    pdf = pdfium.PdfDocument(st.session_state["file_uploaded"])
    page = pdf[0]  # load a page
    cv_text = page.get_textpage().get_text_range()
    return cv_text

def get_system_prompt(cv_text, position_text):
    if position_text:
        prompt = get_system_prompt_with_site_text(cv_text, position_text)
    else:
        prompt = get_system_prompt_only_conversation(cv_text)
    return prompt

def display_conversation(messages,messages_container):
    """Displays the conversation history."""
    for message in messages:
        if message['role'] == "system":
            continue
        with messages_container:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

def get_user_input():
    """Gets input from the user."""
    prompt = st.chat_input("Write your message here")
    if prompt:
        _state["user_input"] = ""  # Reset input field
        return prompt
    return None

def display_feedback(feedback):
    """Displays current feedback."""
    with st.sidebar:
        st.header("Current feedback:")
        st.markdown(feedback)

def add_restart_feature():
    """Adds a button to restart the conversation."""
    if st.sidebar.button('Restart Conversation'):
        _state["file_uploader_key"] += 1
        _state["position_text"] = ""
        _state["feedback"] = "No feedback yet. Start the conversation to get feedback."
        _state.messages = [{"role": "assistant", "content": "Good morning. How are you today?"}]
        _state["file_uploaded"] = None
        st.experimental_rerun()
