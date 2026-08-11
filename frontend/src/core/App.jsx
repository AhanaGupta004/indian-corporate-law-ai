import { useEffect, useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import { useAuthStore } from '../features/auth/models/authStore'
import Login from '../features/auth/views/LoginView'
import Layout from './LayoutView'
import { PageLoader } from '../shared/ui/Loader'

export default function App() {
  const { isLoggedIn } = useAuthStore()
  const [appReady, setAppReady] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setAppReady(true), 600)
    return () => clearTimeout(t)
  }, [])

  return (
    <>
      <AnimatePresence>
        {!appReady && <PageLoader show message="Initializing…" />}
      </AnimatePresence>
      {appReady && (isLoggedIn ? <Layout /> : <Login />)}
    </>
  )
}