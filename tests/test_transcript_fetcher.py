"""Tests for transcript fetching and caching."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled

from yt_transcript.transcript_fetcher import TranscriptFetcher


@pytest.fixture
def mock_cache_dir(tmp_path):
    """Create a temporary directory for cache files."""
    return tmp_path


@pytest.fixture
def mock_cache_file(mock_cache_dir):
    """Create a mock cache file with known content."""
    video_id = "test_video"
    cache_file = mock_cache_dir / f"{video_id}.json"
    mock_transcript = [
        {"start": 0.0, "duration": 5.0, "text": "Cached transcript line."}
    ]
    cache_file.write_text(json.dumps(mock_transcript))
    return video_id, cache_file


@pytest.fixture
def temp_cache_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def fetcher(temp_cache_dir):
    return TranscriptFetcher(cache_dir=temp_cache_dir)


@pytest.fixture
def mock_video_info():
    """Mock video info returned by yt-dlp"""
    return {
        "title": "Test Video",
        "uploader": "Test Channel",
        "chapters": [
            {"title": "Introduction", "start_time": 0, "end_time": 120},
            {"title": "Main Content", "start_time": 120, "end_time": 360},
            {"title": "Conclusion", "start_time": 360, "end_time": 480},
        ],
    }


def test_fetch_transcript_new(monkeypatch, mock_cache_dir):
    """Test fetching a new transcript when no cache exists."""
    # Mock the YouTube transcript API response
    mock_transcript = [
        {"text": "Mock transcript line 1.", "start": 0.0, "duration": 1.0},
        {"text": "Mock transcript line 2.", "start": 1.0, "duration": 1.0},
        {"text": "Mock transcript line 3.", "start": 2.0, "duration": 1.0},
    ]

    def mock_get_transcript(*args, **kwargs):
        return mock_transcript

    # Patch both the cache directory and the transcript API
    monkeypatch.setattr(
        "yt_transcript.transcript_fetcher.get_cache_dir", lambda: mock_cache_dir
    )
    monkeypatch.setattr(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        mock_get_transcript,
    )

    # Create an instance of TranscriptFetcher
    fetcher = TranscriptFetcher(cache_dir=mock_cache_dir)
    transcript = fetcher.fetch_transcript("new_video")

    assert len(transcript) == 3  # Our mock data has 3 lines
    assert transcript[0]["text"] == "Mock transcript line 1."

    # Verify it was cached
    cache_file = mock_cache_dir / "new_video.json"
    assert cache_file.exists()


def test_fetch_transcript_from_cache(monkeypatch, mock_cache_file):
    """Test loading a transcript from cache."""
    video_id, cache_file = mock_cache_file
    monkeypatch.setattr(
        "yt_transcript.transcript_fetcher.get_cache_dir", lambda: cache_file.parent
    )

    # Create an instance of TranscriptFetcher
    fetcher = TranscriptFetcher(cache_dir=cache_file.parent)
    transcript = fetcher.fetch_transcript(video_id)

    assert len(transcript) == 1
    assert transcript[0]["text"] == "Cached transcript line."


def test_fetch_transcript_no_cache(monkeypatch, mock_cache_file):
    """Test bypassing cache with no_cache flag."""
    video_id, cache_file = mock_cache_file

    # Mock the YouTube transcript API response
    mock_transcript = [
        {"text": "Mock transcript line 1.", "start": 0.0, "duration": 1.0},
        {"text": "Mock transcript line 2.", "start": 1.0, "duration": 1.0},
        {"text": "Mock transcript line 3.", "start": 2.0, "duration": 1.0},
    ]

    def mock_get_transcript(*args, **kwargs):
        return mock_transcript

    monkeypatch.setattr(
        "yt_transcript.transcript_fetcher.get_cache_dir", lambda: cache_file.parent
    )
    monkeypatch.setattr(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        mock_get_transcript,
    )

    fetcher = TranscriptFetcher(cache_dir=cache_file.parent)
    transcript = fetcher.fetch_transcript(video_id, no_cache=True)

    assert len(transcript) == 3  # Should get fresh mock data
    assert transcript[0]["text"] == "Mock transcript line 1."


def test_fetch_transcript_corrupted_cache(monkeypatch, mock_cache_dir):
    """Test handling of corrupted cache files."""
    video_id = "corrupted_video"
    cache_file = mock_cache_dir / f"{video_id}.json"
    cache_file.write_text("invalid json")

    # Mock the YouTube transcript API response
    mock_transcript = [
        {"text": "Mock transcript line 1.", "start": 0.0, "duration": 1.0},
        {"text": "Mock transcript line 2.", "start": 1.0, "duration": 1.0},
        {"text": "Mock transcript line 3.", "start": 2.0, "duration": 1.0},
    ]

    def mock_get_transcript(*args, **kwargs):
        return mock_transcript

    monkeypatch.setattr(
        "yt_transcript.transcript_fetcher.get_cache_dir", lambda: mock_cache_dir
    )
    monkeypatch.setattr(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        mock_get_transcript,
    )

    fetcher = TranscriptFetcher(cache_dir=mock_cache_dir)
    transcript = fetcher.fetch_transcript(video_id)

    assert len(transcript) == 3  # Should get fresh mock data
    assert transcript[0]["text"] == "Mock transcript line 1."


def test_fetch_transcript_success(fetcher):
    # Using a known YouTube video with transcripts
    video_id = "UNP03fDSj1U"  # This is a TED talk
    transcript = fetcher.fetch_transcript(video_id)

    assert isinstance(transcript, list)
    assert len(transcript) > 0
    assert all(isinstance(segment, dict) for segment in transcript)
    assert all("text" in segment for segment in transcript)
    assert all("start" in segment for segment in transcript)
    assert all("duration" in segment for segment in transcript)


def test_cache_functionality(fetcher, temp_cache_dir, monkeypatch):
    video_id = "test_video_id"

    # Mock transcript data
    mock_transcript = [
        {"text": "Test transcript", "start": 0.0, "duration": 1.0},
    ]

    def mock_get_transcript(*args, **kwargs):
        return mock_transcript

    # Mock the YouTube API calls
    monkeypatch.setattr(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        mock_get_transcript,
    )

    # First fetch - should save to cache
    transcript1 = fetcher.fetch_transcript(video_id)
    cache_file = os.path.join(temp_cache_dir, f"{video_id}.json")
    assert os.path.exists(cache_file)

    # Second fetch - should load from cache
    with open(cache_file) as f:
        cached_data = json.load(f)
    assert cached_data == transcript1


def test_invalid_video_id(fetcher):
    with pytest.raises((TranscriptsDisabled, NoTranscriptFound)):
        fetcher.fetch_transcript("invalid_video_id")


def test_get_video_info_with_chapters(mock_video_info):
    """Test fetching video info when chapters are available"""
    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        # Configure the mock
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_video_info
        )

        fetcher = TranscriptFetcher()
        video_info = fetcher.get_video_info("test123")

        assert video_info["title"] == "Test Video"
        assert video_info["channel_name"] == "Test Channel"
        assert video_info["video_id"] == "test123"
        assert len(video_info["chapters"]) == 3

        # Verify chapter structure
        first_chapter = video_info["chapters"][0]
        assert first_chapter["title"] == "Introduction"
        assert first_chapter["start"] == 0
        assert first_chapter["end"] == 120


def test_get_video_info_without_chapters():
    """Test fetching video info when no chapters are available"""
    mock_info = {"title": "Test Video", "uploader": "Test Channel", "chapters": None}

    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = (
            mock_info
        )

        fetcher = TranscriptFetcher()
        video_info = fetcher.get_video_info("test123")

        assert video_info["chapters"] == []


def test_get_video_info_handles_errors():
    """Test error handling when fetching video info fails"""
    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        mock_ydl.return_value.__enter__.return_value.extract_info.side_effect = (
            Exception("API Error")
        )

        fetcher = TranscriptFetcher()
        video_info = fetcher.get_video_info("test123")

        assert video_info["title"] == "Unknown Title"
        assert video_info["channel_name"] == "Unknown Channel"
        assert video_info["chapters"] == []


# def test_language_selection(fetcher, monkeypatch):
#     video_id = "test_video_id"

#     # Mock transcript data
#     mock_transcript_en = [
#         {"text": "English transcript", "start": 0.0, "duration": 1.0},
#     ]
#     mock_transcript_es = [
#         {"text": "Spanish transcript", "start": 0.0, "duration": 1.0},
#     ]

#     class MockTranscriptList:
#         def find_transcript(self, language_codes):
#             # Add print for debugging
#             print(f"Requested language codes: {language_codes}")
#             class MockTranscript:
#                 def fetch(self):
#                     # Check the first language code in the list
#                     return mock_transcript_en if language_codes[0] == 'en' else mock_transcript_es
#             return MockTranscript()

#     # Mock the YouTube API calls
#     monkeypatch.setattr(
#         'youtube_transcript_api.YouTubeTranscriptApi.list_transcripts',
#         lambda video_id: MockTranscriptList()  # Changed from lambda _ to lambda video_id for clarity
#     )

#     # Try fetching in English
#     transcript_en = fetcher.fetch_transcript(video_id, languages=['en'])  # Changed from language='en' to languages=['en']
#     assert isinstance(transcript_en, list)
#     assert len(transcript_en) > 0
#     assert transcript_en[0]["text"] == "English transcript"

#     # Try fetching in Spanish
#     transcript_es = fetcher.fetch_transcript(video_id, languages=['es'])  # Changed from language='es' to languages=['es']
#     assert isinstance(transcript_es, list)
#     assert len(transcript_es) > 0
#     assert transcript_es[0]["text"] == "Spanish transcript"
