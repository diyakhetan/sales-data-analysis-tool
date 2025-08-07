import streamlit as st
from difflib import get_close_matches

faq_dict = {
    "Data Upload & Cleaning": {
        "Why isn’t my dataset uploading?": 
            "Ensure the file is in CSV format and under the upload size limit. Also, check if required columns are present and correctly named.",
        
        "What file formats are supported for upload?": 
            "Currently, only CSV files are supported. Excel files (.xlsx) must be converted to CSV before upload.",
        
        "What transformations are performed in the ETL step?": 
            "The pipeline handles nulls, converts data types, removes duplicates, and standardizes key fields like dates or amounts.",
        
        "How should I format my date column for the app to read it correctly?": 
            "Use consistent formats like YYYY-MM-DD. Avoid ambiguous formats like DD/MM/YYYY which may fail silently.",
        
        "Can I upload multiple datasets for cross-referencing?": 
            "Yes, upload the secondary dataset in the sidebar. Ensure a common mapping key exists between both files.",
    },

    "Anomaly Detection": {
        "How does the app define an anomaly using z-score?": 
            "It calculates the Z-score for a numerical column. If the absolute score exceeds a threshold (e.g., 3), it's flagged as an anomaly.",
        
        "Why are no anomalies being detected in my data?": 
            "Either your data is consistent, or the z-score threshold is too high. Try using a lower threshold (e.g., 2).",

        "Why are some anomalies marked incorrectly?": 
            "Z-score is sensitive to outliers and assumes normal distribution. Try preprocessing or visual inspection if needed.",
    },

    "Visualizations": {
        "Why are some charts not loading or showing blank?": 
            "The filtered dataset may be empty or key plotting columns may be missing or misnamed.",
        
        "How can I filter the data shown in charts?": 
            "Use the sidebar filters to select date ranges, categories, or thresholds before visualizing.",
        
        "Why do I see 'NaN' in my chart axes or tooltips?": 
            "This could be due to missing values in the plotted column. Check data cleaning steps and reprocess.",
    
    },

    "Forecasting": {
        "Why is the forecasting model taking a long time to load?": 
            "Prophet can be slow with large datasets or high forecast horizons. Try reducing the data size or forecast window.",
        
        "What do I do if the forecast looks inaccurate or flat?": 
            "Check if your historical data has sufficient variation. Avoid using overly aggregated or sparse data.",
        
        "Can I change the forecast period (e.g., forecast next 90 days)?": 
            "Yes, use the forecast settings in the sidebar to adjust the forecast horizon.",
        
        "Why are the confidence intervals in the forecast too wide?": 
            "High variability or lack of trend in your data causes Prophet to widen uncertainty bounds.",
        
        "What are the minimum requirements for time series forecasting?": 
            "You need a date/time column and a numeric target column with regular frequency (daily, weekly, etc.).",
    },

    "File Export": {
        "Why does the Excel export only contain part of the data?": 
            "Some data may be filtered out. Also, Excel has limitations on sheet name length and number of rows in older versions.",
        
        "Can I export anomalies or forecasts separately?": 
            "Yes, each section allows for exporting relevant tables individually using the 'Export to Excel' button.",
        
        "Where is the exported file saved?": 
            "Streamlit creates a temporary download link; check your browser's download folder.",
    },

    "General App Issues": {
        "The FAQ bot isn’t responding—what can I do?": 
            "Check your internet connection. If the issue persists, the backend for the bot may be down or overloaded.",
        
        "How do I reset the app or clear all data?": 
            "Refresh the browser tab to reload the session.",
        
        "Does the app work offline?": 
            "No, Streamlit apps require an active internet connection unless deployed on a local server.",
        
        "What browsers are best supported?": 
            "We recommend using Chrome, Firefox, or Edge. Safari may have issues with file upload or rendering charts.",
        
        "Why am I getting a 'ValueError' or 'TypeError'?": 
            "This typically means a column was misformatted or a required value is missing. Check your input data and reload.",
        
        "Can I view a log of the errors happening in the app?": 
            "If you're running locally, check the terminal/console output.",
    }
}


# Define this first
def get_answer(category, question, faq_dict):
    try:
        return faq_dict[category][question]
    except KeyError:
        return "🤖 Sorry, I couldn't find that question."



def show_faq_tab():
    st.title("🤖 FAQ Bot")

    if st.button("❌ Clear Chat"):
        st.session_state.chat = []
        st.rerun()

    if "chat" not in st.session_state:
        st.session_state.chat = []

    st.markdown("#### 💡 Suggested Questions")

    # Step 1: Category selection
    selected_category = st.selectbox(
        "Choose a category:",
        options=[""] + list(faq_dict.keys()),
        index=0
    )

    # Step 2: Question selection within the category
    if selected_category:
        questions = list(faq_dict[selected_category].keys())
        selected_question = st.selectbox(
            "Now choose a question:",
            options=[""] + questions,
            index=0
        )

        # Step 3: Show answer and add to chat
        if selected_question:
            answer = get_answer(selected_category, selected_question, faq_dict)
            st.session_state.chat.append(("You", selected_question))
            st.session_state.chat.append(("Bot", answer))

    # Step 4: Display chat history
    st.markdown("### 💬 Conversation")
    for speaker, msg in st.session_state.chat:
        st.markdown(f"**{speaker}:** {msg}")