import {useEffect,useState} from 'react';
import {Download,Leaf,TriangleAlert,ArrowRight} from 'lucide-react';
import {useLanguage} from '../context/LanguageContext';
import {request,API_BASE} from '../services/api';
import {formatNumber} from '../utils/formatLabValue';
import HindiSpeech from './HindiSpeech';
import TranslateResult from './TranslateResult';
import Loading from './Loading';
const labels={title:['Diet Guide','आहार मार्गदर्शिका'],intro:['Indian food ideas based on your verified report values.','आपकी रिपोर्ट के सत्यापित मानों पर आधारित भारतीय भोजन के सुझाव।'],eat_more:['Eat More','अधिक खाएँ'],limit:['Limit','सीमित करें'],avoid:['Avoid','बचें'],chart:['7-day diet chart','7 दिन की आहार तालिका'],download:['Download PDF','PDF डाउनलोड करें'],preparing:['Preparing PDF…','PDF तैयार हो रही है…'],loading:['Preparing your Diet Guide…','आपकी आहार मार्गदर्शिका तैयार हो रही है…'],retry:['Try again','फिर प्रयास करें'],day:['Day','दिन'],page:['Page','पृष्ठ'],sources:['Guidance sources','मार्गदर्शन के स्रोत'],general:['General balanced-food ideas','सामान्य संतुलित भोजन के सुझाव'],paused:['Meal plan needs clinician review','भोजन योजना के लिए चिकित्सक की समीक्षा आवश्यक है'],failure:['Unable to load your Diet Guide. Please try again.','आहार मार्गदर्शिका नहीं खुल सकी। कृपया फिर प्रयास करें।'],exportFailure:['Unable to download the PDF. Please try again.','PDF डाउनलोड नहीं हो सकी। कृपया फिर प्रयास करें।']};
const meals={early_morning:['Early morning','सुबह जल्दी'],breakfast:['Breakfast','नाश्ता'],snack:['Snack','हल्का नाश्ता'],lunch:['Lunch','दोपहर का भोजन'],evening_snack:['Evening snack','शाम का नाश्ता'],dinner:['Dinner','रात का भोजन']};
const swapLabels={title:['Simple food swaps','भोजन के आसान विकल्प'],instead:['Instead of','इसकी जगह'],choose:['Choose','यह चुनें']};
export default function DietGuide({report}){
 const {language}=useLanguage();const [guide,setGuide]=useState(null);const [busy,setBusy]=useState(true);const [error,setError]=useState(false);const [exporting,setExporting]=useState(false);const [exportError,setExportError]=useState(false);const [attempt,setAttempt]=useState(0);
 const label=key=>labels[key][language==='hi'?1:0];const local=value=>value?.[language]||value?.en||'';
 useEffect(()=>{let active=true;setBusy(true);setGuide(null);setError(false);setExportError(false);request(`/reports/${encodeURIComponent(report.report_id)}/diet`).then(result=>{if(active)setGuide(result);}).catch(()=>{if(active)setError(true);}).finally(()=>{if(active)setBusy(false);});return()=>{active=false;};},[report.report_id,attempt]);
 async function download(){setExporting(true);setExportError(false);try{const response=await fetch(`${API_BASE}/reports/${encodeURIComponent(report.report_id)}/diet/pdf?language=${language}`,{credentials:'include'});if(!response.ok){if(response.status===401)window.dispatchEvent(new Event('session-expired'));throw new Error('PDF download failed');}const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`medguide-diet-guide-${language}.pdf`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch{setExportError(true);}finally{setExporting(false);}}
 if(busy)return <div className="diet-guide diet-loading"><Loading label={label('loading')}/></div>;
 if(error)return <section className="diet-guide"><h3>{label('title')}</h3><p className="error" role="alert">{label('failure')}</p><button className="secondary" onClick={()=>setAttempt(value=>value+1)}>{label('retry')}</button></section>;
 if(!guide)return null;
 const swaps=guide.plan_paused?[]:guide.swaps||[];const swapLabel=key=>swapLabels[key][language==='hi'?1:0];
 const speech=[guide.summary?.hi,...(guide.warnings||[]).map(warning=>warning.message?.hi),...swaps.map(swap=>`${swap.instead_of?.hi} की जगह ${swap.choose?.hi}। ${swap.reason?.hi}`),...['eat_more','limit','avoid'].flatMap(key=>[labels[key][1],...(guide[key]||[]).map(item=>`${item.food?.hi}। ${item.reason?.hi}। ${(item.evidence||[]).map(evidence=>`${evidence.test_name}: ${evidence.value} ${evidence.unit||''}`).join('। ')}`)]),...guide.days.flatMap(day=>[`दिन ${day.day}`, ...Object.entries(meals).map(([key,names])=>`${names[1]}: ${day.meals[key]?.hi}`)]),guide.disclaimer?.hi].filter(Boolean).join('। ');
 return <section className="diet-guide" aria-label={label('title')}>
  <div className="section-heading diet-heading"><div><span className="eyebrow"><Leaf size={15}/>{label('title')}</span><h3>{label('title')}</h3><p className="muted">{label('intro')}</p><small>{report.filename}</small></div><button className="secondary" onClick={download} disabled={exporting}><Download size={16}/>{exporting?label('preparing'):label('download')}</button></div>
  {(guide.warnings||[]).map((warning,index)=><div className={`diet-warning ${warning.level==='critical'?'critical':'notice'}`} role={warning.level==='critical'?'alert':'status'} key={index}><TriangleAlert size={19}/><div><p>{local(warning.message)}</p><Evidence items={warning.evidence} pageLabel={label('page')}/></div></div>)}
  <p className="diet-summary">{local(guide.summary)}</p>
  {!guide.personalized&&<span className="badge">{label('general')}</span>}
  <HindiSpeech hindiText={speech}/>
  {!!swaps.length&&<section className="diet-swaps"><h4>{swapLabel('title')}</h4><div className="diet-swap-grid">{swaps.map((swap,index)=><article className="diet-swap" key={index}><div className="diet-swap-choice"><div><small>{swapLabel('instead')}</small><strong>{local(swap.instead_of)}</strong></div><ArrowRight size={18} aria-hidden="true"/><div><small>{swapLabel('choose')}</small><strong>{local(swap.choose)}</strong></div></div><p>{local(swap.reason)}</p><Evidence items={swap.evidence} pageLabel={label('page')}/></article>)}</div></section>}
  <div className="diet-lists">{['eat_more','limit','avoid'].map(key=><div className={`diet-list diet-${key}`} key={key}><h4>{label(key)}</h4><ul>{(guide[key]||[]).map((item,index)=><li key={index}><strong>{local(item.food)}</strong><p>{local(item.reason)}</p><Evidence items={item.evidence} pageLabel={label('page')}/></li>)}</ul></div>)}</div>
  <h4 className="diet-chart-title">{label('chart')}</h4>{guide.plan_paused&&<p className="notice">{label('paused')}</p>}
  <div className="diet-days">{guide.days.map(day=><article className="diet-day" key={day.day}><h4>{label('day')} {day.day}</h4><dl>{Object.entries(meals).map(([key,names])=><div key={key}><dt>{names[language==='hi'?1:0]}</dt><dd>{local(day.meals[key])}</dd></div>)}</dl></article>)}</div>
  <p className="diet-disclaimer">{local(guide.disclaimer)}</p>
  {!!guide.sources?.length&&<details className="diet-sources"><summary>{label('sources')}</summary><ul>{guide.sources.map(source=><li key={source.url}><a href={source.url} target="_blank" rel="noreferrer"><TranslateResult text={source.title}/></a></li>)}</ul></details>}
  {exportError&&<p className="error" role="alert">{label('exportFailure')}</p>}
 </section>;
}
function Evidence({items=[],pageLabel}){return !!items.length&&<div className="diet-evidence">{items.map((item,index)=><small key={index}><TranslateResult text={item.test_name}/>: <strong>{formatNumber(item.value)} {item.unit||''}</strong> · {pageLabel} {item.page}</small>)}</div>;}
