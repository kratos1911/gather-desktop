"""Bounded, English image OCR. Pixels are not visual/photo-search embeddings."""
import csv
import base64
import ctypes
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import warnings

MEDIA = ('image/png', 'image/jpeg')
PARSER_VERSION = 'image-tesseract-5.5.0-eng-v1'
ENGINE = 'tesseract-5.5.0-lstm'
MODEL_SHA256 = '7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'
PILLOW_VERSION = '13.0.0'
MAX_BYTES = 65536
MAX_PIXELS = 1048576
MAX_SIDE = 4096
MAX_REGIONS = 128
MAX_WORDS = 2048
TSV_FIELDS = 'level page_num block_num par_num line_num word_num left top width height conf text'.split()
ERRORS = frozenset(('image_size image_invalid image_dimensions image_animated '
    'image_text_required image_text_limit image_region_limit image_invalid_output '
    'image_parser_unavailable image_busy image_timeout image_cancelled').split())


class ImageError(ValueError):
    """Content-free, allowlisted failure."""


def validate_bytes(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ImageError('image_size')
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):
        return MEDIA[0]
    if raw.startswith(b'\xff\xd8\xff'):
        return MEDIA[1]
    raise ImageError('image_invalid')


def dimensions(width, height):
    if (type(width) is not int or type(height) is not int or
            not 1 <= width <= MAX_SIDE or not 1 <= height <= MAX_SIDE or
            width * height > MAX_PIXELS):
        raise ImageError('image_dimensions')


def validate_text(body, regions, text_sha256, width, height):
    dimensions(width, height)
    if (type(body) is not str or not body.strip() or len(body.encode('utf-8')) > MAX_BYTES
            or any((ord(c) < 32 and c not in '\t\r\n') or 127 <= ord(c) <= 159 for c in body)
            or hashlib.sha256(body.encode('utf-8')).hexdigest() != text_sha256):
        raise ImageError('image_invalid_output')
    if type(regions) is not list or not 1 <= len(regions) <= MAX_REGIONS:
        raise ImageError('image_invalid_output')
    end = 0
    for number, region in enumerate(regions, 1):
        if (type(region) is not dict or set(region) !=
                {'number', 'start', 'end', 'x', 'y', 'width', 'height', 'confidence'}
                or any(type(region[k]) is not int for k in region if k != 'confidence')
                or region['number'] != number or region['start'] != end
                or not end < region['end'] <= len(body)
                or not body[end:region['end']].strip()
                or region['x'] < 0 or region['y'] < 0
                or region['width'] <= 0 or region['height'] <= 0
                or region['x'] + region['width'] > width
                or region['y'] + region['height'] > height
                or type(region['confidence']) not in (int, float)
                or not math.isfinite(region['confidence'])
                or not 0 <= region['confidence'] <= 100):
            raise ImageError('image_invalid_output')
        end = region['end']
    if end != len(body):
        raise ImageError('image_invalid_output')


def validate_document(value, raw):
    media = validate_bytes(raw)
    fields = {'source_sha256', 'text_sha256', 'parser_version', 'engine',
              'ocr_model_sha256', 'language', 'media_type', 'width', 'height', 'body', 'regions'}
    if (type(value) is not dict or set(value) != fields
            or value['source_sha256'] != hashlib.sha256(raw).hexdigest()
            or value['parser_version'] != PARSER_VERSION or value['engine'] != ENGINE
            or value['ocr_model_sha256'] != MODEL_SHA256 or value['language'] != 'eng'
            or value['media_type'] != media):
        raise ImageError('image_invalid_output')
    validate_text(value['body'], value['regions'], value['text_sha256'], value['width'], value['height'])
    return value


def _decode(raw):
    """Validate actual pixels inside the disposable child, never in an HTTP handler."""
    media = validate_bytes(raw)
    import PIL
    from PIL import Image, ImageOps
    if PIL.__version__ != PILLOW_VERSION:
        raise ImageError('image_parser_unavailable')
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format != ('PNG' if media == 'image/png' else 'JPEG'):
                    raise ImageError('image_invalid')
                dimensions(*source.size)
                if getattr(source, 'n_frames', 1) != 1:
                    raise ImageError('image_animated')
                source.verify()
            with Image.open(io.BytesIO(raw)) as source:
                upright = ImageOps.exif_transpose(source)
                dimensions(*upright.size)
                # Composite transparency onto white; do not infer hidden text.
                if 'A' in upright.getbands() or 'transparency' in upright.info:
                    rgba = upright.convert('RGBA')
                    image = Image.new('RGB', rgba.size, 'white')
                    image.paste(rgba, mask=rgba.getchannel('A'))
                else:
                    image = upright.convert('RGB')
                image.load()
                return image
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageError('image_dimensions') from None
    except ImageError:
        raise
    except Exception:
        raise ImageError('image_invalid') from None


def _recognize(image):
    """Use the pinned C API in-process: cancellation leaves no OCR grandchildren."""
    model = Path('/usr/share/tesseract-ocr/5/tessdata/eng.traineddata')
    if not model.is_file() or hashlib.sha256(model.read_bytes()).hexdigest() != MODEL_SHA256:
        raise ImageError('image_parser_unavailable')
    os.environ['OMP_THREAD_LIMIT'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    try:
        lib = ctypes.CDLL('/usr/lib/x86_64-linux-gnu/libtesseract.so.5')
        pointer, integer, string = ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        signatures = {
            'TessVersion': (string, []),
            'TessBaseAPICreate': (pointer, []),
            'TessBaseAPIInit2': (integer, [pointer, string, string, integer]),
            'TessBaseAPISetPageSegMode': (None, [pointer, integer]),
            'TessBaseAPISetSourceResolution': (None, [pointer, integer]),
            'TessBaseAPISetImage': (None, [pointer, pointer, integer, integer, integer, integer]),
            'TessBaseAPIRecognize': (integer, [pointer, pointer]),
            'TessBaseAPIGetTsvText': (pointer, [pointer, integer]),
            'TessDeleteText': (None, [pointer]),
            'TessBaseAPIEnd': (None, [pointer]),
            'TessBaseAPIDelete': (None, [pointer]),
        }
        for name, (restype, argtypes) in signatures.items():
            method = getattr(lib, name)
            method.restype, method.argtypes = restype, argtypes
        if lib.TessVersion() != b'5.5.0':
            raise ImageError('image_parser_unavailable')
    except (OSError, AttributeError):
        raise ImageError('image_parser_unavailable') from None
    handle, text = lib.TessBaseAPICreate(), None
    if not handle:
        raise ImageError('image_parser_unavailable')
    try:
        if lib.TessBaseAPIInit2(handle, str(model.parent).encode(), b'eng', 1):
            raise ImageError('image_parser_unavailable')
        lib.TessBaseAPISetPageSegMode(handle, 3)
        pixels = ctypes.create_string_buffer(image.tobytes())
        lib.TessBaseAPISetImage(handle, pixels, image.width, image.height, 3, image.width * 3)
        lib.TessBaseAPISetSourceResolution(handle, 300)
        if lib.TessBaseAPIRecognize(handle, None):
            raise ImageError('image_invalid')
        text = lib.TessBaseAPIGetTsvText(handle, 0)
        if not text:
            raise ImageError('image_text_required')
        output = ctypes.string_at(text)
        if len(output) > 524288:
            raise ImageError('image_text_limit')
        # The C API returns rows; unlike the CLI renderer, it omits the header.
        return '\t'.join(TSV_FIELDS) + '\n' + output.decode('utf-8')
    finally:
        if text:
            lib.TessDeleteText(text)
        lib.TessBaseAPIEnd(handle)
        lib.TessBaseAPIDelete(handle)


def from_tsv(tsv, raw, width, height):
    """Pure output adapter; synthetic TSV is test evidence, never a live fallback."""
    media = validate_bytes(raw)
    dimensions(width, height)
    if type(tsv) is not str or len(tsv.encode('utf-8')) > 524288:
        raise ImageError('image_invalid_output')
    reader = csv.DictReader(io.StringIO(tsv), delimiter='\t', quoting=csv.QUOTE_NONE)
    expected = TSV_FIELDS
    if reader.fieldnames != expected:
        raise ImageError('image_invalid_output')
    lines, words, rows = {}, 0, 0
    try:
        for row in reader:
            rows += 1
            if rows > MAX_WORDS * 4 or set(row) != set(expected) or any(v is None for v in row.values()):
                raise ImageError('image_invalid_output')
            if row['level'] not in ('1','2','3','4','5'):
                raise ImageError('image_invalid_output')
            if row['level'] != '5':
                continue
            word = row['text'].strip()
            if not word:
                continue
            words += 1
            if words > MAX_WORDS:
                raise ImageError('image_text_limit')
            if any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in word):
                raise ImageError('image_invalid_output')
            key = tuple(int(row[k]) for k in ('page_num', 'block_num', 'par_num', 'line_num'))
            x, y, w, h = (int(row[k]) for k in ('left', 'top', 'width', 'height'))
            conf = float(row['conf'])
            if (key[0] != 1 or any(i < 1 for i in key) or min(x, y) < 0 or min(w, h) < 1
                    or x + w > width or y + h > height or not math.isfinite(conf) or not 0 <= conf <= 100):
                raise ImageError('image_invalid_output')
            lines.setdefault(key, []).append((word, x, y, w, h, conf))
            if len(lines) > MAX_REGIONS:
                raise ImageError('image_region_limit')
    except ImageError:
        raise
    except (ValueError, TypeError, csv.Error):
        raise ImageError('image_invalid_output') from None
    if not lines:
        raise ImageError('image_text_required')
    parts, regions, offset = [], [], 0
    for number, line in enumerate(lines.values(), 1):
        part = ' '.join(item[0] for item in line) + ('\n\n' if number < len(lines) else '')
        x, y = min(i[1] for i in line), min(i[2] for i in line)
        right, bottom = max(i[1] + i[3] for i in line), max(i[2] + i[4] for i in line)
        regions.append(dict(number=number, start=offset, end=offset + len(part), x=x, y=y,
                            width=right-x, height=bottom-y, confidence=round(sum(i[5] for i in line)/len(line), 3)))
        parts.append(part)
        offset += len(part)
    body = ''.join(parts)
    if len(body.encode('utf-8')) > MAX_BYTES:
        raise ImageError('image_text_limit')
    return validate_document(dict(source_sha256=hashlib.sha256(raw).hexdigest(),
        text_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest(), parser_version=PARSER_VERSION,
        engine=ENGINE, ocr_model_sha256=MODEL_SHA256, language='eng', media_type=media,
        width=width, height=height, body=body, regions=regions), raw)


def _extract(raw):
    image = _decode(raw)
    return from_tsv(_recognize(image), raw, image.width, image.height)


def extract_image(raw, *, cancel=None):
    validate_bytes(raw)
    from services.worker.document_parser import extract
    return extract(raw, script=Path(__file__).resolve(), validate=validate_document,
        error=ImageError, prefix='image', child_errors=ERRORS, cancel=cancel)


def enrich_published(api, source_id, version_id, documents):
    if (not isinstance(documents, list) or len(documents) != 1
            or documents[0].get('parser_version') != PARSER_VERSION):
        return documents
    metadata = api('POST', '/rest/v1/rpc/read_published_image', {'p_source':source_id,'p_version':version_id})
    if metadata is None:
        return []
    fields = {'media_type','text_sha256','width','height','engine','ocr_model_sha256','language','regions'}
    if (type(metadata) is not dict or set(metadata) != fields or metadata['media_type'] not in MEDIA
            or metadata['engine'] != ENGINE or metadata['ocr_model_sha256'] != MODEL_SHA256
            or metadata['language'] != 'eng'):
        raise ImageError('image_invalid_output')
    validate_text(documents[0]['body'], metadata['regions'], metadata['text_sha256'],
                  metadata['width'], metadata['height'])
    return [dict(documents[0], **metadata)]


def attach_original(api, source_id, version_id, documents):
    """Original bytes are fetched only for explicit Open, never for search context."""
    if (not isinstance(documents, list) or len(documents) != 1
            or not isinstance(documents[0], dict) or documents[0].get('media_type') not in MEDIA):
        return documents
    original = api('POST', '/rest/v1/rpc/read_published_image_original',
                   {'p_source':source_id,'p_version':version_id})
    if original is None:
        return []
    if (type(original) is not dict or set(original) != {'media_type','source_sha256','content_base64'}
            or original['media_type'] != documents[0]['media_type']
            or original['source_sha256'] != documents[0]['source_sha256']
            or type(original['content_base64']) is not str or len(original['content_base64']) > 87384):
        raise ImageError('image_invalid_output')
    try:
        raw = base64.b64decode(original['content_base64'], validate=True)
    except (ValueError, TypeError):
        raise ImageError('image_invalid_output') from None
    if (validate_bytes(raw) != original['media_type']
            or hashlib.sha256(raw).hexdigest() != original['source_sha256']):
        raise ImageError('image_invalid_output')
    return [dict(documents[0], image_base64=original['content_base64'])]


def _child():
    try:
        from services.worker.document_parser import limits
        limits()
        result = _extract(sys.stdin.buffer.read(MAX_BYTES + 1))
        output = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()
        if len(output) > 524288:
            raise ImageError('image_invalid_output')
        sys.stdout.buffer.write(output)
        return 0
    except Exception as error:
        sys.stdout.write(json.dumps({'error': str(error) if isinstance(error, ImageError) else 'image_invalid'}))
        return 1


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    raise SystemExit(_child() if sys.argv[1:] == ['--child'] else 2)
