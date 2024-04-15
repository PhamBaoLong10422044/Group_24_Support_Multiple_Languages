# Imports
import sys
import os
from dotenv import load_dotenv
from pydub import AudioSegment
from ibm_watson import LanguageTranslatorV3, SpeechToTextV1, TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pyaudio
import wave
from Group_24_Support_Multiple_Languages import Port
from collections import Counter
# Initialize IBM Watson services
load_dotenv()
LT_API_KEY = os.getenv("L_API_KEY")
LT_SERVICE_URL = os.getenv("L_SERVICE_URL")
STT_API_KEY = os.getenv("STT_API_KEY")
STT_SERVICE_URL = os.getenv("STT_SERVICE_URL")
TTS_API_KEY = os.getenv("TTS_API_KEY")
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL")

lt_authenticator = IAMAuthenticator(LT_API_KEY)
lt = LanguageTranslatorV3(version='2018-05-01', authenticator=lt_authenticator)
lt.set_service_url(LT_SERVICE_URL)

stt_authenticator = IAMAuthenticator(STT_API_KEY)
speech_to_text = SpeechToTextV1(authenticator=stt_authenticator)
speech_to_text.set_service_url(STT_SERVICE_URL)

tts_authenticator = IAMAuthenticator(TTS_API_KEY)
tts = TextToSpeechV1(authenticator=tts_authenticator)
tts.set_service_url(TTS_SERVICE_URL)

# Constants for recording
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

def record_audio(duration):
    """Record audio from the microphone."""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    print("* I'm listen to you...")
    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* Got it!")
    stream.stop_stream()
    stream.close()
    audio.terminate()

    wav_file = "../recorded_audio.wav"
    with wave.open(wav_file, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))

    mp3_file = "../recorded_audio.mp3"
    audio = AudioSegment.from_wav(wav_file)
    audio.export(mp3_file, format="mp3")

    return mp3_file

def convert_audio_to_text(audio_file_path, custom_language_model, trans_model, output_language):
    """Convert audio to text."""
    audio = AudioSegment.from_file(audio_file_path)
    with open(audio_file_path, 'rb') as audio_file:
        response = speech_to_text.recognize(
            audio=audio_file,
            content_type='audio/mp3',
            model=custom_language_model
        ).get_result()
    transcripts = [result['alternatives'][0]['transcript'] for result in response['results']]
    transcript = " ".join(transcripts)

    if custom_language_model != output_language:
        translate = lt.translate(text=transcript, model_id=trans_model).get_result()
        translate_text = translate["translations"][0]["translation"]
        print("Original transcript:", transcript)
        print("Translated text in {}: ".format(output_language), translate_text)
        return translate_text
    else:
        print("Transcript in {}: ".format(output_language), transcript)
        return transcript

def text_to_audio(text, output_mp3_file, output_voice):
    """Convert text to audio."""
    response = tts.synthesize(
        text=text,
        accept='audio/mp3',
        voice=output_voice
    ).get_result()

    with open(output_mp3_file, 'wb') as audio_file:
        audio_file.write(response.content)
    return output_mp3_file

def training(key_word):
    """Train the assistant."""
    keyword_list = key_word.split()
    file_path = "encoding.txt.example"
    all_checked = False  # Flag to keep track of whether all elements have been checked
    # Count occurrences of each keyword
    keyword_counts = Counter(keyword_list)

    with open(file_path, "w") as file:
        for keyword, count in keyword_counts.items():
            # Write keywords that are duplicate once (count == 2)
            if count >= 2 and keyword == keyword_list[0]:
                file.write("on_light: " + keyword_list[0] + '\n')
            elif count >= 2 and keyword == keyword_list[1]:
                file.write("on_light: " + keyword_list[1] + '\n')
            elif count >= 2 and keyword == keyword_list[-1]:
                file.write("off_light: " + keyword_list[-1] + '\n')
    return file_path


def action(textfile, transcript):
    """Perform action based on transcript."""
    sentence_words = transcript.split()
    with open(textfile, "r") as file:
        mode_ids = {}
        for line in file:
            parts = line.strip().split(': ')
            if len(parts) == 2:
                mode, ids = parts
                mode_ids[mode] = ids.split(', ')

        if sentence_words[0] == "end":
            sys.exit()
        elif sentence_words == []:
            sys.exit()
        else:
            for mode, ids in mode_ids.items():
                for word in sentence_words:
                    if word in ids:
                        print(f"Activating {mode} mode with ID: {word}")
                        if mode == "on_light":
                            Port.sendCommand("1")
                        elif mode == "off_light":
                            Port.sendCommand("0")


def main():
    while True:
        service = input("Enter your service (Translator/Assistant): ")

        #Translator
        if service == "Translator":
            input_language = input("Enter input language (English, German, French): ")
            output_language = input("Enter output language (English, German, French): ")
            duration = int(input("Enter duration of recording in seconds: "))
            audio_file_path = record_audio(duration)
            print("Converting audio to text...")
            if input_language == "English":
                if output_language == "German":
                    transcript = convert_audio_to_text(audio_file_path, "en-US_Telephony", "en-de", output_language)
                    print(transcript)
                    audio_file = text_to_audio(transcript, "output_German.mp3", "de-DE_DieterV3Voice")
                elif output_language == "French":
                    transcript = convert_audio_to_text(audio_file_path, "en-US_Telephony", "en-fr", output_language)
                    print(transcript)
                    audio_file = text_to_audio(transcript, "output_French.mp3", "fr-FR_NicolasV3Voice")
            elif input_language == "German":
                if output_language == "English":
                    transcript = convert_audio_to_text(audio_file_path, "de-DE_Telephony", "de-en", output_language)
                    print(transcript)
                    audio_file = text_to_audio(transcript, "../output_English.mp3", "en-US_AllisonV3Voice")
                elif output_language == "French":
                    transcript = convert_audio_to_text(audio_file_path, "de-DE_Telephony", "de-fr", output_language)
                    print(transcript)
                    audio_file = text_to_audio(transcript, "output_French.mp3", "fr-FR_NicolasV3Voice")
            elif input_language == "French":
                if output_language == "English":
                    transcript = convert_audio_to_text(audio_file_path, "fr-FR_Telephony", "fr-en", output_language)
                    print(transcript)
                    audio_file = text_to_audio(transcript, "../output_English.mp3", "en-US_AllisonV3Voice")
                elif output_language == "German":
                    transcript = convert_audio_to_text(audio_file_path, "fr-FR_Telephony", "fr-de", output_language)
                    print(transcript)
                    audio_file = text_to_audio(transcript, "output_German.mp3", "de-DE_DieterV3Voice")
            command = input("Type q to quit, p to play audio once, c to continue: ")
            if command == "q":
                os.remove(audio_file)
                break
            elif command == "p":
                os.system(audio_file)
                break
            elif command == "c":
                pass
        #Assistant
        elif service == "Assistant":
            language = input("Enter your language (English, German, French): ")
            if language == "English":
                ans = input("Have you trained your Assistant? (Yes/No): ")
                if ans.lower() == "no":
                    print("Start training...")
                    print("Please speak 4 keywords, where the first two keywords are for on_light mode and the remaining two keywords are for off_light mode!!!")
                    audio_file_path = record_audio(10)
                    transcript_train = convert_audio_to_text(audio_file_path, "en-US_Telephony", " ", "en-US_Telephony")
                    print(transcript_train)
                    encodings_file = training(transcript_train.lower())
                    print("Model trained!")
                    command = input("Type q to use model, c to continue: ")
                    if command == "q":
                        os.remove(encodings_file)
                        break
                    else:
                        print("Using trained model...")
                        while True:
                            print("Speak to request...")
                            audio_file_path = record_audio(5)
                            transcript = convert_audio_to_text(audio_file_path, "en-US_Telephony", "de-en",
                                                               "en-US_Telephony")
                            print(transcript)
                            action(encodings_file, transcript.lower())

                elif ans.lower() == "yes":
                    print("Using trained model...")
                    while True:
                        print("Speak to request...")
                        audio_file_path = record_audio(5)
                        transcript = convert_audio_to_text(audio_file_path, "en-US_Telephony", "de-en", "en-US_Telephony")
                        print(transcript)
                        action(r"C:\Users\long0\PycharmProjects\SupportMultiLanguageApplication\encoding.txt", transcript.lower())
            # Similarly implement Assistant for German and French
            elif language == "German":
                ans = input("Haben Sie Ihren Assistenten geschult? (Ja/ Nein):")
                if ans.lower() == "nein":
                    print("Beginne zu trainieren...")
                    print("Bitte sprechen Sie 4 Schlüsselwörter aus, wobei die ersten beiden Schlüsselwörter für den On_Light-Modus und die restlichen beiden Schlüsselwörter für den Off_Light-Modus gelten!!!")
                    audio_file_path = record_audio(10)
                    transcript_train = convert_audio_to_text(audio_file_path, "de-DE_Telephony", "de-en", "English")
                    print(transcript_train)
                    encodings_file = training(transcript_train.lower())
                    print("Model trainiert!")
                    command = input("Geben Sie q ein, um das Modell zu verwenden, und c, um fortzufahren:")
                    if command == "q":
                        os.remove(encodings_file)
                        break
                    else:
                        print("Unter Verwendung eines trainierten Modells...")
                        while True:
                            print("Sprechen Sie mit der Anfrage...")
                            audio_file_path = record_audio(5)
                            transcript = convert_audio_to_text(audio_file_path, "de-DE_Telephony", "de-en",
                                                               "English")
                            print(transcript)
                            action(encodings_file, transcript.lower())

                elif ans.lower() == "ja":
                    print("Using trained model...")
                    while True:
                        print("Unter Verwendung eines trainierten Modells...")
                        while True:
                            print("Sprechen Sie mit der Anfrage...")
                            audio_file_path = record_audio(5)
                            transcript = convert_audio_to_text(audio_file_path, "de-DE_Telephony", "de-en",
                                                               "English")
                            print(transcript)
                            action(r"C:\Users\long0\PycharmProjects\SupportMultiLanguageApplication\encoding.txt", transcript.lower())
        command = input("Type q to quit, c to continue: ")
        if command == "q":
            break
        elif command == "c":
            pass

if __name__ == '__main__':
    main()
