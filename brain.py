from openai import OpenAI
from config import OPENAI_API_KEY

import config
print(config.__file__)

client = OpenAI(api_key=OPENAI_API_KEY)

def think(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Jarvis, a concise but intelligent AI assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    print(think("Say hello in one sentence."))