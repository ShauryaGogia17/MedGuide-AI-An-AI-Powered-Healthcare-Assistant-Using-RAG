import {useCallback,useEffect,useState,lazy,Suspense} from 'react';
import {CircleHelp} from 'lucide-react';
import {useAuth} from './context/AuthContext';
import {request,getHealth} from './services/api';
import Sidebar from './components/Sidebar';
import MedicalDisclaimer from './components/MedicalDisclaimer';
import Loading from './components/Loading';
import LanguageToggle from './components/LanguageToggle';
import TranslateResult from './components/TranslateResult';
import {useLanguage} from './context/LanguageContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Reports from './pages/Reports';
const HealthTimeline=lazy(()=>import('./pages/HealthTimeline'));
import ChatBox from './components/ChatBox';
const DoctorBrief=lazy(()=>import('./pages/DoctorBrief'));
const DietGuide=lazy(()=>import('./pages/DietGuide'));
const BloodGuide=lazy(()=>import('./pages/BloodGuide'));
const titles={overview:'Overview',reports:'My reports',ask:'Ask MedGuide',timeline:'Health timeline',brief:'Doctor visit brief',diet:'Diet Guide',blood:'Blood Guide'};
function Workspace({user,logout}){
 const {t}=useLanguage();
 const [active,setActive]=useState('overview');const [reports,setReports]=useState([]);const [timeline,setTimeline]=useState(null);const [loading,setLoading]=useState(true);const [timelineLoading,setTimelineLoading]=useState(true);const [error,setError]=useState('');const [timelineError,setTimelineError]=useState('');const [sessionError,setSessionError]=useState('');const [healthy,setHealthy]=useState(null);
 const refresh=useCallback(()=>{setLoading(true);setTimelineLoading(true);setError('');setTimelineError('');request('/reports').then(data=>setReports(data.reports)).catch(error=>setError(error.message)).finally(()=>setLoading(false));request('/timeline').then(setTimeline).catch(error=>setTimelineError(error.message)).finally(()=>setTimelineLoading(false));getHealth().then(()=>setHealthy(true)).catch(()=>setHealthy(false));},[]);
 useEffect(refresh,[refresh]);
 function navigate(next){window.dispatchEvent(new Event('medguide-navigation'));setActive(next);}
 async function signOut(){try{await logout();}catch(error){setSessionError(error.message);}}
 return <div className="workspace"><Sidebar active={active} onNavigate={navigate} user={user} onLogout={signOut}/><div className="workspace-main"><header className="topbar"><span>{t('Workspace')} <span className="breadcrumb">/ {t(titles[active])}</span></span><div><LanguageToggle/><span className={`service-status ${healthy===false?'offline':''}`}><i/>{t(healthy===null?'Checking services':healthy?'Services connected':'Connection unavailable')}</span><CircleHelp size={19}/></div></header><main className="content"><Suspense fallback={<Loading/>}>{sessionError&&<p className="error" role="alert"><TranslateResult text={sessionError}/></p>}{active==='overview'&&<Dashboard user={user} reports={reports} timeline={timeline} loading={loading} error={error} onNavigate={navigate} onUploaded={refresh}/>} {active==='reports'&&<Reports reports={reports} loading={loading} error={error} onUploaded={refresh} onRetry={refresh}/>}<div hidden={active!=='ask'}><ChatBox active={active==='ask'}/></div>{active==='timeline'&&<HealthTimeline timeline={timeline} loading={timelineLoading} error={timelineError} onRetry={refresh}/>} {active==='brief'&&<DoctorBrief/>}{active==='diet'&&<DietGuide reports={reports} loading={loading} error={error} onRetry={refresh} onNavigate={navigate}/>} {active==='blood'&&<BloodGuide reports={reports} loading={loading} error={error} onRetry={refresh} onNavigate={navigate}/>}</Suspense><MedicalDisclaimer/><footer className="app-footer"><span>{t('MedGuide AI · Evidence for understanding.')}</span><span>{t('Made for better conversations.')}</span></footer></main></div></div>;
}
export default function App(){const {user,loading,logout}=useAuth();if(loading)return <div className="initial-loading"><Loading label="Opening your workspace…"/></div>;return user?<Workspace key={user.id} user={user} logout={logout}/>:<Login/>;}
