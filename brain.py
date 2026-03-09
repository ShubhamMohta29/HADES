from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def think(user_input):
    response = client.chat.completions.create(
        model="llama3-8b-8192",  # free model
        messages=[
            {"role": "system", "content": "You are Jarvis, a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    print(think("Say hello in one sentence."))