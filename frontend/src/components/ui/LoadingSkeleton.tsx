import React from "react";
import { clsx } from "clsx";

export interface LoadingSkeletonProps {
  className?: string;
  rows?: number;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ className, rows = 3 }) => {
  return (
    <div className="w-full space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, idx) => (
        <div
          key={idx}
          className={clsx("h-10 bg-slate-200 rounded-lg w-full", className)}
        />
      ))}
    </div>
  );
};
