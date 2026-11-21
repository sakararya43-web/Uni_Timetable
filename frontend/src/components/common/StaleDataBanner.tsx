import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "../ui/Button";

export interface StaleDataBannerProps {
  isStale: boolean;
  onRebuildGraph?: () => void;
  isRebuilding?: boolean;
}

export const StaleDataBanner: React.FC<StaleDataBannerProps> = ({
  isStale,
  onRebuildGraph,
  isRebuilding = false,
}) => {
  if (!isStale) return null;

  return (
    <div
      role="alert"
      className="flex items-center justify-between p-3 px-4 mb-4 bg-amber-50 border border-amber-300 rounded-lg text-amber-900"
    >
      <div className="flex items-center gap-2.5">
        <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
        <span className="text-xs font-medium">
          Academic or student enrollment data has been modified since the conflict graph was constructed. Timetables may be out of date.
        </span>
      </div>
      {onRebuildGraph && (
        <Button
          variant="outline"
          size="sm"
          className="border-amber-400 bg-amber-100 hover:bg-amber-200 text-amber-900 ml-4 flex-shrink-0"
          onClick={onRebuildGraph}
          isLoading={isRebuilding}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Rebuild Graph
        </Button>
      )}
    </div>
  );
};
