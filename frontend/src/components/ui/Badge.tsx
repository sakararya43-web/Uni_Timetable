import React from "react";
import { clsx } from "clsx";

export type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "neutral";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  icon?: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-slate-100 text-slate-800 border-slate-200",
  success: "bg-emerald-50 text-emerald-800 border-emerald-200",
  warning: "bg-amber-50 text-amber-800 border-amber-200",
  danger: "bg-rose-50 text-rose-800 border-rose-200",
  info: "bg-blue-50 text-blue-800 border-blue-200",
  neutral: "bg-gray-100 text-gray-700 border-gray-200",
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  className,
  icon,
}) => {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",
        variantStyles[variant],
        className
      )}
    >
      {icon && <span className="inline-block w-3.5 h-3.5">{icon}</span>}
      {children}
    </span>
  );
};
