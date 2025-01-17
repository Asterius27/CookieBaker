import json

import google.generativeai as genai

from config import GOOGLE_AI_API_KEY, GOOGLE_AI_GENERATION_CONFIG, GOOGLE_AI_MODEL_NAME, BASE_PROMPT
from util.fileUtil import get_file_content

genai.configure(api_key=GOOGLE_AI_API_KEY)


model = genai.GenerativeModel(
    model_name=GOOGLE_AI_MODEL_NAME,
    generation_config=GOOGLE_AI_GENERATION_CONFIG,
)


def askToGoogleAi(prompt):
    # send request to google gemini api using genai module

    responseMsg = ""

    if prompt and prompt != "":
        chat_session = model.start_chat(history=[])  # Start a new chat for each prompt
        print("[DEBUG] Started a new chat! Sending message and waiting a response:")
        response = chat_session.send_message(prompt)
        print(f"[DEBUG] Raw Response: {response.text}")
        responseMsg = response.text
    return responseMsg


def extractCredentialFromFile(filePath):
    # prepare prompt to send and parse response received from google gemini api

    print(f"Trying with file: {filePath}")
    fileContent = get_file_content(filePath)
    if fileContent:
        print("File read correctly!")
        prompt = f"{BASE_PROMPT}\nHere's the content of the file:\n```\n{fileContent}\n```"
        response = askToGoogleAi(prompt)
        try:
            return True, json.loads(response)
        except Exception as ex:
            print("Exception parsing JSON response")
            print(ex)
            return False, {'credentials': []}
    else:
        print(f"Failed to read file at path {filePath}")
        return True,{'credentials': []}
