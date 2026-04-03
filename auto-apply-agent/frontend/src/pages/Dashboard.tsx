import { useQuery } from '@tanstack/react-query'
import { Briefcase, CheckCircle, Clock, TrendingUp } from 'lucide-react'

export function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      // In production, fetch from API
      return {
        totalJobs: 156,
        applicationsSent: 42,
        interviewRequests: 5,
        successRate: 12,
      }
    },
  })

  if (isLoading) {
    return <div className="p-8 text-white">Loading...</div>
  }

  const statCards = [
    {
      title: 'Jobs Collected',
      value: stats?.totalJobs || 0,
      icon: Briefcase,
      color: 'bg-blue-600',
    },
    {
      title: 'Applications Sent',
      value: stats?.applicationsSent || 0,
      icon: CheckCircle,
      color: 'bg-green-600',
    },
    {
      title: 'Interview Requests',
      value: stats?.interviewRequests || 0,
      icon: Clock,
      color: 'bg-yellow-600',
    },
    {
      title: 'Success Rate',
      value: `${stats?.successRate || 0}%`,
      icon: TrendingUp,
      color: 'bg-purple-600',
    },
  ]

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-8">Dashboard</h1>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <div
              key={stat.title}
              className="bg-gray-800 rounded-lg p-6 border border-gray-700"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">{stat.title}</p>
                  <p className="text-3xl font-bold text-white mt-2">
                    {stat.value}
                  </p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent Activity */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-gray-700">
            <div>
              <p className="text-white font-medium">Application Submitted</p>
              <p className="text-gray-400 text-sm">Senior Embedded Engineer at SpaceX</p>
            </div>
            <span className="text-green-400 text-sm">2 hours ago</span>
          </div>
          <div className="flex items-center justify-between py-3 border-b border-gray-700">
            <div>
              <p className="text-white font-medium">Job Collected</p>
              <p className="text-gray-400 text-sm">AI/ML Engineer at Blue Origin</p>
            </div>
            <span className="text-blue-400 text-sm">4 hours ago</span>
          </div>
          <div className="flex items-center justify-between py-3 border-b border-gray-700">
            <div>
              <p className="text-white font-medium">Interview Requested</p>
              <p className="text-gray-400 text-sm">Flight Software Engineer at NASA JPL</p>
            </div>
            <span className="text-yellow-400 text-sm">1 day ago</span>
          </div>
        </div>
      </div>
    </div>
  )
}
