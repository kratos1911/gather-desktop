"""Pinned PDF-to-text contract. No OCR, rendering, URLs or model calls.

Production extraction runs in a disposable Linux process with hard resource
limits. This is a parser process boundary, not a filesystem/network sandbox.
"""
import hashlib
import io
import json
import logging
from pathlib import Path
import re
import sys

PYPDF_VERSION = '6.21.4'
PARSER_VERSION = 'pdf-pypdf6.21.4-text-v1'
MAX_BYTES = 65536
MAX_PAGES = 20
MAX_STREAM_BYTES = 262144
MAX_REPLY_BYTES = 524288
WALL_SECONDS = 5


class PDFError(ValueError):
    """Fixed content-free diagnostic."""


def validate_bytes(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise PDFError('pdf_size')
    if not re.match(rb'%PDF-(?:1\.[0-7]|2\.0)[\r\n]', raw) or not re.search(rb'%%EOF[\x09\x0a\x0c\x0d\x20]*\Z', raw):
        raise PDFError('pdf_invalid')


def validate_text(body,pages,text_sha256):
    if (not isinstance(body,str)
            or not body.strip() or len(body.encode('utf-8')) > MAX_BYTES
            or any((ord(c)<32 and c not in '\t\r\n') or 127<=ord(c)<=159 for c in body)
            or text_sha256 != hashlib.sha256(body.encode('utf-8')).hexdigest()):
        raise PDFError('pdf_invalid_output')
    if type(pages) is not list or not 1<=len(pages)<=MAX_PAGES:
        raise PDFError('pdf_invalid_output')
    previous = 0
    for number, page in enumerate(pages,1):
        if (type(page) is not dict or set(page)!={'number','start','end'}
                or any(type(page[k]) is not int for k in page)
                or page['number']!=number or page['start']!=previous
                or not previous<page['end']<=len(body)):
            raise PDFError('pdf_invalid_output')
        previous = page['end']
    if previous != len(body): raise PDFError('pdf_invalid_output')
    return pages


def validate_document(value, raw):
    validate_bytes(raw)
    if (type(value) is not dict or set(value) != {'source_sha256','text_sha256','parser_version','body','pages'}
            or value['source_sha256']!=hashlib.sha256(raw).hexdigest() or value['parser_version']!=PARSER_VERSION):
        raise PDFError('pdf_invalid_output')
    validate_text(value['body'],value['pages'],value['text_sha256'])
    return value


def enrich_published(api,source_id,version_id,documents):
    """Read page metadata only for the same currently published, owned version."""
    if not isinstance(documents,list) or len(documents)!=1 or documents[0].get('parser_version')!=PARSER_VERSION:
        return documents
    metadata=api('POST','/rest/v1/rpc/read_published_pdf',{'p_source':source_id,'p_version':version_id})
    if metadata is None: return []  # Deleted/replaced between the two owned reads.
    if type(metadata) is not dict or set(metadata)!={'media_type','text_sha256','pages'} or metadata['media_type']!='application/pdf':
        raise PDFError('pdf_invalid_output')
    validate_text(documents[0]['body'],metadata['pages'],metadata['text_sha256'])
    return [dict(documents[0],**metadata)]


def _extract(raw):
    """Implementation for the bounded child; tests use only owned fixtures."""
    validate_bytes(raw)
    import pypdf
    if pypdf.__version__ != PYPDF_VERSION: raise PDFError('pdf_parser_unavailable')
    pypdf.overwrite_configuration(maximum_declared_stream_length=MAX_STREAM_BYTES,
        array_based_stream_maximum_output_length=MAX_STREAM_BYTES,
        zlib_maximum_output_length=MAX_STREAM_BYTES,lzw_maximum_output_length=MAX_STREAM_BYTES,
        run_length_maximum_output_length=MAX_STREAM_BYTES,stream_decoding_work_maximum_length=MAX_STREAM_BYTES,
        array_maximum_element_count=10000,dictionary_maximum_element_count=10000)
    logging.getLogger('pypdf').disabled = True
    reader = pypdf.PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted: raise PDFError('pdf_encrypted')
    if any(key in reader.trailer['/Root'] for key in ('/OpenAction','/AA','/AcroForm')):
        raise PDFError('pdf_active_content')
    count = len(reader.pages)
    if not 1<=count<=MAX_PAGES: raise PDFError('pdf_page_limit')
    parts, pages, length = [], [], 0
    for number, page in enumerate(reader.pages,1):
        if '/AA' in page: raise PDFError('pdf_active_content')
        stream = page.get_contents()
        if stream is not None and len(stream.get_data())>MAX_STREAM_BYTES:
            raise PDFError('pdf_stream_limit')
        text = page.extract_text()
        if not isinstance(text,str) or not text.strip(): raise PDFError('pdf_text_required')
        # Separators belong to the preceding page, preserving complete coverage.
        text += '\n\n' if number<count else ''
        parts.append(text)
        pages.append({'number':number,'start':length,'end':length+len(text)})
        length += len(text)
        if sum(len(part.encode('utf-8')) for part in parts)>MAX_BYTES:
            raise PDFError('pdf_text_limit')
    body = ''.join(parts)
    return validate_document({'source_sha256':hashlib.sha256(raw).hexdigest(),
        'text_sha256':hashlib.sha256(body.encode()).hexdigest(),
        'parser_version':PARSER_VERSION,'body':body,'pages':pages},raw)


def extract_pdf(raw, *, cancel=None):
    validate_bytes(raw)
    from services.worker.document_parser import extract
    return extract(raw, script=Path(__file__).resolve(), validate=validate_document,
        error=PDFError, prefix='pdf', child_errors={
            'pdf_encrypted','pdf_active_content','pdf_page_limit','pdf_text_required',
            'pdf_stream_limit','pdf_text_limit','pdf_parser_unavailable'}, cancel=cancel)


def _child():
    try:
        from services.worker.document_parser import limits
        limits()
        result=_extract(sys.stdin.buffer.read(MAX_BYTES+1))
        output=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()
        if len(output)>MAX_REPLY_BYTES: raise PDFError('pdf_invalid_output')
        sys.stdout.buffer.write(output)
        return 0
    except Exception as error:
        code=str(error) if isinstance(error,PDFError) else 'pdf_invalid'
        sys.stdout.write(json.dumps({'error':code}))
        return 1


if __name__=='__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    raise SystemExit(_child() if sys.argv[1:]==['--child'] else 2)
