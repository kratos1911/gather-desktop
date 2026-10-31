"""Owned generated PDF fixtures only. No OCR, inference or user documents."""
import hashlib
import io
import sys
import threading
import unittest
from unittest.mock import patch
from services.worker.pdf_processing import (_extract,extract_pdf,validate_document,enrich_published,PDFError,PARSER_VERSION)
from services.worker.search_context import Snapshot,Passage,Hit,assemble_context


def fixture(pages=('Orchard backups are kept for fourteen days.','Archive requests belong on page two.'),encrypted=False):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
    writer=PdfWriter()
    for text in pages:
        page=writer.add_blank_page(width=400,height=400)
        if text is not None:
            font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
            stream=DecodedStreamObject()
            escaped=text.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            stream.set_data(('BT /F1 12 Tf 30 300 Td ('+escaped+') Tj ET').encode('ascii'))
            page[NameObject('/Contents')]=writer._add_object(stream)
    if encrypted: writer.encrypt('not-a-user-password',algorithm='RC4-128')
    out=io.BytesIO();writer.write(out);return out.getvalue()


class PDFProcessingTests(unittest.TestCase):
    def test_exact_page_offsets_hashes_and_deterministic_result(self):
        raw=fixture(); doc=_extract(raw)
        self.assertEqual(doc,_extract(raw))
        self.assertEqual(doc['source_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(doc['parser_version'],PARSER_VERSION)
        self.assertEqual([p['number'] for p in doc['pages']],[1,2])
        self.assertEqual(''.join(doc['body'][p['start']:p['end']] for p in doc['pages']),doc['body'])
        self.assertIn('page two',doc['body'][doc['pages'][1]['start']:])
        self.assertNotEqual(doc['source_sha256'],doc['text_sha256'])
    def test_encrypted_scanned_empty_and_too_many_pages_are_not_partial_success(self):
        for raw,code in ((fixture(encrypted=True),'pdf_encrypted'),(fixture((None,)),'pdf_text_required'),(fixture(tuple('x' for _ in range(21))),'pdf_page_limit')):
            with self.subTest(code=code),self.assertRaisesRegex(PDFError,code): _extract(raw)
    def test_page_and_hash_tampering_rejected(self):
        raw=fixture();doc=_extract(raw)
        for field,value in (('source_sha256','0'*64),('text_sha256','0'*64),('pages',[{'number':2,'start':0,'end':len(doc['body'])}])):
            with self.subTest(field=field),self.assertRaises(PDFError): validate_document(dict(doc,**{field:value}),raw)
    def test_size_signature_and_trailer_rejections(self):
        from services.worker.pdf_processing import validate_bytes
        for raw in (b'not a PDF',b'%PDF-1.7\nmissing trailer',fixture()+b'active trailing bytes',b'%PDF-1.7\n'+b'x'*65536+b'%%EOF\n'):
            with self.assertRaises(PDFError): validate_bytes(raw)
    def test_context_retains_raw_identity_and_returns_correct_page_numbers(self):
        raw=fixture();doc=_extract(raw);p=doc['pages'][1]
        source=Snapshot('owner','source','version',doc['source_sha256'],doc['body'],(Passage('p',p['start'],p['end']),),
            text_sha256=doc['text_sha256'],media_type='application/pdf',pages=tuple((p['number'],p['start'],p['end']) for p in doc['pages']))
        window=assemble_context('owner',[Hit('owner','source','version','p')],[source])['windows'][0]
        self.assertEqual(window['pages'],[2]);self.assertEqual(window['source_sha256'],doc['source_sha256'])
        self.assertIn('page two',window['text'])
    def test_admission_frame_never_runs_pdf_extraction(self):
        import base64
        from services.worker.library_api import validate
        with patch('services.worker.ingestion.extract_pdf',side_effect=AssertionError('pre-auth parser')):
            request=validate('/v1/import',dict(request_id='00000000-0000-0000-0000-000000000001',title='fixture.pdf',media='application/pdf',content_base64=base64.b64encode(fixture()).decode()))
        self.assertIn('original',request)
    def test_existing_coordinator_uses_binary_original_and_page_staging(self):
        from tests.worker.test_ingestion import MemoryRepository,SyntheticProvider
        from services.worker.ingestion import run_once
        repo=MemoryRepository();repo.raw=fixture();doc=_extract(repo.raw)
        repo.job.update(media_type='application/pdf',parser_version=PARSER_VERSION,input_bytes=len(repo.raw),content_sha256=doc['source_sha256'])
        with patch('services.worker.ingestion.extract_pdf',return_value=doc):result=run_once(repo,SyntheticProvider())
        self.assertEqual(result['state'],'ready')
        stage=[args for name,args in repo.calls if name=='stage_pdf'][0]
        self.assertEqual(stage[2:5],(repo.raw,doc['body'],doc['pages']))
        self.assertNotIn('stage_text',[name for name,args in repo.calls])
    def test_changed_original_stops_before_embedding_and_publication(self):
        from tests.worker.test_ingestion import MemoryRepository,SyntheticProvider
        from services.worker.ingestion import run_once
        repo=MemoryRepository();repo.raw=fixture();doc=_extract(repo.raw)
        repo.job.update(media_type='application/pdf',parser_version=PARSER_VERSION,input_bytes=len(repo.raw),content_sha256='0'*64)
        provider=SyntheticProvider()
        with patch('services.worker.ingestion.extract_pdf',return_value=doc),patch.object(provider,'infer',side_effect=AssertionError('inference before integrity')):
            result=run_once(repo,provider)
        self.assertEqual(result['error_code'],'invalid_input')
        self.assertNotIn('publish_text',[name for name,args in repo.calls])
    def test_deleted_metadata_discards_open_and_tampered_pages_fail_closed(self):
        raw=fixture();doc=_extract(raw)
        documents=[dict(doc,source_id='source',version_id='version')]
        self.assertEqual(enrich_published(lambda *a:None,'source','version',documents),[])
        metadata=dict(media_type='application/pdf',text_sha256=doc['text_sha256'],pages=[dict(number=1,start=1,end=len(doc['body']))])
        with self.assertRaises(PDFError):enrich_published(lambda *a:metadata,'source','version',documents)
    def test_server_feature_gate_rejects_pdf_before_parsing(self):
        from scripts.operator_library import PilotSession
        from services.worker.library_session import LibraryError
        session=object.__new__(PilotSession);session.text_files=True;session.pdf_files=False
        with patch('scripts.operator_library.parse',side_effect=AssertionError('disabled parser')):
            with self.assertRaisesRegex(LibraryError,'file_import_disabled'):
                session._validate_import_scope(fixture(),'application/pdf',True)
    @unittest.skipUnless(sys.platform=='linux','Resource-limited production helper is Linux-only; fixture extraction above is not its proof.')
    def test_real_resource_limited_helper_and_cancellation(self):
        raw=fixture();self.assertEqual(extract_pdf(raw),_extract(raw))
        cancel=threading.Event();cancel.set()
        with self.assertRaisesRegex(PDFError,'pdf_cancelled'):extract_pdf(raw,cancel=cancel)


if __name__=='__main__':unittest.main()
