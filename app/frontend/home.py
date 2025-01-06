import streamlit as st
import pandas as pd

def main():
    st.title("File Upload and Display")

    uploaded_file = st.file_uploader("Choose a file", type=['csv'])

    if uploaded_file is not None:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            # Display the dataframe
            st.write("### Data Preview:")
            st.dataframe(df)
            
            # Print to console
            print("File contents:")
            print(df)
            
        except Exception as e:
            st.error(f"Error reading file: {e}")

if __name__ == "__main__":
    main()
