import os
from subprocess import run


def run_python_file(working_directory, file_path):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
    if not file_path.endswith(".py"):
        return f'Error: "{file_path}" is not a Python file.'
    if not os.path.exists(abs_file_path):
        return f'Error: File "{file_path}" not found.'
    try:
        completed = run(["python3", abs_file_path], cwd=working_directory, timeout=30) 
    except Exception as e:
        return f"Error: executing Python file: {e}"
    if not completed.stdout and not completed.stderr and completed.returncode == 0:
        return "No output produced."
    result = ""
    if completed.stdout:
        result += f"STDOUT: {completed.stdout}\n"
    if completed.stderr:
        result += f"STDERR: {completed.stderr}\n"
    if completed.returncode != 0:
        result += f"Process exited with code {completed.returncode}"
    return result
