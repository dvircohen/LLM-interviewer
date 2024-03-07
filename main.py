import streamlit as st

from prompts import get_system_prompt_only_feedback
from utils import initialize_session_state
import ui_components as ui
from api_client import APIClient
from audio_processing import get_recordings
from auth import check_password
from utils import parse_feedback

def main():
    # Initialize session state
    initialize_session_state()

    # Set API client with secrets (adjust as necessary)
    api_client = APIClient(api_key=st.secrets["deepinfra_key"],
                           base_url="https://api.deepinfra.com/v1/openai")

    # UI: Display initial instructions, file uploader, and other UI elements
    ui.display_initial_ui()

    messages_container = st.container(border=False, height=600)
    record_icon_col, chat_col = st.columns([2, 11])

    # Process uploaded files and position text
    uploaded_file = st.session_state["file_uploaded"]
    position_text = st.session_state["position_text"]

    if uploaded_file is not None:
        # Process the uploaded file (PDF parsing etc.)
        cv_text = ui.process_uploaded_file(uploaded_file)
        # Update the conversation based on CV and position description
        system_prompt = ui.get_system_prompt(cv_text, position_text)
        st.session_state.messages.append({"role": "system", "content": system_prompt})

        # Handle audio recordings
        with record_icon_col:
            audio_prompt = get_recordings(st, st.session_state, st.secrets["deepinfra_key"])

        # Display the conversation and input for new messages
        ui.display_conversation(st.session_state.messages,messages_container)
        with chat_col:

            # Handle text input from the user
            user_input = ui.get_user_input()

            with messages_container:
                if user_input or audio_prompt:
                    if audio_prompt:
                        user_input = audio_prompt

                    st.session_state.messages.append({"role": "user", "content": user_input})
                    with st.chat_message("user"):
                        st.markdown(user_input)

                    with st.chat_message("assistant"):
                        with st.spinner("Thinking what to answer..."):
                            # Get response from OpenAI based on the conversation
                            conv_answer = api_client.get_text_from_openai(None, st.session_state)
                            feedback_answer = api_client.get_text_from_openai(get_system_prompt_only_feedback(), st.session_state)

                            st.write(conv_answer)

                    # Update the conversation and feedback in session state
                    st.session_state["feedback"] = feedback_answer
                    st.session_state.messages.append({"role": "assistant", "content": conv_answer})

    # Reset and restart conversation features
    ui.add_restart_feature()

    # UI: Display current feedback
    ui.display_feedback(parse_feedback(st.session_state["feedback"]))

if __name__ == "__main__":
    main()

