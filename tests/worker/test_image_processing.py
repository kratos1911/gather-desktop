"""Synthetic output/security contracts; real OCR is checked separately in Linux."""
import copy
import hashlib
import math
import unittest
from unittest.mock import patch, Mock
import base64

from services.worker.image_processing import (
    ImageError, MODEL_SHA256, MAX_BYTES, dimensions, from_tsv,
    validate_bytes, validate_document,
)

# Header-only adapter bytes are deliberately not a decodable image.
RAW = b'\x89PNG\r\n\x1a\nadapter-fixture'
HEADER = 'level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'


def row(text='Orchard', line=1, word=1, x=5, confidence='96.5'):
    return f'5\t1\t1\t1\t{line}\t{word}\t{x}\t5\t30\t15\t{confidence}\t{text}\n'


class ImageContracts(unittest.TestCase):
    def document(self):
        return from_tsv(HEADER + row('café') + row('backups', line=2), RAW, 100, 50)

    def test_actual_size_type_and_pixel_bounds(self):
        for raw, code in ((b'', 'image_size'), (b'x'*(MAX_BYTES+1), 'image_size'),
                          (b'<svg/>', 'image_invalid'), ('PNG', 'image_size')):
            with self.subTest(code=code):
                with self.assertRaisesRegex(ImageError, '^'+code+'$'):
                    validate_bytes(raw)
        for size in ((True, 20), (0, 10), (4097, 1), (2048, 2048)):
            with self.assertRaisesRegex(ImageError, '^image_dimensions$'):
                dimensions(*size)

    def test_offsets_boxes_confidence_and_identities(self):
        result = self.document()
        self.assertEqual(result['body'], 'café\n\nbackups')
        self.assertEqual([(r['start'], r['end']) for r in result['regions']], [(0, 6), (6, 13)])
        self.assertEqual(result['regions'][0]['confidence'], 96.5)
        self.assertEqual(result['ocr_model_sha256'], MODEL_SHA256)
        self.assertEqual(result['source_sha256'], hashlib.sha256(RAW).hexdigest())
        self.assertNotEqual(result['source_sha256'], result['text_sha256'])
        self.assertEqual(validate_document(result, RAW), result)

    def test_multiword_line_preserves_complete_box_and_low_confidence(self):
        value = from_tsv(HEADER+row('Archive', x=5, confidence='0')+
                         row('requests', word=2, x=45, confidence='80'), RAW, 100, 50)
        self.assertEqual(value['body'], 'Archive requests')
        self.assertEqual(value['regions'][0]['width'], 70)
        self.assertEqual(value['regions'][0]['confidence'], 40)

    def test_literal_quotes_are_not_treated_as_csv_escaping(self):
        value=from_tsv(HEADER+row('"quoted"'),RAW,100,50)
        self.assertEqual(value['body'],'"quoted"')

    def test_no_text_and_excess_regions_are_truthful_failures(self):
        with self.assertRaisesRegex(ImageError, '^image_text_required$'):
            from_tsv(HEADER, RAW, 100, 50)
        with self.assertRaisesRegex(ImageError, '^image_region_limit$'):
            from_tsv(HEADER+''.join(row(line=i) for i in range(1,130)), RAW, 100, 50)

    def test_invalid_output_never_becomes_evidence(self):
        for tsv in ('text only', HEADER+row(confidence='nan'), HEADER+row(confidence='101'),
                    HEADER+row(x=90), HEADER+row(text='bad\x00text')):
            with self.subTest(tsv=repr(tsv[:30])):
                with self.assertRaisesRegex(ImageError, '^image_invalid_output$'):
                    from_tsv(tsv, RAW, 100, 50)

    def test_tampered_hash_model_offsets_and_geometry_rejected(self):
        mutations = (
            lambda d: d.update(source_sha256='0'*64),
            lambda d: d.update(text_sha256='0'*64),
            lambda d: d.update(ocr_model_sha256='0'*64),
            lambda d: d.update(media_type='image/jpeg'),
            lambda d: d['regions'][0].update(start=1),
            lambda d: d['regions'][0].update(x=-1),
            lambda d: d['regions'][0].update(confidence=math.inf),
            lambda d: d['regions'][0].update(confidence=True),
        )
        for change in mutations:
            value=copy.deepcopy(self.document());change(value)
            with self.assertRaisesRegex(ImageError, '^image_invalid_output$'):
                validate_document(value, RAW)

    def test_frame_stays_light_and_server_capability_is_authoritative(self):
        from services.worker.library_api import validate
        from scripts.operator_library import PilotSession
        from services.worker.library_session import LibraryError
        with patch('services.worker.ingestion.extract_image', side_effect=AssertionError('pre-auth OCR')):
            validate('/v1/import',dict(request_id='00000000-0000-0000-0000-000000000001',
                title='fixture.png',media='image/png',content_base64=base64.b64encode(RAW).decode()))
        session=object.__new__(PilotSession);session.text_files=True
        with patch('scripts.operator_library.parse', side_effect=AssertionError('disabled OCR')):
            with self.assertRaisesRegex(LibraryError,'file_import_disabled'):
                session._validate_import_scope(RAW,'image/png',True)

    def test_coordinator_uses_existing_publication_and_stages_ocr_provenance(self):
        from tests.worker.test_ingestion import MemoryRepository, SyntheticProvider
        from services.worker.ingestion import run_once
        from services.worker.image_processing import PARSER_VERSION
        document=self.document();repo=MemoryRepository();repo.raw=RAW
        repo.job.update(media_type='image/png',parser_version=PARSER_VERSION,input_bytes=len(RAW),
                        content_sha256=document['source_sha256'])
        with patch('services.worker.ingestion.extract_image',return_value=document):
            result=run_once(repo,SyntheticProvider())
        self.assertEqual(result['state'],'ready')
        staged=[args for name,args in repo.calls if name=='stage_image'][0]
        self.assertEqual(staged[2:4],(RAW,document['body']))
        self.assertEqual(staged[4]['regions'],document['regions'])

    def test_parser_timeout_is_retryable_and_never_calls_embedding(self):
        from tests.worker.test_ingestion import MemoryRepository, SyntheticProvider
        from services.worker.ingestion import run_once
        from services.worker.image_processing import PARSER_VERSION
        repo=MemoryRepository();repo.raw=RAW
        repo.job.update(media_type='image/png',parser_version=PARSER_VERSION,input_bytes=len(RAW),
                        content_sha256=hashlib.sha256(RAW).hexdigest())
        provider=SyntheticProvider();provider.infer=Mock()
        with patch('services.worker.ingestion.extract_image',side_effect=ImageError('image_timeout')):
            result=run_once(repo,provider)
        self.assertEqual(result['error_code'],'timeout');provider.infer.assert_not_called()
        self.assertNotIn('publish_text',[name for name,_ in repo.calls])

    def test_context_cites_regions_and_rejects_cross_owner_or_changed_text(self):
        from dataclasses import replace
        from services.worker.search_context import Snapshot, Passage, Hit, assemble_context
        document=self.document()
        source=Snapshot('u','s','v',document['source_sha256'],document['body'],
            (Passage('p',6,len(document['body'])),),media_type='image/png',
            text_sha256=document['text_sha256'],image_regions=tuple(document['regions']),image_dimensions=(100,50))
        result=assemble_context('u',[Hit('u','s','v','p')],[source])
        self.assertEqual(result['windows'][0]['ocr_regions'],[2])
        for item in (replace(source,owner_id='other'),replace(source,text_sha256='0'*64)):
            with self.assertRaises(ValueError):assemble_context('u',[Hit('u','s','v','p')],[item])

    def test_open_original_binds_bytes_to_owned_version_and_stale_reads_disappear(self):
        from services.worker.image_processing import attach_original
        document=self.document()
        self.assertEqual(attach_original(lambda *args:None,'s','v',[document]),[])
        original=dict(media_type='image/png',source_sha256=document['source_sha256'],
                      content_base64=base64.b64encode(RAW).decode())
        self.assertEqual(attach_original(lambda *args:original,'s','v',[document])[0]['image_base64'],original['content_base64'])
        original['source_sha256']='0'*64
        with self.assertRaises(ImageError):attach_original(lambda *args:original,'s','v',[document])


if __name__ == '__main__':
    unittest.main()
