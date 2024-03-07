from streamlit import session_state as _state

def parse_feedback(feedback):
    if "No feedback yet." in feedback:
        return "No feedback yet. Start the conversation to get feedback."
    else:
        return feedback

    import streamlit as st

def initialize_session_state():
    # Initialize session state variables if they haven't been set already
    keys_to_initialize = {
        "file_uploader_key": 0,
        "last_recorder": None,
        "openai_model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "file_uploaded": None,
        "position_text": None,
        "feedback": "No feedback yet. Start the conversation to get feedback.",
        "messages": [{"role": "assistant", "content": "Good morning. How are you today?"}],
        "password_correct": False,  # Assuming the application uses a password check
        # Add any other session state variables your application requires
    }

    for key, default_value in keys_to_initialize.items():
        if key not in _state:
            _state[key] = default_value

