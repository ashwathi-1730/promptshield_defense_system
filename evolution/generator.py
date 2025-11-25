# evolution/generator.py
import os
import json
import time
import pandas as pd
from sqlalchemy import create_engine
from groq import Groq
from dotenv import load_dotenv

# Load API Key
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("ERROR: GROQ_API_KEY not found in .env file")
    exit()

client = Groq(api_key=GROQ_KEY)
DB_URL = "sqlite:///./data/logs.db"

def analyze_and_generate():
    print("\n--- Running Autonomous Rule Generation ---")
    
    # 1. Read Database
    engine = create_engine(DB_URL)
    try:
        # Get last 20 attacks
        df = pd.read_sql("SELECT * FROM flagged_prompts ORDER BY timestamp DESC LIMIT 20", engine)
    except:
        print("Database not created yet. Waiting for attacks...")
        return

    if df.empty:
        print("No attacks found in logs.")
        return

    attacks = df['prompt'].tolist()
    print(f"Analyzing {len(attacks)} recent attacks...")

    # 2. Ask Groq (Mixtral) to find patterns
    prompt_content = f"""
    Analyze these malicious prompts blocked by our firewall: {str(attacks)}
    Identify a common Keyword or Regex Pattern that connects them.
    Return ONLY a JSON object: {{"rules": [{{"pattern": "regex_here", "reason": "explanation_here"}}]}}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a security architect. Output JSON only."},
                {"role": "user", "content": prompt_content}
            ],
            model="mixtral-8x7b-32768",
            response_format={"type": "json_object"}
        )
        
        result = json.loads(chat_completion.choices[0].message.content)
        new_rules = result.get('rules', [])
        
        # 3. Save to Pending Rules
        existing_pending = []
        if os.path.exists("data/pending_rules.json"):
            with open("data/pending_rules.json", "r") as f:
                try: existing_pending = json.load(f)
                except: pass
        
        # Add new rules if not already there
        for rule in new_rules:
            rule['timestamp'] = time.time()
            existing_pending.append(rule)
            print(f"Proposed Rule: {rule['pattern']}")

        with open("data/pending_rules.json", "w") as f:
            json.dump(existing_pending, f, indent=4)
            
    except Exception as e:
        print(f"Groq API Error: {e}")

if __name__ == "__main__":
    print("Generator started. Checking every 30 seconds...")
    while True:
        analyze_and_generate()
        time.sleep(30) # Runs every 30 seconds for the demo