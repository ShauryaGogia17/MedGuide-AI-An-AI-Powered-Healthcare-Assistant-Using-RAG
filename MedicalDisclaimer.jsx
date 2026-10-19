import {ShieldCheck} from 'lucide-react';
import {useLanguage} from '../context/LanguageContext';
export default function MedicalDisclaimer(){const {t}=useLanguage();return <aside className="disclaimer"><ShieldCheck size={18}/><p><strong>{t("General awareness only, not a substitute for a doctor's advice.")}</strong> {t('MedGuide is an educational aid. It does not diagnose, prescribe, or replace a qualified healthcare professional. For urgent symptoms, seek urgent medical care.')}</p></aside>;}
