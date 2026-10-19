import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],resolve:{dedupe:['react','react-dom','vitest','@testing-library/react','recharts']},test:{include:['../tests/frontend/**/*.test.{js,jsx}'],environment:'jsdom'}});
