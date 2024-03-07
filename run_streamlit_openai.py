import streamlit as st
from openai import OpenAI
import pypdfium2 as pdfium
import json
from prompts import get_system_prompt, get_system_prompt_with_site_text
import hmac

# client = OpenAI(api_key=st.secrets["open_key"])
client = OpenAI(api_key=st.secrets["open_key"])


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
    st.session_state["openai_model"] = "gpt-4-0125-preview"
    # st.session_state["openai_model"] = "gpt-3.5-turbo"

if "file_uploaded" not in st.session_state:
    st.session_state["file_uploaded"] = None

if "position_text" not in st.session_state:
    st.session_state["position_text"] = None

if "feedback" not in st.session_state:
    st.session_state["feedback"] = "No feedback yet. Start the conversation to get feedback."

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Good morning. How are you today?"}]




st.session_state["file_uploaded"] = st.sidebar.file_uploader("Choose a file",['pdf'],key=st.session_state["file_uploader_key"])

st.session_state["position_text"] = st.sidebar.text_input('Position description (optional)')

if st.sidebar.button('Restart Conversation'):
    st.session_state["file_uploader_key"] += 1
    st.session_state["feedback"] = "No feedback yet. Start the conversation to get feedback."
    st.session_state.messages = [{"role": "assistant", "content": "Good morning. How are you today?"}]
    st.session_state["file_uploaded"] = None
    st.experimental_rerun()

if st.session_state["file_uploaded"] is not None:
    for message in st.session_state.messages:
        if message['role'] == "system":
            continue

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    pdf = pdfium.PdfDocument(st.session_state["file_uploaded"])
    page = pdf[0]  # load a page
    cv_text = page.get_textpage().get_text_range()

    if st.session_state["position_text"]:
        st.session_state.messages.append({"role": "system", "content": get_system_prompt_with_site_text(cv_text,st.session_state["position_text"])})
    else:
        st.session_state.messages.append({"role": "system", "content": get_system_prompt(cv_text)})


    if prompt := st.chat_input("Hi, Nice to meet you"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking what to answer..."):

                answer = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=False,
                    response_format={"type": "json_object"},

                )
            response = st.write(answer.choices[0].message.content)

            answer_json = json.loads(answer.choices[0].message.content)

            response = st.write(answer_json['next message'])
        if answer_json['feedback']:
            st.session_state["feedback"] = answer_json['feedback']
        st.session_state.messages.append({"role": "assistant", "content": answer_json['next message']})

with st.sidebar:
    st.header("Current feedback:")
    st.markdown(st.session_state["feedback"])
