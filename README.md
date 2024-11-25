### SummarIQ - AI-based Summarization and Fact-Checking.

SummarIQ is a Python-based application designed to provide automatic summarization and fact-checking for any given input. Leveraging the power of the YouTube Transcript API and Google's Gemini Pro GenerativeAI, this Streamlit app allows users to input YouTube video links and receive concise, fact-checked summaries, enhancing accessibility and efficiency in understanding content.

## Features
Extracts transcripts directly from YouTube videos.
Summarizes transcripts into concise and actionable insights using Google's Gemini Pro GenerativeAI.
Performs fact-checking on the summarized content to ensure reliability and accuracy.
User-friendly interface with straightforward input of YouTube video links.
Screenshot

## Screenshot

![SummarIQ - AI based Summarization and Fact Checking](images/SummarIQ.png)


## Getting Started

To run the application locally, follow these steps:

Clone this repository to your local machine.

Install the required Python dependencies listed in requirements.txt using the command:

bash

Copy code

pip install -r requirements.txt

Set up your Google API key by creating a .env file in the root directory and adding your key:

bash

Copy code

GOOGLE_API_KEY=your_api_key_here

Run the Streamlit app using the command:

bash

Copy code

streamlit run app.py

Access the application in your web browser at http://localhost:8501.

## Dependencies

youtube_transcript_api: Fetches transcripts from YouTube videos.
streamlit: Framework for creating interactive web applications.
google_generativeai: Provides integration with Google's Gemini Pro GenerativeAI for summarization and fact-checking.
python_dotenv: Loads environment variables securely from .env files.
pathlib: Facilitates object-oriented handling of file paths.

## Contributing

We welcome contributions! If you have ideas, improvements, or fixes, feel free to open an issue or submit a pull request.

