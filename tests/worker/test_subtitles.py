import unittest
from services.worker.subtitles import parse_subtitles, MAX_BYTES
from services.worker.extraction_adapters import ytdlp_passages


class SubtitleTests(unittest.TestCase):
    def test_srt_bom_crlf_multiline(self):
        cues = parse_subtitles('\ufeff1\r\n00:01:02,345 --> 00:01:04,000\r\nHello\r\nworld\r\n'.encode(), 'srt')
        self.assertEqual(cues, [{"start": 62.345, "end": 64.0, "text": "Hello\nworld"}])

    def test_vtt_settings_markup_and_comments(self):
        source = b'WEBVTT\n\nNOTE not spoken\nignore\n\nSTYLE\n::cue { color: red; }\n\ncue-a\n00:01.000 --> 00:03.000 align:start\n<v Ada><b>Tea</b> &amp; coffee <00:02.000>now\n'
        self.assertEqual(parse_subtitles(source, 'vtt')[0]['text'], 'Tea & coffee now')

    def test_overlap_and_repetition_preserved(self):
        source = b'WEBVTT\n\n00:01.000 --> 00:04.000\nHello\n\n00:02.000 --> 00:05.000\nHello'
        self.assertEqual(len(parse_subtitles(source, 'vtt')), 2)

    def test_malformed_times_and_missing_separator(self):
        for source in [b'1\n00:61:00,000 --> 00:62:00,000\nx', b'1\n00:00:02,000 --> 00:00:01,000\nx', b'1\n00:00:01,000 --> 00:00:02,000\nx\n2\n00:00:03,000 --> 00:00:04,000\ny']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse_subtitles(source, 'srt')

    def test_invalid_encoding_header_and_limits(self):
        for payload, format in [(b'\xff', 'srt'), (b'not vtt', 'vtt'), (b'x'*(MAX_BYTES+1), 'srt'), (b'', 'ass')]:
            with self.subTest(format=format), self.assertRaises(ValueError):
                parse_subtitles(payload, format)
        with self.assertRaisesRegex(ValueError, 'SUBTITLE_OUTPUT_LIMIT'):
            parse_subtitles(b'1\n00:00:01,000 --> 00:00:02,000\n'+b'x'*8193, 'srt')

    def test_escaped_tags_remain_plain_text(self):
        cue = parse_subtitles(b'WEBVTT\n\n00:01.000 --> 00:02.000\n&lt;b&gt;literal&lt;/b&gt;', 'vtt')[0]
        self.assertEqual(cue['text'], '<b>literal</b>')

    def test_subtitle_to_passage_integration(self):
        cues = parse_subtitles(b'WEBVTT\n\n00:10.000 --> 00:12.000\nWaterproof jacket', 'vtt')
        result = ytdlp_passages('a', 'https://example.com/video', {'title':'Camping'}, cues=cues, language='en', backend_version='fixture', fetched_at='2026-09-30T00:00:00Z')
        chunk = next(c for c in result['chunks'] if c['evidence_type']=='subtitle')
        self.assertEqual(chunk['cue_spans'][0]['start_seconds'], 10)
        self.assertEqual(chunk['text'], 'Waterproof jacket')

    def test_empty_captions(self):
        self.assertEqual(parse_subtitles(b'WEBVTT\n\nNOTE no captions', 'vtt'), [])


if __name__ == '__main__':
    unittest.main()
