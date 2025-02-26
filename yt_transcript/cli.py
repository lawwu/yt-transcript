"""CLI interface for the YouTube transcript tool."""

import logging

import click

from . import transcript_fetcher
from .summarizer import generate_markdown_summary, summarize_transcript

# Configure logging
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.argument("url", required=False)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.option(
    "--no-cache", is_flag=True, help="Bypass cache and fetch fresh transcript"
)
@click.option("--summarize", is_flag=True, help="Generate a summary of the transcript")
@click.option("--markdown", is_flag=True, help="Output summary in markdown format")
@click.option(
    "--output-file",
    "-o",
    help="Output file path for summary (default: {video_id}_summary.md for markdown)",
)
@click.option(
    "--no-save-transcript", is_flag=True, help="Do not save transcript to a text file"
)
@click.option(
    "--transcript-file",
    help="Output file path for transcript (default: {video_id}_transcript.txt)",
)
@click.option("--chapters", is_flag=True, help="Display chapters for the video")
def yt_transcript_cli(
    url,
    verbose,
    no_cache,
    summarize,
    markdown,
    output_file,
    no_save_transcript,
    transcript_file,
    chapters,
):
    """YouTube Transcript CLI - fetch and process YouTube video transcripts.

    Provide a YouTube URL or video ID to fetch its transcript.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    if not url:
        click.echo("Welcome to YouTube Transcript CLI!")
        click.echo("Please provide a YouTube URL or video ID to fetch a transcript.")
        click.echo("Use --help to see available options.")
        return

    try:
        # Extract video ID from URL
        if "youtube.com" in url or "youtu.be" in url:
            if "youtube.com/watch?v=" in url:
                video_id = url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            else:
                raise ValueError("Invalid YouTube URL format")
        else:
            # Assume the input is already a video ID
            video_id = url

        fetcher = transcript_fetcher.TranscriptFetcher()

        # If chapters flag is set, just display chapters and exit
        if chapters:
            video_info = fetcher.get_video_info(video_id)

            if video_info["chapters"]:
                click.echo(f"\nFound {len(video_info['chapters'])} chapters in video:")
                for chapter in video_info["chapters"]:
                    click.echo(f"\n{chapter['title']}")
                    click.echo(f"Start: {chapter['start']} seconds")
                    click.echo(f"End: {chapter['end']} seconds")
            else:
                click.echo("No chapters found in video")
            return

        # Otherwise, fetch transcript
        logger.info(f"Fetching transcript for video ID: {video_id}")
        transcript = fetcher.fetch_transcript(video_id, no_cache=no_cache)

        if not transcript:
            logger.error("No transcript found for this video")
            return

        # Save transcript to file by default unless --no-save-transcript is specified
        if not no_save_transcript:
            if not transcript_file:
                transcript_file = f"{video_id}_transcript.txt"

            with open(transcript_file, "w", encoding="utf-8") as f:
                for segment in transcript:
                    f.write(f"[{segment['start']:.1f}s] {segment['text']}\n")
            logger.info(f"Transcript saved to {transcript_file}")

        # Print each line of the transcript with timestamp
        for segment in transcript:
            click.echo(f"[{segment['start']:.1f}s] {segment['text']}")

        # After fetching transcript, handle summarization
        if summarize:
            logger.info("Generating summary...")
            # Get complete video info including chapters
            video_info = fetcher.get_video_info(video_id)
            summary = summarize_transcript(video_info, transcript)

            if markdown:
                md_summary = generate_markdown_summary(video_info, summary)

                # Determine output file path
                if not output_file:
                    output_file = f"{video_id}_summary.md"

                # Write to file
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(md_summary)
                logger.info(f"Markdown summary written to {output_file}")

                # Also print to console
                print(md_summary)
            else:
                # Print simple text summary
                for chapter in summary["chapters"]:
                    print(f"\n{chapter['title']}:")
                    print(f"{chapter['summary']}")

    except ValueError as e:
        logger.error(f"Error parsing URL: {e!s}")
    except Exception as e:
        logger.error(f"Failed to fetch transcript: {e!s}")


if __name__ == "__main__":
    yt_transcript_cli()
