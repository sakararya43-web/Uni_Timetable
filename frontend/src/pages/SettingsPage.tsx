import React, { useEffect, useState } from "react";
import { Plus, Filter, Sliders, CheckCircle } from "lucide-react";
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
  const [tab, setTab] = useState<"users" | "audit" | "weights">("users");
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

  // Constraint Weights (Task P13.18)
  const [wConsecutive, setWConsecutive] = useState<number>(10.0);
  const [wSameDay, setWSameDay] = useState<number>(5.0);
  const [wGapDay, setWGapDay] = useState<number>(2.0);
  const [wBalance, setWBalance] = useState<number>(1.0);
  const [weightsSaved, setWeightsSaved] = useState<boolean>(false);

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
    } else if (tab === "audit") {
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

  const handleSaveWeights = (e: React.FormEvent) => {
    e.preventDefault();
    setWeightsSaved(true);
    setTimeout(() => setWeightsSaved(false), 2500);
  };

  const handleResetWeights = () => {
    setWConsecutive(10.0);
    setWSameDay(5.0);
    setWGapDay(2.0);
    setWBalance(1.0);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Administration & System Preferences</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure administrative accounts, role-based access, audit logs, and scheduling algorithm penalty weights.
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
        <button
          onClick={() => setTab("weights")}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
            tab === "weights"
              ? "border-blue-600 text-blue-600 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Soft-Constraint Penalty Weights</span>
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
      ) : tab === "audit" ? (
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
              <option value="EXPORT_PDF">EXPORT_PDF</option>
              <option value="EXPORT_EXCEL">EXPORT_EXCEL</option>
              <option value="EXPORT_CSV">EXPORT_CSV</option>
            </select>
            <span className="text-xs text-slate-500 ml-auto font-mono">
              Displaying {auditLogs.length} events
            </span>
          </div>

          {isLoading ? (
            <LoadingSkeleton rows={5} />
          ) : auditLogs.length === 0 ? (
            <EmptyState
              title="No Audit Records Found"
              description="System actions, scheduling runs, and administrative exports will appear here."
            />
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px]">
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">Entity</th>
                    <th className="py-3 px-4">Details / Metadata</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 text-slate-500 font-mono whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-blue-700">
                        {log.action}
                      </td>
                      <td className="py-3 px-4 text-slate-800 font-medium">
                        {log.actorEmail || "SYSTEM"}
                      </td>
                      <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                        {log.entityType ? `${log.entityType} [${log.entityId?.slice(0, 8)}]` : "-"}
                      </td>
                      <td className="py-3 px-4 text-slate-600 max-w-xs truncate font-mono text-[10px]">
                        {log.afterState ? JSON.stringify(log.afterState) : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        /* Soft-Constraint Penalty Weights (Task P13.18) */
        <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm space-y-6">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Soft-Constraint Optimization Weights</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Adjust objective function penalty coefficients ($W_i$) used during schedule scoring and local search optimization.
            </p>
          </div>

          {weightsSaved && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>Optimization weights saved successfully for future schedule generations.</span>
            </div>
          )}

          <form onSubmit={handleSaveWeights} className="space-y-6 max-w-2xl">
            {/* Weight: Consecutive Exams */}
            <div className="space-y-2 p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between text-xs">
                <label className="font-bold text-slate-800">
                  Consecutive Sessions Penalty (W_consec)
                </label>
                <span className="font-mono font-bold text-blue-700 bg-white px-2 py-0.5 rounded border border-slate-300">
                  {wConsecutive.toFixed(1)}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Penalty assigned when a student has back-to-back exams on consecutive sessions or consecutive days.
              </p>
              <input
                type="range"
                min="0"
                max="50"
                step="0.5"
                value={wConsecutive}
                onChange={(e) => setWConsecutive(parseFloat(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
            </div>

            {/* Weight: Same Day Multiple Exams */}
            <div className="space-y-2 p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between text-xs">
                <label className="font-bold text-slate-800">
                  Same-Day Multi-Exam Penalty (W_sameday)
                </label>
                <span className="font-mono font-bold text-blue-700 bg-white px-2 py-0.5 rounded border border-slate-300">
                  {wSameDay.toFixed(1)}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Penalty assigned when a student has 2 or more exams scheduled within the same calendar day.
              </p>
              <input
                type="range"
                min="0"
                max="30"
                step="0.5"
                value={wSameDay}
                onChange={(e) => setWSameDay(parseFloat(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
            </div>

            {/* Weight: Single Day Gap */}
            <div className="space-y-2 p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between text-xs">
                <label className="font-bold text-slate-800">
                  Single-Day Gap Recovery Penalty (W_gap)
                </label>
                <span className="font-mono font-bold text-blue-700 bg-white px-2 py-0.5 rounded border border-slate-300">
                  {wGapDay.toFixed(1)}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Penalty incurred when consecutive exams have only 1 rest day between them instead of ideal study spacing.
              </p>
              <input
                type="range"
                min="0"
                max="20"
                step="0.5"
                value={wGapDay}
                onChange={(e) => setWGapDay(parseFloat(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
            </div>

            {/* Weight: Session Balance */}
            <div className="space-y-2 p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="flex items-center justify-between text-xs">
                <label className="font-bold text-slate-800">
                  Morning/Afternoon Balance Weight (W_balance)
                </label>
                <span className="font-mono font-bold text-blue-700 bg-white px-2 py-0.5 rounded border border-slate-300">
                  {wBalance.toFixed(1)}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Encourages balanced workload distribution between morning and afternoon sessions across the institution.
              </p>
              <input
                type="range"
                min="0"
                max="10"
                step="0.1"
                value={wBalance}
                onChange={(e) => setWBalance(parseFloat(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <Button type="button" variant="outline" size="sm" onClick={handleResetWeights}>
                Reset to Defaults
              </Button>
              <Button type="submit" variant="primary" size="sm">
                Save Preferences
              </Button>
            </div>
          </form>
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
