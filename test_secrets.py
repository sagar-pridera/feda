import streamlit as st
import json

try:
    # Try to access the secrets
    firebase_creds = json.loads(st.secrets["firebase"]["service_account_key"])
    st.success("Successfully loaded Firebase credentials!")
    # Print the keys (not the values) to verify structure
    st.write("Available keys:", list(firebase_creds.keys()))
except Exception as e:
    st.error(f"Error loading credentials: {str(e)}") 