import {Leaf,ArrowUpRight,CalendarDays,ArrowRightLeft} from 'lucide-react';
import {useLanguage} from '../context/LanguageContext';
export default function OverviewDietCard({onOpen}){
 const {t}=useLanguage();
 return <section className="panel overview-diet-entry"><span className="round-icon"><Leaf size={25}/></span><div><span className="eyebrow">{t('Everyday food choices')}</span><h2>{t('Diet Guide')}</h2><p>{t('Find food swaps and a seven-day Indian meal plan based on your report.')}</p><div className="diet-entry-features"><span><ArrowRightLeft size={14}/>{t('Food swaps')}</span><span><CalendarDays size={14}/>{t('7-day meal plan')}</span><span>{t('Download PDF')}</span></div></div><button className="secondary" onClick={onOpen}>{t('Open Diet Guide')} <ArrowUpRight size={16}/></button></section>;
}
