"""Attach a Scholar Description only after identity/content review; no external sites."""
import argparse,json,hashlib
from pathlib import Path
from extended_search import description_url,html_fetch,scholar_description
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('record',help='JSON object for one search record');p.add_argument('--url',required=True,help='Observed Scholar view_citation URL');p.add_argument('--output',required=True)
    p.add_argument('--html-file',help='Saved HTML of that same observed Scholar detail page, if browser access was necessary')
    p.add_argument('--confirm-original-abstract',action='store_true',help='Only after reading Description and confirming complete author abstract for this paper')
    a=p.parse_args();dest=Path(a.output)
    if dest.exists():raise FileExistsError('Use new output')
    if not description_url(a.url):raise ValueError('Only scholar.google.com citation detail allowed')
    r=json.loads(Path(a.record).read_text());html=Path(a.html_file).read_text() if a.html_file else html_fetch(a.url)
    text,status=scholar_description(html,r['title'])
    r.update(abstract_recovery_policy='scholar_description_only',description=text,description_status=status,scholar_description_url=a.url)
    if text and a.confirm_original_abstract:
        r.update(abstract=text,abstract_source=a.url,abstract_status='PRESENT',description_status='CONFIRMED_AUTHOR_ABSTRACT',abstract_locator='Description')
    elif not r.get('abstract'):r.update(abstract='',abstract_status='MISSING')
    dest.parent.mkdir(parents=True,exist_ok=True)
    snapshot=dest.with_suffix(dest.suffix+'.html')
    if snapshot.exists():raise FileExistsError('Use new snapshot output')
    snapshot.write_text(html)
    r.update(description_snapshot=str(snapshot),description_snapshot_sha256=hashlib.sha256(html.encode()).hexdigest())
    dest.write_text(json.dumps({'source':'google_scholar','results':[r]},ensure_ascii=False,indent=2))
    print(json.dumps({'description_status':r['description_status'],'abstract_status':r.get('abstract_status')}))
