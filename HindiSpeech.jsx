import {useCallback,useEffect,useRef,useState} from 'react';
import {useLanguage} from '../context/LanguageContext';
let currentStop=null;
export function stopHindiSpeech(){currentStop?.();}
function speechParts(text){return (text.match(/[^।!?\n]+[।!?\n]*/g)||[text]).flatMap(part=>{const pieces=[];for(let offset=0;offset<part.length;){let end=Math.min(offset+240,part.length);if(end<part.length){const boundary=part.lastIndexOf(' ',end);if(boundary>offset)end=boundary+1;}pieces.push(part.slice(offset,end));offset=end;}return pieces;}).filter(text=>text.trim());}
export default function HindiSpeech({text,hindiText,active=true}){
 const {t,translate}=useLanguage();const [state,setState]=useState('idle');const [error,setError]=useState('');const version=useRef(0),mounted=useRef(true),utterance=useRef(null),stopRef=useRef(null);
 const stop=useCallback(()=>{version.current++;if(currentStop===stopRef.current){window.speechSynthesis?.cancel();currentStop=null;}utterance.current=null;if(mounted.current){setState('idle');setError('');}},[]);
 stopRef.current=stop;
 useEffect(()=>{mounted.current=true;const cancel=()=>stopRef.current();window.addEventListener('medguide-navigation',cancel);return()=>{mounted.current=false;stopRef.current();window.removeEventListener('medguide-navigation',cancel);};},[]);
 useEffect(()=>{stopRef.current();},[text,hindiText,active]);
 async function play(){
  if(!active)return;stopHindiSpeech();stopRef.current();const token=version.current;currentStop=stopRef.current;const synthesis=window.speechSynthesis;
  if(!synthesis||!window.SpeechSynthesisUtterance){setError('Text-to-speech is unavailable in this browser.');currentStop=null;return;}
  setState('loading');setError('');
  try{const translated=hindiText||await translate(text);if(!mounted.current||token!==version.current)return;
   let voice=synthesis.getVoices().find(voice=>/^hi(?:[-_]|$)/i.test(voice.lang));
   if(!voice){await new Promise(resolve=>{let timer;const loaded=()=>{clearTimeout(timer);synthesis.removeEventListener?.('voiceschanged',loaded);resolve();};synthesis.addEventListener?.('voiceschanged',loaded);timer=setTimeout(loaded,800);});if(!mounted.current||token!==version.current)return;voice=synthesis.getVoices().find(voice=>/^hi(?:[-_]|$)/i.test(voice.lang));}
   if(!voice){setState('idle');setError('Hindi voice is unavailable on this device. Install a Hindi voice in your device settings and try again.');currentStop=null;return;}
   const parts=speechParts(translated);if(!parts.length){stopRef.current();return;}setState('playing');
   function speak(index){if(!mounted.current||token!==version.current)return;const next=new window.SpeechSynthesisUtterance(parts[index]);next.lang='hi-IN';next.voice=voice;next.onend=()=>{if(token!==version.current)return;if(index+1<parts.length)speak(index+1);else stopRef.current();};next.onerror=event=>{if(token!==version.current||event.error==='canceled'||event.error==='interrupted')return;stopRef.current();setError('Hindi audio could not be played. Please try again.');};utterance.current=next;synthesis.speak(next);}speak(0);
  }catch{if(mounted.current&&token===version.current){setState('idle');setError('Hindi translation unavailable. Please try again.');currentStop=null;}}
 }
 function toggle(){if(state==='paused'){window.speechSynthesis.resume();setState('playing');}else{window.speechSynthesis.pause();setState('paused');}}
 return <div className="speech-controls"><button className="secondary" type="button" onClick={play} disabled={!active||!String(hindiText||text||'').trim()||state!=='idle'}>{t('Listen in Hindi')}</button>{['playing','paused'].includes(state)&&<button className="secondary" type="button" onClick={toggle}>{t(state==='paused'?'Play':'Pause')}</button>}{state!=='idle'&&<button className="secondary" type="button" onClick={stop}>{t('Stop')}</button>}<span className="speech-status" role="status">{state==='loading'?t('Preparing Hindi audio…'):state==='playing'?t('Playing Hindi audio'):state==='paused'?t('Audio paused'):''}</span>{error&&<span className="speech-error" role="alert">{t(error)}</span>}</div>;
}
