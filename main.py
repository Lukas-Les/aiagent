import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")


try:
    args = sys.argv.copy()
    if is_verbose := "--verbose" in args:
        args.remove("--verbose")
    prompt = args[1]
except:
    sys.exit(1)

client = genai.Client(api_key=api_key)
messages = [
    types.Content(role="user", parts=[types.Part(text=prompt)]),
]
# prompt = "Why is Boot.dev such a great place to learn backend development? Use one paragraph maximum."
response = client.models.generate_content(
    model='gemini-2.0-flash-001', contents=messages,
)
prompt_tokens = response.usage_metadata.prompt_token_count
response_tokens = response.usage_metadata.candidates_token_count

print(response.text)
if is_verbose:
    print(f"User prompt: {prompt}")
    print(f"Prompt tokens: {prompt_tokens}")
    print(f"Response tokens: {response_tokens}")
