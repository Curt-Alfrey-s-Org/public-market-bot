/**
 * Registration form — username, email, password, confirm password, license key.
 */

import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '@/api/client'
import PasswordStrengthMeter from './PasswordStrengthMeter'
import styles from '@/styles/Register.module.css'

const USERNAME_MIN = 3
const USERNAME_MAX = 20
const PASSWORD_MIN = 8
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validatePassword(password: string): string | null {
  if (password.length < PASSWORD_MIN) return `Password must be at least ${PASSWORD_MIN} characters`
  if (!/[A-Z]/.test(password)) return 'Password must contain at least one uppercase letter'
  if (!/[a-z]/.test(password)) return 'Password must contain at least one lowercase letter'
  if (!/\d/.test(password)) return 'Password must contain at least one number'
  if (!/[^a-zA-Z0-9]/.test(password)) return 'Password must contain at least one special character'
  return null
}

interface RegisterFormProps {
  appName: string
}

export default function RegisterForm({ appName }: RegisterFormProps) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [licenseKey, setLicenseKey] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)
    setFieldErrors({})

    const errs: Record<string, string> = {}

    const u = username.trim()
    if (u.length < USERNAME_MIN || u.length > USERNAME_MAX) {
      errs.username = `Username must be ${USERNAME_MIN}-${USERNAME_MAX} characters`
    }
    if (!EMAIL_REGEX.test(email.trim())) {
      errs.email = 'Please enter a valid email address'
    }
    const pwdErr = validatePassword(password)
    if (pwdErr) errs.password = pwdErr
    if (password !== confirmPassword) {
      errs.confirmPassword = 'Passwords do not match'
    }
    if (!licenseKey.trim()) {
      errs.licenseKey = 'License key is required'
    }

    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs)
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/auth/register-centralized', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: u,
          email: email.trim().toLowerCase(),
          password,
          license_key: licenseKey.trim(),
          captcha_token: 'dummy-captcha'
        })
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || err.message || 'Registration failed')
      }

      setSuccess(true)
      setUsername('')
      setEmail('')
      setPassword('')
      setConfirmPassword('')
      setLicenseKey('')
    } catch (err: unknown) {
      const msg = typeof err === 'string' ? err : (err && typeof err === 'object' && 'message' in err ? (err as any).message : null)
      setError(typeof msg === 'string' ? msg : 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className={styles.card}>
        <h2 className={styles.title}>Sign Up</h2>
        <p className={styles.subtitle}>Create an account for {appName}</p>
        <div className={styles.successBox} role="alert">
          Registration successful! Check your email to verify.
        </div>
        <p className={styles.footer}>
          <Link to="/" className={styles.footerLink}>Back to Sign In</Link>
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className={styles.card}>
      <h2 className={styles.title}>Sign Up</h2>
      <p className={styles.subtitle}>Create an account for {appName}</p>

      {error && <div className={styles.errorBox}>{error}</div>}

      <div className={styles.formGroup}>
        <label htmlFor="reg-username" className={styles.label}>Username</label>
        <input
          type="text"
          id="reg-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          className={`${styles.input} ${fieldErrors.username ? styles.inputError : ''}`}
          disabled={loading}
          placeholder={`${USERNAME_MIN}-${USERNAME_MAX} characters`}
        />
        {fieldErrors.username && <p className={styles.errorText}>{fieldErrors.username}</p>}
      </div>

      <div className={styles.formGroup}>
        <label htmlFor="reg-email" className={styles.label}>Email</label>
        <input
          type="email"
          id="reg-email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          className={`${styles.input} ${fieldErrors.email ? styles.inputError : ''}`}
          disabled={loading}
          placeholder="operator@example.com"
        />
        {fieldErrors.email && <p className={styles.errorText}>{fieldErrors.email}</p>}
      </div>

      <div className={styles.formGroup}>
        <label htmlFor="reg-password" className={styles.label}>Password</label>
        <input
          type="password"
          id="reg-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          className={`${styles.input} ${fieldErrors.password ? styles.inputError : ''}`}
          disabled={loading}
          placeholder="8+ chars, upper, lower, number, special"
        />
        <PasswordStrengthMeter password={password} className={styles.strengthMeter} />
        {fieldErrors.password && <p className={styles.errorText}>{fieldErrors.password}</p>}
      </div>

      <div className={styles.formGroup}>
        <label htmlFor="reg-confirm" className={styles.label}>Confirm Password</label>
        <input
          type="password"
          id="reg-confirm"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          autoComplete="new-password"
          className={`${styles.input} ${fieldErrors.confirmPassword ? styles.inputError : ''}`}
          disabled={loading}
          placeholder="Repeat password"
        />
        {fieldErrors.confirmPassword && <p className={styles.errorText}>{fieldErrors.confirmPassword}</p>}
      </div>

      <div className={styles.formGroup}>
        <label htmlFor="reg-license" className={styles.label}>License Key</label>
        <input
          type="text"
          id="reg-license"
          value={licenseKey}
          onChange={(e) => setLicenseKey(e.target.value)}
          className={`${styles.input} ${fieldErrors.licenseKey ? styles.inputError : ''}`}
          disabled={loading}
          placeholder="e.g., FREE-TRIAL-2024 or your license key"
        />
        {fieldErrors.licenseKey && <p className={styles.errorText}>{fieldErrors.licenseKey}</p>}
        <p className={styles.helperText}>Free trial key: FREE-TRIAL-2024</p>
      </div>

      <div className={styles.captchaPlaceholder}>
        CAPTCHA will be integrated here.
      </div>

      <button type="submit" disabled={loading} className={styles.submitBtn}>
        {loading ? 'Creating account...' : 'Create account'}
      </button>

      <p className={styles.footer}>
        Already have an account? <Link to="/" className={styles.footerLink}>Sign In</Link>
      </p>
    </form>
  )
}
