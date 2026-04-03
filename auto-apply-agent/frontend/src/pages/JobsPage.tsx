import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Filter, ExternalLink, Play } from 'lucide-react'

export function JobsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const queryClient = useQueryClient()

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', searchTerm],
    queryFn: async () => {
      // In production, fetch from API
      return [
        {
          id: '1',
          title: 'Senior Embedded Systems Engineer',
          company: 'SpaceX',
          location: 'Hawthorne, CA',
          matchScore: 0.92,
          status: 'pending',
          source: 'adzuna',
          applyUrl: '#',
          collectedAt: new Date().toISOString(),
        },
        {
          id: '2',
          title: 'Flight Software Engineer',
          company: 'Blue Origin',
          location: 'Kent, WA',
          matchScore: 0.88,
          status: 'ready_to_apply',
          source: 'jooble',
          applyUrl: '#',
          collectedAt: new Date().toISOString(),
        },
        {
          id: '3',
          title: 'AI/ML Engineer - Aerospace',
          company: 'NASA JPL',
          location: 'Pasadena, CA',
          matchScore: 0.85,
          status: 'applied',
          source: 'adzuna',
          applyUrl: '#',
          collectedAt: new Date().toISOString(),
        },
      ]
    },
  })

  const applyMutation = useMutation({
    mutationFn: async (jobId: string) => {
      // In production, call API
      return { success: true }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-600'
      case 'ready_to_apply':
        return 'bg-blue-600'
      case 'applied':
        return 'bg-green-600'
      case 'failed':
        return 'bg-red-600'
      default:
        return 'bg-gray-600'
    }
  }

  if (isLoading) {
    return <div className="p-8 text-white">Loading...</div>
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-white">Jobs</h1>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center">
          <Search className="w-5 h-5 mr-2" />
          Collect Jobs
        </button>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
        <div className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search jobs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            Filters
          </button>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Job</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Company</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Location</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Match</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {jobs?.map((job) => (
              <tr key={job.id} className="hover:bg-gray-750">
                <td className="px-6 py-4">
                  <div>
                    <p className="text-white font-medium">{job.title}</p>
                    <p className="text-gray-400 text-sm">{job.source}</p>
                  </div>
                </td>
                <td className="px-6 py-4 text-white">{job.company}</td>
                <td className="px-6 py-4 text-gray-300">{job.location}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <div className="w-16 bg-gray-700 rounded-full h-2 mr-2">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${(job.matchScore || 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-white text-sm">
                      {Math.round((job.matchScore || 0) * 100)}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`${getStatusColor(job.status)} text-white px-3 py-1 rounded-full text-xs`}>
                    {job.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <a
                      href={job.applyUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300"
                    >
                      <ExternalLink className="w-5 h-5" />
                    </a>
                    {job.status !== 'applied' && (
                      <button
                        onClick={() => applyMutation.mutate(job.id)}
                        className="text-green-400 hover:text-green-300"
                        disabled={applyMutation.isPending}
                      >
                        <Play className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
