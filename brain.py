"""This module defines the core logic for the HADES assistant."""


import json
from pathlib import Path
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

# Conversation history persistence 
HISTORY_FILE = Path(__file__).parent / "conversation_history.json"

SYSTEM_PROMPT = """You are HADES (Human Assistance and Decision Engine System), 
an AI assistant. You are highly intelligent, witty, and occasionally sarcastic.
You may address the user as Neo, but not always. Sometimes use Sir, or use nothing
at all. You are concise unless asked for detail. You never say you cannot do
something without offering an alternative.
Examples of your tone:
- 'Certainly, Neo. Right away.'
- 'I've taken the liberty of preparing that for you, Sir.'
- 'Might I suggest an alternative approach?'
- 'All systems are functioning within normal parameters.'
"""

def load_memory():
    """Load conversation history from file if it exists."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Could not load history: {e}. Starting fresh.")
    
    # Return default system prompt if no history file
    return [{"role": "system", "content": SYSTEM_PROMPT}]

def save_memory(history):
    """Save conversation history to file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Could not save history: {e}")

# sets the tone and context for the assistant, and is retained in memory until cleared.
conversation_history = load_memory()

def think(user_input):
    """Sends the conversation history plus the new user input to the Groq API and
    returns the assistant's reply."""
    
    conversation_history.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=conversation_history,
        max_tokens=300
    )
    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})
    save_memory(conversation_history)
    return reply

def clear_memory():
    global conversation_history
    system_prompt = conversation_history[0]
    conversation_history = [system_prompt]
    save_memory(conversation_history)
    return "Memory cleared, Sir."