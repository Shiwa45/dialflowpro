import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import { AgentPanel } from './pages/agent/AgentPanel'
import { LoginPage } from './pages/LoginPage'
import { AdminLayout } from './components/admin/AdminLayout'
import { Dashboard } from './pages/admin/Dashboard'
import { LiveMonitoring } from './pages/admin/LiveMonitoring'
import { LiveAgentTracking } from './pages/admin/LiveAgentTracking'
import { AIAgentsPage } from './pages/admin/ai/AIAgentsPage'
import { AIAgentBuilder } from './pages/admin/ai/AIAgentBuilder'
import { AICallReviewPage } from './pages/admin/ai/AICallReviewPage'
import { CampaignsPage } from './pages/admin/CampaignsPage'
import { CampaignCreate } from './pages/admin/CampaignCreate'
import { CampaignDetail } from './pages/admin/CampaignDetail'
import { ContactsPage } from './pages/admin/ContactsPage'
import { SmsCampaignsPage } from './pages/admin/SmsCampaignsPage'
import { SmsCampaignCreate } from './pages/admin/SmsCampaignCreate'
import { QueuesPage } from './pages/admin/QueuesPage'
import { DncPage } from './pages/admin/DncPage'
import { ReportsPage } from './pages/admin/ReportsPage'
import { SettingsPage } from './pages/admin/SettingsPage'
import { UsersPage } from './pages/admin/UsersPage'

export function App() {
  const { user, isAgent, isAdmin } = useAuthStore()

  if (!user) {
    return <LoginPage />
  }

  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        {/* Agent gets ONLY the agent panel - no CRM navigation */}
        {isAgent() && (
          <>
            <Route path="/" element={<AgentPanel />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        )}

        {/* Admin/Manager gets full CRM with sidebar */}
        {isAdmin() && (
          <>
            <Route path="/" element={<AdminLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="live-monitoring" element={<LiveMonitoring />} />
              <Route path="agent-tracking" element={<LiveAgentTracking />} />

              {/* AI Voice Agents */}
              <Route path="ai-agents" element={<AIAgentsPage />} />
              <Route path="ai-agents/new" element={<AIAgentBuilder />} />
              <Route path="ai-agents/:id" element={<AIAgentBuilder />} />
              <Route path="ai-calls" element={<AICallReviewPage />} />
              
              {/* Voice Campaigns */}
              <Route path="campaigns" element={<CampaignsPage />} />
              <Route path="campaigns/create" element={<CampaignCreate />} />
              <Route path="campaigns/:id" element={<CampaignDetail />} />
              <Route path="campaigns/:id/edit" element={<CampaignCreate />} />
              
              {/* SMS Campaigns */}
              <Route path="sms-campaigns" element={<SmsCampaignsPage />} />
              <Route path="sms-campaigns/create" element={<SmsCampaignCreate />} />
              
              {/* Contacts */}
              <Route path="contacts" element={<ContactsPage />} />
              
              {/* Queues */}
              <Route path="queues" element={<QueuesPage />} />
              
              {/* DNC */}
              <Route path="dnc" element={<DncPage />} />
              
              {/* Users & Agents */}
              <Route path="users" element={<UsersPage />} />

              {/* Reports */}
              <Route path="reports" element={<ReportsPage />} />

              {/* Settings */}
              <Route path="settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        )}

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
