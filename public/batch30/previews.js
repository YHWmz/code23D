(()=>{
const style=document.createElement('style');style.textContent='.artifact-previews{min-width:220px;max-width:420px}.artifact-previews figure{margin:14px 0}.artifact-previews img,.artifact-previews video{width:100%;max-height:300px;object-fit:contain;background:#edf1f7;border-radius:8px}.artifact-previews figcaption{font-size:12px;overflow-wrap:anywhere;color:#526176}.artifact-previews summary{cursor:pointer;color:#175ac6}';document.head.append(style);
async function update(){
 const data=await fetch('previews.json',{cache:'no-store'}).then(r=>r.json());
 for(const row of document.querySelectorAll('table tr')){
  const link=row.querySelector('a[href^="tasks/"]');if(!link)continue;
  const tid=link.getAttribute('href').split('/')[1];
  ['opus','astra'].forEach((role,index)=>{
   const cell=row.cells[index+2],items=data.runs[tid+'/'+role]||[];if(!cell||!items.length)return;
   const key=JSON.stringify(items);let box=cell.querySelector('.artifact-previews');if(box?.dataset.key===key)return;
   if(!box){box=document.createElement('div');box.className='artifact-previews';cell.append(box);}box.replaceChildren();box.dataset.key=key;
   items.forEach((item,i)=>{
    const fig=document.createElement('figure');
    if(item.kind==='video'){const video=document.createElement('video');video.controls=true;video.preload='metadata';video.playsInline=true;video.src=item.url;fig.append(video);}
    else {const a=document.createElement('a');a.href=item.url;a.target='_blank';a.rel='noopener';const img=document.createElement('img');img.src=item.thumbnail;img.alt=tid+' '+role+' '+item.name;img.loading='lazy';a.append(img);fig.append(a);}
    const caption=document.createElement('figcaption');caption.textContent=item.name+(item.kind==='image'?' · 点击查看大图（网页压缩版）':' · 提交视频');fig.append(caption);
    if(i===0)box.append(fig);else{let more=box.querySelector('details');if(!more){more=document.createElement('details');const summary=document.createElement('summary');summary.textContent='更多产物（'+(items.length-1)+'）';more.append(summary);box.append(more);}more.append(fig);}
   });
  });
 }
}
update().catch(console.error);
// Avoid interrupting video playback with the report's timed page refresh.
document.querySelector('meta[http-equiv="refresh"]')?.remove();

})();
