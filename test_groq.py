from groq import Groq
from dotenv import load_dotenv
import os

# Load your API key from the .env file
# Why: you never want API keys hardcoded in your code
# If you push to GitHub with a hardcoded key, it gets stolen within minutes
load_dotenv()

# Create a Groq client
# Why: this is your connection to the Groq API
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

# Send a message and get a response
# Why chat.completions.create: LLMs are built around "chat" — 
# you send a list of messages, it continues the conversation
response = client.chat.completions.create(
    model="llama-3.1-8b-instant",  # Llama 3 8B — free and fast
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant."
            # Why system message: this sets the LLM's behavior
            # Think of it as background instructions it always follows
        },
        {
            "role": "user",
            "content": "Hello! Can you tell me what you are in one sentence?"
            # Why user message: this is what "you" are saying
        }
    ]
)

print(response)
# Why this path: the response object has nested fields
# response.choices[0].message.content is where the actual text lives
print(response.choices[0].message.content)
