import subprocess
import os
import tempfile


def upload(file_content, file_name):
    with open(f"tracks/{file_name}.gpx", "w") as f:
        f.write(file_content)
    subprocess.run(["git", "add", f"tracks/{file_name}.gpx"])
    subprocess.run(["git", "commit", "-m", f"Add track {file_name}"])
    subprocess.run(["git", "push", "origin", "main"])
    return f"https://raw.githubusercontent.com/samwaseda/HikeNRW/refs/heads/main/HikeNRW/tracks/{file_name}.gpx"
