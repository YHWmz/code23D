from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'public').resolve();errors=[];count=0
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key in ['href','src'] and value:links.append(value)
for p in root.rglob('*'):
 if not p.is_file():continue
 count+=1
 if p.stat().st_size>25*1024**2:errors.append('Oversized: '+str(p))
 if p.name in ['credentials.json','.env'] or 'submissions' in p.relative_to(root).parts:errors.append('Disallowed: '+str(p))
 if p.suffix=='.html':
  links=[];Links().feed(p.read_text())
  for link in links:
   u=urlsplit(link)
   if u.scheme or u.netloc or not u.path:continue
   target=(root/u.path.lstrip('/') if u.path.startswith('/') else p.parent/unquote(u.path)).resolve()
   if not target.is_relative_to(root) or not target.exists():errors.append(f'Broken link: {p.relative_to(root)} -> {link}')
manifest=root/'batch30/previews.json'
if manifest.exists():
 for items in json.loads(manifest.read_text())['runs'].values():
  for item in items:
   for key in ['url','thumbnail']:
    if item.get(key) and not (manifest.parent/item[key]).is_file():errors.append('Missing preview: '+item[key])
print(json.dumps({'files':count,'errors':errors},ensure_ascii=False,indent=2))
if errors:sys.exit(1)
