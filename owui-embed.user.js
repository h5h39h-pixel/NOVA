// ==UserScript==
// @name         AI Control Center — embed in Open WebUI
// @namespace    local.ai.controlcenter
// @version      1.0
// @description  Adds a "Control Center" button to Open WebUI that opens the dashboard as an in-app panel (iframe overlay).
// @match        http://localhost:3000/*
// @match        http://127.0.0.1:3000/*
// @grant        none
// ==/UserScript==
(function () {
  'use strict';
  const URL = 'http://localhost:8900';

  // floating launcher button
  const btn = document.createElement('button');
  btn.textContent = '⚡ Control Center';
  Object.assign(btn.style, {
    position: 'fixed', right: '18px', bottom: '18px', zIndex: 99999,
    background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', border: '0',
    padding: '11px 16px', borderRadius: '12px', font: '600 13px Segoe UI,sans-serif',
    cursor: 'pointer', boxShadow: '0 8px 24px rgba(99,102,241,.5)'
  });

  // full-screen overlay panel with iframe
  const overlay = document.createElement('div');
  Object.assign(overlay.style, {
    position: 'fixed', inset: '0', zIndex: 100000, display: 'none',
    background: 'rgba(0,0,0,.65)', backdropFilter: 'blur(4px)'
  });
  const panel = document.createElement('div');
  Object.assign(panel.style, {
    position: 'absolute', inset: '3% 3% 3% 3%', borderRadius: '16px', overflow: 'hidden',
    border: '1px solid #262a36', boxShadow: '0 30px 80px rgba(0,0,0,.6)', background: '#0a0b0f'
  });
  const close = document.createElement('button');
  close.textContent = '✕';
  Object.assign(close.style, {
    position: 'absolute', top: '10px', right: '14px', zIndex: 2, width: '34px', height: '34px',
    borderRadius: '8px', border: '1px solid #262a36', background: '#13151c', color: '#fff', cursor: 'pointer'
  });
  const frame = document.createElement('iframe');
  frame.src = URL;
  Object.assign(frame.style, { width: '100%', height: '100%', border: '0' });

  panel.appendChild(frame); panel.appendChild(close); overlay.appendChild(panel);
  btn.onclick = () => { overlay.style.display = 'block'; };
  close.onclick = () => { overlay.style.display = 'none'; };
  overlay.onclick = e => { if (e.target === overlay) overlay.style.display = 'none'; };

  window.addEventListener('load', () => {
    document.body.appendChild(btn);
    document.body.appendChild(overlay);
  });
})();
