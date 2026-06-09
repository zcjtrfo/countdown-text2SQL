import streamlit as st
import sqlite3
import pandas as pd
import json # <-- NEW IMPORT
from google import genai

# --- 1. CONFIGURATION & AUTHENTICATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    st.error("API Key not found. Please configure Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 2. THE DATABASE SCHEMA ---
# (Paste your massive schema string here just like before)
SCHEMA_TEXT = """
-- [YOUR FULL COUNTDOWN SCHEMA GOES HERE]
"""

# --- 3. THE LLM FUNCTION ---
def translate_text_to_sql(user_question):
    """Sends the schema and user question to Gemini to get SQL and assumptions."""
    
    prompt = f"""
    You are an expert SQLite developer and Countdown show historian. 
    Translate the user's question into a valid, read-only SQL query.
    
    CRITICAL RULES:
    1. You MUST respond with a valid JSON object.
    2. Do NOT wrap the JSON in markdown blocks (no ```json).
    3. The JSON must exactly match the structure below.
    
    JSON STRUCTURE:
    {{
        "sql_query": "The raw SQL query string here",
        "assumptions": [
            "Any assumption you made about what the user meant.",
            "Any clarification about edge cases (e.g., 'Excluding tiebreaks').",
            "If the question was perfectly clear, write 'No major assumptions made.'"
        ]
    }}
    
    DATABASE SCHEMA:
    {SCHEMA_TEXT}
    
    USER QUESTION: 
    {user_question}
    """
    
    # We enforce JSON output using the config
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    
    # Parse the JSON string into a Python dictionary
    try:
        result_dict = json.loads(response.text)
        return result_dict.get("sql_query", ""), result_dict.get("assumptions", [])
    except json.JSONDecodeError:
        raise ValueError("The LLM failed to return valid JSON.")

# --- 4. THE STREAMLIT UI ---
st.title("🔢 Countdown TV Show Explorer")
st.markdown("Ask a question about historical Countdown episodes, contestants, and scores in plain English.")

user_question = st.text_input("Example: Who had the highest score in series 50?")

if user_question:
    with st.spinner("Analyzing question and writing SQL..."):
        try:
            # 1. Get the SQL and Assumptions from Gemini
            generated_sql, assumptions = translate_text_to_sql(user_question)
            
            # 2. Display the Assumptions
            st.write("### AI Agent Assumptions")
            if assumptions:
                for assumption in assumptions:
                    st.markdown(f"* {assumption}")
            else:
                st.write("* No major assumptions made.")
                
            st.divider() # Visual separator
            
            # 3. Display the SQL
            st.write("### Generated SQL Query")
            st.code(
