import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import {AuthProvider} from './context/AuthContext';
import {LanguageProvider} from './context/LanguageContext';
import './styles.css';
createRoot(document.getElementById('root')).render(<StrictMode><LanguageProvider><AuthProvider><App/></AuthProvider></LanguageProvider></StrictMode>);
