import {Droplets,ArrowUpRight,Microscope,FileText} from 'lucide-react';
import {useLanguage} from '../context/LanguageContext';
export default function OverviewBloodCard({onOpen}){
 const {t}=useLanguage();
 return <section className="panel overview-diet-entry overview-blood-entry"><span className="round-icon"><Droplets size={25}/></span><div><span className="eyebrow">{t('A closer look at blood')}</span><h2>{t('Blood Guide')}</h2><p>{t('Understand blood-report readings and explore blood-smear microscope images.')}</p><div className="diet-entry-features"><span><FileText size={14}/>{t('Blood-report explanations')}</span><span><Microscope size={14}/>{t('Microscope image analysis')}</span></div></div><button className="secondary" onClick={onOpen}>{t('Open Blood Guide')} <ArrowUpRight size={16}/></button></section>;
}
