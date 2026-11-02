"""
import speech_recognition as sr

recognizer = sr.Recognizer()

print("Available microphones:")

for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(index, name)

print("\nStarting microphone test...")

try:
    with sr.Microphone() as source:
        print("Listening... Speak now!")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=8
        )

    print("Processing speech...")

    text = recognizer.recognize_google(audio)

    print("You said:", text)

except Exception as e:
    print("MICROPHONE ERROR:", repr(e))


import pyaudio
import speech_recognition as sr

recognizer = sr.Recognizer()

audio_system = pyaudio.PyAudio()

print("Available microphones:")

for i in range(audio_system.get_device_count()):
    info = audio_system.get_device_info_by_index(i)

    if info["maxInputChannels"] > 0:
        print(i, info["name"])

# Change this to the microphone device index if necessary
MIC_INDEX = None

try:
    microphone = sr.Microphone(device_index=MIC_INDEX)

    with microphone as source:
        print("\nListening... Speak now!")

        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=8
        )

    print("Processing speech...")

    text = recognizer.recognize_google(audio)

    print("You said:", text)

except Exception as e:
    print("ERROR:", repr(e))

finally:
    audio_system.terminate()


import pyaudio
import speech_recognition as sr

p = pyaudio.PyAudio()

try:
    device_index = 10

    info = p.get_device_info_by_index(device_index)

    sample_rate = int(info["defaultSampleRate"])

    print("Testing microphone:", info["name"])

    print("Default microphone:", info["name"])
    print("Device index:", device_index)
    print("Sample rate:", sample_rate)

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=1024
    )

    print("\nRecording for 5 seconds. Speak now!")

    frames = []

    for i in range(int(sample_rate / 1024 * 5)):
        frames.append(stream.read(
            1024,
            exception_on_overflow=False
        ))

    stream.stop_stream()
    stream.close()

    print("Recording finished.")

    audio_bytes = b"".join(frames)

    audio_data = sr.AudioData(
        audio_bytes,
        sample_rate,
        2
    )

    print("Sending recording for speech recognition...")

    recognizer = sr.Recognizer()

    result = recognizer.recognize_google(audio_data)

    print("\nYOU SAID:", result)

except Exception as e:
    print("\nERROR:", repr(e))

finally:
    p.terminate()

import pyaudio

p = pyaudio.PyAudio()

for i in range(p.get_device_count()):

    info = p.get_device_info_by_index(i)

    if info["maxInputChannels"] > 0:

        print("\n----------------------------")
        print("Device:", i)
        print("Name:", info["name"])
        print("Input channels:", info["maxInputChannels"])
        print("Sample rate:", info["defaultSampleRate"])

        for channels in range(1, int(info["maxInputChannels"]) + 1):

            try:
                supported = p.is_format_supported(
                    int(info["defaultSampleRate"]),
                    input_device=i,
                    input_channels=channels,
                    input_format=pyaudio.paInt16
                )

                print("Channels", channels, "SUPPORTED")

            except ValueError:
                print("Channels", channels, "NOT SUPPORTED")

p.terminate()



import pyaudio

p = pyaudio.PyAudio()

device_index = 2

info = p.get_device_info_by_index(device_index)

print("Testing:", info["name"])

rate = int(info["defaultSampleRate"])

try:
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=1024
    )

    print("\nMICROPHONE OPENED SUCCESSFULLY!")
    print("Speak into your microphone for 5 seconds.")

    for i in range(int(rate / 1024 * 5)):
        data = stream.read(
            1024,
            exception_on_overflow=False
        )

        print("Received audio data:", len(data), "bytes")

    stream.stop_stream()
    stream.close()

    print("\nRecording test successful!")

except Exception as e:
    print("\nMICROPHONE ERROR:", repr(e))

finally:
    p.terminate()


import pyaudio
import speech_recognition as sr

p = pyaudio.PyAudio()
recognizer = sr.Recognizer()

device_index = 2
sample_rate = 44100
channels = 1

try:
    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=1024
    )

    print("James is listening. Speak now!")

    frames = []

    for i in range(int(sample_rate / 1024 * 5)):
        data = stream.read(
            1024,
            exception_on_overflow=False
        )
        frames.append(data)

    stream.stop_stream()
    stream.close()

    print("Processing your speech...")

    audio_bytes = b"".join(frames)

    audio_data = sr.AudioData(
        audio_bytes,
        sample_rate,
        2
    )

    text = recognizer.recognize_google(audio_data)

    print("\nJAMES HEARD:", text)

except sr.UnknownValueError:
    print("Could not understand the recording.")

except sr.RequestError as e:
    print("Speech recognition service error:", e)

except Exception as e:
    print("ERROR:", repr(e))

finally:
    p.terminate()
"""
