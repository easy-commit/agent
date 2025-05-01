from dotenv import load_dotenv
import openai
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

def generate_commit_message_with_gpt(commit_messages, staged_diff):
    prompt = f"""Tu es une IA qui aide à écrire des messages de commit clairs et alignés sur les conventions du projet.
Voici des exemples récents :
{chr(10).join(f"- {m}" for m in commit_messages)}

Voici le diff actuel :
{staged_diff}

Génère un message de commit adapté et cohérent avec les exemples."""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )
    return response['choices'][0]['message']['content'].strip()
