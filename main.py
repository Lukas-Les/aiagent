import os
import sys

from enum import Enum

from dotenv import load_dotenv
from google import genai
from google.genai import types

from functions import get_files_info, run_python

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

If you are asked to "fix bug", or "make something" you can write code if needed.
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

schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="gets a file content.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path of the file to read contents from, relative to the working directory.",
            ),
        },
    ),
)


schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="executes a provided python file.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path of the file to execute, relative to the working directory.",
            ),
        },
    ),
)

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="writes content to a file.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path of the file to write to.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="Content to write to a file",
            ),
        },
    ),
)
available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ]
)


functions = {
    "get_files_info": get_files_info.get_files_info,
    "get_file_content": get_files_info.get_file_content,
    "run_python_file": run_python.run_python_file,
    "write_file": get_files_info.write_file,
}

working_directory = "./calculator"


def call_function(function_call_part: types.FunctionCall, verbose: bool=False) -> types.Content:
    assert function_call_part.name is not None
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")
    if not (func_to_call := functions.get(function_call_part.name)):
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_call_part.name,
                    response={"error": f"Unknown function: {function_call_part.name}"},
                )
            ],
        )
    if function_call_part.args:
        result = func_to_call(working_directory=working_directory, **function_call_part.args)
    else:
        result = func_to_call(working_directory)
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_call_part.name,
                response={"result": result},
            )
        ],
    )

messages = [
    types.Content(role="user", parts=[types.Part(text=prompt)]),
]

i = 0
final_response = None
while i <= 20:
    i += 1
    response = client.models.generate_content(
        model='gemini-2.0-flash-001', contents=messages, config=types.GenerateContentConfig(tools=[available_functions], system_instruction=system_prompt)
    )
    if response.candidates:
        for candidate in response.candidates:
            if candidate.content:
                messages.append(candidate.content)
    if response.function_calls:
        for f_call in response.function_calls:
            result = call_function(function_call_part=f_call, verbose=is_verbose)
            messages.append(result)
            if not result or not result.parts[0].function_response.response:  # type: ignore
                raise Exception("response not found!")
            if is_verbose:
                print(f"-> {result.parts[0].function_response.response['result']}")  # type: ignore
    else:
        final_response = response
        break
assert final_response is not None
print(final_response.text)
if is_verbose:
    print(f"User prompt: {prompt}")
    print(f"Prompt tokens: {final_response.usage_metadata.prompt_token_count}")
    print(f"Response tokens: {final_response.usage_metadata.candidates_token_count}")
