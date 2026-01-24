import { useState } from 'react'

function App() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="container" style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          Mini<span style={{ color: 'var(--color-primary)' }}>TMS</span>
        </h1>
        <p style={{ color: 'var(--color-text-muted)' }}>
          Система управления перевозками
        </p>
        <div style={{ marginTop: '2rem' }}>
          <button className="btn btn-primary">Войти в систему</button>
        </div>
      </div>
    </div>
  )
}

export default App
