"""Export observable tool evidence with deterministic explanations, excluding reasoning and raw logs."""
import base64,collections,hashlib,html,json,re
from pathlib import Path
ROOTS=[Path('/root/blenderworld/experiment'),Path('/root/blenderworld/experiment_30_20261113')]
STAGES=['读取任务与参考','编写与修改制作脚本','运行 Blender 与渲染','查看图像与检查产物','诊断与环境检查']
def clean(s,limit=5000):
 s=str(s);s=re.sub(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+','[图像编码省略]',s)
 s=re.sub(r'(?i)(Bearer\s+|(?:api[_-]?key|authorization|token)[\"\s:=]+)[A-Za-z0-9_.-]{12,}',r'\1[已隐藏]',s)
 s=re.sub(r'\bsk-[A-Za-z0-9_-]+','[已隐藏]',s)
 return s[:limit]+('\n…［网页节选，后续内容省略］' if len(s)>limit else '')
def explain(name,inp):
 text='\n'.join(str(v) for v in inp.values());low=text.lower();path=inp.get('file_path',inp.get('path',''));cmd=inp.get('command','')
 if name=='Read':
  if re.search(r'\.(png|jpe?g|webp|gif)$',path,re.I):return (0 if '/inputs/' in path else 3),'打开参考图或制作过程中的图像',path
  return (0 if '/inputs/' in path else 4),'读取题目与附件' if '/inputs/' in path else '读取脚本或运行记录',path
 if name in ['Write','Edit','MultiEdit']:
  features=[label for pat,label in [(r'primitive_|from_pydata|bmesh|geometrynode','几何物体'),(r'material|bsdf|shadernode','材质'),(r'light|world.color','灯光'),(r'camera|lens|look_at','相机'),(r'keyframe|frame_set|frame_end','动画'),(r'render\.|cycles','渲染设置'),(r'ImageDraw|ImageFont|from PIL','贴图图像'),(r'save_as_mainfile','保存工程')] if re.search(pat,text,re.I)]
  return 1,('写入文件' if name=='Write' else '修改文件')+('：'+'、'.join(features) if features else '，准备或调整制作内容'),path
 if name=='Bash':
  target=cmd.splitlines()[0][:200] if cmd else ''
  if re.search(r'blender[^\n]*(?: -b|--background| -P|--python)',cmd):return 2,'调用后台 Blender，执行脚本或渲染',target
  if ('bpy' in cmd or re.search(r'cat\s*>.*\.py|write_text\(',cmd)) and ('<<' in cmd or 'write_text' in cmd):return 1,'通过终端写入或调整 Python / bpy 脚本',target
  if 'ffmpeg' in cmd or 'ffprobe' in cmd:return 3,'用 FFmpeg 提取帧、检查或编码视频',target
  if '/inputs/' in cmd and any(x in cmd for x in ['cat ','ls ','find ','head ']):return 0,'读取题目、附件或参考文件清单',target
  if any(x in low for x in ['tail ','grep ','ps ','sleep ','pgrep','kill ','traceback']):return 4,'检查进程或日志，跟进执行状态与问题',target
  if any(x in low for x in ['exports','final.blend','file ','identify']):return 3,'检查或整理交付文件',target
  return 4,'执行终端命令，准备环境或检查制作状态',target
 return 4,{'Grep':'搜索代码或运行日志','Glob':'查找文件路径'}.get(name,'调用工具 '+name),path or inp.get('pattern','')
def parse(log):
 events=[];byid={}
 for line_no,line in enumerate(log.open(errors='replace'),1):
  try:d=json.loads(line)
  except ValueError:continue
  message=d.get('message',{})
  if not isinstance(message,dict):continue
  blocks=message.get('content',[])
  if not isinstance(blocks,list):continue
  for b in blocks:
   if b.get('type')=='tool_use' and b.get('id') not in byid:
    inp=b.get('input',{});name=b.get('name','');stage,title,target=explain(name,inp)
    evidence=inp.get('content','') if name=='Write' else ('替换前：\n'+str(inp.get('old_string',''))+'\n替换后：\n'+str(inp.get('new_string','')) if name=='Edit' else (inp.get('command','') if name=='Bash' else json.dumps(inp,ensure_ascii=False,indent=2)))
    # Preserve a compact index of code signals even when the long script is truncated.
    patterns=[r'bpy\.ops\.mesh\.\w+',r'ShaderNode\w+',r'lights\.new\([^\n]{0,120}',r'(?:camera|cam)\.(?:lens|location|rotation_euler)[^\n]{0,120}',r'(?:render\.(?:engine|resolution_x|resolution_y|filepath)|cycles\.(?:samples|use_denoising))\s*=[^\n]{0,110}',r'keyframe_insert\([^\n]{0,110}|frame_end\s*=[^\n]{0,60}',r'bpy\.ops\.wm\.save_as_mainfile\([^\n]{0,130}',r'def\s+\w+\(']
    signals=[]
    for pattern in patterns:signals.extend(dict.fromkeys(re.findall(pattern,evidence)) .keys())
    signals=list(dict.fromkeys(signals))[:60]
    item={'signals':signals,'n':len(events)+1,'tool':name,'stage':STAGES[stage],'title':title,'target':clean(target,240),'evidence':clean(evidence),'line':line_no,'time':d.get('timestamp',''),'result':'日志未匹配到返回内容','error':False,'id':b.get('id')};events.append(item);byid[b.get('id')]=item
   elif b.get('type')=='tool_result' and b.get('tool_use_id') in byid:
    event=byid[b['tool_use_id']];c=b.get('content','');txt=c if isinstance(c,str) else '\n'.join(x.get('text','') for x in c if x.get('type')=='text') if isinstance(c,list) else ''
    isimage=isinstance(c,list) and any(x.get('type')=='image' for x in c)
    event['error']=bool(b.get('is_error'));event['result']=clean(txt,1800) or ('工具返回图像内容；不复制日志图像编码。' if isimage else '工具已返回，未附文本。')
 return events

def build(out):
 out=Path(out);dest=out/'trajectories';dest.mkdir(exist_ok=True);index=[];previews=json.loads((out/'batch30/previews.json').read_text())['runs'];retries=json.loads((ROOTS[1]/'results/retry_summary.json').read_text())['runs']
 for root in ROOTS:
  initial=root==ROOTS[0];tasks=['bw_0003','bw_0006','bw_0100','bw_0111','bw_0214'] if initial else json.loads((root/'results/comparison.json').read_text())['state']['tasks'];prefix='' if initial else 'batch30/'
  for task in tasks:
   txt=(out/prefix/'tasks'/task/'index.html').read_text();match=re.search(r'<h1>(.*?)</h1>',txt,re.S);title=re.sub('<[^>]+>','',html.unescape(match[1])) if match else task
   for role in ['opus','astra']:
    log=root/'logs'/f'generation_{role}_{task}.jsonl';events=parse(log);state=json.loads((root/'results'/f'generation_{role}_{task}.json').read_text());resultfile=out/prefix/'evaluation'/role/task/'tasks'/task/'result.json'
    if not resultfile.exists():resultfile=out/f'batch30/results/{role}_{task}.json'
    score=json.loads(resultfile.read_text()).get('score');key=task+'_'+role
    media=[{**x,'url':'../batch30/'+x['url'],'thumbnail':'../batch30/'+(x.get('thumbnail') or x['url'])} for x in previews.get(task+'/'+role,[])][:3] if not initial else []
    if initial:
     if task=='bw_0214':media=[{'kind':'video','name':'提交视频预览','url':f'../media/{role}.mp4'}]
     else:
      for fig in re.findall(r'<figure>(.*?)</figure>',(out/'pilot.html').read_text(),re.S):
       pic=re.search(r'<img[^>]*src="([^"]+)"',fig)
       if role+' · '+task in fig and pic:
        url='../'+pic[1]
        if pic[1].startswith('data:image/'):
         header,payload=pic[1].split(',',1);extension='png' if 'image/png' in header else 'jpg';url=f'preview_{task}_{role}.{extension}';(dest/url).write_bytes(base64.b64decode(payload))
        media=[{'kind':'image','name':'提交产物预览','url':url,'thumbnail':url}];break
    record={'key':key,'task':task,'role':role,'title':title,'tools':dict(collections.Counter(x['tool'] for x in events)),'stages':dict(collections.Counter(x['stage'] for x in events)),'calls':len(events),'errors':sum(x['error'] for x in events),'seconds':state.get('seconds'),'score':score,'retry':not initial and any(r['task']==task and r['role']==role for r in retries),'input':'../'+prefix+'tasks/'+task+'/index.html','scoreUrl':'../'+str(resultfile.relative_to(out)),'media':media,'log':str(log.relative_to(root)),'batch':root.name,'sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'blend_exists':state.get('blend_exists'),'events':events}
    (dest/(key+'.json')).write_text(json.dumps(record,ensure_ascii=False));index.append({k:v for k,v in record.items() if k not in ['events','media']})
 (dest/'index.json').write_text(json.dumps(index,ensure_ascii=False));(dest/'index.html').write_text((Path(__file__).parent/'trajectory_page.html').read_text())
 for p in [out/'index.html',out/'batch30/index.html']:
  content=p.read_text();url='trajectories/' if p.parent==out else '../trajectories/'
  if 'data-trajectory-nav' not in content:content=content.replace('<h1',f'<nav data-trajectory-nav><a href="{url}">模型究竟怎样制作 Blender？查看轨迹解读 →</a></nav><h1',1)
  if p==out/'index.html':
   content=re.sub(r'(<a href="(?:batch30/results/(opus|astra)_(bw_\d+)\.json|evaluation/(opus|astra)/(bw_\d+)/tasks/bw_\d+/result\.json)">评分详情</a>)(?! · <a data-trajectory-run)',lambda m:m[1]+f' · <a data-trajectory-run href="trajectories/?task={m[3] or m[5]}&amp;model={m[2] or m[4]}">制作轨迹</a>',content)
  p.write_text(content)
 for initial in [True,False]:
  prefix='' if initial else 'batch30/'
  for p in (out/prefix/'tasks').glob('bw_*/index.html'):
   task=p.parent.name;content=p.read_text();rel='../../../trajectories/' if not initial else '../../trajectories/'
   if 'data-trajectory-nav' not in content:
    nav='<nav data-trajectory-nav>'+' · '.join(f'<a href="{rel}?task={task}&amp;model={role}">{label} 制作轨迹</a>' for role,label in [('opus','Opus'),('astra','Astra')])+'</nav>';p.write_text(content.replace('<h1',nav+'<h1',1))
 print('Trajectories:',len(index),'runs;',sum(x['calls'] for x in index),'tool calls')
if __name__=='__main__':
 import sys
 build(Path(sys.argv[1] if len(sys.argv)>1 else 'public'))
