import { motion } from 'framer-motion'
import { useUIStore } from '../../../shared/store/uiStore'

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString()
}

export default function AdminAgents({ agents, setSelectedAgent }) {
  const { setPage } = useUIStore()

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-in fade-in">
      <div>
        <h1 className="text-3xl font-outfit font-extrabold text-gray-900 dark:text-white tracking-tight">Agent Management</h1>
        <p className="text-gray-500 dark:text-gray-400 font-poppins mt-2">View and manage all registered agents on the platform.</p>
      </div>
      
      <div className="bg-white/60 dark:bg-neutral-900/40 backdrop-blur-md rounded-2xl border border-gray-200 dark:border-neutral-800 overflow-hidden shadow-lg shadow-black/5">
        <div className="overflow-x-auto">
          {agents.length === 0 ? (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400 font-poppins text-sm">No agents found.</div>
          ) : (
            <table className="w-full text-left font-poppins text-sm">
              <thead className="bg-gray-50 dark:bg-neutral-900/50 text-gray-500 dark:text-gray-400 font-semibold border-b border-gray-200 dark:border-neutral-800">
                <tr>
                  <th className="px-6 py-4">Email</th>
                  <th className="px-6 py-4">Company</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Applied Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-neutral-800">
                {agents.map((agent) => (
                  <motion.tr 
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} key={agent.id}
                    className="hover:bg-gray-50 dark:hover:bg-neutral-800/30 transition-colors cursor-pointer"
                    onClick={() => { setSelectedAgent(agent); setPage('admin_agent_detail'); }}
                  >
                    <td className="px-6 py-4 text-gray-900 dark:text-white font-medium">{agent.email}</td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400 capitalize">{agent.company || 'N/A'}</td>
                    <td className="px-6 py-4">
                      {agent.status === 'approved' ? (
                        <span className="bg-green-500/10 text-green-600 dark:text-green-400 text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">Approved</span>
                      ) : (
                        <span className="bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">Pending</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400">
                      {formatDate(agent.created_at)}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
