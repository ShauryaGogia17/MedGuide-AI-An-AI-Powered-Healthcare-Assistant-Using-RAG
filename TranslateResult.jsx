import {useEffect,useState} from 'react';
import {useLanguage} from '../context/LanguageContext';
export default function TranslateResult({text,preserveOriginal=false,originalLabel='Original text'}){
 const {language,t,translate}=useLanguage();const source=String(text??'');const [result,setResult]=useState({source:'',text:'',error:false});const [retry,setRetry]=useState(0);
 useEffect(()=>{let active=true;if(language==='hi'&&source){setResult({source,text:'',error:false});translate(source).then(text=>{if(active)setResult({source,text,error:false});}).catch(()=>{if(active)setResult({source,text:'',error:true});});}return()=>{active=false;};},[language,source,retry,translate]);
 if(!source)return null;if(language==='en')return source;
 const current=result.source===source?result:null;
 return <span className="translated-result"><span lang="hi">{current?.text||<span className={current?.error?'translation-error':'translation-status'} role={current?.error?'alert':'status'}>{t(current?.error?'Hindi translation unavailable. Please try again.':'Translation loading…')}{current?.error&&<> <button className="text-button" type="button" onClick={()=>setRetry(value=>value+1)}>{t('Try again')}</button></>}</span>}</span>{preserveOriginal&&<span className="original-evidence" lang="en"><small>{t(originalLabel)}</small>{source}</span>}</span>;
}
