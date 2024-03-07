import hmac
import streamlit as st

def check_password(session_state, secret_password):
    if session_state.get("password_correct", False):
        return True

    def password_entered():
        if hmac.compare_digest(session_state["password"], secret_password):
            session_state["password_correct"] = True
            del session_state["password"]
        else:
            session_state["password_correct"] = False

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in session_state:
        st.error("😕 Password incorrect")
    return False
