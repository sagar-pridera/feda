import streamlit as st
import pandas as pd
from backend.process_feedback_service import ProcessFeedbackService
from backend.llm_service import LLMService
from backend.database_service import DatabaseService
import asyncio
import logging

# Add at the start of your main.py
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    st.title("Feda AI")

    # Add batch size selector
    batch_size = st.sidebar.slider(
        "Batch Size",
        min_value=10,
        max_value=100,
        value=50,
        step=10,
        help="Number of feedback entries to process at once"
    )

    # Initialize services with selected batch size
    @st.cache_resource
    def init_services(batch_size):
        llm_service = LLMService()
        db_service = DatabaseService()
        asyncio.run(db_service.initialize())
        return ProcessFeedbackService(llm_service, db_service, batch_size=batch_size)

    process_feedback_service = init_services(batch_size)

    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xls', 'xlsx', 'json'])

    if uploaded_file is not None:
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                data = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.json'):
                data = pd.read_json(uploaded_file)
            else:
                content = uploaded_file.read().decode('utf-8')
                data = pd.DataFrame({'Content': [content]})

            # Display the dataframe
            st.write("### Data Preview:")
            st.dataframe(data, height=300)

            # Let user select the feedback and email columns
            feedback_column = st.selectbox(
                "Select the column containing feedback",
                options=data.columns.tolist()
            )
            
            email_column = st.selectbox(
                "Select the column containing email (optional)",
                options=['None'] + data.columns.tolist()
            )

            # Process feedback for each row
            if st.button("Process Feedback"):
                st.write("### Processing Results:")
                
                progress_bar = st.progress(0)
                
                # Prepare batch data
                feedback_data = []
                for index, row in data.iterrows():
                    feedback_data.append({
                        'feedback': row[feedback_column],
                        'email': row[email_column] if email_column != 'None' else ""
                    })
                
                # Process in batches
                results = []
                total_batches = (len(feedback_data) + batch_size - 1) // batch_size
                
                for i in range(0, len(feedback_data), batch_size):
                    batch = feedback_data[i:i + batch_size]
                    with st.spinner(f'Processing batch {(i//batch_size)+1}/{total_batches}...'):
                        batch_results = asyncio.run(
                            process_feedback_service.process_feedback_batch(batch)
                        )
                        results.extend(batch_results)
                    
                    # Update progress
                    progress_bar.progress((i + len(batch)) / len(feedback_data))
                
                # Convert results to DataFrame for display
                results_df = pd.DataFrame(results)
                st.write("### Processed Feedback Results:")
                st.dataframe(results_df)
                
                # Show common issues analysis
                if len(results) > 1:
                    with st.spinner('Analyzing common issues...'):
                        common_issues = asyncio.run(
                            process_feedback_service.analyze_common_issues(
                                [r['original_feedback'] for r in results]
                            )
                        )
                        
                        st.write("### Common Issues Analysis:")
                        issues_df = pd.DataFrame(
                            list(common_issues.items()), 
                            columns=['Category', 'Count']
                        ).sort_values('Count', ascending=False)
                        st.bar_chart(issues_df.set_index('Category'))

        except Exception as e:
            st.error(f"Error processing file: {e}")
            logging.error(f"Error details: ", exc_info=True)

if __name__ == "__main__":
    main()
