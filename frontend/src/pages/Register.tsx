import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api'
import { setToken } from '../auth'

export default function Register() {
  const navigate = useNavigate()
  const [tenantName, setTenantName] = useState('')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      const data = await register({
        tenant_name: tenantName,
        email,
        full_name: fullName,
        password,
      })
      setToken(data.access_token)
      navigate('/dashboard')
    } catch {
      setError('Ese email ya está registrado')
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Crear cuenta</h1>
        <p className="hint">Se crea tu organización y quedas como administrador.</p>
        {error && <p className="error">{error}</p>}
        <label>
          Empresa (tenant)
          <input
            value={tenantName}
            onChange={(e) => setTenantName(e.target.value)}
            required
          />
        </label>
        <label>
          Tu nombre
          <input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
        </label>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <button type="submit">Registrarme</button>
        <p>
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
      </form>
    </div>
  )
}