import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/site.css'

if (
  window.location.pathname === '/debug/creepy-eye' ||
  window.location.pathname === '/debug/creepy-eye/'
) {
  window.location.replace('/debug/creepy-eye/index.html');
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
