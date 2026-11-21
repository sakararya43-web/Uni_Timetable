import React from "react";

export const OverviewPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Overview Dashboard</h1>
          <p className="text-sm text-slate-500">Active examination scheduling cycle summary and metrics.</p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "Active Cycle", value: "Fall 2026 End-Term" },
          { label: "Exams Scheduled", value: "0" },
          { label: "Conflict Density", value: "0.0%" },
          { label: "Schedule Status", value: "Draft" },
        ].map((stat, i) => (
          <div key={i} className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{stat.label}</p>
            <p className="text-2xl font-semibold text-slate-800 mt-1">{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
