import time

RUN_TIME_STR = time.strftime('%Y-%m-%d_%H-%M-%S')

DEFAULT_DIR_FOR_REPOS = "repos"
DEFAULT_DIR_FOR_LOGS = "logs"
DEFAULT_DIR_FOR_OUTPUTS = "outputs"
DEFAULT_FILENAME_FOR_OUTPUT = "OUTPUT"
DEFAULT_FILENAME_FOR_ERROR = "ERROR"
DEFAULT_FILENAME_FOR_STATS = "STATS"

TIME_SECONDS_BETWEEN_REQUESTS = 5

# put your key obtained from google ai studio https://aistudio.google.com/welcome
GOOGLE_AI_API_KEY = "your-google-ai-api-key-here"


GOOGLE_AI_MODEL_NAME = "gemini-1.5-flash"
GOOGLE_AI_GENERATION_CONFIG = {
    "top_p": 0.0,
    "top_k": 0,
    "response_mime_type": "application/json",
}

BASE_PROMPT = """You are an expert web application developer helping us locate credentials in documentation and configuration files that can be used to authenticate into the web application at hand. Be helpful and answer in detail while preferring to use information from reputable sources.

I will provide a text file that may contain one or more usernames and passwords, or emails and passwords.
Credentials can be hidden anywhere in the text: be smart! 
In particular, pay attention to code snippets that are delimited by the ``` symbol.
Please provide a list of all the credentials you find in there. 

Output JSON with this format {"credentials": [ {"username":"...", "password":"..."} ]}. 

If there are no credentials, just return {"credentials": []}.
"""
