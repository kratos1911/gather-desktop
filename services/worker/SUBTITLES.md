# Caption parsing contract

`parse_subtitles(payload: bytes, format: "srt" | "vtt")` returns ordered
`{start, end, text}` cues for the existing yt-dlp output adapter. No fetching.

Supported subset: strict UTF-8, optional BOM, CR/LF normalization, numbered SRT
or optional VTT cue identifiers, millisecond timestamps, multiline text, overlapping
cues, VTT header metadata and NOTE/STYLE/REGION blocks. VTT layout settings are
ignored. Display tags/inline timestamps are stripped before entity decoding.
Decoded text must always be rendered as text, never trusted HTML.

Bounds: 128 KiB input, 1000 cues, 8 KiB UTF-8 per cue, 64 KiB joined text.
Malformed timing, unordered starts, invalid encoding, control characters and
unsupported formats raise content-free ValueError codes. No partial cue list
is returned. Empty caption tracks return an empty list, not invented speech.

This is not complete WebVTT conformance. Styling/regions/voice markup are not
retained as presentation, speaker identity is not inferred, and repeated rolling
captions are not deduplicated. JSON3, TTML, ASS and legacy SRT encodings are not
supported. The future runner must explicitly select compatible caption formats.

Parser version: subtitle-text-v1. The future runner must record this alongside
backend version and source/subtitle provenance when storing parsed artifacts.
Current integration is synthetic tests only; no caption file has been downloaded.

Reference: https://www.w3.org/TR/webvtt1/
