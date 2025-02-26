"""Tests for the summarizer module."""

from unittest.mock import Mock, patch

import pytest

from yt_transcript.summarizer import (
    extract_chapters,
    generate_markdown_summary,
    summarize_transcript,
)


@pytest.fixture
def sample_video_info():
    return {
        "title": "Test Video",
        "channel_name": "Test Channel",
        "video_id": "test123",
    }


@pytest.fixture
def sample_video_info_with_chapters():
    return {
        "title": "Test Video",
        "channel_name": "Test Channel",
        "video_id": "test123",
        "chapters": [
            {"title": "Introduction", "start": 0, "end": 120},
            {"title": "Main Content", "start": 120, "end": 360},
        ],
    }


@pytest.fixture
def sample_transcript():
    return [
        {"text": "First segment", "start": 0.0, "duration": 5.0},
        {"text": "Second segment", "start": 5.0, "duration": 5.0},
        {"text": "Middle segment", "start": 130.0, "duration": 5.0},
        {"text": "Last segment", "start": 350.0, "duration": 5.0},
    ]


def test_summarize_transcript(sample_video_info, sample_transcript):
    summary = summarize_transcript(sample_video_info, sample_transcript)

    assert "chapters" in summary
    assert len(summary["chapters"]) > 0

    for chapter in summary["chapters"]:
        assert "title" in chapter
        assert "summary" in chapter
        assert "start" in chapter
        assert "end" in chapter


def test_generate_markdown_summary(sample_video_info):
    summary_data = {
        "chapters": [
            {
                "title": "Test Chapter",
                "start": 0.0,
                "end": 300.0,
                "summary": "Test summary",
            }
        ]
    }

    markdown = generate_markdown_summary(sample_video_info, summary_data)

    # Check markdown structure
    assert sample_video_info["title"] in markdown
    assert sample_video_info["channel_name"] in markdown
    assert "Test Chapter" in markdown
    assert "Test summary" in markdown
    assert f"https://youtube.com/watch?v={sample_video_info['video_id']}" in markdown


def test_extract_chapters_with_youtube_chapters(
    sample_video_info_with_chapters, sample_transcript
):
    """Test chapter extraction when YouTube chapters are available"""
    chapters = extract_chapters(sample_transcript, sample_video_info_with_chapters)

    assert len(chapters) == 2
    assert chapters[0]["title"] == "Introduction"
    assert chapters[0]["start"] == 0
    assert chapters[0]["end"] == 120
    assert "First segment" in chapters[0]["text"]
    assert "Second segment" in chapters[0]["text"]

    assert chapters[1]["title"] == "Main Content"
    assert "Middle segment" in chapters[1]["text"]


def test_extract_chapters_fallback_to_segments(sample_transcript):
    """Test chapter extraction falls back to time segments when no chapters available"""
    video_info = {
        "title": "Test Video",
        "channel_name": "Test Channel",
        "video_id": "test123",
        "chapters": [],
    }

    chapters = extract_chapters(sample_transcript, video_info)

    assert len(chapters) > 0
    assert chapters[0]["title"].startswith("Section")
    assert "First segment" in chapters[0]["text"]


def test_summarize_transcript_with_chapters(
    sample_video_info_with_chapters, sample_transcript
):
    """Test full transcript summarization with chapters"""
    with patch("yt_transcript.summarizer.get_openai_client") as mock_get_client:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Summary: Test summary"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = summarize_transcript(
            sample_video_info_with_chapters, sample_transcript
        )

        assert len(result["chapters"]) == 2
        assert result["chapters"][0]["title"] == "Introduction"
        assert result["chapters"][0]["summary"] == "Test summary"
