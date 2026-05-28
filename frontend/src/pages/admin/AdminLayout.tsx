import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/admin/Sidebar'

export default function AdminLayout() {
  return (
    <div className="h-screen flex bg-[#0A0E1A]">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <Outlet />
      </div>
    </div>
  )
}
