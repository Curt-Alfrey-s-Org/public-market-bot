/**
 * Password strength meter — visual indicator for 8+ chars, upper, lower, number, special.
 */

interface PasswordStrengthMeterProps {
  password: string
  className?: string
}

function getStrength(password: string): { score: number; label: string } {
  if (!password) return { score: 0, label: '' }
  let score = 0
  if (password.length >= 8) score += 1
  if (/[a-z]/.test(password)) score += 1
  if (/[A-Z]/.test(password)) score += 1
  if (/\d/.test(password)) score += 1
  if (/[^a-zA-Z0-9]/.test(password)) score += 1
  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong', 'Very strong']
  return { score, label: labels[score] }
}

export default function PasswordStrengthMeter({ password, className = '' }: PasswordStrengthMeterProps) {
  if (!password) return null

  const { score, label } = getStrength(password)
  const pct = (score / 5) * 100
  const color =
    pct <= 20 ? 'rgb(239, 68, 68)' : pct <= 40 ? 'rgb(245, 158, 11)' : pct <= 60 ? 'rgb(234, 179, 8)' : pct <= 80 ? 'rgb(34, 197, 94)' : 'rgb(34, 197, 94)'

  return (
    <div className={className}>
      <div
        style={{
          height: 4,
          borderRadius: 2,
          background: 'rgb(51, 65, 85)',
          overflow: 'hidden',
          marginBottom: 4,
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: color,
            transition: 'width 0.2s ease',
          }}
        />
      </div>
      {label && <span style={{ fontSize: 12, color: 'rgb(148, 163, 184)' }}>{label}</span>}
    </div>
  )
}
