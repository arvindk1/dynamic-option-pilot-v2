import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Suppress known custom element redefinition warnings in development
const originalError = console.error;
console.error = (...args: unknown[]) => {
  const message = args[0];
  if (typeof message === 'string' && message.includes('mce-autosize-textarea') && message.includes('already been defined')) {
    return; // Suppress this specific error
  }
  originalError.apply(console, args);
};

console.log('🚀 main.tsx loading...');

try {
  const rootElement = document.getElementById("root");
  console.log('🎯 Root element found:', rootElement);
  
  if (!rootElement) {
    throw new Error('Root element not found');
  }
  
  console.log('🔧 Creating React root...');
  const root = createRoot(rootElement);
  
  console.log('🎨 Rendering App component...');
  root.render(<App />);
  
  console.log('✅ App rendered successfully');
} catch (error) {
  console.error('❌ Error in main.tsx:', error);
  document.body.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial;">
      <h1>Main.tsx Error</h1>
      <p>Error: ${error.message}</p>
      <pre>${error.stack}</pre>
    </div>
  `;
}
