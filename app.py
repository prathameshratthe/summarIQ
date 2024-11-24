import os
import re
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable
import openai

# Load environment variables
load_dotenv()

# Configure APIs
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Summarization prompt
PROMPT = """Welcome, Video Summarizer! Your task is to distill the essence of a given YouTube video transcript into a concise summary. 
Your summary should capture the key points and essential information, presented in bullet points, within a 250-word limit. 
Let's dive into the provided transcript and extract the vital details for our audience."""

# Function to validate YouTube URL
def is_valid_youtube_url(url):
    pattern = r"^https?://(www\.)?youtube\.com/watch\?v=.+$"
    return re.match(pattern, url) is not None

# Function to extract transcript details
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([i["text"] for i in transcript_text])
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except VideoUnavailable:
        return "The video is unavailable or invalid."
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Function to generate summary using Google Gemini Pro
def generate_gemini_content(transcript_text, prompt):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)

        response = genai.generate(
            model="text-bison-001",  # Update based on available model
            prompt=prompt + "\n" + transcript_text,
        )
        return response.generations[0]["text"]
    except Exception as e:
        return f"Error generating summary with Gemini Pro: {str(e)}"

# Function to generate summary using OpenAI GPT (fallback)
def generate_summary_with_openai(transcript_text, prompt):
    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt + "\n" + transcript_text}],
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating summary with OpenAI: {str(e)}"

# Streamlit UI
st.title("Gemini YouTube Transcript Summarizer: Extract Key Insights from YouTube Videos")
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    if is_valid_youtube_url(youtube_link):
        video_id = youtube_link.split("=")[1]
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

        if st.button("Get Detailed Notes"):
            with st.spinner("Processing..."):
                # Extract transcript
                transcript_text = extract_transcript_details(youtube_link)

                if transcript_text and not transcript_text.startswith("An error occurred"):
                    # Attempt to use Google Gemini Pro
                    if GOOGLE_API_KEY:
                        summary = generate_gemini_content(transcript_text, PROMPT)
                        if "Error generating" in summary and OPENAI_API_KEY:
                            st.warning("Google Gemini Pro failed. Switching to OpenAI.")
                            summary = generate_summary_with_openai(transcript_text, PROMPT)
                    # Use OpenAI directly if no Google API key
                    elif OPENAI_API_KEY:
                        summary = generate_summary_with_openai(transcript_text, PROMPT)
                    else:
                        summary = "No valid API keys configured. Please check your environment variables."

                    # Display summary
                    st.markdown("## Detailed Notes:")
                    st.write(summary)
                else:
                    st.error(transcript_text)
    else:
        st.error("Please enter a valid YouTube video URL.")
