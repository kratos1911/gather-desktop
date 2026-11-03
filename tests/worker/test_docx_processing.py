"""Generated nonsensitive OOXML only; synthetic vectors never prove live search."""
import base64
import hashlib
import io
import sys
import threading
import unittest
import warnings
import zipfile
from unittest.mock import patch
from xml.sax.saxutils import escape

from services.worker.docx_processing import (
    DOCXError, MEDIA, PARSER_VERSION, W, _extract, extract_docx, enrich_published, validate_document,
)


def fixture(paragraphs=('Orchard backups last fourteen days.', 'Archive requests belong in the Cedar queue.'),
            extra=None, document=None):
    types = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>')
    rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>')
    body = ''.join('<w:p><w:r><w:t>' + escape(text) + '</w:t></w:r></w:p>' for text in paragraphs)
    xml = document or ('<w:document xmlns:w="' + W[1:-1] + '"><w:body>' + body + '</w:body></w:document>')
    parts = {'[Content_Types].xml': types, '_rels/.rels': rels, 'word/document.xml': xml, **(extra or {})}
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
    return output.getvalue()


class DOCXProcessingTests(unittest.TestCase):
    def test_deterministic_unicode_offsets_and_separate_hashes(self):
        raw = fixture(('Résumé 😀', 'Two <three> & four'))
        doc = _extract(raw)
        self.assertEqual(doc, _extract(raw))
        self.assertEqual(doc['body'], 'Résumé 😀\n\nTwo <three> & four')
        self.assertEqual(doc['paragraphs'], [dict(number=1, start=0, end=10), dict(number=2, start=10, end=len(doc['body']))])
        self.assertEqual(doc['source_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(doc['source_sha256'], doc['text_sha256'])

    def test_tables_runs_tabs_and_line_breaks_keep_order(self):
        document = ('<w:document xmlns:w="' + W[1:-1] + '"><w:body>'
            '<w:p><w:r><w:t>First</w:t><w:tab/><w:t>value</w:t><w:br/><w:t>next</w:t></w:r></w:p>'
            '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
            '</w:body></w:document>')
        self.assertEqual(_extract(fixture(document=document))['body'], 'First\tvalue\nnext\n\nCell')

    def test_generic_zip_traversal_duplicates_and_oversized_parts_rejected(self):
        for raw in (b'PK\x03\x04not a zip', fixture(extra={'../outside.xml': '<x/>'}),
                    fixture(extra={'big.xml': 'x' * 524289}), fixture(paragraphs=tuple('x' for _ in range(129)))):
            with self.subTest(size=len(raw)), self.assertRaises(DOCXError):
                _extract(raw)
        out = io.BytesIO(fixture())
        with warnings.catch_warnings(), zipfile.ZipFile(out, 'a') as archive:
            warnings.simplefilter('ignore', UserWarning)
            archive.writestr('word/document.xml', '<duplicate/>')
        with self.assertRaises(DOCXError):
            _extract(out.getvalue())

    def test_macros_active_relationships_entities_and_tracked_changes_rejected(self):
        external = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="x" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate" '
            'Target="https://example.invalid/no-fetch" TargetMode="External"/></Relationships>')
        dtd = '<!DOCTYPE w:document [<!ENTITY x "never expand">]>'
        for raw in (fixture(extra={'word/vbaProject.bin': b'not executed'}),
                    fixture(extra={'word/_rels/document.xml.rels': external}),
                    fixture(document=dtd + '<w:document xmlns:w="' + W[1:-1] + '"><w:body/></w:document>'),
                    fixture(document='<w:document xmlns:w="' + W[1:-1] + '"><w:body><w:ins/></w:body></w:document>')):
            with self.subTest(), self.assertRaises(DOCXError):
                _extract(raw)

    def test_xml_depth_text_and_paragraph_limits_fail_without_partial_output(self):
        for raw in (fixture(paragraphs=('', ' ')), fixture(paragraphs=('x' * 65537,)),
                    fixture(extra={'deep.xml': '<x>' * 65 + '</x>' * 65}),
                    fixture(extra={'dtd.xml': '<?xml version="1.0"?><!DOCTYPE x SYSTEM "file:///never-read"><x/>'})):
            with self.subTest(), self.assertRaises(DOCXError):
                _extract(raw)

    def test_large_passive_style_parts_fit_but_total_expansion_remains_bounded(self):
        style = lambda size: '<w:styles xmlns:w="' + W[1:-1] + '">' + ' ' * size + '</w:styles>'
        raw = fixture(extra={'word/styles.xml': style(349000), 'word/stylesWithEffects.xml': style(438000)})
        self.assertEqual(_extract(raw)['body'], _extract(fixture())['body'])
        oversized = fixture(extra={f'part{n}.xml': style(400000) for n in range(3)})
        with self.assertRaisesRegex(DOCXError, 'docx_archive_limit'):
            _extract(oversized)
        with self.assertRaisesRegex(DOCXError, 'docx_archive_limit'):
            _extract(fixture(extra={'large.xml': style(524289)}))

    def test_nested_paragraphs_simple_fields_and_alternate_content_are_not_duplicated(self):
        for body in (
            '<w:p><w:p><w:r><w:t>nested</w:t></w:r></w:p></w:p>',
            '<w:p><w:fldSimple w:instr="DDE unused"><w:r><w:t>cached</w:t></w:r></w:fldSimple></w:p>',
            '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"/>',
        ):
            xml = '<w:document xmlns:w="' + W[1:-1] + '"><w:body>' + body + '</w:body></w:document>'
            with self.subTest(body=body), self.assertRaises(DOCXError):
                _extract(fixture(document=xml))

    def test_tampered_metadata_and_late_replacement_fail_closed(self):
        raw = fixture()
        doc = _extract(raw)
        with self.assertRaises(DOCXError):
            validate_document(dict(doc, paragraphs=[dict(number=1, start=1, end=len(doc['body']))]), raw)
        docs = [dict(doc)]
        self.assertEqual(enrich_published(lambda *a: None, 'source', 'version', docs), [])
        with self.assertRaises(DOCXError):
            enrich_published(lambda *a: dict(media_type=MEDIA, text_sha256='0'*64, paragraphs=doc['paragraphs']), 's', 'v', docs)

    def test_frame_does_not_parse_before_auth_and_trusted_gate_defaults_off(self):
        from services.worker.library_api import validate
        from scripts.operator_library import PilotSession
        from services.worker.library_session import LibraryError
        raw = fixture()
        with patch('services.worker.ingestion.extract_docx', side_effect=AssertionError('pre-auth parse')):
            validate('/v1/import', dict(request_id='00000000-0000-0000-0000-000000000001',
                title='fixture.docx', media=MEDIA, content_base64=base64.b64encode(raw).decode()))
        session = object.__new__(PilotSession)
        session.text_files = True
        with patch('scripts.operator_library.parse', side_effect=AssertionError('disabled parser')):
            with self.assertRaisesRegex(LibraryError, 'file_import_disabled'):
                session._validate_import_scope(raw, MEDIA, True)

    def test_coordinator_uses_existing_jobs_and_docx_staging(self):
        from tests.worker.test_ingestion import MemoryRepository, SyntheticProvider
        from services.worker.ingestion import run_once
        repo = MemoryRepository()
        repo.raw = fixture()
        doc = _extract(repo.raw)
        repo.job.update(media_type=MEDIA, parser_version=PARSER_VERSION, input_bytes=len(repo.raw), content_sha256=doc['source_sha256'])
        with patch('services.worker.ingestion.extract_docx', return_value=doc):
            result = run_once(repo, SyntheticProvider())
        self.assertEqual(result['state'], 'ready')
        stages = [args for name, args in repo.calls if name == 'stage_docx']
        self.assertEqual(stages[0][2:5], (repo.raw, doc['body'], doc['paragraphs']))

    def test_context_has_paragraph_citations_and_checks_exact_text_hash(self):
        from services.worker.search_context import Snapshot, Passage, Hit, assemble_context
        doc = _extract(fixture())
        item = doc['paragraphs'][1]
        source = Snapshot('u','s','v',doc['source_sha256'],doc['body'],
            (Passage('p',item['start'],item['end']),),media_type=MEDIA,text_sha256=doc['text_sha256'],
            paragraphs=tuple((p['number'],p['start'],p['end']) for p in doc['paragraphs']))
        window = assemble_context('u', [Hit('u','s','v','p')], [source])['windows'][0]
        self.assertEqual(window['paragraphs'], [2])
        self.assertNotIn('pages', window)
        from dataclasses import replace
        with self.assertRaises(ValueError):
            assemble_context('u', [Hit('u','s','v','p')], [replace(source, text_sha256='0'*64)])

    @unittest.skipUnless(sys.platform == 'linux', 'Production resource-limited parser requires Linux.')
    def test_real_limited_helper_cancellation_and_shared_extraction_slot(self):
        from services.worker.document_parser import SLOT
        raw = fixture()
        self.assertEqual(extract_docx(raw), _extract(raw))
        event = threading.Event()
        event.set()
        with self.assertRaisesRegex(DOCXError, 'docx_cancelled'):
            extract_docx(raw, cancel=event)
        self.assertTrue(SLOT.acquire(blocking=False))
        try:
            with self.assertRaisesRegex(DOCXError, 'docx_busy'):
                extract_docx(raw)
        finally:
            SLOT.release()


if __name__ == '__main__':
    unittest.main()
