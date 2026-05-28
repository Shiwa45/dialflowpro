import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, UserRole } from '@/types';
import api from '@/api/client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAgent: () => boolean;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      
      login: async (username, password) => {
        const { data } = await api.post('/accounts/users/login/', { username, password });
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);

        const tenantSchema =
          data.user.tenant &&
          typeof data.user.tenant === 'object' &&
          'schema_name' in data.user.tenant
            ? data.user.tenant.schema_name
            : null;

        if (tenantSchema) {
          localStorage.setItem('tenant_schema', tenantSchema);
        } else {
          localStorage.removeItem('tenant_schema');
        }

        set({ user: data.user, isAuthenticated: true });
      },
      
      logout: () => {
        localStorage.clear();
        set({ user: null, isAuthenticated: false });
      },
      
      isAgent: () => get().user?.role === UserRole.AGENT,
      isAdmin: () => {
        const role = get().user?.role;
        return role === UserRole.SUPERADMIN || role === UserRole.MANAGER;
      },
    }),
    {
      name: 'auth-storage', // name of the item in the storage (must be unique)
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
