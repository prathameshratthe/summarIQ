import os
import re
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable
import google.generativeai as genai
from google.cloud import speech_v1 as speech
import io
import requests
from pytube import YouTube
import yt_dlp
import ffmpeg
from vosk import Model, KaldiRecognizer
import wave
import whisper

# Load environment variables
load_dotenv()

# Configure Google Gemini Pro API
api_key = os.getenv("AIzaSyDe1-tmszp0nrSRs_Thp0b9IRrp_ni4NLQ", "AIzaSyDe1-tmszp0nrSRs_Thp0b9IRrp_ni4NLQ")
genai.configure(api_key=api_key)

# Set the Google Cloud JSON key file path
os.environ["42ed106edf2ad843a7efafd9657d4816da0ddb11"] = "C:/Users/prath/OneDrive - rknec.edu/Desktop/VII/Gemini-YT-Transcript-Summarizer/summariq-42ed106edf2a.json"

# Summarization prompt
PROMPT = """Welcome, Video Summarizer! Your task is to distill the essence of a given YouTube video transcript into a concise summary. 
Your summary should capture the key points and essential information, presented in bullet points, within a 250-word limit. 
Let's dive into the provided transcript and extract the vital details for our audience."""

# Function to validate YouTube URL
def is_valid_youtube_url(url):
    pattern = r"^https?://(www\.)?youtube\.com/watch\?v=.+$"
    print(f"[DEBUG] Validating YouTube URL: {url}")
    return re.match(pattern, url) is not None

# Function to download audio using yt-dlp
def download_audio_yt_dlp(youtube_url):
    try:
        print("[DEBUG] Downloading audio using yt-dlp...")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            audio_file = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".mp4", ".mp3")
            print(f"[INFO] Audio downloaded to {audio_file}")
            return audio_file
    except Exception as e:
        print(f"[ERROR] yt-dlp audio download failed: {e}")
        return None

# Function to extract transcript or fallback to audio transcription
def get_video_transcript_or_transcribe(youtube_video_url):
    try:
        # Attempt to fetch the transcript using YouTubeTranscriptApi
        video_id = youtube_video_url.split("v=")[1]
        print(f"[DEBUG] Attempting to fetch transcript for video ID: {video_id}")
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry["text"] for entry in transcript])
        print("[INFO] Successfully fetched transcript from YouTube.")
        return transcript_text
    except TranscriptsDisabled:
        print("[WARNING] Transcripts are disabled for this video. Falling back to audio transcription.")
    except VideoUnavailable:
        print("[ERROR] The video is unavailable or invalid. Falling back to audio transcription.")
    except Exception as e:
        print(f"[ERROR] Error fetching transcript: {e}. Falling back to audio transcription.")

    # If transcript fetching fails, fallback to audio download and transcription
    print("[DEBUG] Proceeding with audio extraction and transcription...")
    audio_file = download_audio_yt_dlp(youtube_video_url)
    if audio_file:
        return transcribe_audio(audio_file)
    else:
        print("[ERROR] Failed to download audio. Unable to proceed with transcription.")
        return None

# Function to generate summary using Google Gemini Pro
def generate_gemini_content(transcript_text, prompt):
    try:
        print("[DEBUG] Generating summary using Google Gemini Pro...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"{prompt}\n{transcript_text}")
        if response and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return "No content was generated by the model."
    except Exception as e:
        print(f"[ERROR] Error generating summary with Gemini Pro: {e}")
        return f"Error generating summary: {e}"

# Function to transcribe audio to text using Google Cloud Speech-to-Text V2
def transcribe_audio(audio_path):
    try:
        print(f"[DEBUG] Transcribing audio file with Google Cloud: {audio_path}")
        from google.cloud.speech_v2 import SpeechClient
        from google.cloud.speech_v2.types import cloud_speech

        # Instantiate the client
        client = SpeechClient()

        # Read the audio file as bytes
        with open(audio_path, "rb") as f:
            audio_content = f.read()

        # Configure the recognition settings
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="short",
        )

        # Replace PROJECT_ID with your actual Google Cloud project ID
        PROJECT_ID = "summariq"
        recognizer = f"projects/{PROJECT_ID}/locations/global/recognizers/_"

        # Create the recognition request
        request = cloud_speech.RecognizeRequest(
            recognizer=recognizer,
            config=config,
            content=audio_content,
        )

        # Perform the transcription
        response = client.recognize(request=request)

        # Combine all transcript segments
        transcript = " ".join(result.alternatives[0].transcript for result in response.results)
        print("[INFO] Transcription completed successfully using Google Cloud Speech-to-Text V2.")
        return transcript
    except Exception as e:
        print(f"[ERROR] Google Cloud Speech-to-Text V2 transcription failed: {e}")
        print("[DEBUG] Falling back to offline transcription...")
        return offline_transcription(audio_path)

# Offline transcription using vosk
def transcribe_with_vosk(audio_path):
    try:
        print("[DEBUG] Starting offline transcription using Vosk...")
        model = Model("model")
        wf = wave.open(audio_path, "rb")

        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in (8000, 16000):
            print("[DEBUG] Converting audio to Vosk-compatible format...")
            converted_audio_path = "converted_audio.wav"
            ffmpeg.input(audio_path).output(converted_audio_path, ar=16000, ac=1).run()
            wf = wave.open(converted_audio_path, "rb")

        rec = KaldiRecognizer(model, wf.getframerate())
        transcript = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = eval(rec.Result())
                transcript += result.get("text", "") + " "
        print("[INFO] Transcription completed using Vosk.")
        return transcript.strip()
    except Exception as e:
        print(f"[ERROR] Vosk transcription failed: {e}")
        return None

# Offline transcription using Whisper
def transcribe_with_whisper(audio_path):
    try:
        print("[DEBUG] Starting offline transcription using Whisper...")
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        print("[INFO] Transcription completed using Whisper.")
        return result["text"]
    except Exception as e:
        print(f"[ERROR] Whisper transcription failed: {e}")
        return None

# Unified offline transcription function
def offline_transcription(audio_path):
    vosk_transcript = transcribe_with_vosk(audio_path)
    if vosk_transcript:
        return vosk_transcript
    whisper_transcript = transcribe_with_whisper(audio_path)
    if whisper_transcript:
        return whisper_transcript
    return "Offline transcription failed."

# Streamlit UI
st.title("SummarIQ: AI-Driven Video Summaries and Fact-Checking")
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    if is_valid_youtube_url(youtube_link):
        video_id = youtube_link.split("v=")[1]
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

        if st.button("Get Detailed Notes"):
            with st.spinner("Processing..."):
                transcript_text = get_video_transcript_or_transcribe(youtube_link)
                if transcript_text:
                    summary = generate_gemini_content(transcript_text, PROMPT)
                    st.markdown("### Summary:")
                    st.write(summary)
                else:
                    st.error("Failed to generate summary. Unable to fetch or transcribe content.")
    else:
        st.error("Please enter a valid YouTube video URL.")
