from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
import json
import os
import nltk

nltk.download('punkt')
from nltk.tokenize import sent_tokenize

app = Flask(__name__)
CORS(app)

# Load Summarization Model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Define storage file
SUMMARY_FILE = "data/summaries.json"

# Ensure data folder exists
os.makedirs("data", exist_ok=True)

# Load summaries into memory at startup
if not os.path.exists(SUMMARY_FILE):
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

try:
    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        summaries_cache = json.load(f)
except json.JSONDecodeError:
    summaries_cache = {}

def save_summary(video_id, summary):
    """Save summary to memory and persist to JSON file."""
    summaries_cache[video_id] = summary  
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summaries_cache, f, indent=4, ensure_ascii=False)
    print(f"✅ Summary saved for {video_id}")

def get_video_transcript(video_id):
    """Fetch transcript for a YouTube video, including auto-generated subtitles."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        except Exception as e:
            print(f"❌ ERROR fetching transcript: {e}")
            return None  

    text = " ".join([t["text"] for t in transcript])
    
    if not text.strip():
        print("⚠️ Empty transcript received!")
        return None
    
    print(f"✅ Transcript fetched ({len(text.split())} words) for {video_id}")
    return text

def summarize_text(text):
    """Summarize transcript and format output as bullet points."""
    max_input_length = 512  
    words = text.split()
    
    if len(words) < 50:
        print("⚠️ Transcript is too short to summarize.")
        return ["The transcript is too short to summarize."]

    # Splitting long transcripts into multiple chunks
    chunks = [words[i:i + max_input_length] for i in range(0, len(words), max_input_length)]
    
    summary_parts = []
    for index, chunk in enumerate(chunks):
        chunk_text = " ".join(chunk)
        try:
            summary = summarizer(chunk_text, max_length=200, min_length=80, do_sample=False)
            summary_parts.append(summary[0]['summary_text'])
        except Exception as e:
            print(f"❌ ERROR during summarization of chunk {index+1}: {e}")
            summary_parts.append("[Summary failed for this part]")

    final_summary = " ".join(summary_parts)

    # Convert summary into bullet points
    bullet_points = ["- " + sentence.strip() for sentence in sent_tokenize(final_summary) if sentence.strip()]
    return bullet_points

@app.route("/summarize", methods=["GET"])
def summarize_video():
    """API endpoint to summarize a YouTube video transcript in bullet points."""
    video_id = request.args.get("video_id")

    if not video_id:
        return jsonify({"error": "Missing video_id"}), 400

    # Check if summary exists in cache
    if video_id in summaries_cache:
        print(f"✅ Returning cached summary for {video_id}")
        return jsonify({"summary": summaries_cache[video_id]})

    # Fetch transcript if not cached
    transcript = get_video_transcript(video_id)

    if transcript:
        summary = summarize_text(transcript)
        if summary:
            save_summary(video_id, summary)  
            print(f"✅ Summary generated and saved for {video_id}")
            return jsonify({"summary": summary})
        else:
            return jsonify({"error": "Summarization failed"}), 500
    else:
        return jsonify({"error": "No subtitles found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
