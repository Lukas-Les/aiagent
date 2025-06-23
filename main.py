import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

try:
    args = sys.argv.copy()
    if is_verbose := "--verbose" in args:
        args.remove("--verbose")
    prompt = args[1]
except:
    sys.exit(1)

client = genai.Client(api_key=api_key)


schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
    ]
)


messages = [
    types.Content(role="user", parts=[types.Part(text=prompt)]),
]
# prompt = "Why is Boot.dev such a great place to learn backend development? Use one paragraph maximum."
response = client.models.generate_content(
    model='gemini-2.0-flash-001', contents=messages, config=types.GenerateContentConfig(tools=[available_functions], system_instruction=[system_prompt])
)
prompt_tokens = response.usage_metadata.prompt_token_count
response_tokens = response.usage_metadata.candidates_token_count
if response.function_calls:
    for f_call in response.function_calls:
        print(f"Calling function: {f_call.name}({f_call.args})")
else:
    print(response.text)
if is_verbose:
    print(f"User prompt: {prompt}")
    print(f"Prompt tokens: {prompt_tokens}")
    print(f"Response tokens: {response_tokens}")
