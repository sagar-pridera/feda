import streamlit as st
import pandas as pd
from backend.process_feedback_service import FeedbackProcessor
from backend.llm_service import ModelName
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    st.title("Feda AI")
    
    # Initialize processor
    processor = FeedbackProcessor(
        model=ModelName.MIXTRAL,
        batch_size=50
    )

    # Add batch size selector
    batch_size = st.sidebar.slider(
        "Batch Size",
        min_value=10,
        max_value=100,
        value=50,
        step=10,
        help="Number of feedback entries to process at once"
    )

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
                            processor.process_feedback_batch(batch)
                        )
                        results.extend(batch_results)
                    
                    # Update progress
                    progress_bar.progress((i + len(batch)) / len(feedback_data))
                
                # Convert results to DataFrame for display
                if len(results) > 0:
                    results_df = pd.DataFrame(results)
                    
                    # Format the categories column to display as comma-separated string
                    results_df['categories'] = results_df['categories'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
                    
                    # Reorder columns if needed
                    columns_order = ['email', 'original_feedback', 'sentiment', 'categories', 'summary', 'created_at']
                    results_df = results_df[columns_order]
                    
                    st.write("### Processed Feedback Results:")
                    st.dataframe(
                        results_df,
                        column_config={
                            "email": st.column_config.TextColumn("Email"),
                            "original_feedback": st.column_config.TextColumn("Original Feedback"),
                            "sentiment": st.column_config.TextColumn("Sentiment"),
                            "categories": st.column_config.TextColumn("Categories"),
                            "summary": st.column_config.TextColumn("Summary"),
                            "created_at": st.column_config.DatetimeColumn("Created At")
                        },
                        hide_index=False
                    )
                
                # Show common issues analysis
                if len(results) > 1:
                    with st.spinner('Analyzing common issues...'):
                        common_issues = asyncio.run(
                            processor.analyze_common_issues(
                                [r['original_feedback'] for r in results]
                            )
                        )
                        
                        # First show the common issues chart
                        st.write("### Common Issues Analysis:")
                        issues_df = pd.DataFrame(
                            list(common_issues.items()), 
                            columns=['Category', 'Count']
                        ).sort_values('Count', ascending=False)
                        st.bar_chart(issues_df.set_index('Category'))

                        # Then show the detailed category analysis
                        st.write("### Detailed Category Breakdown:")
                        
                        # Create a DataFrame for category details
                        detailed_analysis = []
                        for category, count in common_issues.items():
                            # Find all feedback that matches this category
                            matching_feedback = [
                                {
                                    'feedback': r['original_feedback'],
                                    'sentiment': r['sentiment'],
                                    'summary': r['summary']
                                }
                                for r in results 
                                if category in r['categories']
                            ]
                            
                            # Add to detailed analysis
                            detailed_analysis.append({
                                'Category': category,
                                'Count': count,
                                'Examples': matching_feedback
                            })
                        
                        # Create and display the detailed table
                        for analysis in detailed_analysis:
                            with st.expander(f"📊 {analysis['Category']} ({analysis['Count']} items)"):
                                examples_df = pd.DataFrame(analysis['Examples'])
                                st.dataframe(
                                    examples_df,
                                    column_config={
                                        "feedback": st.column_config.TextColumn(
                                            "Feedback",
                                            width="large"
                                        ),
                                        "sentiment": st.column_config.TextColumn(
                                            "Sentiment",
                                            width="small"
                                        ),
                                        "summary": st.column_config.TextColumn(
                                            "Summary",
                                            width="medium"
                                        )
                                    },
                                    hide_index=True
                                )

        except Exception as e:
            st.error(f"Error processing file: {e}")
            logging.error(f"Error details: ", exc_info=True)

if __name__ == "__main__":
    main()
