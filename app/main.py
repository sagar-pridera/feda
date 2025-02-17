import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
                    processed_count = 0
                    failed_count = 0
                    results = []
                    
                    # Process in batches
                    total_batches = (len(feedback_data) + batch_size - 1) // batch_size
                    
                    for i in range(0, len(feedback_data), batch_size):
                        batch = feedback_data[i:i + batch_size]
                        with st.spinner(f'Processing batch {(i//batch_size)+1}/{total_batches}...'):
                            try:
                                batch_results = asyncio.run(
                                    processor.process_feedback_batch(batch)
                                )
                                
                                # Count processed and failed items
                                for result in batch_results:
                                    if result.get('category') == 'Error':
                                        failed_count += 1
                                    else:
                                        processed_count += 1
                                
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
                                # Add error results for the batch and count them
                                error_results = [
                                    ProcessedFeedback.create_error_response(
                                        FeedbackItem(text=item['feedback'], email=item.get('email', '')),
                                        f"Batch processing error: {str(e)}"
                                    ).to_dict()
                                    for item in batch
                                ]
                                results.extend(error_results)
                                failed_count += len(error_results)
                            
                            # Update progress
                            progress_bar.progress((i + len(batch)) / len(feedback_data))
                    
                    # Show summary with accurate counts
                    st.write(f"""
                    ### Processing Summary:
                    - Total items: {total_items}
                    - Successfully processed: {processed_count}
                    - Failed to process: {failed_count}
                    - Missing/Skipped: {total_items - (processed_count + failed_count)}
                    """)
                    
                    if failed_count > 0:
                        with st.expander("Show Processing Errors"):
                            for result in results:
                                if result.get('category') == 'Error':
                                    st.error(f"""
                                    Failed feedback: {result['original_feedback'][:100]}...
                                    Error: {result['summary']}
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
                        
                        # Show category distribution
                        if len(results) > 1:
                            with st.spinner('Analyzing feedback...'):
                                valid_results = [r for r in results if r['category'] != 'Error']
                                if valid_results:
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

                        # Add missed items section at the correct level
                        missed_count = total_items - (processed_count + failed_count)
                        if missed_count > 0:
                            st.write("### ⚠️ Missed or Skipped Items")
                            
                            # Find items that weren't processed
                            processed_emails = {r['email'] for r in results}
                            missed_items = [
                                item for item in feedback_data 
                                if item['email'] not in processed_emails
                            ]
                            
                            if missed_items:
                                missed_df = pd.DataFrame([
                                    {
                                        'Email': item['email'],
                                        'Feedback': item['feedback'],
                                        'Possible Reason': 'Item was skipped during processing'
                                    }
                                    for item in missed_items
                                ])
                                
                                st.dataframe(
                                    missed_df,
                                    column_config={
                                        "Email": st.column_config.TextColumn(
                                            width="medium"
                                        ),
                                        "Feedback": st.column_config.TextColumn(
                                            width="large"
                                        ),
                                        "Possible Reason": st.column_config.TextColumn(
                                            width="medium"
                                        )
                                    },
                                    hide_index=True
                                )
                                
                                # Add download button for missed items
                                csv = missed_df.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    "Download Missed Items CSV",
                                    csv,
                                    "missed_items.csv",
                                    "text/csv",
                                    key='download-missed-csv'
                                )

                        # After the category distribution and missed items sections
                        if len(results) > 1:
                            st.write("### 📈 Category Distribution Chart")
                            
                            # Prepare data for charts
                            category_counts = {}
                            sentiment_by_category = {}
                            
                            for result in valid_results:
                                category = result['category']
                                sentiment = result['sentiment']
                                
                                # Count categories
                                if category not in category_counts:
                                    category_counts[category] = 0
                                    sentiment_by_category[category] = {'positive': 0, 'negative': 0, 'neutral': 0}
                                
                                category_counts[category] += 1
                                sentiment_by_category[category][sentiment] += 1
                            
                            # Create two columns for charts
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Category distribution pie chart
                                fig_pie = go.Figure(data=[go.Pie(
                                    labels=list(category_counts.keys()),
                                    values=list(category_counts.values()),
                                    hole=0.4,
                                    textinfo='label+percent',
                                    hoverinfo='label+value'
                                )])
                                fig_pie.update_layout(
                                    title='Feedback Categories',
                                    showlegend=False,
                                    height=400
                                )
                                st.plotly_chart(fig_pie, use_container_width=True)
                            
                            with col2:
                                # Sentiment distribution by category bar chart
                                categories = list(sentiment_by_category.keys())
                                positive_vals = [sentiment_by_category[cat]['positive'] for cat in categories]
                                negative_vals = [sentiment_by_category[cat]['negative'] for cat in categories]
                                neutral_vals = [sentiment_by_category[cat]['neutral'] for cat in categories]
                                
                                fig_bar = go.Figure()
                                
                                # Add bars for each sentiment
                                fig_bar.add_trace(go.Bar(
                                    name='Positive',
                                    x=categories,
                                    y=positive_vals,
                                    marker_color='green'
                                ))
                                fig_bar.add_trace(go.Bar(
                                    name='Neutral',
                                    x=categories,
                                    y=neutral_vals,
                                    marker_color='gray'
                                ))
                                fig_bar.add_trace(go.Bar(
                                    name='Negative',
                                    x=categories,
                                    y=negative_vals,
                                    marker_color='red'
                                ))
                                
                                fig_bar.update_layout(
                                    title='Sentiment by Category',
                                    barmode='stack',
                                    height=400,
                                    showlegend=True,
                                    xaxis_tickangle=-45,
                                    yaxis_title='Number of Feedback Items'
                                )
                                st.plotly_chart(fig_bar, use_container_width=True)
                            
                            # Add a table with detailed statistics
                            st.write("### 📊 Detailed Statistics")
                            stats_data = []
                            for category in categories:
                                total = category_counts[category]
                                sentiments = sentiment_by_category[category]
                                stats_data.append({
                                    'Category': category,
                                    'Total Items': total,
                                    'Positive': f"{sentiments['positive']} ({(sentiments['positive']/total*100):.1f}%)",
                                    'Neutral': f"{sentiments['neutral']} ({(sentiments['neutral']/total*100):.1f}%)",
                                    'Negative': f"{sentiments['negative']} ({(sentiments['negative']/total*100):.1f}%)"
                                })
                            
                            stats_df = pd.DataFrame(stats_data)
                            st.dataframe(
                                stats_df,
                                column_config={
                                    "Category": st.column_config.TextColumn(
                                        width="medium"
                                    ),
                                    "Total Items": st.column_config.NumberColumn(
                                        width="small"
                                    ),
                                    "Positive": st.column_config.TextColumn(
                                        width="small"
                                    ),
                                    "Neutral": st.column_config.TextColumn(
                                        width="small"
                                    ),
                                    "Negative": st.column_config.TextColumn(
                                        width="small"
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
