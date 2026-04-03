import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Briefcase, FileCheck, Settings } from 'lucide-react'

export function Layout() {
  const location = useLocation()

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/jobs', icon: Briefcase, label: 'Jobs' },
    { path: '/applications', icon: FileCheck, label: 'Applications' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ]

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700">
        <div className="p-6">
          <h1 className="text-xl font-bold text-white">AutoApply Agent</h1>
          <p className="text-sm text-gray-400 mt-1">AI Job Applications</p>
        </div>
        
        <nav className="mt-6">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center px-6 py-3 text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
