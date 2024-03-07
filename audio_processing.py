import json

import requests

from api_client import APIClient
from audio_recorder_streamlit import audio_recorder
from streamlit import session_state as _state
import streamlit as st
def get_recordings(st, session_state, secret_key):
    with st.container():
        audio_bytes = audio_recorder(text="Record", pause_threshold=1.5, icon_size="2x", key=str(4))
        if audio_bytes and audio_bytes != session_state["last_recorder"]:
            session_state["last_recorder"] = audio_bytes
            with st.spinner("Please wait."):
                audio_prompt = get_text_from_recording(audio_bytes)
        else:
            audio_prompt = None
        return audio_prompt

def get_text_from_recording(recording):
    headers = {'Authorization': f'bearer {st.secrets["deepinfra_key"]}'}
    files = {'audio': recording}
    url = 'https://api.deepinfra.com/v1/inference/openai/whisper-base.en'
    response = requests.post(url, headers=headers, files=files)
    response = json.loads(response.text)['text']
    # Printing the response
    return response
