import { Activity } from 'lucide-react'
import { useUIStore } from '../../../shared/store/uiStore'
import { adminAPI } from '../../../shared/utils/api'
import toast from 'react-hot-toast'
import { useState } from 'react'

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString()
}

export default function AdminAgentDetail({ selectedAgent, fetchData }) {
  const { setPage } = useUIStore()
  const [actionLoading, setActionLoading] = useState(false)

  const handleApprove = async (id) => {
    setActionLoading(true)
    const tid = toast.loading('Approving agent...')
    try {
      await adminAPI.approveAgent(id)
      toast.success('Agent approved and credentials sent via email!', { id: tid })
      fetchData() // Refresh list
    } catch (err) {
      toast.error(err.message || 'Failed to approve agent', { id: tid })
    } finally {
      setActionLoading(false)
    }
  }

  const handleResetLimit = async (id) => {
    setActionLoading(true)
    const tid = toast.loading('Resetting document limit...')
    try {
      const res = await adminAPI.resetLimit(id)
      toast.success(res.message || 'Agent daily document limit reset to 0!', { id: tid })
      fetchData() // Refresh list
    } catch (err) {
      toast.error(err.message || 'Failed to reset limit', { id: tid })
    } finally {
      setActionLoading(false)
    }
  }

  if (!selectedAgent) return null

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-in slide-in-from-right-4 duration-300">
      <div className="flex items-center gap-4">
        <button onClick={() => setPage('admin_agents')} className="p-2 hover:bg-gray-200 dark:hover:bg-neutral-800 rounded-full transition-colors text-gray-500">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        </button>
        <div>
          <h1 className="text-3xl font-outfit font-extrabold text-gray-900 dark:text-white tracking-tight">Agent Details</h1>
          <p className="text-gray-500 dark:text-gray-400 font-poppins mt-1">ID: {selectedAgent.id}</p>
        </div>
      </div>

      <div className="flex flex-col gap-6">
        <div className="bg-white/60 dark:bg-neutral-900/40 backdrop-blur-md rounded-3xl border border-gray-200 dark:border-neutral-800 p-8 shadow-lg shadow-black/5">
          <h3 className="font-outfit font-bold text-lg text-gray-900 dark:text-white mb-6">Profile Information</h3>
          <div className="space-y-4 font-poppins text-sm">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-4 border-b border-gray-100 dark:border-neutral-800 pb-3">
              <span className="text-gray-500 shrink-0">Email</span>
              <span className="font-medium text-gray-900 dark:text-white text-left sm:text-right break-all">{selectedAgent.email}</span>
            </div>
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-4 border-b border-gray-100 dark:border-neutral-800 pb-3">
              <span className="text-gray-500 shrink-0">Company</span>
              <span className="font-medium text-gray-900 dark:text-white capitalize text-left sm:text-right">{selectedAgent.company || 'N/A'}</span>
            </div>
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-4 border-b border-gray-100 dark:border-neutral-800 pb-3">
              <span className="text-gray-500 shrink-0">Purpose</span>
              <span className="font-medium text-gray-900 dark:text-white capitalize text-left sm:text-right">{selectedAgent.purpose?.replace('_', ' ') || 'N/A'}</span>
            </div>
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-4 border-b border-gray-100 dark:border-neutral-800 pb-3">
              <span className="text-gray-500 shrink-0">Source</span>
              <span className="font-medium text-gray-900 dark:text-white capitalize text-left sm:text-right">{selectedAgent.source?.replace('_', ' ') || 'N/A'}</span>
            </div>
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-4 border-b border-gray-100 dark:border-neutral-800 pb-3">
              <span className="text-gray-500 shrink-0">AI Experience</span>
              <span className="font-medium text-gray-900 dark:text-white text-left sm:text-right">{selectedAgent.is_new_to_ai ? 'New to AI' : 'Experienced'}</span>
            </div>
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-4 pb-3">
              <span className="text-gray-500 shrink-0 flex items-center gap-2"><Activity size={14}/> Daily Docs Used</span>
              <span className="font-medium text-gray-900 dark:text-white text-left sm:text-right">{selectedAgent.daily_doc_count} / 5</span>
            </div>
          </div>
          
          {selectedAgent.status === 'pending' ? (
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-neutral-800 flex justify-end">
              <button
                disabled={actionLoading}
                onClick={() => handleApprove(selectedAgent.id)}
                className="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3 rounded-xl text-sm font-semibold tracking-wide shadow-md shadow-orange-500/20 transition-all disabled:opacity-50"
              >
                Approve Agent
              </button>
            </div>
          ) : (
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-neutral-800 flex justify-end">
              <button
                disabled={actionLoading}
                onClick={() => handleResetLimit(selectedAgent.id)}
                className="bg-transparent border border-orange-500/30 text-orange-500 hover:bg-orange-500/10 px-8 py-3 rounded-xl text-sm font-semibold tracking-wide transition-all disabled:opacity-50"
              >
                Reset Upload Limit
              </button>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
