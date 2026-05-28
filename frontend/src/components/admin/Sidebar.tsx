import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Phone, Users, BarChart, Settings, LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/auth'

export default function Sidebar() {
  const { logout, user } = useAuthStore()

  return (
    <aside className="w-64 bg-[#0F1419] border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="h-14 border-b border-gray-800 flex items-center px-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-500 rounded-lg" />
          <span className="font-semibold text-white">DialFlow Pro</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        <NavItem to="/" icon={<LayoutDashboard />}>Dashboard</NavItem>
        <NavItem to="/campaigns" icon={<Phone />}>Campaigns</NavItem>
        <NavItem to="/contacts" icon={<Users />}>Contacts</NavItem>
        <NavItem to="/reports" icon={<BarChart />}>Reports</NavItem>
        <NavItem to="/settings" icon={<Settings />}>Settings</NavItem>
      </nav>

      {/* User Info */}
      <div className="border-t border-gray-800 p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
            {user?.first_name?.[0] || user?.username?.[0] || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white truncate">
              {user?.first_name || user?.username}
            </div>
            <div className="text-xs text-gray-400 truncate">{user?.email}</div>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}

function NavItem({ to, icon, children }: {
  to: string
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
          isActive
            ? 'bg-blue-500 text-white'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'
        }`
      }
    >
      <span className="w-5 h-5">{icon}</span>
      <span>{children}</span>
    </NavLink>
  )
}
