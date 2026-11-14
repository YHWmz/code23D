"""Export an allowlisted static review snapshot for Cloudflare Pages."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,html,json,re,shutil
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--source',default='/root/blenderworld/experiment/review_web');p.add_argument('--output',required=True);args=p.parse_args()
src=Path(args.source);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
stamp=datetime.now(timezone.utc).isoformat(timespec='seconds');converted={};skipped=[]
files=list(src.rglob('*'))
for f in files:
 if not f.is_file():continue
 rel=f.relative_to(src)
 if 'submissions' in rel.parts:skipped.append(str(rel));continue
 if f.suffix.lower() not in {'.html','.json','.png','.jpg','.jpeg','.webp','.mp4','.webm','.txt','.md','.js','.zip'}:continue
 target=out/rel;target.parent.mkdir(parents=True,exist_ok=True)
 if 'previews' in rel.parts and f.suffix.lower() in {'.png','.jpg','.jpeg'} and not f.stem.endswith('_thumb'):
  new=rel.with_suffix('.webp');target=out/new
  with Image.open(f) as im:
   im.thumbnail((2560,2560));im.convert('RGB').save(target,'WEBP',quality=88,method=4)
  converted[str(rel)]=str(new)
 else:shutil.copy2(f,target)
 if target.stat().st_size>25*1024**2:raise ValueError('Cloudflare file limit: '+str(rel))
notice=f'<aside style="padding:14px;background:#fff4d6;border:1px solid #e8cd86;margin:16px 0">公开审核快照 · 更新时间 {html.escape(stamp)}。测试仍在进行时，状态以此快照为准；公网内容需再次同步仓库才会更新。大图为网页压缩版，原始参考输入保留。完整工程 ZIP 保存在实验服务器，未包含在本站。</aside>'
for f in out.rglob('*'):
 if f.suffix not in {'.html','.json','.js'}:continue
 text=f.read_text()
 for old,new in converted.items():
  text=text.replace(old,new)
  if old.startswith('batch30/'):text=text.replace(old[len('batch30/'):],new[len('batch30/'):])
 if f.suffix=='.html':
  text=re.sub(r'<a\b[^>]*href=["\'][^"\']*submissions/[^"\']+["\'][^>]*>.*?</a>','<span style="color:#68768a">工程 ZIP：保存在实验服务器</span>',text,flags=re.S)
  text=re.sub(r'<meta http-equiv="refresh"[^>]*>','',text)
  text=text.replace('页面每 60 秒刷新。','当前显示已发布快照。')
  text=text.replace('<main>','<main>'+notice,1) if '<main>' in text else re.sub(r'(<body\b[^>]*>)',lambda m:m.group(1)+notice,text,count=1)
  if '公开审核快照' not in text and '<h1' in text:text=text.replace('<h1',notice+'<h1',1)
  if f==out/'batch30/index.html':text=text.replace('</body>','<script src="previews.js"></script></body>')
 if f==out/'batch30/previews.js':
  text=text.replace('点击查看原图','点击查看大图（网页压缩版）')
  text=text.replace("setInterval(()=>update().catch(console.error),30000);",'')
  text=text.replace("setInterval(()=>{if(![...document.querySelectorAll('video')].some(v=>!v.paused))location.reload();},120000);",'')
 f.write_text(text)
(out/'snapshot.json').write_text(json.dumps({'exported_at':stamp,'source':'BlenderWorld local review','excluded_submission_archives':len(skipped),'converted_preview_images':len(converted),'live_sync':False},indent=2))
(out/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n\n/*.json\n  Cache-Control: public, max-age=60\n')
print(json.dumps({'files':sum(f.is_file() for f in out.rglob('*')),'bytes':sum(f.stat().st_size for f in out.rglob('*') if f.is_file()),'excluded_archives':len(skipped),'converted':len(converted),'snapshot':stamp}))
