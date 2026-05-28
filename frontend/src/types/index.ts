// User roles from Django backend
export enum UserRole {
  SUPERADMIN = 1,
  MANAGER = 2,
  AGENT = 3,
  CALENDAR_USER = 4,
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  tenant: number | { id: number; schema_name?: string; name?: string } | null;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export enum AgentStatus {
  LOGGED_OUT = 0,
  AVAILABLE = 1,
  ON_BREAK = 2,
}

export interface Agent {
  id: number;
  name: string;
  status: AgentStatus;
  state: string;
  calls_answered: number;
  talk_time: number;
}

export interface Queue {
  id: number;
  name: string;
  waiting_calls: number;
  active_agents: number;
}
