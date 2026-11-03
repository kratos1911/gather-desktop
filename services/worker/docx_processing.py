"""Bounded native DOCX body-text extraction. No Office, network, images or macros."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile
import xml.etree.ElementTree as ET

MEDIA = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
PARSER_VERSION = 'docx-ooxml-body-v1'
MAX_BYTES = 65536
MAX_MEMBERS = 128
MAX_PART_BYTES = 524288
MAX_EXPANDED_BYTES = 1048576
MAX_PARAGRAPHS = 128
MAX_NODES = 20000
MAX_DEPTH = 64
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
CT = '{http://schemas.openxmlformats.org/package/2006/content-types}'
REL = '{http://schemas.openxmlformats.org/package/2006/relationships}'
OFFICE_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
MAIN_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'
ERRORS = frozenset('docx_size docx_invalid docx_invalid_output docx_archive_limit docx_active_content '
    'docx_unsupported_content docx_text_required docx_text_limit docx_paragraph_limit '
    'docx_parser_unavailable docx_busy docx_timeout docx_cancelled'.split())


class DOCXError(ValueError):
    """Fixed content-free error code."""


def validate_bytes(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise DOCXError('docx_size')
    if not raw.startswith(b'PK\x03\x04'):
        raise DOCXError('docx_invalid')


def validate_text(body, paragraphs, text_sha256):
    if (type(body) is not str or not body.strip() or len(body.encode('utf-8')) > MAX_BYTES
            or any((ord(c) < 32 and c not in '\t\r\n') or 127 <= ord(c) <= 159 for c in body)
            or hashlib.sha256(body.encode('utf-8')).hexdigest() != text_sha256):
        raise DOCXError('docx_invalid_output')
    if type(paragraphs) is not list or not 1 <= len(paragraphs) <= MAX_PARAGRAPHS:
        raise DOCXError('docx_invalid_output')
    previous = 0
    for number, item in enumerate(paragraphs, 1):
        if (type(item) is not dict or set(item) != {'number', 'start', 'end'}
                or any(type(item[k]) is not int for k in item) or item['number'] != number
                or item['start'] != previous or not previous < item['end'] <= len(body)
                or not body[item['start']:item['end']].strip()):
            raise DOCXError('docx_invalid_output')
        previous = item['end']
    if previous != len(body):
        raise DOCXError('docx_invalid_output')


def validate_document(value, raw):
    validate_bytes(raw)
    if (type(value) is not dict or set(value) != {'source_sha256', 'text_sha256', 'parser_version', 'body', 'paragraphs'}
            or value['source_sha256'] != hashlib.sha256(raw).hexdigest()
            or value['parser_version'] != PARSER_VERSION):
        raise DOCXError('docx_invalid_output')
    validate_text(value['body'], value['paragraphs'], value['text_sha256'])
    return value


class _Tree(ET.TreeBuilder):
    def __init__(self):
        super().__init__()
        self.nodes = self.depth = 0
        self.paragraph_open = False

    def doctype(self, *args):
        raise DOCXError('docx_active_content')

    def start(self, tag, attrs):
        self.nodes += 1
        self.depth += 1
        if self.nodes > MAX_NODES or self.depth > MAX_DEPTH:
            raise DOCXError('docx_archive_limit')
        if tag == W + 'p':
            if self.paragraph_open:
                raise DOCXError('docx_invalid')
            self.paragraph_open = True
        return super().start(tag, attrs)

    def end(self, tag):
        self.depth -= 1
        if tag == W + 'p':
            self.paragraph_open = False
        return super().end(tag)


def _xml(raw):
    try:
        text = raw.decode('utf-8-sig')  # UTF-16/other encodings are explicitly unsupported.
        if '\0' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
            raise DOCXError('docx_active_content')
        return ET.fromstring(text, parser=ET.XMLParser(target=_Tree()))
    except (UnicodeError, ET.ParseError):
        raise DOCXError('docx_invalid') from None


def _extract(raw):
    validate_bytes(raw)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if not 1 <= len(members) <= MAX_MEMBERS:
                raise DOCXError('docx_archive_limit')
            parts, names, total = {}, set(), 0
            for info in members:
                name = info.filename
                path = PurePosixPath(name)
                if (not name or info.orig_filename != name or len(name) > 240 or '\\' in name or '\0' in name
                        or path.is_absolute() or '..' in path.parts or str(path) != name.rstrip('/')
                        or name.casefold() in names or stat.S_ISLNK(info.external_attr >> 16)
                        or info.flag_bits & 1 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                    raise DOCXError('docx_invalid')
                if info.file_size > MAX_PART_BYTES or total + info.file_size > MAX_EXPANDED_BYTES:
                    raise DOCXError('docx_archive_limit')
                names.add(name.casefold())
                total += info.file_size
                if re.search(r'(vba|activex|embeddings|oleobject|attachedtemplate|afchunk)', name, re.I):
                    raise DOCXError('docx_active_content')
                with archive.open(info) as stream:
                    part = stream.read(MAX_PART_BYTES + 1)
                if len(part) != info.file_size or len(part) > MAX_PART_BYTES:
                    raise DOCXError('docx_archive_limit')
                parts[name] = part  # Never extract archive paths to disk.
            if not {'[Content_Types].xml', '_rels/.rels', 'word/document.xml'} <= parts.keys():
                raise DOCXError('docx_invalid')
            types = _xml(parts['[Content_Types].xml'])
            if types.tag != CT + 'Types':
                raise DOCXError('docx_invalid')
            main = [n for n in types if n.tag == CT + 'Override' and n.get('PartName') == '/word/document.xml']
            if len(main) != 1 or main[0].get('ContentType') != MAIN_TYPE:
                raise DOCXError('docx_invalid')
            if any(re.search(r'(macroenabled|vbaproject|oleobject|activex)', n.get('ContentType', ''), re.I) for n in types):
                raise DOCXError('docx_active_content')
            root_relationship = False
            for name, part in parts.items():
                if not name.endswith(('.xml', '.rels')):
                    continue
                tree = _xml(part)
                if name.endswith('.rels'):
                    if tree.tag != REL + 'Relationships':
                        raise DOCXError('docx_invalid')
                    seen = set()
                    for rel in tree:
                        if rel.tag != REL + 'Relationship' or not rel.get('Id') or rel.get('Id') in seen:
                            raise DOCXError('docx_invalid')
                        seen.add(rel.get('Id'))
                        kind, target = rel.get('Type', ''), rel.get('Target', '')
                        if name == '_rels/.rels' and kind == OFFICE_REL + 'officeDocument':
                            if root_relationship or target not in ('word/document.xml', '/word/document.xml') or rel.get('TargetMode'):
                                raise DOCXError('docx_invalid')
                            root_relationship = True
                        # Hyperlink labels are text only; targets are never followed.
                        if rel.get('TargetMode') and not (rel.get('TargetMode') == 'External' and kind == OFFICE_REL + 'hyperlink'):
                            raise DOCXError('docx_active_content')
                        if re.search(r'(oleobject|activex|attachedtemplate|afchunk|vbaproject)', kind, re.I):
                            raise DOCXError('docx_active_content')
            if not root_relationship:
                raise DOCXError('docx_invalid')
            document = _xml(parts['word/document.xml'])
            body = document.find(W + 'body')
            if document.tag != W + 'document' or body is None:
                raise DOCXError('docx_invalid')
            unsupported = {'altChunk', 'object', 'pict', 'txbxContent', 'ins', 'del', 'moveFrom', 'moveTo',
                           'instrText', 'fldChar', 'fldSimple', 'footnoteReference', 'endnoteReference', 'subDoc', 'vanish'}
            unsupported_tags = {W + name for name in unsupported} | {
                '{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent'}
            if any(node.tag in unsupported_tags for node in document.iter()):
                raise DOCXError('docx_unsupported_content')
            texts = []
            for paragraph in body.iter(W + 'p'):
                chunks = []
                for node in paragraph.iter():
                    if node.tag == W + 't':
                        chunks.append(node.text or '')
                    elif node.tag == W + 'tab':
                        chunks.append('\t')
                    elif node.tag in (W + 'br', W + 'cr'):
                        chunks.append('\n')
                text = ''.join(chunks)
                if text.strip():
                    texts.append(text)
                if len(texts) > MAX_PARAGRAPHS:
                    raise DOCXError('docx_paragraph_limit')
            if not texts:
                raise DOCXError('docx_text_required')
            result, paragraphs, offset = [], [], 0
            for number, text in enumerate(texts, 1):
                text += '\n\n' if number < len(texts) else ''
                result.append(text)
                paragraphs.append(dict(number=number, start=offset, end=offset + len(text)))
                offset += len(text)
            body = ''.join(result)
            if len(body.encode('utf-8')) > MAX_BYTES:
                raise DOCXError('docx_text_limit')
            return validate_document(dict(source_sha256=hashlib.sha256(raw).hexdigest(),
                text_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest(),
                parser_version=PARSER_VERSION, body=body, paragraphs=paragraphs), raw)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, ValueError) as exc:
        if isinstance(exc, DOCXError):
            raise
        raise DOCXError('docx_invalid') from None


def extract_docx(raw, *, cancel=None):
    validate_bytes(raw)
    from services.worker.document_parser import extract
    return extract(raw, script=Path(__file__).resolve(), validate=validate_document,
                   error=DOCXError, prefix='docx', child_errors=ERRORS, cancel=cancel)


def enrich_published(api, source_id, version_id, documents):
    if type(documents) is not list or len(documents) != 1 or documents[0].get('parser_version') != PARSER_VERSION:
        return documents
    metadata = api('POST', '/rest/v1/rpc/read_published_docx', {'p_source': source_id, 'p_version': version_id})
    if metadata is None:
        return []
    if type(metadata) is not dict or set(metadata) != {'media_type', 'text_sha256', 'paragraphs'} or metadata['media_type'] != MEDIA:
        raise DOCXError('docx_invalid_output')
    validate_text(documents[0]['body'], metadata['paragraphs'], metadata['text_sha256'])
    return [dict(documents[0], **metadata)]


def _child():
    try:
        from services.worker.document_parser import limits, MAX_REPLY_BYTES
        limits()
        result = _extract(sys.stdin.buffer.read(MAX_BYTES + 1))
        output = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()
        if len(output) > MAX_REPLY_BYTES:
            raise DOCXError('docx_invalid_output')
        sys.stdout.buffer.write(output)
        return 0
    except Exception as exc:
        sys.stdout.write(json.dumps({'error': str(exc) if isinstance(exc, DOCXError) else 'docx_invalid'}))
        return 1


if __name__ == '__main__':
    # Isolated mode needs only the trusted checkout/image root, never user paths.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    raise SystemExit(_child() if sys.argv[1:] == ['--child'] else 2)
