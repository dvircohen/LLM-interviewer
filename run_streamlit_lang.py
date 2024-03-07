import streamlit as st
from openai import OpenAI
import pypdfium2 as pdfium
import json
from prompts import get_system_prompt, get_system_prompt_with_site_text
import hmac

from text import *

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

if "lang" not in st.session_state:
    st.session_state["lang"] = 'en'

option = st.sidebar.radio(
    "Change Language",('English', 'עברית'),horizontal=True)
if option == 'English':
    st.session_state["lang"] = 'en'
elif option == 'עברית':
    st.session_state["lang"] = 'he'

if not check_password():
    st.stop()  # Do not continue if check_password is not True.


if "openai_model" not in st.session_state:
    # st.session_state["openai_model"] = "gpt-4-0125-preview"
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "feedback" not in st.session_state:
    st.session_state["feedback"] = no_feedback[st.session_state["lang"]]

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": first_message[st.session_state["lang"]]}]

uploaded_file = st.sidebar.file_uploader("Choose a file")

position_text = st.sidebar.text_input(position_description[st.session_state["lang"]])
if uploaded_file is not None:
    for message in st.session_state.messages:
        if message['role'] == "system":
            continue

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    pdf = pdfium.PdfDocument(uploaded_file)
    page = pdf[0]  # load a page
    cv_text = page.get_textpage().get_text_range()

    if position_text:
        st.session_state.messages.append({"role": "system", "content": get_system_prompt_with_site_text(cv_text,position_text)})
    else:
        st.session_state.messages.append({"role": "system", "content": get_system_prompt(cv_text)})


    if prompt := st.chat_input("Hi, Nice to meet you"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(loading_text[st.session_state["lang"]]):

                answer = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=False,
                    response_format={"type": "json_object"},
                )

            answer_json = json.loads(answer.choices[0].message.content)

            response = st.write(answer_json['next message'])
        if answer_json['feedback']:
            st.session_state["feedback"] = answer_json['feedback']
        st.session_state.messages.append({"role": "assistant", "content": answer_json['next message']})

with st.sidebar:
    st.header("Current feedback:")
    st.markdown(st.session_state["feedback"])
