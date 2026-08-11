import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminAPI } from '../../../shared/utils/api'
import { useUIStore } from '../../../shared/store/uiStore'

import AdminOverview from './AdminOverviewView'
import AdminAgents from './AdminAgentsView'
import AdminAgentDetail from './AdminAgentDetailView'

export default function AdminPanel() {
  const [agents, setAgents] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState(null)
  
  const { page } = useUIStore()

  const fetchData = async () => {
    setLoading(true)
    try {
      const [agentsData, statsData] = await Promise.all([
        adminAPI.getAllAgents(),
        adminAPI.getStats()
      ])
      setAgents(agentsData)
      setStats(statsData)
    } catch (err) {
      toast.error('Failed to load admin data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Loader2 className="animate-spin text-orange-500 w-8 h-8" />
      </div>
    )
  }

  return (
    <div className="h-full bg-transparent overflow-hidden animate-in fade-in duration-500 flex flex-col min-h-0">
      <div className={`flex-1 min-h-0 bg-gray-50/30 dark:bg-black/10 overflow-y-auto`}>
        {page === 'admin_overview' && <AdminOverview stats={stats} />}
        {page === 'admin_agents' && <AdminAgents agents={agents} setSelectedAgent={setSelectedAgent} />}
        {page === 'admin_agent_detail' && <AdminAgentDetail selectedAgent={selectedAgent} fetchData={fetchData} />}
      </div>
    </div>
  )
}
