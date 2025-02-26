# yt-transcript

A command-line tool to fetch, cache, and summarize YouTube video transcripts. Optionally generate AI-powered summaries.

## Features

- 📝 Fetch official or auto-generated YouTube transcripts
- 💾 Cache transcripts locally to avoid repeated network calls
- 🤖 Generate AI-powered summaries using OpenAI GPT
- 🎯 Extract or generate chapter markers
- 📋 Export to JSON or Markdown formats

## Installation

```bash
pip install yt-transcript
```

Set `OPENAI_API_KEY` environment variable
```bash
export OPENAI_API_KEY=<your-openai-api-key>
```

## Examples

Fetch transcript

```bash
yt-transcript https://www.youtube.com/watch?v=7xTGNNLPyMI

yt-transcript https://www.youtube.com/watch?v=IziXJt5iUHo
```

Fetch transcript and summarize (videos that have chapters)
```bash
yt-transcript https://www.youtube.com/watch?v=7xTGNNLPyMI --summarize --markdown

yt-transcript https://www.youtube.com/watch?v=IziXJt5iUHo --summarize --markdown
```

Fetch transcript and summarize (videos that don't have chapters)
```bash
yt-transcript https://www.youtube.com/watch?v=f0RbwrBcFmc&ab_channel=LangChain --summarize --markdown
```

## TODO

- [ ] Add local Whisper transcription fallback if no transcript is available
- [x] Remove fetch keyword