import requests
import json
from openai import OpenAI
import streamlit as st

class APIClient:
    def __init__(self, api_key, base_url):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    # def get_text_from_recording(self, recording, secret_key):
    #     headers = {'Authorization': f'bearer {secret_key}'}
    #     files = {'audio': recording}
    #     url = 'https://api.deepinfra.com/v1/inference/openai/whisper-base.en'
    #     response = requests.post(url, headers=headers, files=files).text
    #     response = json.loads(response)['text']
    #     return response


    def get_text_from_openai(self, system_prompt, session_state):
        messages = [{"role": m["role"], "content": m["content"]} for m in session_state.messages]
        if system_prompt:
            for message in messages:
                if message["role"] == "system":
                    message['content'] = system_prompt
            messages.append({"role": "user", "content": "Provide feedback on the current conversation. Write a single paragraph and nothing else."})
        answer = self.client.chat.completions.create(
            model=session_state["openai_model"],
            messages=messages,
            stream=False,
            response_format={"type": "json_object"},
        )
        return answer.choices[0].message.content
