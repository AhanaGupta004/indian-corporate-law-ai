const API = 'http://localhost:5000'
const tok = () => { try { return JSON.parse(localStorage.getItem('lb_user') || 'null')?.access_token } catch { return null } }
const authH = () => { const t = tok(); return t ? { Authorization: `Bearer ${t}` } : {} }

const handleRes = async (res) => {
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    let msg = t;
    try { const j = JSON.parse(t); msg = j.detail || j.message || t; } catch(e) {}
    throw new Error(msg || `${res.status} Error`);
  }
  return res.json();
}

const req = async (path, opts = {}) => {
  const res = await fetch(`${API}${path}`, { ...opts, headers: { 'Content-Type': 'application/json', ...authH(), ...opts.headers } })
  return handleRes(res)
}

export const authAPI = {
  signup: (email, company, is_new_to_ai, purpose, source, captchaToken) => fetch(`${API}/api/auth/signup`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, company, is_new_to_ai, purpose, source, captcha_token: captchaToken}) }).then(handleRes),
  login:  (email, password, captchaToken) => fetch(`${API}/api/auth/login`,  { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email, password, captcha_token: captchaToken}) }).then(handleRes),
  verifyOTP: (temp_token, otp) => fetch(`${API}/api/auth/verify-otp`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({temp_token, otp}) }).then(handleRes),
  getMe:  (token) => fetch(`${API}/api/auth/me`, { headers:{'Authorization':`Bearer ${token}`} }).then(handleRes),
}

export const adminAPI = {
  getPendingAgents: () => req('/api/auth/admin/agents/pending'),
  getAllAgents: () => req('/api/auth/admin/agents/all'),
  approveAgent: (id) => req(`/api/auth/admin/agents/approve/${id}`, { method: 'POST' }),
  resetLimit: (id) => req(`/api/auth/admin/agents/reset-limit/${id}`, { method: 'POST' }),
  getStats: () => req('/api/auth/admin/stats'),
}



export const documentAPI = {
  upload: async (file) => {
    const fd = new FormData(); fd.append('file', file)
    const res = await fetch(`${API}/api/documents/upload`, { method:'POST', headers: authH(), body: fd })
    return handleRes(res)
  },
  list:   () => req('/api/documents'),
  get:    (id) => req(`/api/documents/${id}`),
  delete: (id) => req(`/api/documents/${id}`, { method:'DELETE' }),
  fileUrl: (id) => `${API}/api/documents/${id}/file`,  // used with auth header fetch → blob
}

export const summarizeAPI = {
  trigger: (docId) => req(`/summarize/${docId}`, { method: 'POST' }),
  get: (docId) => req(`/result/${docId}`),
  cancel: (docId) => req(`/api/documents/${docId}/cancel`, { method: 'POST' })
}



export const fetchFileAsBlob = async (docId) => {
  const res = await fetch(`${API}/api/documents/${docId}/file`, { headers: authH() })
  if (!res.ok) throw new Error('Cannot fetch file')
  return res.blob()
}

export const healthCheck = async () => { try { return (await fetch(`${API}/health`)).ok } catch { return false } }
