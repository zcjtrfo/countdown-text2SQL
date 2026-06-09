import streamlit as st
import sqlite3
import pandas as pd
from google import genai

# --- 1. CONFIGURATION & AUTHENTICATION ---
# Streamlit securely stores your API key in its secrets manager.
# If running locally, ensure you have a .env file or streamlit secrets configured.
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    st.error("API Key not found. Please configure Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 2. THE DATABASE SCHEMA ---
# The LLM must know your exact column names and data types to write valid SQL.
# Replace this string with your actual Countdown database schema!
SCHEMA_TEXT = """
-- --- CORE REFERENCE TABLES ---

CREATE TABLE person (
    id         int primary key,
    name       text not null,
    page_title text not null
);

CREATE TABLE format (
    id      int primary key,
    name    text not null,
    rounds  text not null
);

CREATE TABLE series (
    id      int primary key,   -- primary key
    name    text not null      -- name of series, e.g. "Series 69"
);

-- --- GAME & EPISODE TABLES ---

CREATE TABLE game (
    ep_id     text not null,               -- primary key: episode ID used by the wiki
    series    int references series(id),   -- series ID: foreign key into SERIES table
    ep_type   text not null,               -- episode type code
    format    int references format(id),   -- format: foreign key into FORMAT table
    tx_date   text,                        -- first broadcast date (NULL if unbroadcast)
    tiebreak  int,                         -- 1 if this game went to a tiebreak, 0 if not
    max_score int,                         -- maximum possible score in this game
    primary key (ep_id)
);

CREATE TABLE game_player (
    ep_id   text not null references game(ep_id),  -- episode ID: foreign key into GAME table
    seat    int,                                   -- which seat the player sat in: 1 is camera left (champion's chair), 2 is camera right (challenger's chair)
    p_id    int references person(id),             -- player ID: foreign key into PERSON table
    name    text,                                  -- name the player used for this episode
    score   int,                                   -- this player's final score in this episode
    primary key (ep_id, p_id),
    unique (ep_id, seat)
);

CREATE TABLE game_guest (
    ep_id   text not null references game(ep_id),
    p_id    int not null references person(id),
    name    text not null,
    primary key (ep_id, p_id)
);

CREATE TABLE game_lex (
    ep_id   text not null references game(ep_id),
    p_id    int not null references person(id),
    name    text not null,
    primary key (ep_id, p_id)
);

-- --- PLAYER ROUND PERFORMANCE TABLES ---

CREATE TABLE player_letters (
    ep_id       text not null references game(ep_id),  -- foreign key into GAME table
    round_no    int not null,                          -- round number in this game
    p_id        int not null references person(id),    -- player; foreign key into PERSON table
    word        text,                                  -- word this player offered
    adj         int,                                   -- adjudication (0=Accepted, 1=Unacceptable, 2=Not from selection, 3=Not written down, Negative=Misdeclared length)
    score       int,                                   -- player's score for this round
    cumul_score int,                                   -- player's score so far in this game, up to and including this round
    primary key(ep_id, round_no, p_id)
);

CREATE TABLE player_numbers (
    ep_id        text not null references game(ep_id),   -- foreign key into GAME table
    round_no     int not null,                           -- round number in this game
    p_id         int not null references person(id),     -- player ID: foreign key into PERSON table
    dec          int,                                    -- player's declaration or 0 if no declaration
    adj          int,                                    -- adjudication: 0 if accepted, nonzero if not
    method       text,                                   -- player's method, if given
    score        int,                                    -- points scored by player in this round
    cumul_score  int,                                    -- points scored by player so far in this game, up to and including this round
    primary key(ep_id, round_no, p_id)
);

CREATE TABLE player_conundrums (
    ep_id       text not null references game(ep_id), -- foreign key to GAME table
    round_no    int not null,                         -- round number within this game
    p_id        int not null references person(id),   -- foreign key to PERSON table
    buzz        int,                                  -- 1 if contestant buzzed, 0 otherwise
    buzz_time   real,                                 -- time of buzz
    answer      text,                                 -- contestant's answer
    score       int,                                  -- contestant's score for this round
    cumul_score int,                                  -- contestant's cumulative score so far in the game, up to and including this round
    primary key(ep_id, round_no, p_id)
);

-- --- ROUND DETAILS TABLES ---

CREATE TABLE round_letters (
    ep_id           text not null references game(ep_id),  -- episode ID: foreign key into GAME table
    round_no        int not null,                          -- round number in this game
    selection       text,                                  -- letters selection for this round
    max_score       int,                                   -- maximum score available from this round
    max_cumul_score int,                                   -- maximum score available so far in this game, up to and including this round
    primary key(ep_id, round_no)
);

CREATE TABLE round_numbers (
    ep_id           text not null references game(ep_id),   -- episode ID: foreign key into GAME table
    round_no        int not null,                           -- round number in this game
    target          int,                                    -- target for this round
    arith_dec       int,                                    -- arithmetician's declaration, if known
    arith_method    text,                                   -- arithmetician's method, if known
    best_dec        int,                                    -- a closest possible declaration
    best_method     text,                                   -- a method for achieving best_dec
    max_score       int,                                    -- maximum number of points available from this round
    max_cumul_score int,                                    -- maximum number of points available so far in this game, up to and including this round
    primary key(ep_id, round_no)
);

CREATE TABLE round_numbers_sel (
    ep_id    text not null references game(ep_id),  -- episode ID: foreign key into GAME game
    round_no int,                                   -- round number in this game
    seq      int not null,                          -- sequence number between 0 and 5 for this number - 0 is the leftmost number, 5 the rightmost
    num      int,                                   -- the number
    primary key(ep_id, round_no, seq)
);

CREATE TABLE round_conundrums (
    ep_id           text not null references game(ep_id), -- episode ID: foreign key into GAME table
    round_no        int not null,                         -- round number in this game
    tiebreak        int,                                  -- 1 if this was a tiebreak, 0 if not
    selection       text,                                 -- the conundrum scramble
    order_known     int,                                  -- 1 if the order of the letters in the selection field is known to be correct, 0 if not
    answer          text,                                 -- the correct answer
    max_score       int,                                  -- the maximum score available in this round (always 10)
    max_cumul_score int,                                  -- the maximum score available in the game so far, up to and including this round
    primary key(ep_id, round_no)
);

-- --- VIEWS ---

CREATE VIEW round_player_union as
    select ep_id, round_no, 'L' round_type, p_id, score, cumul_score from player_letters
    union
    select ep_id, round_no, 'N' round_type, p_id, score, cumul_score from player_numbers
    union
    select ep_id, round_no, 'C' round_type, p_id, score, cumul_score from player_conundrums;

CREATE VIEW round_union as
    select ep_id, round_no, 'L' round_type, max_score, max_cumul_score from round_letters
    union
    select ep_id, round_no, 'N' round_type, max_score, max_cumul_score from round_numbers
    union
    select ep_id, round_no, 'C' round_type, max_score, max_cumul_score from round_conundrums;
"""

# --- 3. THE LLM FUNCTION ---
def translate_text_to_sql(user_question):
    """Sends the schema and user question to Gemini to get a SQL query."""
    
    prompt = f"""
    You are an expert SQLite developer. Your job is to translate a user's question into a valid, read-only SQL query.
    
    CRITICAL RULES:
    1. Respond ONLY with the raw SQL code. 
    2. Do NOT wrap the SQL in markdown blocks (no ```sql).
    3. Do NOT include any explanations or conversational text.
    
    DATABASE SCHEMA:
    {SCHEMA_TEXT}
    
    USER QUESTION: 
    {user_question}
    """
    
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )
    
    # Strip any accidental whitespace or markdown that the LLM might stubbornly include
    clean_sql = response.text.strip().replace("```sql", "").replace("```", "").strip()
    return clean_sql

# --- 4. THE STREAMLIT UI ---
st.title("🔢 Countdown TV Show Explorer")
st.markdown("Ask a question about historical Countdown episodes, contestants, and scores in plain English.")

# Chat input
user_question = st.text_input("Example: Who had the highest score in series 50?")

if user_question:
    with st.spinner("Translating your question to SQL..."):
        try:
            # 1. Get the SQL from Gemini
            generated_sql = translate_text_to_sql(user_question)
            
            st.write("**Generated SQL Query:**")
            st.code(generated_sql, language="sql")
            
            # 2. Connect to the database safely
            # Note: Using URI ensures the database is opened in READ-ONLY mode. 
            # This prevents the LLM from executing destructive commands like DROP TABLE.
            # Make sure your database file is named "countdown (8).db" and is in the same folder.
            db_uri = 'file:countdown (8).db?mode=ro'
            conn = sqlite3.connect(db_uri, uri=True)
            
            # 3. Execute the query and load results into a Pandas DataFrame
            results_df = pd.read_sql_query(generated_sql, conn)
            conn.close()
            
            # 4. Display the results
            if results_df.empty:
                st.info("The query ran successfully, but returned no results.")
            else:
                st.write("**Results:**")
                st.dataframe(results_df, use_container_width=True)
                
        except sqlite3.Error as e:
            st.error(f"**Database Error:** The generated SQL was invalid. \n\nDetails: {e}")
        except Exception as e:
            st.error(f"**Application Error:** {e}")
