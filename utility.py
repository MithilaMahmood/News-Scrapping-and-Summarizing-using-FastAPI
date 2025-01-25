import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_summary(news_body):
    """
    Summarize the news article using the Llama model hosted on Groq Cloud.
    """
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # Ensure GROQ_API_KEY is set in .env
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Replace with your model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in news summarization in english. Summarize the following news article into 3-5 bullet points in english."
                },
                {
                    "role": "user",
                    "content": news_body
                }
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Error generating summary: {e}")
