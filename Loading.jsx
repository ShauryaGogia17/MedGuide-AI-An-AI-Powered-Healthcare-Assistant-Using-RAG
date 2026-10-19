import {useLanguage} from '../context/LanguageContext';
export default function Loading({label='Loading…'}){const {t}=useLanguage();return <div className="loading" role="status"><span className="spinner"/>{t(label)}</div>;}
