"""Content-free monotonic timings. Overlapping preparation is reported separately."""
import time

STAGES=frozenset(('claim','renew_lease','validate_manifest','read_original','parse_original',
    'chunk_original','stage_text','read_completed_passages','embed_passage','stage_vectors','publish'))
DB_KEYS=frozenset(('operations','helpers_started','connects','total_ms','connect_ms','context_ms','execute_ms'))


class StageClock:
    def __init__(self):
        self.started=self.previous=time.monotonic()
        self.current='claim'
        self.stages={}

    def enter(self,name):
        if name not in STAGES: raise ValueError('invalid_timing_stage')
        now=time.monotonic()
        self.stages[self.current]=self.stages.get(self.current,0)+(now-self.previous)*1000
        self.current,self.previous=name,now

    def finish(self):
        self.enter(self.current)
        return {'total_ms':round((self.previous-self.started)*1000,2),
                'stages_ms':{k:round(v,2) for k,v in self.stages.items()}}


def safe_timing(value):
    """Reject unknown keys and any document-shaped or non-finite measurement."""
    if type(value) is not dict or set(value)-{'total_ms','stages_ms','database','preparation_ms','early_prepare',
                                             'selection_ms','dispatch_total_ms'}:
        return None
    def number(n): return type(n) in (int,float) and 0<=n<=3600000
    if not number(value.get('total_ms')): return None
    stages=value.get('stages_ms')
    if type(stages) is not dict or set(stages)-STAGES or not all(number(n) for n in stages.values()):
        return None
    result={'total_ms':value['total_ms'],'stages_ms':stages.copy()}
    database=value.get('database')
    if database is not None:
        if type(database) is not dict or set(database)-DB_KEYS or not all(number(n) for n in database.values()): return None
        result['database']=database.copy()
    if 'preparation_ms' in value:
        if not number(value['preparation_ms']): return None
        result['preparation_ms']=value['preparation_ms']
    if 'early_prepare' in value:
        if type(value['early_prepare']) is not bool:return None
        result['early_prepare']=value['early_prepare']
    for key in ('selection_ms','dispatch_total_ms'):
        if key in value:
            if not number(value[key]):return None
            result[key]=value[key]
    return result
