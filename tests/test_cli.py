"""Tests for the CLI interface."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from yt_transcript.cli import yt_transcript_cli


def test_welcome_message():
    """Test that running without arguments displays the welcome message."""
    runner = CliRunner()
    result = runner.invoke(yt_transcript_cli)
    assert result.exit_code == 0
    assert "Welcome to YouTube Transcript CLI!" in result.output
    assert "Please provide a YouTube URL or video ID" in result.output


@patch("yt_transcript.transcript_fetcher.TranscriptFetcher")
def test_fetch_transcript(mock_fetcher_class):
    """Test fetching a transcript."""
    # Setup mock
    mock_fetcher = MagicMock()
    mock_fetcher_class.return_value = mock_fetcher
    mock_fetcher.fetch_transcript.return_value = [
        {"text": "Test transcript", "start": 0.0, "duration": 5.0}
    ]

    # Run command
    runner = CliRunner()
    result = runner.invoke(yt_transcript_cli, ["dQw4w9WgXcQ"])

    # Verify results
    assert result.exit_code == 0
    mock_fetcher.fetch_transcript.assert_called_once()
    assert "[0.0s] Test transcript" in result.output


@patch("yt_transcript.transcript_fetcher.TranscriptFetcher")
def test_chapters_flag(mock_fetcher_class):
    """Test the --chapters flag."""
    # Setup mock
    mock_fetcher = MagicMock()
    mock_fetcher_class.return_value = mock_fetcher
    mock_fetcher.get_video_info.return_value = {
        "chapters": [{"title": "Test Chapter", "start": 0, "end": 60}]
    }

    # Run command
    runner = CliRunner()
    result = runner.invoke(yt_transcript_cli, ["dQw4w9WgXcQ", "--chapters"])

    # Verify results
    assert result.exit_code == 0
    mock_fetcher.get_video_info.assert_called_once()
    assert "Found 1 chapters in video" in result.output
    assert "Test Chapter" in result.output


@patch("yt_transcript.transcript_fetcher.TranscriptFetcher")
def test_verbose_flag(mock_fetcher_class, caplog):
    """Test the --verbose flag."""
    # Setup mock
    mock_fetcher = MagicMock()
    mock_fetcher_class.return_value = mock_fetcher
    mock_fetcher.fetch_transcript.return_value = [
        {"text": "Test transcript", "start": 0.0, "duration": 5.0}
    ]

    # Run command with verbose flag
    runner = CliRunner()
    result = runner.invoke(yt_transcript_cli, ["dQw4w9WgXcQ", "--verbose"])

    # Verify results
    assert result.exit_code == 0
    assert "Verbose logging enabled" in caplog.text


@patch("yt_transcript.cli.summarize_transcript")
@patch("yt_transcript.transcript_fetcher.TranscriptFetcher")
def test_summarize_flag(mock_fetcher_class, mock_summarize):
    """Test the --summarize flag."""
    # Setup mocks
    mock_fetcher = MagicMock()
    mock_fetcher_class.return_value = mock_fetcher

    # Setup transcript mock
    mock_fetcher.fetch_transcript.return_value = [
        {"text": "Test transcript", "start": 0.0, "duration": 5.0}
    ]

    # Setup video info mock
    mock_fetcher.get_video_info.return_value = {
        "title": "Test Video",
        "channel_name": "Test Channel",
        "video_id": "dQw4w9WgXcQ",
        "chapters": [],
    }

    # Setup summarize mock
    mock_summarize.return_value = {
        "chapters": [
            {"title": "Summary", "summary": "This is a summary", "start": 0, "end": 60}
        ]
    }

    # Run command with summarize flag
    runner = CliRunner()
    result = runner.invoke(yt_transcript_cli, ["dQw4w9WgXcQ", "--summarize"])

    # Verify results
    assert result.exit_code == 0
    mock_summarize.assert_called_once()
    assert "Summary" in result.output
    assert "This is a summary" in result.output
