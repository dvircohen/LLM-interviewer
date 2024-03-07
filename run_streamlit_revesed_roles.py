import requests
import streamlit as st
from openai import OpenAI
import pypdfium2 as pdfium
import json
from prompts import get_system_prompt, get_system_prompt_with_site_text, get_system_prompt_only_feedback, \
    get_system_prompt_only_conversation, get_system_prompt_candidate_only_conversation, \
    get_system_prompt_candidate_only_feedback, get_system_prompt_candidate_with_site_text
import hmac
from audio_recorder_streamlit import audio_recorder

client = OpenAI(api_key= st.secrets["deepinfra_key"],
    base_url="https://api.deepinfra.com/v1/openai",
)

def parse_feedback(feedback):
    if "No feedback yet." in feedback:
        return "No feedback yet. Start the conversation to get feedback."
    else:
        return feedback

def get_text_from_recording(recording):
    headers = {'Authorization': f'bearer {st.secrets["deepinfra_key"]}'}
    files = {'audio': recording}
    url = 'https://api.deepinfra.com/v1/inference/openai/whisper-base.en'
    response = requests.post(url, headers=headers, files=files).text
    response = json.loads(response)['text']
    # Printing the response
    return response

def get_recordings():
    with st.container():
        if audio_bytes := audio_recorder(text="Record",pause_threshold=1.5 ,icon_size="2x"):
            audio_prompt = get_text_from_recording(audio_bytes)
        else:
            audio_prompt = None
        return audio_prompt

def get_text_from_openai(system_prompt=None):
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]
    if system_prompt:
        for i in range(0, len(messages)):
            if messages[i]["role"] == "system":
                messages[i]['content'] = system_prompt
            messages.append({"role": "user", "content": "Provide feedback on the current conversation. Write a single paragraph and nothing else."})
    answer = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=messages,
        stream=False,
        response_format={"type": "json_object"},

    )
    return answer.choices[0].message.content

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

if "file_uploader_key" not in st.session_state:
    st.session_state["file_uploader_key"] = 0

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "mistralai/Mixtral-8x7B-Instruct-v0.1"

if "file_uploaded" not in st.session_state:
    st.session_state["file_uploaded"] = None

if "position_text" not in st.session_state:
    st.session_state["position_text"] = None

if "feedback" not in st.session_state:
    st.session_state["feedback"] = "No feedback yet. Start the conversation to get feedback."

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Good morning. Im ready to start the interview"}]


text_title = st.empty()
text_intro = st.empty()
info_text = st.empty()

if st.session_state["file_uploaded"] is None:
    text_title.title("Welcome to the LLM interviewer")
    text_intro.subheader("""To start, upload your CV. 
You can also paste a job description text to make the interviewer be aware of the specific position.""")
    info_text.write("We know your CV and conversation are private, and we are not saving anything on our servers.")

st.session_state["file_uploaded"] = st.sidebar.file_uploader("Choose a file",['pdf'],key=st.session_state["file_uploader_key"])

st.session_state["position_text"] = st.sidebar.text_input('Position description (optional). Press enter after pasting the text.')
if st.session_state["position_text"] != "":
    st.sidebar.markdown("Position description uploaded")

if st.sidebar.button('Restart Conversation'):
    st.session_state["file_uploader_key"] += 1
    st.session_state["position_text"] = ""
    st.session_state["feedback"] = "No feedback yet. Start the conversation to get feedback."
    st.session_state.messages = [{"role": "assistant", "content": "Good morning. How are you today?"}]
    st.session_state["file_uploaded"] = None
    st.experimental_rerun()

messages_container = st.container(border=False,height=800)


col1, col2 = st.columns([2, 11])

if st.session_state["file_uploaded"] is not None:
    text_title.empty()
    text_intro.empty()
    info_text.empty()

    for message in st.session_state.messages:
        if message['role'] == "system":
            continue
        with messages_container:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


    pdf = pdfium.PdfDocument(st.session_state["file_uploaded"])
    page = pdf[0]  # load a page
    cv_text = page.get_textpage().get_text_range()

    if st.session_state["position_text"]:
        st.session_state.messages.append({"role": "system", "content": get_system_prompt_candidate_with_site_text(cv_text,st.session_state["position_text"])})
    else:
        st.session_state.messages.append({"role": "system", "content": get_system_prompt_candidate_only_conversation(cv_text)})


    with col1:
        audio_prompt = get_recordings()

    with col2:
        prompt = st.chat_input("Write your message here")

        with messages_container:
            if prompt or audio_prompt:
                if audio_prompt:
                    prompt = audio_prompt
                    audio_prompt = None
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking what to answer..."):
                        conv_answer = get_text_from_openai()
                        feedback_answer = get_text_from_openai(get_system_prompt_candidate_only_feedback())
                        response = st.write(conv_answer)
                st.session_state["feedback"] = feedback_answer
                st.session_state.messages.append({"role": "assistant", "content": conv_answer})

with st.sidebar:
    st.header("Current feedback:")
    st.markdown(parse_feedback(st.session_state["feedback"]))
