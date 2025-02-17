import streamlit as st
import pandas as pd
from backend.process_feedback_service import FeedbackProcessor
from backend.llm_service import ModelName
import asyncio
import logging
from backend.models.categories import Categories
from backend.models.feedback_models import ProcessedFeedback, FeedbackItem

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
        batch_size=100
    )

    # Add batch size selector
    batch_size = st.sidebar.slider(
        "Batch Size",
        min_value=50,
        max_value=150,
        value=100,
        step=3,
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
            st.write("### 📊 Data Preview:")
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
                st.write("### ⚙️ Processing Results:")
                
                progress_bar = st.progress(0)
                
                try:
                    # Prepare batch data
                    feedback_data = []
                    for index, row in data.iterrows():
                        feedback_data.append({
                            'feedback': row[feedback_column],
                            'email': row[email_column] if email_column != 'None' else ""
                        })
                    
                    # Show total items to be processed
                    total_items = len(feedback_data)
                    
                    
                    # Process in batches
                    results = []
                    total_batches = (len(feedback_data) + batch_size - 1) // batch_size
                    
                    for i in range(0, len(feedback_data), batch_size):
                        batch = feedback_data[i:i + batch_size]
                        with st.spinner(f'Processing batch {(i//batch_size)+1}/{total_batches}...'):
                            try:
                                # Add logging for batch processing
                                st.write(f"Processing batch of {len(batch)} items...")
                                
                                batch_results = asyncio.run(
                                    processor.process_feedback_batch(batch)
                                )
                                
                                # Log any failed items in the batch
                                for j, result in enumerate(batch_results):
                                    if result.get('category') == 'Error':
                                        try:
                                            feedback_text = batch[j]['feedback'][:100] if j < len(batch) else "Unknown feedback"
                                            st.warning(f"Failed to process item {i+j+1}: {feedback_text}...")
                                            st.write(f"Error: {result['summary']}")
                                        except (IndexError, KeyError) as e:
                                            st.warning(f"Error accessing feedback item {i+j+1}")
                                
                                results.extend(batch_results)
                            except Exception as e:
                                st.error(f"Batch processing error: {str(e)}")
                                logging.error(f"Error processing batch: {str(e)}", exc_info=True)
                                # Add error results for the batch
                                results.extend([
                                    ProcessedFeedback.create_error_response(
                                        FeedbackItem(text=item['feedback'], email=item.get('email', '')),
                                        f"Batch processing error: {str(e)}"
                                    ).to_dict()
                                    for item in batch
                                ])
                            
                            # Update progress
                            progress_bar.progress((i + len(batch)) / len(feedback_data))
                    
                    # Show summary of processing
                    successful_results = [r for r in results if r['category'] != 'Error']
                    error_results = [r for r in results if r['category'] == 'Error']
                    
                    st.write(f"""
                    ### Processing Summary:
                    - Total items: {total_items}
                    - Successfully processed: {len(successful_results)}
                    - Failed to process: {len(error_results)}
                    """)
                    
                    if error_results:
                        with st.expander("Show Processing Errors"):
                            for error in error_results:
                                st.error(f"""
                                Failed feedback: {error['original_feedback'][:100]}...
                                Error: {error['summary']}
                                """)
                    
                    # Convert results to DataFrame for display
                    if len(results) > 0:
                        results_df = pd.DataFrame(results)
                        
                        # Format the details column to display as comma-separated string
                        results_df['details'] = results_df['details'].apply(
                            lambda x: ', '.join(x) if isinstance(x, list) else x
                        )
                        
                        # Show total processed items
                        st.success(f"Successfully processed {len(results)} feedback items")
                        
                        # Show the results table
                        st.write("### 📝 Processed Feedback Results:")
                        st.dataframe(
                            results_df,
                            column_config={
                                "email": st.column_config.TextColumn("Email"),
                                "original_feedback": st.column_config.TextColumn("Original Feedback"),
                                "sentiment": st.column_config.TextColumn("Sentiment"),
                                "category": st.column_config.TextColumn("Category"),
                                "subcategory": st.column_config.TextColumn("Subcategory"),
                                "details": st.column_config.ListColumn("Tag"),
                                "summary": st.column_config.TextColumn("Summary"),
                                "created_at": st.column_config.DatetimeColumn("Created At")
                            },
                            hide_index=False
                        )
                        
                        # Show analysis
                        if len(results) > 1:
                            with st.spinner('Analyzing feedback...'):
                                # Get all valid results (excluding errors)
                                valid_results = [r for r in results if r['category'] != 'Error']
                                
                                if valid_results:
                                    # Show category distribution
                                    st.write("### 📊 Category Distribution")
                                    
                                    # Create analysis dictionary
                                    analysis = {}
                                    for result in valid_results:
                                        category = result['category']
                                        subcategory = result['subcategory']
                                        
                                        if category not in analysis:
                                            analysis[category] = {}
                                        if subcategory not in analysis[category]:
                                            analysis[category][subcategory] = 0
                                            
                                        analysis[category][subcategory] += 1
                                    
                                    # Display results by category
                                    for category, subcategories in analysis.items():
                                        total_items = sum(subcategories.values())
                                        with st.expander(f"{category} ({total_items} items)"):
                                            # Show examples directly without additional headers
                                            examples_df = pd.DataFrame([
                                                {
                                                    'Email': r['email'],
                                                    'Feedback': r['original_feedback'],
                                                    'Subcategory': r['subcategory'],
                                                    'Details': ', '.join(r['details']),
                                                    'Summary': r['summary']
                                                }
                                                for r in valid_results 
                                                if r['category'] == category
                                            ])
                                            st.dataframe(
                                                examples_df,
                                                column_config={
                                                    "Email": st.column_config.TextColumn(
                                                        width="medium"
                                                    ),
                                                    "Feedback": st.column_config.TextColumn(
                                                        width="large"
                                                    ),
                                                    "Subcategory": st.column_config.TextColumn(
                                                        width="small"
                                                    ),
                                                    "Details": st.column_config.TextColumn(
                                                        width="medium"
                                                    ),
                                                    "Summary": st.column_config.TextColumn(
                                                        width="large"
                                                    )
                                                },
                                                hide_index=True
                                            )
                except Exception as e:
                    st.error(f"⚠️ Error processing file: {e}")
                    logging.error(f"Error details: ", exc_info=True)

        except Exception as e:
            st.error(f"⚠️ Error processing file: {e}")
            logging.error(f"Error details: ", exc_info=True)

if __name__ == "__main__":
    main()
