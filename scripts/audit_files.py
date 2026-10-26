"""Read-only tracked-file inventory/reference audit. Never deletes/imports files."""
import argparse
import ast
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
STARTUP = ('AGENTS.md','RULES.md','docs/PRD.md','docs/ARCHITECTURE.md',
           'docs/DESIGN.md','TASKS.md','docs/MEMORY.md')
TEXT = {'.md','.py','.ps1','.ts','.tsx','.css','.json','.yaml','.yml','.toml',
        '.sql','.txt','.mjs','.sh','.html','.example','.gitignore'}


def category(path):
    if path in STARTUP: return 'current-context'
    if path.startswith('docs/history/'): return 'historical-context'
    if path.startswith('legacy/'): return 'historical-prototype'
    if path.startswith('tests/'): return 'tests-or-frozen-evidence'
    if path.startswith('supabase/migrations/'): return 'ordered-migration'
    if path.startswith('docs/'): return 'reference-or-knowledge'
    if path.endswith(('LICENSE','NOTICE','.lock','package-lock.json')) or 'NOTICE' in path:
        return 'license-or-locked-input'
    if path.startswith(('deploy/','.github/')) or Path(path).name.startswith(('Dockerfile','compose.')):
        return 'build-deployment-or-CI'
    if path.startswith('scripts/'): return 'operator-or-maintenance-entrypoint'
    if path.startswith(('services/','apps/')): return 'application-or-build-input'
    return 'repository-configuration-or-entrypoint'


def tracked_files():
    raw = subprocess.run(['git','ls-files','-z'],cwd=ROOT,check=True,capture_output=True).stdout
    return sorted(p.decode('utf-8') for p in raw.split(b'\0') if p)


def without_examples(body):
    body = re.sub(r'(?ms)^```[^\n]*\n.*?^```[^\n]*$', '', body)
    return re.sub(r'`[^`\n]*`','',body)


def import_references(texts,paths):
    incoming={p:set() for p in paths}
    modules={'.'.join(Path(p).with_suffix('').parts).removesuffix('.__init__'):p
             for p in paths if p.endswith('.py')}
    for source,body in texts.items():
        if source.endswith('.py'):
            package='.'.join(Path(source).parent.parts)
            try: tree=ast.parse(body)
            except SyntaxError: continue
            for node in ast.walk(tree):
                names=[]
                if isinstance(node,ast.Import): names=[n.name for n in node.names]
                if isinstance(node,ast.ImportFrom):
                    base=node.module or ''
                    if node.level:
                        parts=package.split('.')
                        base='.'.join(parts[:len(parts)-node.level+1]+([base] if base else []))
                    names=[base,*[base+'.'+n.name for n in node.names]]
                for name in names:
                    target=modules.get(name) or modules.get(package+'.'+name)
                    if target and target!=source: incoming[target].add(source)
        elif Path(source).suffix in ('.ts','.tsx','.mjs'):
            for match in re.finditer(r'''(?:from\s*|import\s*(?:\(\s*)?)["']([^"']+)["']''',body):
                target=match.group(1)
                if not target.startswith('.'): continue
                base=(ROOT/Path(source).parent/target).resolve()
                candidates=[base,*[Path(str(base)+suffix) for suffix in ('.ts','.tsx','.mjs','.css')],base/'index.ts']
                for candidate in candidates:
                    if candidate.is_relative_to(ROOT):
                        relative=candidate.relative_to(ROOT).as_posix()
                        if relative in incoming: incoming[relative].add(source); break
    return incoming


def broken_links(texts, paths):
    stems = Counter(Path(p).stem for p in paths if p.endswith('.md'))
    issues=[]
    for name, text in texts.items():
        if not name.endswith('.md'): continue
        body=without_examples(text)
        targets=[(m.group(1).strip('<>'),'markdown') for m in re.finditer(
            r'(?<!!)\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+[^)]*)?\)',body)]
        targets += [(m.group(1).split('|',1)[0],'wiki') for m in re.finditer(r'\[\[([^\]\n]+)\]\]',body)]
        for target,kind in targets:
            target=unquote(target.split('#',1)[0].split('?',1)[0])
            if not target or re.match(r'^[a-zA-Z][\w+.-]*:',target) or target.startswith(('/','\\')):
                continue
            candidates=[ROOT/Path(name).parent/target]
            if kind=='wiki':
                candidates=[ROOT/target,*candidates]
                candidates += [p.with_suffix('.md') for p in list(candidates) if not p.suffix]
            if any(p.resolve().is_relative_to(ROOT) and p.exists() for p in candidates): continue
            if kind=='wiki' and not Path(target).suffix and stems[Path(target).name]==1: continue
            issues.append({'source':name,'target':target,'kind':kind})
    return issues


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='output/file-audit/current')
    parser.add_argument('--check-links',action='store_true')
    args=parser.parse_args()
    destination=(ROOT/args.output).resolve()
    if not destination.is_relative_to(ROOT/'output'):
        raise SystemExit('Reports must stay under the repository output directory.')
    paths=tracked_files()
    texts={}
    sizes={}
    syntax=[]
    hashes={}
    for name in paths:
        path=ROOT/name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT) or not path.is_file(): continue
        sizes[name]=path.stat().st_size
        if sizes[name]<=2*1024*1024:
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            hashes.setdefault(digest,[]).append(name)
        if sizes[name]>2*1024*1024 or (path.suffix not in TEXT and path.name not in ('.gitignore','.ignore','.dockerignore','.gitattributes')):
            continue
        try: texts[name]=path.read_text(encoding='utf-8-sig')
        except (UnicodeError,OSError): continue
        if path.suffix=='.py':
            try: ast.parse(texts[name],filename=name)
            except SyntaxError: syntax.append(name)
    folded={p:text.lower() for p,text in texts.items()}
    imports=import_references(texts,paths)
    basenames=Counter(Path(p).name.lower() for p in paths)
    rows=[]
    for name in paths:
        base=Path(name).name.lower()
        incoming=[p for p,body in folded.items() if p!=name and base in body]
        current=[p for p in incoming if not p.startswith(('docs/history/','legacy/'))]
        rows.append({'path':name,'bytes':sizes.get(name,0),'category':category(name),
            'mandatory_startup':name in STARTUP,'current_text_ref_files':len(current),
            'historical_text_ref_files':len(incoming)-len(current),
            'static_import_ref_files':len(imports[name]),
            'basename_ambiguous':basenames[base]>1,'examples':'; '.join(sorted(set(current)|imports[name])[:5]),
            'disposition':'keep; absence of a literal reference is not evidence of disuse'})
    links=broken_links(texts,paths)
    summary={'tracked_files':len(paths),'text_files_inspected':len(texts),
        'categories':dict(Counter(row['category'] for row in rows)),
        'startup_bytes':sum(sizes.get(p,0) for p in STARTUP),
        'startup_text_characters':sum(len(texts.get(p,'')) for p in STARTUP),
        'startup_files':{p:sizes.get(p,0) for p in STARTUP},
        'zero_literal_ref_files':sum(row['current_text_ref_files']==0 for row in rows),
        'python_syntax_errors':syntax,'broken_local_links':links,
        'duplicate_byte_groups':[names for names in hashes.values() if len(names)>1],
        'limits':'Literal reference counts are approximate, not runtime usage. Tests/migrations/config/manual tools may be convention-loaded. No ignored private data, model environments or generated output were scanned.'}
    destination.mkdir(parents=True,exist_ok=True)
    with (destination/'inventory.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (destination/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('tracked_files','text_files_inspected','startup_bytes',
        'startup_text_characters','categories','python_syntax_errors','broken_local_links')},indent=2))
    if args.check_links and (links or syntax): raise SystemExit(1)


if __name__=='__main__':
    main()
