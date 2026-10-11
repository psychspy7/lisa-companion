import {initializeApp} from 'firebase/app';
import {getAuth,GoogleAuthProvider,signInWithPopup,onAuthStateChanged,signOut,browserSessionPersistence,setPersistence} from 'firebase/auth';
const $=id=>document.getElementById(id);let user=null,config=null,auth=null;
function status(text){$('status').textContent=text;}
async function request(path,options={}){
 const headers={'Content-Type':'application/json',...(options.headers||{})};if(user)headers.Authorization='Bearer '+await user.getIdToken();
 const r=await fetch(path,{...options,headers});let data;try{data=await r.json();}catch{throw Error('Lisa service returned an unreadable response.');}
 if(!r.ok)throw Error(data.error||'This request could not finish.');return data;
}
async function run(button,fn){button.disabled=true;try{await fn();}catch(e){status(e.message||'Could not complete this request.');}finally{button.disabled=false;}}
function providers(list,settings){
 $('providers').replaceChildren();
 for(const provider of list){
  const box=document.createElement('div');box.className='provider';
  const heading=document.createElement('div');heading.className='provider-title';
  const title=document.createElement('strong');title.textContent=provider.id;
  const badge=document.createElement('span');badge.className='badge';badge.textContent=provider.configured?'Key saved':'Not connected';heading.append(title,badge);box.append(heading);
  const key=document.createElement('input');key.type='password';key.autocomplete='new-password';key.placeholder='Paste a replacement API key';key.setAttribute('aria-label',provider.id+' API key');box.append(key);
  const model=document.createElement('input');model.placeholder=provider.id==='elevenlabs'?'Voice ID':'Model ID';model.value=settings[provider.id==='elevenlabs'?'eleven_voice_id':provider.id+'_model']||'';model.setAttribute('aria-label',provider.id+' model');
  if(['groq','gemini','openrouter','meta'].includes(provider.id))box.append(model);
  const row=document.createElement('div');row.className='row';
  const add=(label,fn)=>{const b=document.createElement('button');b.textContent=label;b.onclick=()=>run(b,fn);row.append(b);};
  add('Save key',async()=>{if(!key.value.trim())throw Error('Paste a complete key first.');await request('/api/admin/providers/'+provider.id,{method:'PUT',body:JSON.stringify({key:key.value.trim()})});key.value='';badge.textContent='Key saved';status(provider.id+' key saved securely.');});
  if(['groq','gemini','openrouter','meta'].includes(provider.id))add('Save model',async()=>{await request('/api/admin/settings',{method:'POST',body:JSON.stringify({[provider.id+'_model']:model.value.trim()})});status('Model saved.');});
  if(['groq','gemini','openrouter','meta','elevenlabs'].includes(provider.id)){
   const select=document.createElement('select');select.hidden=true;select.setAttribute('aria-label',provider.id+' available models or voices');box.append(select);
   add(provider.id==='elevenlabs'?'Load voices':'Load models',async()=>{const result=await request('/api/admin/providers/'+provider.id+'/models');select.replaceChildren();for(const m of result.models){const o=document.createElement('option');o.value=m.id;o.textContent=m.name+' · '+m.id;select.append(o);}select.hidden=false;select.onchange=()=>{if(provider.id==='elevenlabs')$('settings').elements.eleven_voice_id.value=select.value;else model.value=select.value;};select.dispatchEvent(new Event('change'));status('Choose a model or voice, then save it.');});
  }
  add('Test connection',async()=>{const result=await request('/api/admin/providers/'+provider.id+'/test',{method:'POST',body:'{}'});status(result.reply||result.note||provider.id+' connected.');});
  add('Remove key',async()=>{if(!confirm('Remove the saved '+provider.id+' key?'))return;await request('/api/admin/providers/'+provider.id,{method:'DELETE'});badge.textContent='Not connected';status('Provider key removed.');});
  box.append(row);$('providers').append(box);
 }
}
async function loadConsole(){
 const data=await request('/api/config');config=data.settings;$('owner').textContent=data.owner.email;
 for(const [k,v] of Object.entries(config)){const e=$('settings').elements.namedItem(k);if(e){if(e.type==='checkbox')e.checked=v;else e.value=v;}}
 providers(data.providers,config);$('welcome').hidden=true;$('console').hidden=false;$('logout').hidden=false;
 $('pairing').hidden=!new URL(location.href).searchParams.has('device');status('Connected. Your provider keys stay on the backend.');
}
$('settings').onsubmit=e=>{e.preventDefault();run(e.submitter,async()=>{const form=$('settings'),value={};for(const item of form.elements){if(!item.name)continue;value[item.name]=item.type==='checkbox'?item.checked:item.type==='number'?Number(item.value):item.value;}await request('/api/admin/settings',{method:'POST',body:JSON.stringify(value)});status('Lisa’s preferences are saved.');});};
$('approve').onclick=()=>run($('approve'),async()=>{const id=new URL(location.href).searchParams.get('device');await request('/api/device/approve',{method:'POST',body:JSON.stringify({device_id:id,user_code:$('pair-code').value,refresh_token:user.refreshToken})});$('pairing').hidden=true;history.replaceState({},'',location.pathname);status('Your desktop Lisa is linked. You can return to the app.');});
$('logout').onclick=()=>run($('logout'),async()=>{await signOut(auth);});
(async()=>{
 try{
  const firebase=await request('/api/login-config');if(!firebase.apiKey||!firebase.projectId)throw Error('Google sign-in is not configured yet.');
  auth=getAuth(initializeApp(firebase));await setPersistence(auth,browserSessionPersistence);
  $('login').onclick=()=>run($('login'),async()=>{const provider=new GoogleAuthProvider();provider.setCustomParameters({prompt:'select_account'});await signInWithPopup(auth,provider);});
  onAuthStateChanged(auth,async value=>{user=value;if(user){try{await loadConsole();}catch(e){$('console').hidden=true;$('welcome').hidden=false;status(e.message);}}else{$('console').hidden=true;$('welcome').hidden=false;$('logout').hidden=true;status('');}});
 }catch(e){status(e.message);$('login').disabled=true;}
})();
