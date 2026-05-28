import { useEffect, useState, useCallback } from 'react'
import {
  Plus, Pencil, Trash2, X, AlertTriangle, RefreshCw,
  User, Users, UserCheck, Key, Phone,
  ShieldCheck, Briefcase, HeadphonesIcon, Eye, EyeOff,
  ToggleLeft, ToggleRight, Upload,
} from 'lucide-react'
import api from '@/api/client'

/* ─── role config ──────────────────────────────── */
const ROLES = [
  { value: 2, label: 'Manager',     color: 'bg-blue-500/10 text-blue-400 border-blue-500/20',   icon: Briefcase       },
  { value: 3, label: 'Agent',       color: 'bg-green-500/10 text-green-400 border-green-500/20', icon: HeadphonesIcon  },
  { value: 1, label: 'Superadmin',  color: 'bg-purple-500/10 text-purple-400 border-purple-500/20', icon: ShieldCheck },
  { value: 4, label: 'Calendar',    color: 'bg-gray-500/10 text-gray-400 border-gray-700',       icon: User            },
]
const roleById = (id: number) => ROLES.find(r => r.value === id) ?? ROLES[0]

/* ─── shared styles ────────────────────────────── */
const inp = 'w-full px-4 py-2.5 bg-[#1F2937] border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 placeholder-gray-500'
const lbl = 'block text-sm font-medium text-gray-300 mb-1.5'

/* ═══ Modal shell ═══════════════════════════════════════════ */
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0D1117] border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 sticky top-0 bg-[#0D1117]">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="p-1 text-gray-500 hover:text-white rounded-lg hover:bg-gray-800 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}

function ModalFooter({ onClose, busy, label }: { onClose: () => void; busy: boolean; label: string }) {
  return (
    <div className="flex gap-3 pt-4 border-t border-gray-800 mt-4">
      <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm">Cancel</button>
      <button type="submit" disabled={busy} className="flex-1 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl transition-colors text-sm font-medium">
        {busy ? 'Saving…' : label}
      </button>
    </div>
  )
}

function DeleteModal({ user, onConfirm, onCancel }: { user: any; onConfirm: () => void; onCancel: () => void }) {
  return (
    <Modal title="Delete User" onClose={onCancel}>
      <div className="flex items-start gap-4 mb-6">
        <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="w-5 h-5 text-red-400" />
        </div>
        <p className="text-sm text-gray-300 mt-1">
          Delete <span className="font-semibold text-white">@{user.username}</span>? All their data will be permanently removed.
        </p>
      </div>
      <div className="flex gap-3">
        <button onClick={onCancel}  className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm">Cancel</button>
        <button onClick={onConfirm} className="flex-1 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-colors text-sm font-medium">Delete</button>
      </div>
    </Modal>
  )
}

/* ═══ Create / Edit modal ═══════════════════════════════════ */
const BLANK_FORM = {
  username: '', email: '', first_name: '', last_name: '',
  phone: '', role: 2, is_active: true,
  password: '', password_confirm: '', extension: '', sip_password: '',
}
type UserForm = typeof BLANK_FORM

function UserModal({ initial, onSave, onClose }: {
  initial?: any
  onSave: () => void
  onClose: () => void
}) {
  const isEdit = !!initial
  const [form, setForm] = useState<UserForm>(
    isEdit
      ? {
          ...BLANK_FORM,
          username:   initial.username    ?? '',
          email:      initial.email       ?? '',
          first_name: initial.first_name  ?? '',
          last_name:  initial.last_name   ?? '',
          phone:      initial.phone       ?? '',
          role:         initial.role          ?? 2,
          is_active:    initial.is_active     ?? true,
          extension:    initial.agent_extension ?? '',
          sip_password: '',   // never pre-fill passwords from server
        }
      : { ...BLANK_FORM }
  )
  const [busy, setBusy] = useState(false)
  const [err, setErr]   = useState('')
  const [showPw, setShowPw] = useState(false)

  const set = (p: Partial<UserForm>) => setForm(f => ({ ...f, ...p }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      if (isEdit) {
        await api.patch(`/accounts/users/${initial.id}/`, {
          email: form.email, first_name: form.first_name,
          last_name: form.last_name, phone: form.phone,
          role: form.role,
        })
        if (form.role === 3) {
          await api.patch(`/accounts/users/${initial.id}/update_extension/`, {
            extension:    form.extension,
            sip_password: form.sip_password,
          })
        }
      } else {
        await api.post('/accounts/users/', {
          username: form.username, email: form.email,
          password: form.password, password_confirm: form.password_confirm,
          first_name: form.first_name, last_name: form.last_name,
          phone: form.phone, role: form.role,
          extension: form.extension, sip_password: form.sip_password,
        })
      }
      onSave()
    } catch (e: any) {
      const d = e?.response?.data
      setErr(typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Failed to save user.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={isEdit ? `Edit ${initial.username}` : 'Add New User'} onClose={onClose}>
      <form onSubmit={submit}>
        {err && <p className="text-sm text-red-400 mb-4 bg-red-500/5 border border-red-500/20 rounded-xl px-3 py-2">{err}</p>}

        <div className="space-y-3 mb-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={lbl}>First Name</label>
              <input value={form.first_name} onChange={e => set({ first_name: e.target.value })} className={inp} placeholder="John" />
            </div>
            <div>
              <label className={lbl}>Last Name</label>
              <input value={form.last_name} onChange={e => set({ last_name: e.target.value })} className={inp} placeholder="Doe" />
            </div>
          </div>

          {!isEdit && (
            <div>
              <label className={lbl}>Username <span className="text-red-400">*</span></label>
              <input value={form.username} onChange={e => set({ username: e.target.value })} className={inp} placeholder="johndoe" required />
            </div>
          )}

          <div>
            <label className={lbl}>Email <span className="text-red-400">*</span></label>
            <input type="email" value={form.email} onChange={e => set({ email: e.target.value })} className={inp} placeholder="john@company.com" required />
          </div>

          <div>
            <label className={lbl}>Phone</label>
            <input value={form.phone} onChange={e => set({ phone: e.target.value })} className={inp} placeholder="+15551234567" />
          </div>

          <div>
            <label className={lbl}>Role <span className="text-red-400">*</span></label>
            <select value={form.role} onChange={e => set({ role: Number(e.target.value) })} className={inp}>
              {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>

          {/* SIP Extension + Password — only for agents */}
          {form.role === 3 && (
            <div className="bg-gray-800/40 border border-gray-700 rounded-xl p-4 space-y-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">SIP Extension (FreeSWITCH)</p>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={lbl}>Extension Number</label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
                    <input
                      value={form.extension}
                      onChange={e => set({ extension: e.target.value })}
                      className={`${inp} pl-9`}
                      placeholder="1001"
                    />
                  </div>
                </div>

                <div>
                  <label className={lbl}>SIP Password</label>
                  <div className="relative">
                    <input
                      type={showPw ? 'text' : 'password'}
                      value={form.sip_password}
                      onChange={e => set({ sip_password: e.target.value })}
                      className={`${inp} pr-10`}
                      placeholder={isEdit ? '(unchanged)' : 'e.g. s3cr3t!'}
                    />
                    <button type="button" onClick={() => setShowPw(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                      {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <p className="text-xs text-gray-600">
                Saving with an extension and SIP password pushes the extension to FreeSWITCH automatically.
              </p>
            </div>
          )}

          {/* Password — create only */}
          {!isEdit && (
            <>
              <div>
                <label className={lbl}>Password <span className="text-red-400">*</span></label>
                <div className="relative">
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={form.password}
                    onChange={e => set({ password: e.target.value })}
                    className={`${inp} pr-10`}
                    placeholder="Min. 8 characters"
                    required minLength={8}
                  />
                  <button type="button" onClick={() => setShowPw(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                    {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className={lbl}>Confirm Password <span className="text-red-400">*</span></label>
                <input
                  type={showPw ? 'text' : 'password'}
                  value={form.password_confirm}
                  onChange={e => set({ password_confirm: e.target.value })}
                  className={inp}
                  placeholder="Repeat password"
                  required
                />
              </div>
            </>
          )}
        </div>

        <ModalFooter onClose={onClose} busy={busy} label={isEdit ? 'Save Changes' : 'Create User'} />
      </form>
    </Modal>
  )
}

/* ═══ Reset Password modal ══════════════════════════════════ */
function ResetPasswordModal({ user, onDone, onClose }: { user: any; onDone: () => void; onClose: () => void }) {
  const [pw, setPw]       = useState('')
  const [showPw, setShowPw] = useState(false)
  const [busy, setBusy]   = useState(false)
  const [err,  setErr]    = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (pw.length < 8) { setErr('Minimum 8 characters.'); return }
    setBusy(true); setErr('')
    try {
      await api.post(`/accounts/users/${user.id}/set_password/`, { password: pw })
      onDone()
    } catch (e: any) {
      setErr(e?.response?.data?.password ?? 'Failed to reset password.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={`Reset Password — @${user.username}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        {err && <p className="text-sm text-red-400">{err}</p>}
        <div>
          <label className={lbl}>New Password <span className="text-red-400">*</span></label>
          <div className="relative">
            <input
              type={showPw ? 'text' : 'password'}
              value={pw}
              onChange={e => setPw(e.target.value)}
              className={`${inp} pr-10`}
              placeholder="Min. 8 characters"
              required minLength={8} autoFocus
            />
            <button type="button" onClick={() => setShowPw(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
              {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>
        <ModalFooter onClose={onClose} busy={busy} label="Reset Password" />
      </form>
    </Modal>
  )
}

/* ═══ Main page ══════════════════════════════════════════════ */
export function UsersPage() {
  const [users,        setUsers]       = useState<any[]>([])
  const [loading,      setLoading]     = useState(true)
  const [search,       setSearch]      = useState('')
  const [roleFilter,   setRoleFilter]  = useState('')

  const [userModal,    setUserModal]   = useState<'create' | 'edit' | null>(null)
  const [editUser,     setEditUser]    = useState<any>(null)
  const [deleteUser,   setDeleteUser]  = useState<any>(null)
  const [resetUser,    setResetUser]   = useState<any>(null)
  const [toastMsg,     setToastMsg]    = useState('')
  const [syncAllBusy,  setSyncAllBusy] = useState(false)
  // syncExt: userId → 'syncing' | 'ok' | 'warn:<msg>' | 'error:<msg>'
  const [syncExt,      setSyncExt]     = useState<Record<number, string>>({})

  const toast = (msg: string) => { setToastMsg(msg); setTimeout(() => setToastMsg(''), 3000) }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/accounts/users/')
      setUsers(data.results ?? data)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async () => {
    if (!deleteUser) return
    try {
      await api.delete(`/accounts/users/${deleteUser.id}/`)
      setDeleteUser(null); load(); toast('User deleted.')
    } catch (e) { console.error(e) }
  }

  const handleSyncExtension = async (u: any) => {
    setSyncExt(s => ({ ...s, [u.id]: 'syncing' }))
    try {
      const { data } = await api.post(`/accounts/users/${u.id}/sync_extension/`)
      if (!data.success) {
        setSyncExt(s => ({ ...s, [u.id]: `error:${data.message}` }))
        return
      }
      setSyncExt(s => ({
        ...s,
        [u.id]: data.xml_written && data.message?.includes('CLI')
          ? `warn:${data.message}`
          : 'ok',
      }))
      toast(`Extension ${u.agent_extension} synced to FreeSWITCH.`)
    } catch (e: any) {
      const msg = e?.response?.data?.message ?? 'Sync failed'
      setSyncExt(s => ({ ...s, [u.id]: `error:${msg}` }))
    }
  }

  const handleSyncAllExtensions = async () => {
    const agentIds = users.filter(u => u.role === 3 && u.agent_extension).map(u => u.id)
    setSyncAllBusy(true)
    setSyncExt(s => ({
      ...s,
      ...Object.fromEntries(agentIds.map(id => [id, 'syncing'])),
    }))
    try {
      const { data } = await api.post('/accounts/users/sync_all_extensions/')
      const next: Record<number, string> = {}
      for (const r of data.results ?? []) {
        if (r.skipped) {
          next[r.user_id] = `warn:${r.message}`
        } else if (!r.success) {
          next[r.user_id] = `error:${r.message}`
        } else if (r.xml_written && !r.reloaded) {
          next[r.user_id] = `warn:${r.message}`
        } else {
          next[r.user_id] = 'ok'
        }
      }
      setSyncExt(s => ({ ...s, ...next }))
      toast(data.message ?? 'Extensions synced.')
    } catch (e: any) {
      const msg = e?.response?.data?.message ?? 'Sync all failed'
      setSyncExt(s => ({
        ...s,
        ...Object.fromEntries(agentIds.map(id => [id, `error:${msg}`])),
      }))
    } finally {
      setSyncAllBusy(false)
    }
  }

  const handleToggleActive = async (u: any) => {
    try {
      const { data } = await api.post(`/accounts/users/${u.id}/toggle_active/`)
      setUsers(prev => prev.map(x => x.id === u.id ? { ...x, is_active: data.is_active } : x))
      toast(`${u.username} ${data.is_active ? 'activated' : 'deactivated'}.`)
    } catch (e) { console.error(e) }
  }

  const filtered = users.filter(u => {
    const matchSearch = `${u.username} ${u.first_name} ${u.last_name} ${u.email}`.toLowerCase().includes(search.toLowerCase())
    const matchRole   = roleFilter ? u.role === Number(roleFilter) : true
    return matchSearch && matchRole
  })

  const stats = {
    total:    users.length,
    agents:   users.filter(u => u.role === 3).length,
    managers: users.filter(u => u.role === 2).length,
    active:   users.filter(u => u.is_active).length,
  }

  return (
    <div className="p-8">
      {/* Toast */}
      {toastMsg && (
        <div className="fixed top-6 right-6 z-50 bg-green-500 text-white text-sm font-medium px-4 py-2.5 rounded-xl shadow-lg shadow-green-500/20 flex items-center gap-2">
          <UserCheck className="w-4 h-4" /> {toastMsg}
        </div>
      )}

      {/* Modals */}
      {userModal && (
        <UserModal
          initial={userModal === 'edit' ? editUser : undefined}
          onSave={() => { setUserModal(null); setEditUser(null); load(); toast(userModal === 'edit' ? 'User updated.' : 'User created.') }}
          onClose={() => { setUserModal(null); setEditUser(null) }}
        />
      )}
      {deleteUser && <DeleteModal user={deleteUser} onConfirm={handleDelete} onCancel={() => setDeleteUser(null)} />}
      {resetUser  && (
        <ResetPasswordModal
          user={resetUser}
          onDone={() => { setResetUser(null); toast(`Password reset for ${resetUser.username}.`) }}
          onClose={() => setResetUser(null)}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Users & Agents</h1>
          <p className="text-gray-400 text-sm">Manage user accounts, roles, and SIP extensions</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSyncAllExtensions}
            disabled={syncAllBusy || users.every(u => u.role !== 3 || !u.agent_extension)}
            className="flex items-center gap-2 px-4 py-2.5 bg-green-500 hover:bg-green-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-xl transition-colors shadow-lg shadow-green-500/20 disabled:shadow-none"
          >
            {syncAllBusy ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {syncAllBusy ? 'Syncing...' : 'Sync All Extensions'}
          </button>
          <button
            onClick={() => { setEditUser(null); setUserModal('create') }}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl transition-colors shadow-lg shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" /> Add User
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Users"  value={stats.total}    icon={<Users        className="w-5 h-5 text-blue-400"   />} accent="blue"   />
        <StatCard label="Agents"       value={stats.agents}   icon={<HeadphonesIcon className="w-5 h-5 text-green-400"  />} accent="green"  />
        <StatCard label="Managers"     value={stats.managers} icon={<Briefcase    className="w-5 h-5 text-purple-400" />} accent="purple" />
        <StatCard label="Active"       value={stats.active}   icon={<UserCheck    className="w-5 h-5 text-yellow-400" />} accent="yellow" />
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-xs">
          <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by name, username, email…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#111827] border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          />
        </div>
        <select
          value={roleFilter}
          onChange={e => setRoleFilter(e.target.value)}
          className="px-3 py-2 bg-[#111827] border border-gray-700 rounded-xl text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 cursor-pointer"
        >
          <option value="">All Roles</option>
          {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
        <button onClick={load} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Table */}
      <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="py-16 flex items-center justify-center gap-3 text-gray-500">
            <RefreshCw className="w-5 h-5 animate-spin" />
            <span className="text-sm">Loading users…</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center">
            <Users className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">{search || roleFilter ? 'No users match your filter' : 'No users yet'}</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-[#0D1117] border-b border-gray-800">
              <tr>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Extension</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filtered.map(u => <UserRow
                key={u.id}
                user={u}
                syncState={syncExt[u.id]}
                onEdit={() => { setEditUser(u); setUserModal('edit') }}
                onDelete={() => setDeleteUser(u)}
                onResetPw={() => setResetUser(u)}
                onToggle={() => handleToggleActive(u)}
                onSync={() => handleSyncExtension(u)}
              />)}
            </tbody>
          </table>
        )}
      </div>

      {!loading && (
        <p className="mt-3 text-xs text-gray-600">
          Showing {filtered.length} of {users.length} user{users.length !== 1 ? 's' : ''}
        </p>
      )}
    </div>
  )
}

/* ─── sub-components ────────────────────────────── */
function UserRow({ user, syncState, onEdit, onDelete, onResetPw, onToggle, onSync }: {
  user: any
  syncState?: string
  onEdit: () => void; onDelete: () => void
  onResetPw: () => void; onToggle: () => void; onSync: () => void
}) {
  const role      = roleById(user.role)
  const isAgent   = user.role === 3
  const initials  = ((user.first_name?.[0] ?? '') + (user.last_name?.[0] ?? '')).toUpperCase() || user.username?.[0]?.toUpperCase() || '?'
  const extension = user.agent_extension ?? ''
  const isSyncing = syncState === 'syncing'
  const syncOk    = syncState === 'ok'
  const syncWarn  = syncState?.startsWith('warn:') && syncState.includes('XML written')
  const syncAttention = syncState?.startsWith('warn:') && !syncState.includes('XML written')
  const syncErr   = syncState?.startsWith('error:')
  const syncMsg    = syncWarn || syncAttention || syncErr ? syncState!.split(':').slice(1).join(':') : ''

  return (
    <tr className="hover:bg-white/[0.02] transition-colors">
      {/* User info */}
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-sm font-bold
            ${user.is_active ? 'bg-blue-500/20 text-blue-300' : 'bg-gray-700 text-gray-500'}`}>
            {initials}
          </div>
          <div>
            <div className="text-sm font-semibold text-white">
              {[user.first_name, user.last_name].filter(Boolean).join(' ') || user.username}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">@{user.username} · {user.email}</div>
          </div>
        </div>
      </td>

      {/* Role */}
      <td className="px-6 py-4">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${role.color}`}>
          <role.icon className="w-3 h-3" />
          {role.label}
        </span>
      </td>

      {/* SIP Extension + sync status */}
      <td className="px-6 py-4">
        {extension ? (
          <div className="flex flex-col gap-1">
            <span className="inline-flex items-center gap-1.5 text-sm text-gray-300 font-mono bg-gray-800 px-2.5 py-0.5 rounded-lg border border-gray-700 w-fit">
              <Phone className="w-3 h-3 text-gray-500" /> {extension}
            </span>
            {syncOk   && <span className="text-xs text-green-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block"/>Synced to FS</span>}
            {syncAttention && <span className="text-xs text-yellow-400 flex items-center gap-1" title={syncMsg}><span className="w-1.5 h-1.5 rounded-full bg-yellow-400 inline-block"/>{syncMsg}</span>}
            {syncWarn && <span className="text-xs text-yellow-400 flex items-center gap-1" title={syncState!.slice(5)}><span className="w-1.5 h-1.5 rounded-full bg-yellow-400 inline-block"/>XML written — run reloadxml</span>}
            {syncErr  && <span className="text-xs text-red-400 flex items-center gap-1" title={syncMsg}><span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block"/>{syncMsg}</span>}
          </div>
        ) : (
          <span className="text-xs text-gray-600">—</span>
        )}
      </td>

      {/* Active toggle */}
      <td className="px-6 py-4">
        <button
          onClick={onToggle}
          title={user.is_active ? 'Click to deactivate' : 'Click to activate'}
          className="flex items-center gap-1.5 text-xs font-medium transition-colors"
        >
          {user.is_active
            ? <><ToggleRight className="w-5 h-5 text-green-400" /><span className="text-green-400">Active</span></>
            : <><ToggleLeft  className="w-5 h-5 text-gray-500" /><span className="text-gray-500">Inactive</span></>
          }
        </button>
      </td>

      {/* Actions */}
      <td className="px-6 py-4 text-right">
        <div className="flex items-center justify-end gap-1">
          {/* Sync extension to FreeSWITCH — agents only */}
          {isAgent && (
            <IBtn
              title={extension ? 'Sync extension to FreeSWITCH' : 'Set extension first'}
              cls={`hover:bg-green-500/10 hover:text-green-400 ${!extension ? 'opacity-30 pointer-events-none' : ''}`}
              onClick={onSync}
            >
              {isSyncing
                ? <RefreshCw className="w-4 h-4 animate-spin" />
                : <Upload    className="w-4 h-4" />}
            </IBtn>
          )}
          <div className="w-px h-4 bg-gray-700 mx-0.5" />
          <IBtn title="Edit"           cls="hover:bg-blue-500/10 hover:text-blue-400"     onClick={onEdit}>    <Pencil className="w-4 h-4" /></IBtn>
          <IBtn title="Reset Password" cls="hover:bg-yellow-500/10 hover:text-yellow-400" onClick={onResetPw}><Key    className="w-4 h-4" /></IBtn>
          <IBtn title="Delete"         cls="hover:bg-red-500/10 hover:text-red-400"       onClick={onDelete}>  <Trash2 className="w-4 h-4" /></IBtn>
        </div>
      </td>
    </tr>
  )
}

function IBtn({ children, title, onClick, cls }: { children: React.ReactNode; title: string; onClick: () => void; cls: string }) {
  return (
    <button title={title} onClick={onClick} className={`p-1.5 text-gray-400 rounded-lg transition-colors ${cls}`}>
      {children}
    </button>
  )
}

function StatCard({ label, value, icon, accent }: { label: string; value: number; icon: React.ReactNode; accent: string }) {
  const borders: Record<string, string> = { blue: 'border-blue-500/20', green: 'border-green-500/20', purple: 'border-purple-500/20', yellow: 'border-yellow-500/20' }
  return (
    <div className={`bg-[#111827] border ${borders[accent] ?? 'border-gray-800'} rounded-2xl p-5`}>
      <div className="flex items-center justify-between mb-3">
        <div className="p-2 bg-gray-800/80 rounded-lg">{icon}</div>
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}
