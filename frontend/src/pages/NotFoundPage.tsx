import React from "react";
import { Link } from "react-router-dom";

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
      <h1 className="text-4xl font-extrabold text-slate-800">404</h1>
      <p className="text-slate-500 mt-2">The requested page could not be found.</p>
      <Link to="/" className="mt-4 text-brand-600 hover:underline font-medium text-sm">
        Return to Dashboard
      </Link>
    </div>
  );
};
