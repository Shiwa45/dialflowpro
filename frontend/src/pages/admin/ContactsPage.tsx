import { useEffect, useState, useCallback } from 'react'
import {
  Plus, Upload, Search, Trash2, Pencil, X,
  BookOpen, User, AlertTriangle, RefreshCw,
} from 'lucide-react'
import api from '@/api/client'

/* ─── types ─────────────────────────────────────────── */
interface Phonebook { id: number; name: string; description: string; contact_count: number }
interface Contact   { id: number; contact: string; first_name: string; last_name: string; email: string; status: number }

/* ─── shared input/label styles ────────────────────── */
const inp  = 'w-full px-4 py-2.5 bg-[#1F2937] border border-gray-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 placeholder-gray-500'
const lbl  = 'block text-sm font-medium text-gray-300 mb-1.5'

/* ═══════════════════════════════════════════════════ */
/*  Phonebook modal (create / edit)                   */
/* ═══════════════════════════════════════════════════ */
function PhonebookModal({
  initial,
  onSave,
  onClose,
}: {
  initial?: Phonebook | null
  onSave: (pb: Phonebook) => void
  onClose: () => void
}) {
  const [name, setName]   = useState(initial?.name        ?? '')
  const [desc, setDesc]   = useState(initial?.description ?? '')
  const [busy, setBusy]   = useState(false)
  const [err,  setErr]    = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      const payload = { name, description: desc }
      const { data } = initial
        ? await api.patch(`/dialer-contact/phonebooks/${initial.id}/`, payload)
        : await api.post('/dialer-contact/phonebooks/', payload)
      onSave(data)
    } catch (e: any) {
      setErr(e?.response?.data?.name?.[0] ?? 'Failed to save phonebook.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={initial ? 'Edit Phonebook' : 'New Phonebook'} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        {err && <p className="text-sm text-red-400">{err}</p>}
        <div>
          <label className={lbl}>Name <span className="text-red-400">*</span></label>
          <input value={name} onChange={e => setName(e.target.value)} className={inp} placeholder="e.g. Leads Q1 2024" required />
        </div>
        <div>
          <label className={lbl}>Description</label>
          <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={2} className={inp} placeholder="Optional notes..." />
        </div>
        <ModalFooter onClose={onClose} busy={busy} label={initial ? 'Save Changes' : 'Create Phonebook'} />
      </form>
    </Modal>
  )
}

/* ═══════════════════════════════════════════════════ */
/*  Contact modal (create / edit)                     */
/* ═══════════════════════════════════════════════════ */
function ContactModal({
  phonebookId,
  initial,
  onSave,
  onClose,
}: {
  phonebookId: number
  initial?: Contact | null
  onSave: (c: Contact) => void
  onClose: () => void
}) {
  const [form, setForm] = useState({
    contact:    initial?.contact    ?? '',
    first_name: initial?.first_name ?? '',
    last_name:  initial?.last_name  ?? '',
    email:      initial?.email      ?? '',
    status:     initial?.status     ?? 1,
  })
  const [busy, setBusy] = useState(false)
  const [err,  setErr]  = useState('')

  const set = (p: Partial<typeof form>) => setForm(f => ({ ...f, ...p }))

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true); setErr('')
    try {
      const payload = initial
        ? form
        : { ...form, phonebook: phonebookId }
      const { data } = initial
        ? await api.patch(`/dialer-contact/contacts/${initial.id}/`, payload)
        : await api.post('/dialer-contact/contacts/', payload)
      onSave(data)
    } catch (e: any) {
      const d = e?.response?.data
      if (typeof d === 'object') {
        setErr(Object.values(d).flat().join(' '))
      } else {
        setErr('Failed to save contact.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={initial ? 'Edit Contact' : 'Add Contact'} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        {err && <p className="text-sm text-red-400">{err}</p>}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={lbl}>First Name</label>
            <input value={form.first_name} onChange={e => set({ first_name: e.target.value })} className={inp} placeholder="John" />
          </div>
          <div>
            <label className={lbl}>Last Name</label>
            <input value={form.last_name} onChange={e => set({ last_name: e.target.value })} className={inp} placeholder="Doe" />
          </div>
        </div>
        <div>
          <label className={lbl}>Phone Number <span className="text-red-400">*</span></label>
          <input value={form.contact} onChange={e => set({ contact: e.target.value })} className={inp} placeholder="+15551234567" required />
        </div>
        <div>
          <label className={lbl}>Email</label>
          <input type="email" value={form.email} onChange={e => set({ email: e.target.value })} className={inp} placeholder="john@example.com" />
        </div>
        <div>
          <label className={lbl}>Status</label>
          <select value={form.status} onChange={e => set({ status: Number(e.target.value) })} className={inp}>
            <option value={1}>Active</option>
            <option value={2}>Inactive</option>
            <option value={3}>Blocked</option>
          </select>
        </div>
        <ModalFooter onClose={onClose} busy={busy} label={initial ? 'Save Changes' : 'Add Contact'} />
      </form>
    </Modal>
  )
}

/* ═══════════════════════════════════════════════════ */
/*  CSV Import modal                                  */
/* ═══════════════════════════════════════════════════ */
function ImportModal({
  phonebook,
  onDone,
  onClose,
}: {
  phonebook: Phonebook
  onDone: () => void
  onClose: () => void
}) {
  const [file,   setFile]   = useState<File | null>(null)
  const [skip,   setSkip]   = useState(true)
  const [busy,   setBusy]   = useState(false)
  const [result, setResult] = useState<any>(null)
  const [err,    setErr]    = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setBusy(true); setErr('')
    const fd = new FormData()
    fd.append('phonebook', String(phonebook.id))
    fd.append('csv_file', file)
    fd.append('skip_duplicates', String(skip))
    try {
      const { data } = await api.post('/dialer-contact/contacts/import_csv/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(data)
      onDone()
    } catch (e: any) {
      setErr(e?.response?.data?.detail ?? 'Import failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={`Import CSV → ${phonebook.name}`} onClose={onClose}>
      {result ? (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3">
              <div className="text-2xl font-bold text-green-400">{result.created}</div>
              <div className="text-xs text-gray-400 mt-1">Created</div>
            </div>
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-3">
              <div className="text-2xl font-bold text-yellow-400">{result.skipped}</div>
              <div className="text-xs text-gray-400 mt-1">Skipped</div>
            </div>
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
              <div className="text-2xl font-bold text-red-400">{result.errors}</div>
              <div className="text-xs text-gray-400 mt-1">Errors</div>
            </div>
          </div>
          {result.error_details?.length > 0 && (
            <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-3 text-xs text-red-400 space-y-1 max-h-32 overflow-auto">
              {result.error_details.map((e: string, i: number) => <p key={i}>{e}</p>)}
            </div>
          )}
          <button onClick={onClose} className="w-full px-4 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-medium">
            Done
          </button>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          {err && <p className="text-sm text-red-400">{err}</p>}
          <div className="bg-gray-800/50 rounded-xl p-3 text-xs text-gray-400">
            CSV columns: <span className="text-gray-200 font-mono">contact, first_name, last_name, email, status</span>
          </div>
          <div>
            <label className={lbl}>CSV File <span className="text-red-400">*</span></label>
            <input
              type="file"
              accept=".csv"
              onChange={e => setFile(e.target.files?.[0] ?? null)}
              className="w-full px-4 py-2 bg-[#1F2937] border border-gray-700 rounded-xl text-white text-sm file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:bg-blue-500 file:text-white"
              required
            />
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <div onClick={() => setSkip(s => !s)} className={`relative w-10 h-5 rounded-full transition-colors ${skip ? 'bg-blue-500' : 'bg-gray-700'}`}>
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${skip ? 'translate-x-5' : 'translate-x-0.5'}`} />
            </div>
            <span className="text-sm text-gray-300">Skip duplicate numbers</span>
          </label>
          <ModalFooter onClose={onClose} busy={busy} label="Import" />
        </form>
      )}
    </Modal>
  )
}

/* ═══════════════════════════════════════════════════ */
/*  Delete confirm modal                              */
/* ═══════════════════════════════════════════════════ */
function DeleteModal({ label, onConfirm, onCancel }: { label: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <Modal title="Confirm Delete" onClose={onCancel}>
      <div className="flex items-start gap-4 mb-6">
        <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="w-5 h-5 text-red-400" />
        </div>
        <p className="text-sm text-gray-300 mt-1">
          Are you sure you want to delete <span className="font-semibold text-white">"{label}"</span>? This cannot be undone.
        </p>
      </div>
      <div className="flex gap-3">
        <button onClick={onCancel}  className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm">Cancel</button>
        <button onClick={onConfirm} className="flex-1 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-colors text-sm">Delete</button>
      </div>
    </Modal>
  )
}

/* ─── shared modal shell ────────────────────────────── */
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0D1117] border border-gray-700 rounded-2xl w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="p-1 text-gray-500 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}

function ModalFooter({ onClose, busy, label }: { onClose: () => void; busy: boolean; label: string }) {
  return (
    <div className="flex gap-3 pt-2">
      <button type="button" onClick={onClose} className="flex-1 px-4 py-2.5 border border-gray-700 text-gray-300 rounded-xl hover:bg-gray-800 transition-colors text-sm">Cancel</button>
      <button type="submit" disabled={busy} className="flex-1 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 text-white rounded-xl transition-colors text-sm font-medium">
        {busy ? 'Saving...' : label}
      </button>
    </div>
  )
}

/* ═══════════════════════════════════════════════════ */
/*  Main page                                         */
/* ═══════════════════════════════════════════════════ */
export function ContactsPage() {
  const [phonebooks,        setPhonebooks]       = useState<Phonebook[]>([])
  const [selectedPb,        setSelectedPb]       = useState<Phonebook | null>(null)
  const [contacts,          setContacts]         = useState<Contact[]>([])
  const [loading,           setLoading]          = useState(false)
  const [search,            setSearch]           = useState('')

  // Modal states
  const [pbModal,           setPbModal]          = useState<'create' | 'edit' | null>(null)
  const [contactModal,      setContactModal]     = useState<'create' | 'edit' | null>(null)
  const [editContact,       setEditContact]      = useState<Contact | null>(null)
  const [deleteContact,     setDeleteContact]    = useState<Contact | null>(null)
  const [deletePb,          setDeletePb]         = useState<Phonebook | null>(null)
  const [showImport,        setShowImport]       = useState(false)

  /* ─── fetch ─── */
  const loadPhonebooks = useCallback(async () => {
    try {
      const { data } = await api.get('/dialer-contact/phonebooks/')
      const list: Phonebook[] = data.results ?? data
      setPhonebooks(list)
      if (list.length > 0 && !selectedPb) setSelectedPb(list[0])
    } catch (e) { console.error(e) }
  }, [selectedPb])

  const loadContacts = useCallback(async () => {
    if (!selectedPb) return
    setLoading(true)
    try {
      const { data } = await api.get(`/dialer-contact/contacts/?phonebook=${selectedPb.id}`)
      setContacts(data.results ?? data)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }, [selectedPb])

  useEffect(() => { loadPhonebooks() }, [])
  useEffect(() => { loadContacts()   }, [selectedPb])

  /* ─── phonebook CRUD ─── */
  const handlePbSaved = (pb: Phonebook) => {
    setPbModal(null)
    loadPhonebooks()
    if (selectedPb?.id === pb.id) setSelectedPb(pb)
  }

  const confirmDeletePb = async () => {
    if (!deletePb) return
    try {
      await api.delete(`/dialer-contact/phonebooks/${deletePb.id}/`)
      setDeletePb(null)
      if (selectedPb?.id === deletePb.id) setSelectedPb(null)
      loadPhonebooks()
    } catch (e) { console.error(e) }
  }

  /* ─── contact CRUD ─── */
  const handleContactSaved = () => {
    setContactModal(null); setEditContact(null)
    loadContacts()
  }

  const confirmDeleteContact = async () => {
    if (!deleteContact) return
    try {
      await api.delete(`/dialer-contact/contacts/${deleteContact.id}/`)
      setDeleteContact(null)
      loadContacts()
    } catch (e) { console.error(e) }
  }

  const filtered = contacts.filter(c =>
    `${c.contact} ${c.first_name} ${c.last_name} ${c.email}`.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-8">
      {/* ── Modals ── */}
      {pbModal && (
        <PhonebookModal
          initial={pbModal === 'edit' ? selectedPb : null}
          onSave={handlePbSaved}
          onClose={() => setPbModal(null)}
        />
      )}
      {contactModal && selectedPb && (
        <ContactModal
          phonebookId={selectedPb.id}
          initial={contactModal === 'edit' ? editContact : null}
          onSave={handleContactSaved}
          onClose={() => { setContactModal(null); setEditContact(null) }}
        />
      )}
      {showImport && selectedPb && (
        <ImportModal phonebook={selectedPb} onDone={loadContacts} onClose={() => setShowImport(false)} />
      )}
      {deleteContact && (
        <DeleteModal
          label={deleteContact.contact}
          onConfirm={confirmDeleteContact}
          onCancel={() => setDeleteContact(null)}
        />
      )}
      {deletePb && (
        <DeleteModal
          label={deletePb.name}
          onConfirm={confirmDeletePb}
          onCancel={() => setDeletePb(null)}
        />
      )}

      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">Lead Management</h1>
          <p className="text-gray-400 text-sm">Manage your contacts and phonebooks</p>
        </div>
        <button
          onClick={() => setPbModal('create')}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl transition-colors shadow-lg shadow-blue-500/20"
        >
          <Plus className="w-4 h-4" />
          New Phonebook
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* ── Sidebar ── */}
        <div className="lg:col-span-1">
          <div className="bg-[#111827] border border-gray-800 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white">Phonebooks</h3>
              <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">{phonebooks.length}</span>
            </div>

            {phonebooks.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                <p className="text-xs text-gray-600">No phonebooks yet</p>
              </div>
            ) : (
              <div className="space-y-1">
                {phonebooks.map(pb => (
                  <div
                    key={pb.id}
                    onClick={() => setSelectedPb(pb)}
                    className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer transition-colors ${
                      selectedPb?.id === pb.id
                        ? 'bg-blue-500 text-white'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                    }`}
                  >
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{pb.name}</div>
                      <div className={`text-xs mt-0.5 ${selectedPb?.id === pb.id ? 'text-blue-100' : 'text-gray-600'}`}>
                        {pb.contact_count ?? 0} contacts
                      </div>
                    </div>
                    {selectedPb?.id === pb.id && (
                      <div className="flex items-center gap-1 flex-shrink-0 ml-2" onClick={e => e.stopPropagation()}>
                        <button
                          title="Edit"
                          onClick={() => setPbModal('edit')}
                          className="p-1 rounded-lg hover:bg-blue-400/30 transition-colors"
                        >
                          <Pencil className="w-3 h-3" />
                        </button>
                        <button
                          title="Delete"
                          onClick={() => setDeletePb(pb)}
                          className="p-1 rounded-lg hover:bg-red-400/30 transition-colors"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Contacts Panel ── */}
        <div className="lg:col-span-3">
          {!selectedPb ? (
            <div className="bg-[#111827] border border-gray-800 rounded-2xl p-16 text-center">
              <BookOpen className="w-12 h-12 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">Select or create a phonebook to manage contacts</p>
              <button
                onClick={() => setPbModal('create')}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-colors text-sm"
              >
                <Plus className="w-4 h-4" /> New Phonebook
              </button>
            </div>
          ) : (
            <div className="bg-[#111827] border border-gray-800 rounded-2xl overflow-hidden">
              {/* Toolbar */}
              <div className="p-4 border-b border-gray-800">
                <div className="flex items-center justify-between gap-3">
                  <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
                    <input
                      type="text"
                      value={search}
                      onChange={e => setSearch(e.target.value)}
                      placeholder="Search contacts..."
                      className="w-full pl-9 pr-4 py-2 bg-[#1F2937] border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowImport(true)}
                      className="flex items-center gap-1.5 px-3 py-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20 rounded-xl transition-colors text-sm"
                    >
                      <Upload className="w-4 h-4" />
                      Import CSV
                    </button>
                    <button
                      onClick={() => { setEditContact(null); setContactModal('create') }}
                      className="flex items-center gap-1.5 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-colors text-sm font-medium"
                    >
                      <Plus className="w-4 h-4" />
                      Add Contact
                    </button>
                    <button onClick={loadContacts} className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl transition-colors" title="Refresh">
                      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Table */}
              <table className="w-full">
                <thead className="bg-[#0D1117] border-b border-gray-800">
                  <tr>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Phone</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/60">
                  {loading ? (
                    <tr><td colSpan={5} className="py-12 text-center text-gray-500 text-sm">Loading contacts...</td></tr>
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-16 text-center">
                        <User className="w-10 h-10 text-gray-700 mx-auto mb-3" />
                        <p className="text-gray-500 text-sm">{search ? 'No contacts match your search' : 'No contacts yet'}</p>
                        {!search && (
                          <button
                            onClick={() => { setEditContact(null); setContactModal('create') }}
                            className="mt-3 inline-flex items-center gap-1.5 text-sm text-blue-400 hover:underline"
                          >
                            <Plus className="w-3.5 h-3.5" /> Add first contact
                          </button>
                        )}
                      </td>
                    </tr>
                  ) : (
                    filtered.map(c => (
                      <tr key={c.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-gray-700 flex items-center justify-center flex-shrink-0 text-xs font-semibold text-gray-300">
                              {(c.first_name?.[0] ?? c.contact[1] ?? '?').toUpperCase()}
                            </div>
                            <span className="text-sm text-white">{[c.first_name, c.last_name].filter(Boolean).join(' ') || '—'}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3 text-sm text-gray-300 font-mono">{c.contact}</td>
                        <td className="px-5 py-3 text-sm text-gray-400">{c.email || '—'}</td>
                        <td className="px-5 py-3">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                            c.status === 1 ? 'bg-green-500/10 text-green-400' : 'bg-gray-500/10 text-gray-400'
                          }`}>
                            {c.status === 1 ? 'Active' : c.status === 2 ? 'Inactive' : 'Blocked'}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              title="Edit"
                              onClick={() => { setEditContact(c); setContactModal('edit') }}
                              className="p-1.5 text-gray-400 hover:bg-blue-500/10 hover:text-blue-400 rounded-lg transition-colors"
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                            <button
                              title="Delete"
                              onClick={() => setDeleteContact(c)}
                              className="p-1.5 text-gray-400 hover:bg-red-500/10 hover:text-red-400 rounded-lg transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>

              <div className="px-5 py-3 border-t border-gray-800 text-xs text-gray-600">
                {filtered.length} of {contacts.length} contacts
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
