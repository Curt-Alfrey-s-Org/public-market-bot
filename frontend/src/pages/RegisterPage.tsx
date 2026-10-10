/**
 * Registration page — full-screen auth layout, matches splash theme.
 */

import RegisterForm from '@/components/RegisterForm'
import styles from '@/styles/Register.module.css'

const APP_NAME = 'Market Pie5 Bot'

export default function RegisterPage() {
  return (
    <div className={styles.wrapper}>
      <RegisterForm appName={APP_NAME} />
    </div>
  )
}
