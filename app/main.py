import streamlit as st
import pandas as pd

def main():
    st.title("Feda AI")

    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xls', 'xlsx', 'json'])


    if uploaded_file is not None:
        try:
            # Read the CSV file
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                data = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.json'):
                data = pd.read_json(uploaded_file)
            else:
                # For text files, read as plain text and create single column dataframe
                content = uploaded_file.read().decode('utf-8')
                data = pd.DataFrame({'Content': [content]})

            # Display the dataframe
            st.write("### Data Preview:")
            st.dataframe(data, height=300)


        except Exception as e:
            st.error(f"Error reading file: {e}")

if __name__ == "__main__":
    main()
