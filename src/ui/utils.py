import requests
from speech_recognition import Recognizer, Microphone, UnknownValueError, RequestError
import pyttsx3

API_URL = "http://127.0.0.1:8000/api/v1/"
session_id = "dummy"


def human_stt():
    recognizer = Recognizer()
    with Microphone() as source:
        audio = recognizer.listen(source)
        try:
            stt_output = recognizer.recognize_google(audio)
            return stt_output
        except UnknownValueError:
            "Google Speech Recognition could not understand audio"
        except RequestError as e:
            raise f"Could not request results from Google Speech Recognition service: {e}"


def ai_response(stt_output):
    response = requests.post(f"{API_URL}chat?message={stt_output}&session_id={session_id}")
    if response.status_code == 200:
        return response.json()
    else:
        return "Failed to get response:", response.status_code, response.text


def ai_tts(response):
    engine = pyttsx3.init()
    engine.say(response["response"])
    engine.runAndWait()
    engine.stop()
