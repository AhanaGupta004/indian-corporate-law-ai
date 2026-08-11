import { motion } from 'framer-motion'
import { Users, CheckCircle, Clock } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts'

export function StatCard({ title, value, icon: Icon, color }) {
  return (
    <div className="bg-white/60 dark:bg-neutral-900/40 backdrop-blur-md rounded-2xl border border-gray-200 dark:border-neutral-800 p-6 flex items-center gap-4 shadow-lg shadow-black/5">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white shadow-lg ${color}`}>
        <Icon size={24} />
      </div>
      <div>
        <p className="text-gray-500 dark:text-gray-400 font-poppins text-xs font-semibold uppercase tracking-wider">{title}</p>
        <p className="text-3xl font-outfit font-black text-gray-900 dark:text-white">{value}</p>
      </div>
    </div>
  )
}

export default function AdminOverview({ stats }) {
  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-in fade-in">
      <div>
        <h1 className="text-3xl font-outfit font-extrabold text-gray-900 dark:text-white tracking-tight">System Overview</h1>
        <p className="text-gray-500 dark:text-gray-400 font-poppins mt-2">High-level metrics of platform usage.</p>
      </div>
      
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard title="Total Agents" value={stats.total} icon={Users} color="bg-blue-500" />
          <StatCard title="Approved Agents" value={stats.approved} icon={CheckCircle} color="bg-green-500" />
          <StatCard title="Pending Approvals" value={stats.pending} icon={Clock} color="bg-yellow-500" />
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white/60 dark:bg-neutral-900/40 backdrop-blur-md rounded-2xl border border-gray-200 dark:border-neutral-800 p-6 shadow-lg shadow-black/5">
            <h3 className="text-lg font-outfit font-bold text-gray-900 dark:text-white mb-6">Agent Subscriptions</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={[
                  { name: 'Free', value: stats.tiers?.free || 0 },
                  { name: 'Basic', value: stats.tiers?.basic || 0 },
                  { name: 'Professional', value: stats.tiers?.professional || 0 }
                ]}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f97316" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb', backgroundColor: 'rgba(255, 255, 255, 0.9)' }} />
                  <Area type="monotone" dataKey="value" stroke="#f97316" fillOpacity={1} fill="url(#colorValue)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="bg-white/60 dark:bg-neutral-900/40 backdrop-blur-md rounded-2xl border border-gray-200 dark:border-neutral-800 p-6 shadow-lg shadow-black/5">
            <h3 className="text-lg font-outfit font-bold text-gray-900 dark:text-white mb-6">Approval Status</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Approved', value: stats.approved || 0 },
                      { name: 'Pending', value: stats.pending || 0 }
                    ]}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    <Cell fill="#22c55e" />
                    <Cell fill="#eab308" />
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb' }} />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
