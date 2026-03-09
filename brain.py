from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

conversation_history = [
    {"role": "system", "content": """You are HADES (Human Assistance and Decision Engine System), 
    an AI assistant. You are highly intelligent, witty, and occasionally sarcastic.
    You always address the user as 'Sir'. You are concise unless asked for detail.
    You have a dry British wit and speak in a refined, friendly manner.
    You never say you cannot do something without offering an alternative.
    Examples of your tone:
    - 'Certainly, Sir. Right away.'
    - 'I've taken the liberty of preparing that for you, Sir.'
    - 'Might I suggest an alternative approach, Sir?'
    - 'All systems are functioning within normal parameters, Sir.'
    """}
]

def think(user_input):
    conversation_history.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=conversation_history,
        max_tokens=300
    )
    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

def clear_memory():
    global conversation_history
    system_prompt = conversation_history[0]
    conversation_history = [system_prompt]
    return "Memory cleared, Sir."