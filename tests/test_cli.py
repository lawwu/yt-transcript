"""Tests for the CLI interface."""
from click.testing import CliRunner
from yt_transcript.cli import yt_transcript_cli

def test_help():
    """Test that --help runs without error and returns help text."""
    runner = CliRunner()
    result = runner.invoke(yt_transcript_cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'YouTube Transcript CLI' in result.output

def test_main_command(caplog):
    """Test that the main command runs and displays greeting."""
    runner = CliRunner()
    result = runner.invoke(yt_transcript_cli, ['main'])
    assert result.exit_code == 0
    assert 'Welcome to YouTube Transcript CLI!' in result.output

def test_verbose_flag(caplog):
    """Test that --verbose enables debug logging."""
    runner = CliRunner()
    result = runner.invoke(yt_transcript_cli, ['--verbose', 'main'])
    assert result.exit_code == 0
    assert 'Verbose logging enabled' in caplog.text 