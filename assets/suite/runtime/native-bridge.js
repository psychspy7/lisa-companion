// Only the local Qt page receives this object. Provider keys never enter the DOM.
export async function connectNative(character){
 if(!window.qt?.webChannelTransport)return null;
 await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='qrc:///qtwebchannel/qwebchannel.js';s.onload=resolve;s.onerror=reject;document.head.append(s);});
 return await new Promise(resolve=>new QWebChannel(qt.webChannelTransport,channel=>{
  const bridge=channel.objects.companion,$=id=>document.getElementById(id);let lastReply='';
  window.lisaNative=bridge;
  const state=value=>{try{const s=JSON.parse(value);character.setSpeechLevel(s.talking?s.speechLevel:0);character.setEmotion?.(s.mood);
   if(s.reply&&s.reply!==lastReply){$('reply').textContent=s.reply;lastReply=s.reply;}
   if(s.busy||s.conversation||s.updateNote)$('activity').textContent=s.updateNote||s.status;
   $('mic').setAttribute('aria-pressed',String(s.conversation));$('mic').setAttribute('aria-label',s.conversation?'End conversation':'Start continuous conversation');
  }catch{}};
  bridge.stateChanged.connect(state);bridge.sceneAction.connect(value=>character.perform(value));
  $('composer').onsubmit=e=>{e.preventDefault();const t=$('message').value.trim();if(t){bridge.send(t);$('message').value='';}};
  $('mic').onclick=()=>bridge.toggleVoice();
  $('speak').closest('.setting-row').hidden=true;
  $('activity').textContent='Ready · voice starts only when you tap the microphone';
  const interrupt=document.createElement('button');interrupt.type='button';interrupt.className='icon';interrupt.textContent='■';interrupt.title='Interrupt Lisa';interrupt.setAttribute('aria-label','Interrupt Lisa’s reply');interrupt.onclick=()=>bridge.bargeIn();$('composer').append(interrupt);
  const recovery=document.createElement('button');recovery.textContent='Local recovery settings';recovery.onclick=()=>bridge.localRecoverySettings();$('settings').append(recovery);
  for(const [label,method] of [['Sign in with Google','login'],['Sign out desktop','logout'],['Saved memories','memories'],['Motion studio','studio'],['Control center','openControlCenter'],['Check for updates','checkUpdate'],['Interrupt / stop','interrupt'],['Quit Lisa','quit']]){
   const b=document.createElement('button');b.className='wide';b.textContent=label;b.onclick=()=>bridge[method]();$('settings').append(b);
  }
  $('fullscreen').onclick=()=>bridge.toggleFullscreen();
  document.querySelector('.preview-note').textContent='LISA · private room · created by Virat with Kitty Corp';
  bridge.snapshot(state);resolve(bridge);
 }));
}
