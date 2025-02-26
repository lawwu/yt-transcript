"""Module for transcript summarization using OpenAI GPT."""

import logging
import os
from datetime import timedelta
from typing import Dict, List

from openai import OpenAI

logger = logging.getLogger(__name__)


class SummarizerError(Exception):
    """Custom exception for summarizer errors."""

    pass


def get_openai_client() -> OpenAI:
    """
    Initialize OpenAI client with API key from environment.

    Raises:
        SummarizerError: If OPENAI_API_KEY is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SummarizerError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    return str(timedelta(seconds=int(seconds)))


def extract_chapters(transcript: List[Dict], video_info: Dict) -> List[Dict]:
    """
    Extract chapters from video info or create time-based segments if none available.

    Args:
        transcript: List of transcript segments
        video_info: Dictionary containing video metadata and chapters

    Returns:
        List of chapter dictionaries with start/end times
    """
    # Use YouTube chapters if available
    if video_info.get("chapters"):
        chapters = []
        for chapter in video_info["chapters"]:
            # Find segments that belong to this chapter
            chapter_segments = [
                seg
                for seg in transcript
                if seg["start"] >= chapter["start"] and seg["start"] < chapter["end"]
            ]

            if chapter_segments:
                chapter_text = " ".join(seg["text"] for seg in chapter_segments)
                chapters.append(
                    {
                        "start": chapter["start"],
                        "end": chapter["end"],
                        "text": chapter_text,
                        "title": chapter["title"],
                    }
                )
        return chapters

    # Fallback to 10-minute segments if no chapters available
    logger.info("No YouTube chapters found, falling back to time-based segments")
    segment_length = 600  # 10 minutes in seconds
    total_duration = transcript[-1]["start"] + transcript[-1].get("duration", 0)

    chapters = []
    current_start = 0

    while current_start < total_duration:
        end_time = min(current_start + segment_length, total_duration)

        # Find segments that belong to this chapter
        chapter_segments = [
            seg
            for seg in transcript
            if seg["start"] >= current_start and seg["start"] < end_time
        ]

        if chapter_segments:
            chapter_text = " ".join(seg["text"] for seg in chapter_segments)
            chapters.append(
                {
                    "start": current_start,
                    "end": end_time,
                    "text": chapter_text,
                    "title": f"Section {format_timestamp(current_start)}",
                }
            )

        current_start = end_time

    return chapters


def summarize_chapter(client: OpenAI, chapter: Dict, video_context: str) -> Dict:
    """
    Summarize a single chapter using OpenAI API.

    Args:
        client: OpenAI client instance
        chapter: Dictionary containing chapter text and metadata
        video_context: Brief context about the video

    Returns:
        Updated chapter dict with title and summary
    """
    # Modified prompt to incorporate existing chapter title
    prompt = f"""
    Context: This is a section from {video_context}
    Section Title: {chapter["title"]}

    Text to summarize:
    {chapter["text"]}

    Please provide a concise summary of the main points (3-4 sentences) that captures the key information from this section.

    Format your response as:
    Summary: <summary>
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise video summaries.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        # Parse the response
        content = response.choices[0].message.content
        summary_line = [
            line for line in content.split("\n") if line.startswith("Summary:")
        ][0]

        # Keep the original YouTube chapter title
        chapter["summary"] = summary_line.replace("Summary:", "").strip()

        return chapter

    except Exception as e:
        logger.error(f"Error summarizing chapter: {e!s}")
        chapter["summary"] = "Failed to generate summary for this section."
        return chapter


def summarize_transcript(video_info: Dict, transcript: List[Dict]) -> Dict:
    """
    Summarize a transcript using OpenAI GPT.

    Args:
        video_info: Dictionary containing video metadata
        transcript: List of transcript segments

    Returns:
        Dict containing chapter-based summaries
    """
    try:
        client = get_openai_client()

        # Extract or create chapters
        chapters = extract_chapters(transcript, video_info)

        # Create video context for the summarizer
        video_context = f"a YouTube video titled '{video_info['title']}' from the channel '{video_info['channel_name']}'"

        # Summarize each chapter
        summarized_chapters = []
        for chapter in chapters:
            summarized = summarize_chapter(client, chapter, video_context)
            summarized_chapters.append(summarized)

        return {"chapters": summarized_chapters}

    except Exception as e:
        logger.error(f"Failed to summarize transcript: {e!s}")
        raise SummarizerError(f"Summarization failed: {e!s}")


def generate_markdown_summary(video_info: Dict, summary_data: Dict) -> str:
    """
    Generate a markdown formatted summary.

    Args:
        video_info: Dictionary containing video metadata
        summary_data: Dictionary containing chapter summaries

    Returns:
        Markdown formatted string
    """
    markdown = f"# {video_info['title']}\n\n"
    markdown += f"Channel: {video_info['channel_name']}\n\n"
    markdown += f"Video: https://youtube.com/watch?v={video_info['video_id']}\n\n"
    markdown += "## Summary\n\n"

    for chapter in summary_data["chapters"]:
        timestamp_seconds = int(chapter["start"])
        timestamp = format_timestamp(timestamp_seconds)
        timestamp_url = f"https://youtube.com/watch?v={video_info['video_id']}&t={timestamp_seconds}"

        markdown += f"### [{chapter['title']}]({timestamp_url}) ({timestamp})\n\n"
        markdown += f"{chapter['summary']}\n\n"

    return markdown
