import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

if (typeof window !== 'undefined') {
  if (window.Telegram?.WebApp?.expand) window.Telegram.WebApp.expand()
  if (!window.location.hash || window.location.hash === '#') {
    window.location.hash = '#/'
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
