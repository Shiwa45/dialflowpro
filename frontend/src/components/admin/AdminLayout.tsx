import { Outlet, NavLink } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import {
  LayoutDashboard,
  Phone,
  Users,
  ListOrdered,
  BarChart,
  Settings,
  LogOut,
  MessageSquare,
  Shield,
  Activity,
  Radio,
  Bot,
} from 'lucide-react'

export function AdminLayout() {
  const { user, logout } = useAuthStore()

  const navigation = [
    { name: 'Dashboard',      to: '/',               icon: LayoutDashboard, exact: true },
    { name: 'Live Monitoring',to: '/live-monitoring', icon: Activity    },
    { name: 'Agent Tracking', to: '/agent-tracking',  icon: Radio       },
    { name: 'AI Agents',      to: '/ai-agents',       icon: Bot         },
    { name: 'AI Calls',       to: '/ai-calls',        icon: MessageSquare },
    { name: 'Campaigns',      to: '/campaigns',       icon: Phone       },
    { name: 'SMS Campaigns',  to: '/sms-campaigns',   icon: MessageSquare },
    { name: 'Contacts',       to: '/contacts',        icon: Users       },
    { name: 'Queues',         to: '/queues',          icon: ListOrdered },
    { name: 'DNC Lists',      to: '/dnc',             icon: Shield      },
    { name: 'Users & Agents', to: '/users',           icon: Users       },
    { name: 'Reports',        to: '/reports',         icon: BarChart    },
    { name: 'Settings',       to: '/settings',        icon: Settings    },
  ]

  return (
    <div className="h-screen bg-[#0A0E1A] flex">
      {/* Sidebar */}
      <aside className="w-64 bg-[#111827] border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="h-16 border-b border-gray-800 flex items-center px-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded flex items-center justify-center">
              <Phone className="w-5 h-5 text-white" />
            </div>
            <span className="text-white font-semibold">DialFlow Pro</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-300'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* User Profile */}
        <div className="border-t border-gray-800 p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
              {user?.first_name?.[0] || user?.username?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white truncate">
                {user?.first_name} {user?.last_name}
              </div>
              <div className="text-xs text-gray-400 truncate">
                {user?.role === 1 ? 'Superadmin' : 'Manager'}
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:bg-gray-800 hover:text-gray-300 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
