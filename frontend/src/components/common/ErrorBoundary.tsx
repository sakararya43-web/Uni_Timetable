import { Component, ErrorInfo, ReactNode } from "react";
import { AlertOctagon, RotateCcw } from "lucide-react";
import { Button } from "../ui/Button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught frontend error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center bg-white rounded-xl border border-rose-200 shadow-sm m-4">
          <div className="p-3 bg-rose-100 text-rose-600 rounded-full mb-3">
            <AlertOctagon className="w-8 h-8" />
          </div>
          <h2 className="text-base font-semibold text-slate-900">Application Error Encountered</h2>
          <p className="text-xs text-slate-500 max-w-md mt-1 mb-4">
            {this.state.error?.message || "An unexpected rendering error occurred in this view."}
          </p>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<RotateCcw className="w-4 h-4" />}
            onClick={() => window.location.reload()}
          >
            Reload Application
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
