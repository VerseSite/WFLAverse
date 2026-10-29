/* Campus concept model adapted from the supplied frontend (Three.js r128). */
(()=>{
const ZONES=[{"k": "community", "name": "同学资料", "href": "/members/", "desc": "认识校园里的同学", "pos": [-2.4, 0, 1.5], "col": 10454775}, {"k": "gallery", "name": "校园影像 · 筹备中", "desc": "摄影与艺术作品", "pos": [2.7, 0, 2.0], "col": 15903181, "wip": true}, {"k": "campus", "name": "校园生活 · 筹备中", "desc": "学生参与建设的校园空间", "pos": [-0.3, 0, -1.0], "col": 8369914, "wip": true}, {"k": "opportunities", "name": "委托与招聘 · 筹备中", "desc": "未来的竞赛组队与社团招募", "pos": [-0.2, 0, 2.9], "col": 10343352, "wip": true}, {"k": "projects", "name": "学生项目 · 筹备中", "desc": "展示学生创造的作品", "pos": [-3.2, 0, -1.7], "col": 8152296, "wip": true}, {"k": "media", "name": "校园故事 · 筹备中", "desc": "分享经验与想法", "pos": [3.6, 0, -0.4], "col": 9290751, "wip": true}, {"k": "assistant", "name": "更多可能 · 筹备中", "desc": "等待大家一起建设", "pos": [2.4, 0, -3.4], "col": 14077183, "wip": true}];
function webglOK(){try{const c=document.createElement('canvas');return!!(window.THREE&&(c.getContext('webgl')||c.getContext('experimental-webgl')))}catch(e){return false}}
function Campus3D(host,opts={}){
 const mode=opts.mode||'hero';const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(!webglOK()){host.innerHTML=campusFallback();return{destroy(){},focus(){},reset(){}}}
 const T=THREE;const W=()=>host.clientWidth,H=()=>host.clientHeight;
 const renderer=new T.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(W(),H(),false);
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;renderer.outputEncoding=T.sRGBEncoding;
  host.replaceChildren();host.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-hidden','true');
 const labelLayer=document.createElement('div');labelLayer.className='absolute inset-0 pointer-events-none';host.appendChild(labelLayer);
 const scene=new T.Scene();const camera=new T.PerspectiveCamera(mode==='hero'?32:38,W()/H(),.1,100);
 const isDark=()=>document.documentElement.dataset.theme==='dark'||(!document.documentElement.dataset.theme&&matchMedia('(prefers-color-scheme: dark)').matches);
 const hemi=new T.HemisphereLight(0xEDE6FF,0xA9C4F0,.62);scene.add(hemi);
 const sun=new T.DirectionalLight(0xFFF6EE,1.05);sun.position.set(6,10,5);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);sun.shadow.radius=6;
 Object.assign(sun.shadow.camera,{left:-8,right:8,top:8,bottom:-8,near:1,far:30});scene.add(sun);
 const rim=new T.DirectionalLight(0xB8C8FF,.35);rim.position.set(-6,4,-6);scene.add(rim);
 const world=new T.Group();scene.add(world);
 const M=(c,o={})=>new T.MeshStandardMaterial(Object.assign({color:c,roughness:.82,metalness:.02,flatShading:true},o));
 const add=(geo,mat,x,y,z,parent=world,cast=true)=>{const m=new T.Mesh(geo,mat);m.position.set(x,y,z);m.castShadow=cast;m.receiveShadow=true;parent.add(m);return m};

 /* island */
 const top=add(new T.CylinderGeometry(5.6,5.3,.5,48),M(0xEDE8FF),0,-.25,0,world,false);
 add(new T.CylinderGeometry(5.3,2.2,2.4,24,3),M(0xB4A6EE),0,-1.7,0,world,false);
 add(new T.ConeGeometry(2.2,2.2,18),M(0x9C8CE6),0,-4,0,world,false).rotation.x=Math.PI;
 const lawn=add(new T.CylinderGeometry(5.25,5.25,.06,48),M(0xCFE9CF),0,.03,0,world,false);lawn.receiveShadow=true;
 // paths
 const pathM=M(0xFFFFFF,{roughness:1});
 [[0,0,.02,.9,7.6,0],[0,0,.02,.9,7.6,Math.PI/2],[0,0,.02,.7,6,Math.PI/4]].forEach(p=>{const m=add(new T.BoxGeometry(p[3],.05,p[4]),pathM,0,.07,0,world,false);m.rotation.y=p[5]});
 add(new T.CylinderGeometry(1.15,1.15,.06,32),pathM,0,.08,0,world,false);
 // pond under bridge
 const pond=add(new T.CylinderGeometry(1.05,1.05,.04,32),M(0xA9D2FF,{roughness:.2,metalness:.1}),-.2,.1,3.3,world,false);pond.scale.z=.55;

 /* buildings */
 const zoneObjs={};
 const mk=(z)=>{const g=new T.Group();g.position.set(...z.pos);world.add(g);const c=M(z.col),w=M(0xFFFFFF),dk=M(new T.Color(z.col).multiplyScalar(.82).getHex());const glass=M(0xDCEBFF,{roughness:.15,metalness:.3,emissive:0x000000});
  if(z.k==='community'){add(new T.CylinderGeometry(1,1.05,.14,24),w,0,.07,0,g);for(let i=0;i<6;i++){const a=i/6*Math.PI*2;add(new T.CylinderGeometry(.06,.06,.9,8),w,Math.cos(a)*.75,.55,Math.sin(a)*.75,g)}add(new T.ConeGeometry(1.1,.55,6),c,0,1.27,0,g);add(new T.SphereGeometry(.16,12,10),dk,0,1.62,0,g)}
  if(z.k==='gallery'){add(new T.BoxGeometry(1.9,.7,1),w,0,.35,0,g);for(let i=0;i<3;i++){const r=add(new T.BoxGeometry(.62,.08,1.04),c,-.62+i*.62,.86,0,g);r.rotation.z=.45}add(new T.BoxGeometry(1.6,.36,.04),glass,0,.32,.52,g)}
  if(z.k==='campus'){add(new T.BoxGeometry(2.1,.9,1.1),w,0,.45,0,g);add(new T.BoxGeometry(2.2,.12,1.2),c,0,.96,0,g);add(new T.BoxGeometry(.55,1.9,.55),w,0,1.2,0,g);add(new T.ConeGeometry(.45,.6,4),c,0,2.45,0,g).rotation.y=Math.PI/4;const clk=add(new T.CylinderGeometry(.16,.16,.04,20),M(0x6447D6),0,1.8,.28,g);clk.rotation.x=Math.PI/2;for(let i=0;i<4;i++)add(new T.BoxGeometry(.28,.36,.04),glass,-.75+i*.5,.42,.56,g)}
  if(z.k==='opportunities'){const arc=new T.TorusGeometry(.85,.09,8,24,Math.PI);const a1=add(arc,c,0,.12,-.22,g);const a2=add(arc,c,0,.12,.22,g);const deck=add(new T.BoxGeometry(1.9,.06,.5),w,0,.42,0,g);deck.rotation.z=0;for(let i=-3;i<=3;i++)add(new T.BoxGeometry(.04,.3,.04),w,i*.26,.58,.22,g)}
  if(z.k==='projects'){add(new T.BoxGeometry(1.2,1.2,1.2),glass,0,.6,0,g);add(new T.BoxGeometry(1.28,.1,1.28),c,0,1.25,0,g);add(new T.BoxGeometry(1.28,.1,1.28),c,0,.05,0,g);const cube=add(new T.OctahedronGeometry(.28),M(0xB3A2FF,{emissive:0x5B3FD0,emissiveIntensity:.25}),0,1.75,0,g);cube.userData.spin=true}
  if(z.k==='media'){add(new T.CylinderGeometry(.75,.8,.8,20),w,0,.4,0,g);add(new T.SphereGeometry(.75,20,12,0,Math.PI*2,0,Math.PI/2),c,0,.8,0,g);add(new T.CylinderGeometry(.03,.03,.8,6),w,.3,1.6,0,g);add(new T.SphereGeometry(.09,10,8),M(0xF6C6DE,{emissive:0xF06292,emissiveIntensity:.5}),.3,2.02,0,g)}
  if(z.k==='assistant'){add(new T.CylinderGeometry(.6,.65,.6,16),w,0,.3,0,g);const d=add(new T.SphereGeometry(.6,16,10,0,Math.PI*2,0,Math.PI/2),M(0xE6DEFF,{wireframe:true}),0,.6,0,g);for(let i=0;i<4;i++){const a=i/4*Math.PI*2+.4;add(new T.BoxGeometry(.04,1.5,.04),M(0xC6B9F5),Math.cos(a)*.8,.75,Math.sin(a)*.8,g)}add(new T.BoxGeometry(1.7,.04,.04),M(0xC6B9F5),0,1.2,.56,g)}
  g.traverse(o=>{if(o.isMesh){o.userData.zone=z.k;o.userData.base=o.material.emissive?o.material.emissive.getHex():0}});
  zoneObjs[z.k]={g,z};};
 ZONES.forEach(mk);
 /* trees */
 const treeM=[M(0x9ED39A),M(0x8CCBB0),M(0xC3B2FF)],trunk=M(0xC2B1A0);
 const tr=[[-4.4,0,.2],[-4,0,2.4],[4.5,0,.4],[4.2,0,2.6],[-1.4,0,-3.4],[3.6,0,-3],[-3.6,0,-3.3],[1.6,0,3.9],[-2.2,0,4.1],[4.7,0,-1.6],[-4.8,0,-1.2],[2,0,-.4],[-1.6,0,.2]];
 tr.forEach((p,i)=>{add(new T.CylinderGeometry(.05,.07,.4,6),trunk,p[0],.2,p[2]);const s=.28+((i*37)%10)/40;i%3===0?add(new T.ConeGeometry(s,s*2.4,7),treeM[i%3],p[0],.4+s*1.2,p[2]):add(new T.IcosahedronGeometry(s,0),treeM[i%3],p[0],.45+s,p[2])});
 /* clouds + motes */
 const clouds=[];const cm=M(0xFFFFFF,{transparent:true,opacity:.92});
 for(let i=0;i<4;i++){const c=new T.Group();for(let j=0;j<4;j++)add(new T.IcosahedronGeometry(.32+j%2*.12,1),cm,j*.38-.6,(j%2)*.12,(j%3)*.1,c,false);const a=i/4*Math.PI*2;c.position.set(Math.cos(a)*7,1.8+i%2*1.2,Math.sin(a)*7);c.userData.a=a;c.userData.r=6.6+i%2;scene.add(c);clouds.push(c)}
 const pg=new T.BufferGeometry();const pts=new Float32Array(240*3);for(let i=0;i<240;i++){pts[i*3]=(Math.random()-.5)*16;pts[i*3+1]=Math.random()*7-1;pts[i*3+2]=(Math.random()-.5)*16}pg.setAttribute('position',new T.BufferAttribute(pts,3));
 const motes=new T.Points(pg,new T.PointsMaterial({color:0xB8A6F7,size:.05,transparent:true,opacity:.7}));scene.add(motes);

 /* theme */
 function applyTheme(){const d=isDark();hemi.color.set(d?0x6E5ACF:0xEDE6FF);hemi.groundColor.set(d?0x1A2A55:0xBFD8FF);hemi.intensity=d?.7:.62;sun.intensity=d?.35:1.05;sun.color.set(d?0xBFC8FF:0xFFF6EE);
  motes.material.color.set(d?0xFFF3C4:0xB8A6F7);motes.material.size=d?.07:.05;cm.opacity=d?.25:.92;
  world.traverse(o=>{if(o.isMesh&&o.material.roughness<.3&&!o.material.wireframe){o.material.emissive.set(d?0xFFD98A:0x000000);o.material.emissiveIntensity=d?.55:0}})}
 applyTheme();const onTheme=()=>applyTheme();window.addEventListener('themechange',onTheme);const mq=matchMedia('(prefers-color-scheme: dark)');mq.addEventListener&&mq.addEventListener('change',onTheme);

 /* camera rig */
 const rig={yaw:-.55,pitch:mode==='hero'?.62:.68,dist:mode==='hero'?17:16.5,ty:.4,tx:0,tz:0};const goal={...rig};
 const place=()=>{camera.position.set(rig.tx+Math.sin(rig.yaw)*Math.cos(rig.pitch)*rig.dist,rig.ty+Math.sin(rig.pitch)*rig.dist,rig.tz+Math.cos(rig.yaw)*Math.cos(rig.pitch)*rig.dist);camera.lookAt(rig.tx,rig.ty,rig.tz)};
 /* labels */
 const labels={};ZONES.forEach(z=>{const b=document.createElement('button');b.className='c-label glass';b.innerHTML=`<span class="pin" ${z.wip?'style="background:var(--faint)"':''}></span>${z.name}`;b.setAttribute('aria-label',`${z.name}: ${z.desc}`);
  b.onmouseenter=()=>setHover(z.k);b.onmouseleave=()=>setHover(null);b.onfocus=()=>setHover(z.k);b.onblur=()=>setHover(null);b.onclick=()=>select(z.k);labelLayer.appendChild(b);labels[z.k]=b});
 /* hover + select */
 let hover=null,sel=null;const ray=new T.Raycaster(),mouse=new T.Vector2();
 function setHover(k){if(hover===k)return;hover=k;Object.entries(zoneObjs).forEach(([kk,o])=>{const on=kk===k||kk===sel;o.g.userData.lift=on?1:0;labels[kk].classList.toggle('hot',on)});renderer.domElement.style.cursor=k?'pointer':'grab';opts.onHover&&opts.onHover(k)}
 function select(k){const z=ZONES.find(x=>x.k===k);if(mode==='hero'){if(z.href)location.assign(z.href);else document.getElementById('modules')?.scrollIntoView({behavior:reduce?'instant':'smooth'});return}sel=k;focus(k);opts.onSelect&&opts.onSelect(z)}
 function focus(k){if(!k){reset();return}const z=ZONES.find(x=>x.k===k);sel=k;setHover(null);setHover(k);Object.assign(goal,{tx:z.pos[0]*.85,tz:z.pos[2]*.85,ty:.6,dist:9.5,pitch:.5,yaw:Math.atan2(z.pos[0],z.pos[2])||goal.yaw});auto=false}
 function reset(){sel=null;setHover(null);Object.assign(goal,{tx:0,tz:0,ty:.4,dist:mode==='hero'?17:16.5,pitch:mode==='hero'?.62:.68});auto=!reduce}
 /* drag orbit */
 let drag=null,auto=!reduce,vel=0,lastInteract=0;const el=renderer.domElement;
 el.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,yaw:goal.yaw,pitch:goal.pitch,moved:false};el.setPointerCapture(e.pointerId);auto=false});
 el.addEventListener('pointermove',e=>{const r=el.getBoundingClientRect();mouse.x=(e.clientX-r.left)/r.width*2-1;mouse.y=-(e.clientY-r.top)/r.height*2+1;
  if(drag){const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>4)drag.moved=true;goal.yaw=drag.yaw-dx*.006;if(mode==='full')goal.pitch=Math.max(.25,Math.min(1.2,drag.pitch+dy*.004));vel=-(e.movementX||0)*.0006}else pick()});
 el.addEventListener('pointerup',e=>{const moved=drag&&drag.moved;drag=null;lastInteract=performance.now();if(!moved){pick();if(hover)select(hover)}});
 el.addEventListener('pointerleave',()=>{if(!drag)setHover(sel)});
 if(mode==='full')el.addEventListener('wheel',e=>{e.preventDefault();goal.dist=Math.max(7,Math.min(22,goal.dist+e.deltaY*.01))},{passive:false});
 function pick(){ray.setFromCamera(mouse,camera);const hit=ray.intersectObjects(world.children,true).find(h=>h.object.userData.zone);setHover(hit?hit.object.userData.zone:sel)}
 /* resize + visibility */
 const ro=new ResizeObserver(()=>{renderer.setSize(W(),H(),false);camera.aspect=W()/H();camera.updateProjectionMatrix();if(mode==='hero'){goal.dist=rig.dist=W()<640?23:19.5}});ro.observe(host);
 let visible=true;const vio=new IntersectionObserver(es=>{visible=es[0].isIntersecting;if(visible&&!raf)loop()},{threshold:0});vio.observe(host);
 /* loop */
 let raf=0,t0=performance.now();const v3=new T.Vector3();
 function loop(){raf=0;if(!visible)return;const t=(performance.now()-t0)/1000;
  if(auto&&!drag&&performance.now()-lastInteract>2500)goal.yaw+=.0016;goal.yaw+=vel;vel*=.92;
  for(const k of['yaw','pitch','dist','tx','ty','tz'])rig[k]+=(goal[k]-rig[k])*.07;place();
  world.position.y=reduce?0:Math.sin(t*.8)*.08;
  Object.values(zoneObjs).forEach(o=>{const L=o.g.userData.lift||0;o.g.position.y+=((L*.28)-o.g.position.y)*.12;const s=1+L*.06;o.g.scale.x+=(s-o.g.scale.x)*.12;o.g.scale.y=o.g.scale.z=o.g.scale.x});
  world.traverse(o=>{if(o.userData.spin){o.rotation.y=t*1.2;o.position.y=1.75+Math.sin(t*2)*.08}});
  clouds.forEach(c=>{c.userData.a+=reduce?0:.0009;c.position.x=Math.cos(c.userData.a)*c.userData.r;c.position.z=Math.sin(c.userData.a)*c.userData.r});
  motes.rotation.y=t*.02;
  renderer.render(scene,camera);
  const w=W(),h=H();ZONES.forEach(z=>{const o=zoneObjs[z.k].g;v3.set(0,({campus:3.05,projects:2.25,media:2.35,assistant:1.8,gallery:1.35,opportunities:1.15,community:1.95})[z.k]||1.9,0);o.localToWorld(v3);v3.project(camera);const b=labels[z.k];const behind=v3.z>1;const x=(v3.x+1)/2*w,y=(1-v3.y)/2*h;b.style.transform=`translate(${x}px,${y}px) translate(-50%,-100%)${(hover===z.k||sel===z.k)?' scale(1.06)':''}`;b.classList.toggle('dim',behind||(mode==='hero'&&w<520&&hover!==z.k&&!['community','gallery','campus'].includes(z.k)))});
  if(!reduce||drag||Math.abs(goal.yaw-rig.yaw)>.001||Math.abs(goal.dist-rig.dist)>.01)raf=requestAnimationFrame(loop);else raf=0}
 place();loop();
 return{focus,reset,destroy(){cancelAnimationFrame(raf);visible=false;ro.disconnect();vio.disconnect();window.removeEventListener('themechange',onTheme);mq.removeEventListener&&mq.removeEventListener('change',onTheme);renderer.dispose();host.innerHTML=''}};
}
function campusFallback(){return '<div class="campus-fallback p-6"><img src="/static/verse/island.svg" width="360" alt="悬浮校园岛插画"><p class="text-center muted mt-4">校园概念岛</p></div>';}

const host=document.getElementById('hero-campus');if(host){try{const model=Campus3D(host,{mode:'hero'});window.addEventListener('pagehide',()=>model.destroy(),{once:true});}catch(error){host.innerHTML=campusFallback();}}
})();
