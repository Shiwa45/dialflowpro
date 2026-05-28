# DialFlow Pro - React Frontend

Modern React 18 frontend for DialFlow Pro with role-based interfaces.

## Features

### 🎯 Two Distinct Interfaces

**Agent Panel** - Fullscreen softphone (NO sidebar, NO CRM navigation)
- Clean, focused calling interface
- Dialpad with DTMF tones
- Incoming call screen
- Customer information panel
- Real-time metrics
- Queue selection
- Volume controls

**Admin/Manager CRM** - Full dashboard with sidebar navigation
- Campaign management
- Contact/phonebook management
- Queue monitoring
- SMS campaigns
- DNC lists
- Reports & analytics
- User management (Superadmin only)

## Tech Stack

- **React 18** + TypeScript
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management
- **Axios** - API client with tenant headers
- **React Router v6** - Role-based routing
- **WebSocket** - Real-time updates

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

Opens at http://localhost:3000

### 3. Login

**Admin/Manager:**
- Username: admin
- Password: admin
- Gets: Full CRM with sidebar

**Agent:**
- Username: agent1
- Password: password
- Gets: Agent panel only (no CRM)

## Project Structure

```
src/
├── api/
│   ├── client.ts              # Axios with tenant headers
│   └── endpoints/             # API endpoint modules
├── components/
│   ├── agent/                 # Agent panel components
│   │   ├── Softphone.tsx
│   │   ├── IncomingCallPanel.tsx
│   │   ├── CustomerInfoPanel.tsx
│   │   ├── MetricsBar.tsx
│   │   └── BottomBar.tsx
│   └── admin/                 # Admin CRM components
│       ├── AdminLayout.tsx
│       └── Sidebar.tsx
├── hooks/
│   ├── useWebSocket.ts        # WebSocket manager
│   ├── useAgent.ts            # Agent state
│   └── useQueue.ts            # Queue state
├── pages/
│   ├── agent/
│   │   └── AgentPanel.tsx     # Main agent interface
│   ├── admin/
│   │   ├── Dashboard.tsx
│   │   ├── CampaignsPage.tsx
│   │   └── ...
│   └── LoginPage.tsx
├── store/
│   └── auth.ts                # Auth store (Zustand)
├── types/
│   └── index.ts               # TypeScript interfaces
└── App.tsx                    # Router + role-based routing
```

## 🔐 Tenant-Aware Architecture

**Critical:** Every API request includes tenant header.

### Login Flow

1. POST `/api/auth/token/` with credentials
2. Response includes `user.tenant.schema_name`
3. Store in localStorage: `tenant_schema`
4. All requests include `X-Tenant: {schema_name}` header

### API Client

```typescript
// Automatically adds tenant header to all requests
api.interceptors.request.use((config) => {
  const tenant = localStorage.getItem('tenant_schema');
  if (tenant) {
    config.headers['X-Tenant'] = tenant;
  }
  
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
});
```

## 🎨 Agent Panel Design

Matches the uploaded design image:
- Dark theme (#0A0E1A background)
- 3-column layout
- Real-time metrics at top
- Queue selector at bottom
- No CRM navigation (focused on calling)

## 🏢 Admin CRM Features

- **Dashboard** - Overview metrics and charts
- **Campaigns** - Start/stop voice campaigns
- **SMS Campaigns** - Manage mass texting
- **Contacts** - Phonebooks with CSV import
- **Queues** - Call routing management
- **DNC** - Do-Not-Call lists
- **Reports** - CDR and analytics
- **Settings** - Gateways, users, config

## 🔄 Real-time Updates

WebSocket integration for live updates:

```typescript
// Agent status updates
useWebSocket('/ws/callcenter/agents/', {
  onMessage: (data) => {
    if (data.type === 'agent_status') {
      // Update agent state
    }
  }
});

// Queue updates
useWebSocket('/ws/callcenter/queues/1/', {
  onMessage: (data) => {
    if (data.type === 'queue_update') {
      // Update queue metrics
    }
  }
});
```

## 🚀 Build for Production

```bash
npm run build
# Output in dist/
```

Serve with:
```bash
npm run preview
```

## 🎯 Role-Based Routing

```typescript
// Agent role (3) - ONLY gets agent panel
{isAgent() && (
  <Route path="/" element={<AgentPanel />} />
)}

// Admin/Manager (1, 2) - Gets full CRM
{isAdmin() && (
  <Route path="/" element={<AdminLayout />}>
    <Route index element={<Dashboard />} />
    <Route path="campaigns" element={<CampaignsPage />} />
    ...
  </Route>
)}
```

## API Integration Examples

### Fetch Campaigns

```typescript
import api from '@/api/client';

const { data } = await api.get('/dialer-campaign/campaigns/');
```

### Start Campaign

```typescript
await api.post(`/dialer-campaign/campaigns/${id}/start/`);
```

### Set Agent Available

```typescript
await api.post(`/callcenter/agents/${agentId}/set_available/`);
```

## Environment Variables

Create `.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Development Tips

1. **Hot Module Replacement** - Changes reflect instantly
2. **TypeScript** - Full type safety
3. **Tailwind** - Utility-first CSS
4. **Component isolation** - Agent vs Admin completely separate
5. **Tenant header** - Always included automatically

## Next Steps

1. Install shadcn/ui components for better UX
2. Add form validation with react-hook-form + zod
3. Add charts with recharts
4. Add toast notifications
5. Add loading states
6. Add error boundaries
7. Add E2E tests

## License

MIT
