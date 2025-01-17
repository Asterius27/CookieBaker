import os


def get_file_content(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Error: File not found at {path}")
        return None
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return None


def createDirectoryIfNotExists(dirName):
    if not os.path.exists(dirName):
        os.makedirs(dirName)

