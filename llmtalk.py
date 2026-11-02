
import tkinter as tk
from tkinter import scrolledtext
import speech_recognition as sr
import pyttsx3
import requests
import threading
import queue
import pyaudio
# --------------------------------
# LM STUDIO SETTINGS
# --------------------------------

LOCAL_API_URL ="http://localhost:1234/v1/chat/completions"
MODEL_NAME = "Qwen3-30B-A3B-Instruct-2507-GGUF"

SYSTEM_PROMPT = """
You are James, a helpful, knowledgeable AI assistant.
You can discuss programming, electronics, robotics, science,
and general subjects.

Keep answers informative but reasonably concise.
You are running locally through LM Studio.
"""

# --------------------------------
# GLOBAL VARIABLES
# --------------------------------

messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

task_queue = queue.Queue()
busy = False
voice_enabled = True

# --------------------------------
# TEXT TO SPEECH
# --------------------------------

def speak_response(text):
    if not voice_enabled:
        return

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        task_queue.put(("status", f"Speech error: {e}"))


# --------------------------------
# MICROPHONE INPUT
# --------------------------------
"""
def listen_for_command():

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:

            task_queue.put(("status", "Listening..."))

            recognizer.adjust_for_ambient_noise(
                source, duration=0.5
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10
            )

        task_queue.put(("status", "Recognizing speech..."))

        query = recognizer.recognize_google(audio)

        return query

    except sr.WaitTimeoutError:
        return None

    except sr.UnknownValueError:
        return None

    except Exception as e:
        task_queue.put(("status", f"Microphone error: {e}"))
        return None
"""


MIC_INDEX = 1  # the index that worked in mic_test.py; 2 is an output device

def listen_for_command():
    recognizer = sr.Recognizer()

    with sr.Microphone(device_index=MIC_INDEX, sample_rate=44100) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening... Speak now!")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return None  # couldn't understand the speech
    except sr.RequestError as e:
        return f"Speech service error: {e}"
    """
def listen_for_command():
    recognizer = sr.Recognizer()

    device_index = 2
    sample_rate = 44100
    channels = 1
    chunk = 1024
    record_seconds = 5

    p = pyaudio.PyAudio()
    stream = None
    """
    try:
        task_queue.put(("status", "Listening..."))

        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk
        )

        frames = []

        for i in range(int(sample_rate / chunk * record_seconds)):
            data = stream.read(
                chunk,
                exception_on_overflow=False
            )
            frames.append(data)

        task_queue.put(("status", "Processing speech..."))

        audio_bytes = b"".join(frames)

        audio_data = sr.AudioData(
            audio_bytes,
            sample_rate,
            2
        )

        text = recognizer.recognize_google(audio_data)

        return text

    except sr.UnknownValueError:
        task_queue.put(("status", "Couldn't understand speech."))
        return None

    except sr.RequestError as e:
        task_queue.put(("status", f"Speech recognition error: {e}"))
        return None

    except Exception as e:
        task_queue.put(("status", f"Microphone error: {e}"))
        return None

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()

        p.terminate()


# --------------------------------
# LM STUDIO COMMUNICATION
# --------------------------------

def get_llm_response_local(user_query):

    global messages

    messages.append({
        "role": "user",
        "content": user_query
    })

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:

        response = requests.post(
            LOCAL_API_URL,
            json=payload,
            timeout=320
        )

        response.raise_for_status()

        data = response.json()

        #answer = data["choices"][0]["message"]["content"]
        """
        answer = data["choices"][0]["message"]

        assistant_reply = answer.get("content") or ""

        if not assistant_reply.strip():
            assistant_reply = "I wasn't able to generate a response. Please try again."


        messages.append({
            "role": "assistant",
            "content": answer
        })
        """

        # Get the complete message returned by LM Studio
        answer = data["choices"][0]["message"]

        # Extract only the actual response, not the reasoning
        assistant_reply = answer.get("content") or ""

        # Handle an empty response
        if not assistant_reply.strip():
            assistant_reply = "I wasn't able to generate a response. Please try again."

        # Save the actual response to conversation history
        messages.append({
            "role": "assistant",
            "content": assistant_reply
        })

        return assistant_reply

        #return answer

    except requests.exceptions.RequestException as e:

        # Remove the unanswered user message
        messages.pop()

        return f"LM Studio connection error: {e}"

    except (KeyError, IndexError, ValueError) as e:

        messages.pop()

        return f"Unexpected response from LM Studio: {e}"


# --------------------------------
# BACKGROUND WORKER
# --------------------------------

def process_task(task_type, user_text=None):

    if task_type == "microphone":

        user_text = listen_for_command()

        if not user_text:
            task_queue.put(("status", "No speech recognized."))
            task_queue.put(("finished", None))
            return

    if task_type == "text" or task_type == "microphone":

        task_queue.put(("user", user_text))
        task_queue.put(("status", "James is thinking..."))

        answer = get_llm_response_local(user_text)

        task_queue.put(("answer", answer))

        speak_response(answer)

        task_queue.put(("finished", None))


def start_task(task_type, user_text=None):

    global busy

    if busy:
        return

    busy = True

    send_button.config(state="disabled")
    mic_button.config(state="disabled")

    threading.Thread(
        target=process_task,
        args=(task_type, user_text),
        daemon=True
    ).start()


# --------------------------------
# TKINTER INTERFACE
# --------------------------------

def add_message(speaker, message):

    chat_display.config(state="normal")

    chat_display.insert(
        tk.END,
        f"\n{speaker}:\n{message}\n"
    )

    chat_display.config(state="disabled")
    chat_display.see(tk.END)


def send_text():

    text = input_box.get().strip()

    if not text:
        return

    if text.lower() in ["exit", "quit", "goodbye"]:
        root.destroy()
        return

    input_box.delete(0, tk.END)

    start_task("text", text)


def microphone_input():

    start_task("microphone")


def toggle_voice():

    global voice_enabled

    voice_enabled = not voice_enabled

    if voice_enabled:
        voice_button.config(text="Voice: ON")
    else:
        voice_button.config(text="Voice: OFF")


def clear_conversation():

    global messages

    if busy:
        return

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    chat_display.config(state="normal")
    chat_display.delete("1.0", tk.END)
    chat_display.config(state="disabled")

    status_label.config(text="Conversation cleared.")


def check_queue():

    global busy

    try:

        while True:

            event, data = task_queue.get_nowait()

            if event == "status":
                status_label.config(text=data)

            elif event == "user":
                add_message("YOU", data)

            elif event == "answer":
                add_message("JAMES", data)

            elif event == "finished":

                busy = False

                send_button.config(state="normal")
                mic_button.config(state="normal")

                status_label.config(text="Ready.")

    except queue.Empty:
        pass

    root.after(100, check_queue)


# --------------------------------
# BUILD WINDOW
# --------------------------------

root = tk.Tk()

root.title("James - Local AI Assistant")
root.geometry("750x600")

title_label = tk.Label(
    root,
    text="JAMES",
    font=("Arial", 20, "bold")
)
title_label.pack(pady=10)

chat_display = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    font=("Arial", 11),
    state="disabled"
)

chat_display.pack(
    padx=10,
    pady=10,
    fill=tk.BOTH,
    expand=True
)

input_frame = tk.Frame(root)
input_frame.pack(fill=tk.X, padx=10, pady=5)

input_box = tk.Entry(
    input_frame,
    font=("Arial", 12)
)

input_box.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True,
    padx=5
)

input_box.bind(
    "<Return>",
    lambda event: send_text()
)

send_button = tk.Button(
    input_frame,
    text="Send",
    width=10,
    command=send_text
)

send_button.pack(side=tk.LEFT, padx=5)

mic_button = tk.Button(
    input_frame,
    text="Microphone",
    width=12,
    command=microphone_input
)

mic_button.pack(side=tk.LEFT, padx=5)

control_frame = tk.Frame(root)
control_frame.pack(pady=5)

voice_button = tk.Button(
    control_frame,
    text="Voice: ON",
    command=toggle_voice
)

voice_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(
    control_frame,
    text="Clear Conversation",
    command=clear_conversation
)

clear_button.pack(side=tk.LEFT, padx=5)

status_label = tk.Label(
    root,
    text="Ready.",
    anchor="w"
)

status_label.pack(fill=tk.X, padx=10, pady=5)

root.after(100, check_queue)

add_message(
    "JAMES",
    "Hello! I'm James. What would you like to talk about?"
)

root.mainloop()


"""import speech_recognition as sr
import pyttsx3
import requests  # <--- NEW CORE LIBRARY
import time

# --- CONFIGURATION ---
# *** YOU MUST SET THIS TO YOUR LOCAL SERVER'S URL ***
LOCAL_API_URL = "http://localhost:8000/v1/chat/completions"
MODEL_NAME = "google/gemma-4-e4b"  # e.g., "llama-2-7b"

# --- INITIALIZATION ---
engine = pyttsx3.init()


def speak_response(text):
    #Converts text to speech.
    print("\n🔊 [AI Voice]:", text)
    engine.say(text)
    engine.runAndWait()


# --- 1. SPEECH TO TEXT (STILL THE SAME) ---
def listen_for_command():
    #Listens via the microphone and returns the recognized text.
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Listening... Speak now!")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return "TIMEOUT"

    print("🔍 Processing audio...")
    try:
        query = r.recognize_google(audio)
        print(f"🎤 You Said: {query}")
        return query.lower()
    except Exception as e:
        # Catching all errors here for simplicity in testing the local server connection
        speak_response("Sorry, I could not understand the audio or connect to service.")
        return None


# --- 2. LLM INTERACTION (REPLACED FOR LOCAL SERVER) ---

def get_llm_response_local(user_query):
    Sends the user's text query to a local OpenAI-compatible server.
    print(f"🌐 Contacting Local Server at: {LOCAL_API_URL}")

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": MODEL_NAME,  # Must match the model name your server is running
        "messages": [
            {"role": "system",
             "content": "You are a helpful, engaging, and knowledgeable assistant. Keep your answers concise."},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.7,  # Standard setting
        "max_tokens": 500
    }

    try:
        # Making the POST request to your local server endpoint
        response = requests.post(LOCAL_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Throws an exception for bad status codes (4xx or 5xx)

        data = response.json()
        # The structure usually mirrors OpenAI's response format
        llm_text = data['choices'][0]['message']['content']
        return llm_text

    except requests.exceptions.ConnectionError:
        error_msg = "CONNECTION ERROR: Could not connect to the local LLM server. Is llama.cpp/LM Studio running and accessible at the correct URL?"
        print("\n" + "=" * 50)
        speak_response(error_msg)
        return None
    except requests.exceptions.RequestException as e:
        error_msg = f"An HTTP request error occurred while contacting the server: {e}"
        print("\n" + "=" * 50)
        speak_response(error_msg)
        return None


# --- 3. MAIN APPLICATION LOOP (The Orchestrator) ---

def main_loop():
    #Main loop that ties together listening, processing, and speaking.
    speak_response("System ready to use the local LLM server. Speak your first query.")

    while True:
        user_text = listen_for_command()

        if user_text == "TIMEOUT":
            continue

        elif not user_text or user_text in ["exit", "quit"]:
            speak_response("Goodbye! Shutting down the voice agent.")
            break

            # Call the local server function instead of the OpenAI one
        llm_answer = get_llm_response_local(user_text)

        if llm_answer:  # Only speak if we successfully got an answer back
            speak_response(llm_answer)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n\n👋 Program manually stopped by user (Ctrl+C).")
        """


