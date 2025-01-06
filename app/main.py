import streamlit as st
import pandas as pd

def main():
    st.title("File Upload and Display")

    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xls', 'xlsx', 'json'])


    if uploaded_file is not None:
        try:
            # Read the CSV file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.json'):
                df = pd.read_json(uploaded_file)
            else:
                # For text files, read as plain text and create single column dataframe
                content = uploaded_file.read().decode('utf-8')
                df = pd.DataFrame({'Content': [content]})
            
            # Display the dataframe
            st.write("### Data Preview:")
            st.dataframe(df)
            
            
        except Exception as e:
            st.error(f"Error reading file: {e}")

if __name__ == "__main__":
    main()
