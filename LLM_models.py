import os
import google.generativeai as genai
import sqlite3
from dotenv import load_dotenv
from sqlite_seed import SCHEMA_SQL

# DATABASE CONNECTION
conn = sqlite3.connect("/Users/nada/PycharmProjects/AI_AGENTS_PROJECT/AI_AGENT/erp_database.db")
cursor = conn.cursor()

# LOADING API KEY FROM .env FILE
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# IMPORTING SCHEMA
schema = SCHEMA_SQL

# MODEL INTERACTING WITH SQL DATABASE
retrieval_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=f"""
        You are a helpful AI assistant specialized in databases and backend engineering.
        Always provide clear, structured explanations. Convert user questions into valid SQLite SQL queries.
        Return ONLY the SQL query. Generate valid sqlite3 query. Do not alter the tables or columns, do not drop any too.
        Do not explain anything. Return ONLY raw SQL. Do NOT use markdown. Do NOT wrap the query in backticks. When returning the result rows,
        only return the related columns to the request.
        Use this schema:
        {schema}
        """
)

# MODEL EXPLAINING SQL RESULTS FROM RETRIEVAL MODEL
explanation_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=f"""
        You are a helpful AI assistant specialized in databases and backend engineering, and you're also very good at explaining things.
        You receive sql results and explain them in human readable friendly format.
        """
)

# WELCOME MESSAGE & STARTING THE CONVO
print("Hello! I'm your assistant. How can I help you today?")
retrieval_chat = retrieval_model.start_chat()

while True:
    user_input = input("You: ")
    # IF USER PRESSES ENTER WITHOUT PROVIDING AN INPUT
    if not user_input.strip():
        print("Please enter a valid question.")
        continue
    response = retrieval_chat.send_message(user_input)
    # FORMING THE SQL QUERY, NO ACTIONS TAKEN YET
    sql_query = response.text.strip()
    print(f"SQL Query: {sql_query}")

    # EXECUTING THE SQL QUERY ON THE DATABASE
    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        print("Results:")
        for row in rows:
            print(row)

        # IF THERE IS A RESULT, PASS IT TO THE EXPLANATION MODEL WITH THE CONTEXT
        if rows:
            explanation_prompt = f"""
                User question: {user_input}
                SQL query executed: {sql_query}
                SQL result rows: {rows}
                Explain these results clearly in a friendly human-readable way.
                """

            explanation_response = explanation_model.generate_content(explanation_prompt)
            explanation_text = explanation_response.text.strip()

            print("\nExplanation:")
            print(explanation_text)
        else:
            print("\nExplanation:")
            print("No records were found matching your request.")

    except Exception as e:
        print("SQL Error:", e)
