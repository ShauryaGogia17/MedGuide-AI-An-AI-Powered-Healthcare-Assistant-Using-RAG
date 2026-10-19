import {useState} from 'react';
import {FileText,ChevronDown} from 'lucide-react';
import {formatDate} from '../utils/formatDate';
import {formatNumber} from '../utils/formatLabValue';
import {useLanguage} from '../context/LanguageContext';
import TranslateResult from './TranslateResult';
import HindiSpeech from './HindiSpeech';
import DietGuide from './DietGuide';
export default function ReportCard({report}){
 const {language,t}=useLanguage();const [open,setOpen]=useState(false);
 const speech=[report.filename,...report.warnings,...report.labs.map(lab=>`${lab.test_name}: ${formatNumber(lab.value)} ${lab.unit||''}. Reference: ${lab.reference_range||'not printed'}. ${lab.evidence}`),"General awareness only, not a substitute for a doctor's advice."].join('\n');
 return <article className="report-card"><button className="report-header" onClick={()=>setOpen(!open)} aria-expanded={open}><span className="file-icon"><FileText size={21}/></span><span className="report-label"><strong>{report.filename}</strong><small>{formatDate(report.report_date,language)} · {t('{count} lab values',{count:report.labs.length})} · {t('{count} evidence passages',{count:report.chunks})}</small></span><span className="badge">{t('Ready')}</span><ChevronDown size={18} className={open?'rotated':''}/></button>{open&&<div className="report-details">{report.date_source==='user'&&<p className="muted">{t('Report date supplied by you.')}</p>}{report.warnings.map((warning,index)=><p className="notice" key={index}><TranslateResult text={warning}/></p>)}{!report.labs.length&&<p className="muted">{t('No verified numeric lab values were extracted. You can still ask questions about this report.')}</p>}<HindiSpeech text={speech}/><ul className="reading-list">{report.labs.map((lab,index)=><li key={index}><div><strong><TranslateResult text={lab.test_name} preserveOriginal/></strong><small>{t('Reference')}: {lab.reference_range||t('not printed')} · {t('Page')} {lab.page}</small><small><TranslateResult text={lab.evidence} preserveOriginal originalLabel="Original report evidence"/></small></div><span>{formatNumber(lab.value)} {lab.unit||''}</span></li>)}</ul><DietGuide report={report}/></div>}</article>;
}
