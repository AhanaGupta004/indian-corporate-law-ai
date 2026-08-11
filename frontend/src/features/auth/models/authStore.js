import { create } from 'zustand'
import { authAPI } from '../../../shared/utils/api'

const STORAGE_KEY = 'lb_user'

const stored = () => {
  try {
    const n = localStorage.getItem(STORAGE_KEY)
    if (n) return JSON.parse(n)
    const old = localStorage.getItem('lexai_u')
    if (old) {
      localStorage.setItem(STORAGE_KEY, old)
      localStorage.removeItem('lexai_u')
      return JSON.parse(old)
    }
    return null
  } catch { return null }
}

export const useAuthStore = create((set) => ({
  isLoggedIn: false,
  user: null,

  initAuth: async () => {
    const u = stored()
    if (u?.access_token) {
      set({ isLoggedIn: true, user: u })
      try {
        const profile = await authAPI.getMe(u.access_token)
        const updated = { ...u, ...profile }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        set({ user: updated })
      } catch (e) { console.error("Failed to fetch profile", e) }
    }
  },

  login: async (u) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u))
    set({ isLoggedIn: true, user: u })
    try {
      const profile = await authAPI.getMe(u.access_token)
      const updated = { ...u, ...profile }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      set({ user: updated })
    } catch (e) { console.error("Failed to fetch profile on login", e) }
  },

  logout: () => {
    localStorage.removeItem(STORAGE_KEY)
    set({ isLoggedIn: false, user: null })
  },
  
  incrementDocCount: () => set((state) => {
    if (!state.user) return state
    const updated = { ...state.user, daily_doc_count: (state.user.daily_doc_count || 0) + 1 }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    return { user: updated }
  }),
}))
