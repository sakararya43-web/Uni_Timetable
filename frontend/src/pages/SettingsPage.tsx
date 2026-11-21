import React, { useEffect, useState } from "react";
import { Plus, Filter } from "lucide-react";
import { api } from "../services/api";
import { UserProfile, AuditLogItem, Role } from "../types/api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Dialog } from "../components/ui/Dialog";
import { Badge, BadgeVariant } from "../components/ui/Badge";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

const roleVariants: Record<string, BadgeVariant> = {
  admin: "danger",
  coordinator: "warning",
  faculty: "info",
  student: "neutral",
};

export const SettingsPage: React.FC = () => {
  const [tab, setTab] = useState<"users" | "audit">("users");
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [totalLogs, setTotalLogs] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isCreateUserOpen, setIsCreateUserOpen] = useState<boolean>(false);

  // User form state
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserRole, setNewUserRole] = useState<Role>("coordinator");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Audit filter
  const [auditActionFilter, setAuditActionFilter] = useState("");

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const data = await api.get<UserProfile[]>("/api/v1/users");
      setUsers(data);
    } catch (err) {
      console.error("Failed to load users:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    setIsLoading(true);
    try {
      const url = auditActionFilter
        ? `/api/v1/audit-logs?action=${auditActionFilter}&limit=50`
        : "/api/v1/audit-logs?limit=50";
      const data = await api.get<{ total: number; items: AuditLogItem[] }>(url);
      setAuditLogs(data.items);
      setTotalLogs(data.total);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (tab === "users") {
      fetchUsers();
    } else {
      fetchAuditLogs();
    }
  }, [tab, auditActionFilter]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      await api.post("/api/v1/users", {
        email: newUserEmail,
        password: newUserPassword,
        role: newUserRole,
      });
      setIsCreateUserOpen(false);
      setNewUserEmail("");
      setNewUserPassword("");
      fetchUsers();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || "Failed to create user.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Administration & System Audit</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure administrative accounts, role-based access, and immutable audit logs.
          </p>
        </div>
        {tab === "users" && (
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setIsCreateUserOpen(true)}
          >
            Create User Account
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setTab("users")}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition-all ${
            tab === "users"
              ? "border-blue-600 text-blue-600 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Users & Access Control ({users.length})
        </button>
        <button
          onClick={() => setTab("audit")}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition-all ${
            tab === "audit"
              ? "border-blue-600 text-blue-600 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Immutable Audit Trail ({totalLogs})
        </button>
      </div>

      {tab === "users" ? (
        isLoading ? (
          <LoadingSkeleton rows={5} />
        ) : (
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                  <th className="py-3 px-4">User Email</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Department Scope</th>
                  <th className="py-3 px-4">Account Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">{u.email}</td>
                    <td className="py-3.5 px-4">
                      <Badge variant={roleVariants[u.role] || "default"}>
                        {u.role.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {u.departmentName || "All Departments"}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded-full ${
                          u.isActive
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-slate-100 text-slate-500 border border-slate-200"
                        }`}
                      >
                        {u.isActive ? "ACTIVE" : "INACTIVE"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        /* Audit Trail */
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl shadow-sm">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={auditActionFilter}
              onChange={(e) => setAuditActionFilter(e.target.value)}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Audit Actions</option>
              <option value="SCHEDULE_PUBLISH">SCHEDULE_PUBLISH</option>
              <option value="SCHEDULE_RUN">SCHEDULE_RUN</option>
              <option value="SCHEDULE_SAVE">SCHEDULE_SAVE</option>
              <option value="SCHEDULE_EDIT">SCHEDULE_EDIT</option>
              <option value="EXAM_LOCK">EXAM_LOCK</option>
              <option value="EXAM_UNLOCK">EXAM_UNLOCK</option>
              <option value="GRAPH_BUILD">GRAPH_BUILD</option>
              <option value="EXPORT">EXPORT</option>
            </select>
          </div>

          {isLoading ? (
            <LoadingSkeleton rows={6} />
          ) : auditLogs.length === 0 ? (
            <EmptyState
              title="No Audit Records"
              description="No security or scheduling events match the selected filter."
            />
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Entity</th>
                    <th className="py-3 px-4">Details / Diff</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700 font-mono text-[11px]">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-4 text-slate-500 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-2.5 px-4 font-sans font-semibold text-slate-900">
                        {log.actorEmail || "system"}
                      </td>
                      <td className="py-2.5 px-4 font-sans">
                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-300">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-slate-600">
                        {log.entityType} ({log.entityId ? log.entityId.slice(0, 8) : "N/A"})
                      </td>
                      <td className="py-2.5 px-4 text-slate-500 max-w-xs truncate">
                        {log.afterState ? JSON.stringify(log.afterState) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Create User Dialog */}
      <Dialog
        isOpen={isCreateUserOpen}
        onClose={() => setIsCreateUserOpen(false)}
        title="Create System User"
        description="Register an account with role-based permissions."
        maxWidth="md"
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
          {errorMsg && (
            <p className="p-2.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg">
              {errorMsg}
            </p>
          )}

          <Input
            label="User Email"
            type="email"
            placeholder="e.g. coordinator@univ.edu"
            value={newUserEmail}
            onChange={(e) => setNewUserEmail(e.target.value)}
            required
          />

          <Input
            label="Initial Password"
            type="password"
            placeholder="Minimum 8 characters"
            value={newUserPassword}
            onChange={(e) => setNewUserPassword(e.target.value)}
            required
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">System Role</label>
            <select
              value={newUserRole}
              onChange={(e) => setNewUserRole(e.target.value as Role)}
              className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="admin">Administrator (Full Access)</option>
              <option value="coordinator">Department Coordinator (Scoped)</option>
              <option value="faculty">Faculty Member (Read-only)</option>
              <option value="student">Student (Timetable Only)</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" size="md" onClick={() => setIsCreateUserOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="md" type="submit" isLoading={isSubmitting}>
              Create User
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
};
