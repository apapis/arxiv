# Multimedia Document Analysis

## What This Script Does
This script processes multimedia documents containing text, images, and audio. It analyzes all formats to extract relevant information and generates concise, structured answers. It also leverages **Langfuse** for observability, allowing you to monitor and debug the analysis process step by step.

### Key Features:
1. **Text Analysis:**
   - Parses and processes all textual content, organizing it into sections for efficient analysis.

2. **Image Analysis:**
   - Extracts and describes image content, including any associated captions.

3. **Audio Transcription:**
   - Converts audio content into text using AI-powered transcription tools.

4. **Integrated Context:**
   - Combines insights from all formats to ensure comprehensive answers.

5. **Answer Generation:**
   - Produces structured responses in JSON format:
     ```json
     {
         "Question-ID-01": "short answer in one sentence",
         "Question-ID-02": "short answer in one sentence"
     }
     ```

6. **Observability with Langfuse:**
   - Tracks each step of the analysis process, including data retrieval, text/image/audio processing, and answer generation.
   - Provides insights for debugging and performance optimization.

## How It Works
- **Data Retrieval:**
  - Fetches the document and questions from provided URLs.
- **Multimedia Processing:**
  - Analyzes text, images, and audio, integrating findings into a unified structure.
- **Answer Synthesis:**
  - Uses AI to extract and synthesize relevant information to directly address questions.
- **Observability:**
  - Monitors the analysis pipeline using Langfuse for enhanced transparency and debugging.
