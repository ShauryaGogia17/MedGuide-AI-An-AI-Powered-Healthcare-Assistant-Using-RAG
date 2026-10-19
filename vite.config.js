import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
function healthMiddleware(server){server.middlewares.use('/health',(req,res,next)=>{if(req.method!=='GET')return next();res.setHeader('Content-Type','application/json');res.end(JSON.stringify({status:'ok',service:'frontend'}));});}
export default defineConfig({plugins:[react(),{name:'frontend-health',configureServer:healthMiddleware,configurePreviewServer:healthMiddleware}],server:{port:5173,strictPort:true,proxy:{'/api':'http://127.0.0.1:5000'}},preview:{proxy:{'/api':'http://127.0.0.1:5000'}}});
