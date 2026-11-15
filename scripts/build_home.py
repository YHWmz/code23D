"""Build a unified 35-task homepage from exported, immutable snapshot data."""
from pathlib import Path
import json,html,re
E=html.escape
def build(out):
 legacy=out/'pilot.html'
 legacy.write_text((out/'index.html').read_text())
 old=legacy.read_text();pictures={}
 for fig in re.findall(r'<figure>(.*?)</figure>',old,re.S):
  key=re.search(r'(opus|astra) · (bw_\d+)',fig);img=re.search(r'<img[^>]*src="([^"]+)"',fig)
  if key and img:pictures[(key[2],key[1])]=img[1]
 batch=json.loads((out/'batch30/comparison.json').read_text());snapshot=json.loads((out/'snapshot.json').read_text());previews=json.loads((out/'batch30/previews.json').read_text())['runs']
 initial=['bw_0003','bw_0006','bw_0100','bw_0111','bw_0214'];new=batch['state']['tasks'];lookup={(r['task'],r['role']):r for r in batch['runs']}
 rows=[];scored=0;total_previews=0;paired=[]
 for tid in new+initial:
  isnew=tid in new;prefix='batch30/' if isnew else '';values=[];cells=[]
  input_page=out/prefix/'tasks'/tid/'index.html';heading=re.search(r'<h1>(.*?)</h1>',input_page.read_text());title=heading[1] if heading else tid
  for role in ['opus','astra']:
   if isnew:r=lookup[(tid,role)]
   else:
    result=json.loads((out/'evaluation'/role/tid/'tasks'/tid/'result.json').read_text());r={'status':'已评分','score':result['score']}
   score=r.get('score');values.append(score);scored+=score is not None
   content=f'<p class="status">{E(r["status"])}'+(f' · <b>{score:.2f}</b>' if score is not None else '')+'</p>'
   items=previews.get(tid+'/'+role,[]) if isnew else []
   if isnew and items:
    total_previews+=1
    for i,item in enumerate(items):
     url='batch30/'+item['url']
     if item['kind']=='video':media=f'<video controls playsinline preload="none" src="{E(url)}"></video>'
     else:media=f'<a href="{E(url)}" target="_blank" rel="noopener"><img loading="lazy" src="{E("batch30/"+item["thumbnail"])}" alt="{tid} {role} 产物预览"></a>'
     figure=f'<figure>{media}<figcaption>{E(item["name"])}</figcaption></figure>'
     if i==1:content+=f'<details><summary>更多产物（{len(items)-1}）</summary>'
     content+=figure
    if len(items)>1:content+='</details>'
   elif not isnew:
    total_previews+=1
    if tid=='bw_0214':content+=f'<video controls playsinline preload="none" src="media/{role}.mp4"></video>'
    elif (tid,role) in pictures:content+=f'<img loading="lazy" src="{pictures[tid,role]}" alt="{tid} {role} 产物预览">'
   else:content+='<p class="muted">尚无已打包产物预览</p>'
   if score is not None:
    url=f'batch30/results/{role}_{tid}.json' if isnew else f'evaluation/{role}/{tid}/tasks/{tid}/result.json'
    content+=f'<a href="{url}">评分详情</a>'
   cells.append('<td>'+content+'</td>')
  if all(v is not None for v in values):paired.append(values)
  rows.append(f'<tr data-batch="{"new" if isnew else "initial"}"><td><span class="badge">{"新增 30 题" if isnew else "首批 5 题"}</span><h3>{title}</h3><a href="{prefix}tasks/{tid}/index.html">查看原始输入 →</a></td>'+''.join(cells)+'</tr>')
 means=[sum(p[i] for p in paired)/len(paired) for i in range(2)] if paired else [0,0]
 doc='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BlenderWorld · 35 题模型对比总览</title><style>body{margin:0;background:#f4f7fb;color:#203047;font:16px/1.6 system-ui,sans-serif}main{max-width:1380px;margin:auto;padding:32px 20px}h1{font-size:32px;line-height:1.3}nav{display:flex;gap:20px;flex-wrap:wrap}a{color:#175ac6}aside{background:#fff4d6;padding:14px;margin:20px 0;border-radius:8px}.stats{display:flex;gap:16px;flex-wrap:wrap}.stats div{background:white;padding:16px 24px;border-radius:12px}.stats b{font-size:28px;display:block}.scroll{overflow:auto}table{width:100%;table-layout:fixed;border-collapse:collapse;background:white;margin-top:18px}th,td{padding:16px;border-bottom:1px solid #dde4ed;text-align:left;vertical-align:top}th:first-child{width:23%}h3{font-size:16px;overflow-wrap:anywhere}img,video{width:100%;max-height:320px;object-fit:contain;background:#eef2f7;border-radius:8px}figure{margin:10px 0}figcaption,.muted{font-size:13px;color:#627186;overflow-wrap:anywhere}summary{cursor:pointer;color:#175ac6}.badge{font-size:12px;background:#e6eefb;padding:4px 8px;border-radius:5px}select{padding:9px;margin:14px 0}tr[hidden]{display:none}@media(max-width:700px){table{min-width:760px}main{padding:20px 12px}}</style></head><body><main><h1>BlenderWorld · 35 题模型对比总览</h1><p>Claude Opus 5.5 与 GPT-6-Astra · 首批 5 题 + 新增 30 题，共 70 次计划运行。</p>'''
 doc+=f'<nav><a href="#task-inputs">全部题目与产物</a><a href="batch30/index.html">新增 30 题详细进度</a><a href="pilot.html#task-setup">任务设置与流程图</a><a href="pilot.html">首批五题完整报告</a></nav><aside>公开审核快照：{E(snapshot["exported_at"])}。失败与未完成任务不记作有效零分。公网结果随仓库更新；完整工程 ZIP 保存在实验服务器，大图为网页压缩版。</aside><div class="stats"><div><b>35</b>不同题目</div><div><b>{scored} / 70</b>成功评分</div><div><b>{total_previews}</b>已有产物预览</div><div><b>{len(paired)}</b>双方均已评分的题目</div></div><p>仅比较双方都已评分的 {len(paired)} 道题：Claude {means[0]:.2f}，Astra {means[1]:.2f}。这是阶段性结果，并非全量 benchmark 排名。</p><label>显示范围：<select id="filter"><option value="all">全部 35 题</option><option value="new">新增 30 题</option><option value="initial">首批 5 题</option></select></label><div class="scroll" id="task-inputs"><table><thead><tr><th>任务与输入</th><th>Claude Opus 5.5</th><th>GPT-6-Astra</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></main><script>document.getElementById("filter").onchange=e=>{document.querySelectorAll("tr[data-batch]").forEach(r=>r.hidden=e.target.value!=="all"&&r.dataset.batch!==e.target.value)};</script></body></html>'
 if (out/'batch30/retry_summary.json').exists():doc=doc.replace('<nav>','<p><a href="batch30/retry_summary.json">查看失败任务补跑记录</a></p><nav>',1)
 (out/'index.html').write_text(doc)
 p=out/'batch30/index.html';p.write_text(p.read_text().replace('← 原五题审核主页','← 全部 35 题总览'))
 print('Homepage:',len(new)+len(initial),'tasks;',scored,'scored;',total_previews,'previews')
