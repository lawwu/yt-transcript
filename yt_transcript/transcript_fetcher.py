"""Module for fetching and caching YouTube transcripts."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import yt_dlp
from youtube_transcript_api import (
    NoTranscriptFound,
    YouTubeTranscriptApi,
)

logger = logging.getLogger(__name__)


class TranscriptFetcher:
    def __init__(self, cache_dir: str = "~/.yt-transcript-cache"):
        self.cache_dir = os.path.expanduser(cache_dir)
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

        # Configure yt-dlp
        self.ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,  # Don't download video
        }

    def _get_cache_path(self, video_id: str) -> str:
        return os.path.join(self.cache_dir, f"{video_id}.json")

    def _save_to_cache(self, video_id: str, transcript: List[Dict]) -> None:
        cache_path = self._get_cache_path(video_id)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        logger.debug(f"Saved transcript to cache: {cache_path}")

    def _load_from_cache(self, video_id: str) -> Optional[List[Dict]]:
        cache_path = self._get_cache_path(video_id)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, encoding="utf-8") as f:
                    transcript = json.load(f)
                    logger.debug(f"Loaded transcript from cache: {cache_path}")
                    return transcript
            except json.JSONDecodeError:
                logger.warning(f"Corrupted cache file found: {cache_path}")
                return None
        return None

    def fetch_transcript(
        self,
        video_id: str,
        use_cache: bool = True,
        language: str = None,
        no_cache: bool = False,
    ) -> List[Dict]:
        """
        Fetch transcript for a YouTube video.

        Args:
            video_id: The YouTube video ID
            use_cache: Whether to use cached transcripts
            language: Preferred language code (e.g., 'en', 'es'). If None, gets default.
            no_cache: If True, bypass cache and fetch fresh data

        Returns:
            List of transcript segments, each containing 'text', 'start', and 'duration'

        Raises:
            TranscriptsDisabled: If transcripts are disabled for the video
            NoTranscriptFound: If no transcript is available
        """
        if no_cache:
            use_cache = False

        if use_cache:
            cached = self._load_from_cache(video_id)
            if cached:
                return cached

        try:
            if language:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                try:
                    transcript = transcript_list.find_transcript([language])
                except NoTranscriptFound:
                    # Fallback to auto-translated version if available
                    try:
                        transcript = transcript_list.find_transcript(["en"]).translate(
                            language
                        )
                    except (NoTranscriptFound, Exception):
                        # If no English transcript or translation fails, try getting any available transcript
                        transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript = transcript.fetch()  # Actually fetch the transcript data
            else:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)

            if use_cache:
                self._save_to_cache(video_id, transcript)

            return transcript

        except Exception as e:
            logger.error(f"Error fetching transcript for video {video_id}: {e!s}")
            raise

    def get_video_info(self, video_id: str) -> Dict:
        """
        Get video metadata including chapters using yt-dlp.
        """
        try:
            url = f"https://youtube.com/watch?v={video_id}"
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Extract chapters if available
                chapters = []
                if info.get("chapters"):
                    chapters = [
                        {
                            "title": chapter["title"],
                            "start": chapter["start_time"],
                            "end": chapter["end_time"],
                        }
                        for chapter in info["chapters"]
                    ]

                return {
                    "title": info.get("title", "Unknown Title"),
                    "channel_name": info.get("uploader", "Unknown Channel"),
                    "video_id": video_id,
                    "chapters": chapters,
                }

        except Exception as e:
            logger.error(f"Error fetching video info: {e!s}")
            return {
                "title": "Unknown Title",
                "channel_name": "Unknown Channel",
                "video_id": video_id,
                "chapters": [],
            }


def get_cache_dir():
    """Get the directory path for caching transcripts."""
    cache_dir = Path.home() / ".cache" / "yt-transcript"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
