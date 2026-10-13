import { chromium } from 'file:///C:/Users/HP/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs';
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--allow-file-access-from-files','--no-proxy-server']});
const page=await browser.newPage({viewport:{width:1280,height:800}});
page.on('pageerror',e=>console.log('Page:',e.message));
await page.goto('file:///C:/Users/HP/Downloads/Project%20(Kitty-Corp)/LISA%20AI/2026-10-02/hi/outputs/LISA-Source/assets/suite/runtime/room.html');
await page.waitForFunction(()=>window.lisaRoom?.ready,{timeout:60000});
const data=await page.evaluate(()=>{
 const s=window.lisaRoom; const geometries={},materials={},textures={},nodes=[];
 s.room.updateMatrixWorld(true);
 s.room.traverse(o=>{
  if(!o.isMesh)return;
  const g=o.geometry,m=o.material;if(Array.isArray(m))throw Error('Unexpected materials');
  if(!geometries[g.uuid]){const attrs={};for(const key of ['position','normal','uv'])if(g.attributes[key])attrs[key]=Array.from(g.attributes[key].array);geometries[g.uuid]={attrs,index:g.index?Array.from(g.index.array):null};}
  if(!materials[m.uuid]){
   let texture=null;if(m.map){texture=m.map.uuid;if(!textures[texture]){const c=document.createElement('canvas');c.width=m.map.image.width;c.height=m.map.image.height;c.getContext('2d').drawImage(m.map.image,0,0);textures[texture]=c.toDataURL('image/png');}}
   materials[m.uuid]={color:m.color.toArray(),roughness:m.roughness??1,metalness:m.metalness??0,emissive:m.isMeshBasicMaterial?m.color.toArray():m.emissive?.toArray()??[0,0,0],alpha:m.opacity,transparent:m.transparent,doubleSided:m.side===2,texture};
  }
  let ancestor=o.parent,role='';while(ancestor){if(['bathroom_door','balcony_door'].includes(ancestor.name)){role=ancestor.name;break;}ancestor=ancestor.parent;} nodes.push({name:o.name||'detail',role,geometry:g.uuid,material:m.uuid,matrix:o.matrixWorld.toArray()});
 });
 return {geometries,materials,textures,nodes,anchors:s.anchors,views:s.views,fixtures:s.fixtures.map(f=>({id:f.id,position:f.position,target:f.target,intensity:f.intensity,color:f.color}))};
});
fs.writeFileSync('work/lisa-2.1/room-export.json',JSON.stringify(data));console.log('Exported',data.nodes.length,'meshes',Object.keys(data.geometries).length,'geometries');await browser.close();

