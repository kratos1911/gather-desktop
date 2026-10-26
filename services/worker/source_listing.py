"""Bounded metadata pages. Unsigned cursors carry position, never authority."""
import base64
from datetime import datetime
import json
import re
from uuid import UUID

from services.worker.service_transport import strict_json

MAX_PAGE = 20
FIELDS = frozenset(('source_id','title','kind','created_at','published_version_id',
                    'processing_version_id','job_id','state','attempts','error_code'))
ERRORS = frozenset(('timeout','temporarily_unavailable','invalid_input','lease_expired','superseded','deleted'))


def _id(value):
    if not isinstance(value,str) or str(UUID(value)) != value:
        raise ValueError('invalid_cursor')
    return value


def _date(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z',value):
        raise ValueError('invalid_cursor')
    datetime.strptime(value,'%Y-%m-%dT%H:%M:%S.%fZ')
    return value


def position(cursor):
    if cursor is None:
        return None
    if not isinstance(cursor,str) or not 1 <= len(cursor) <= 256 or not re.fullmatch(r'[A-Za-z0-9_-]+',cursor):
        raise ValueError('invalid_cursor')
    value = strict_json(base64.b64decode(cursor+'='*((-len(cursor))%4),altchars=b'-_',validate=True))
    if type(value) is not dict or set(value) != {'v','created_at','source_id'} or type(value['v']) is not int or value['v'] != 1:
        raise ValueError('invalid_cursor')
    return _date(value['created_at']),_id(value['source_id'])


def parameters(limit=MAX_PAGE,cursor=None):
    if type(limit) is not int or not 1 <= limit <= MAX_PAGE:
        raise ValueError('invalid_cursor')
    before = position(cursor)
    return {'p_limit':limit,'p_before_created_at':before[0] if before else None,
            'p_before_id':before[1] if before else None}


def page(rows,limit=MAX_PAGE,cursor=None):
    parameters(limit,cursor)
    if type(rows) is not list or len(rows)>limit+1:
        raise ValueError('invalid_listing')
    previous = position(cursor)
    for row in rows:
        if type(row) is not dict or set(row)!=FIELDS:
            raise ValueError('invalid_listing')
        current = _date(row['created_at']),_id(row['source_id'])
        if previous is not None and current>=previous:
            raise ValueError('invalid_listing')
        previous = current
        if not isinstance(row['title'],str) or not 1<=len(row['title'].strip())<=500 or row['kind'] not in ('file','bookmark'):
            raise ValueError('invalid_listing')
        for name in ('published_version_id','processing_version_id','job_id'):
            if row[name] is not None: _id(row[name])
        if row['job_id'] is None:
            if any(row[k] is not None for k in ('processing_version_id','state','attempts','error_code')):
                raise ValueError('invalid_listing')
        elif (row['processing_version_id'] is None or row['state'] not in ('queued','processing','ready','failed','cancelled')
              or type(row['attempts']) is not int or not 0<=row['attempts']<=3
              or (row['error_code'] is not None and row['error_code'] not in ERRORS)):
            raise ValueError('invalid_listing')
        if row['state']=='ready' and row['published_version_id']!=row['processing_version_id']:
            raise ValueError('invalid_listing')
    items = rows[:limit]
    next_cursor = None
    if len(rows)>limit:
        last = items[-1]
        raw = json.dumps({'v':1,'created_at':last['created_at'],'source_id':last['source_id']},separators=(',',':')).encode()
        next_cursor = base64.urlsafe_b64encode(raw).decode().rstrip('=')
    return {'items':items,'next_cursor':next_cursor}
