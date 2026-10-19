import {useState} from 'react';
import {useLanguage} from '../context/LanguageContext';
import TranslateResult from './TranslateResult';
import HindiSpeech from './HindiSpeech';
export default function SourceCitation({source,active=true}){
 const {t}=useLanguage();const [open,setOpen]=useState(false);
 return <details className="citation" onToggle={event=>setOpen(event.currentTarget.open)}><summary><span className="source-id">[{source.id}]</span> {source.filename} {source.page&&<span>· {t('Page')} {source.page}</span>} <span className="badge">{t(source.kind==='knowledge'?'Medical knowledge':'Your report')}</span></summary><p className="source-title"><TranslateResult text={source.title}/></p><blockquote><TranslateResult text={source.snippet} preserveOriginal originalLabel="Original report evidence"/></blockquote><HindiSpeech text={source.snippet} active={active&&open}/>{source.url&&/^https:\/\//.test(source.url)&&<a href={source.url} target="_blank" rel="noreferrer">{t('Read original resource ↗')}</a>}</details>;
}
