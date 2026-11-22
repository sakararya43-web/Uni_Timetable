import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Network,
  RefreshCw,
  Download,
  Filter,
  Search,
  Info,
  Sparkles,
  RotateCcw,
  CheckCircle2,
  Palette,
} from "lucide-react";
import { api } from "../services/api";
import { SchedulingCycle, unwrapCycles } from "../types/api";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { EmptyState } from "../components/ui/EmptyState";

interface GraphSummary {
  vertexCount: number;
  edgeCount: number;
  density: number;
  avgDegree: number;
  maxDegree: number;
  chromaticLowerBound: number;
  isolatedVertices: number;
}

interface RawGraphData {
  nodes: Array<{
    id: string;
    subjectCode: string;
    subjectName: string;
    departmentCode?: string;
    degree: number;
    color?: number;
  }>;
  edges: Array<{
    source: string;
    target: string;
    weight: number;
  }>;
}

export interface LightColorTheme {
  id: string;
  name: string;
  bg: string;
  border: string;
  borderActive: string;
  accent: string;
  badgeBg: string;
  badgeText: string;
  minimap: string;
}

export const LIGHT_COLOR_PALETTE: LightColorTheme[] = [
  {
    id: "sky",
    name: "Sky Blue",
    bg: "#f0f7ff",
    border: "#bae6fd",
    borderActive: "#0284c7",
    accent: "#0284c7",
    badgeBg: "#e0f2fe",
    badgeText: "#0369a1",
    minimap: "#38bdf8",
  },
  {
    id: "emerald",
    name: "Mint Emerald",
    bg: "#f0fdf4",
    border: "#bbf7d0",
    borderActive: "#16a34a",
    accent: "#16a34a",
    badgeBg: "#dcfce7",
    badgeText: "#15803d",
    minimap: "#4ade80",
  },
  {
    id: "purple",
    name: "Soft Violet",
    bg: "#faf5ff",
    border: "#e9d5ff",
    borderActive: "#9333ea",
    accent: "#9333ea",
    badgeBg: "#f3e8ff",
    badgeText: "#7e22ce",
    minimap: "#c084fc",
  },
  {
    id: "amber",
    name: "Warm Amber",
    bg: "#fffbeb",
    border: "#fde68a",
    borderActive: "#d97706",
    accent: "#d97706",
    badgeBg: "#fef3c7",
    badgeText: "#b45309",
    minimap: "#fbbf24",
  },
  {
    id: "rose",
    name: "Pastel Rose",
    bg: "#fff1f2",
    border: "#fecdd3",
    borderActive: "#e11d48",
    accent: "#e11d48",
    badgeBg: "#ffe4e6",
    badgeText: "#be123c",
    minimap: "#fb7185",
  },
  {
    id: "teal",
    name: "Seafoam Teal",
    bg: "#f0fdfa",
    border: "#99f6e4",
    borderActive: "#0d9488",
    accent: "#0d9488",
    badgeBg: "#ccfbf1",
    badgeText: "#0f766e",
    minimap: "#2dd4bf",
  },
  {
    id: "indigo",
    name: "Lavender Indigo",
    bg: "#eef2ff",
    border: "#c7d2fe",
    borderActive: "#4f46e5",
    accent: "#4f46e5",
    badgeBg: "#e0e7ff",
    badgeText: "#3730a3",
    minimap: "#818cf8",
  },
  {
    id: "peach",
    name: "Soft Peach",
    bg: "#fff7ed",
    border: "#fed7aa",
    borderActive: "#ea580c",
    accent: "#ea580c",
    badgeBg: "#ffedd5",
    badgeText: "#c2410c",
    minimap: "#fb923c",
  },
  {
    id: "cyan",
    name: "Ice Cyan",
    bg: "#ecfeff",
    border: "#a5f3fc",
    borderActive: "#0891b2",
    accent: "#0891b2",
    badgeBg: "#cffafe",
    badgeText: "#0e7490",
    minimap: "#22d3ee",
  },
  {
    id: "lime",
    name: "Spring Lime",
    bg: "#f7fee7",
    border: "#d9f99d",
    borderActive: "#65a30d",
    accent: "#65a30d",
    badgeBg: "#ecfccb",
    badgeText: "#4d7c0f",
    minimap: "#a3e635",
  },
  {
    id: "fuchsia",
    name: "Orchid Fuchsia",
    bg: "#fdf4ff",
    border: "#f5d0fe",
    borderActive: "#c026d3",
    accent: "#c026d3",
    badgeBg: "#fae8ff",
    badgeText: "#a21caf",
    minimap: "#e879f9",
  },
  {
    id: "slate",
    name: "Cool Slate",
    bg: "#f8fafc",
    border: "#cbd5e1",
    borderActive: "#475569",
    accent: "#475569",
    badgeBg: "#f1f5f9",
    badgeText: "#334155",
    minimap: "#94a3b8",
  },
];

function computeGreedyColoring(
  nodes: Array<{ id: string; degree: number }>,
  edges: Array<{ source: string; target: string }>
): Map<string, number> {
  const adj = new Map<string, Set<string>>();
  for (const n of nodes) {
    adj.set(n.id, new Set());
  }
  for (const e of edges) {
    adj.get(e.source)?.add(e.target);
    adj.get(e.target)?.add(e.source);
  }

  // Welsh-Powell: sort by degree descending
  const sorted = [...nodes].sort((a, b) => b.degree - a.degree);
  const colors = new Map<string, number>();

  for (const node of sorted) {
    const neighbors = adj.get(node.id) || new Set();
    const neighborColors = new Set<number>();
    for (const nbrId of neighbors) {
      const c = colors.get(nbrId);
      if (c !== undefined) {
        neighborColors.add(c);
      }
    }
    let c = 1;
    while (neighborColors.has(c)) {
      c++;
    }
    colors.set(node.id, c);
  }

  return colors;
}

function getDepartmentIndex(code: string, totalColors: number): number {
  let hash = 0;
  for (let i = 0; i < code.length; i++) {
    hash = (hash << 5) - hash + code.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash) % totalColors;
}

export const GraphPage: React.FC = () => {
  const navigate = useNavigate();
  const [cycles, setCycles] = useState<SchedulingCycle[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState<string>("");
  const [summary, setSummary] = useState<GraphSummary | null>(null);
  const [rawGraph, setRawGraph] = useState<RawGraphData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRebuilding, setIsRebuilding] = useState<boolean>(false);
  const [isGraphCreated, setIsGraphCreated] = useState<boolean>(false);
  const [builtCycles, setBuiltCycles] = useState<Record<string, boolean>>({});
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [minDegreeFilter, setMinDegreeFilter] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [colorMode, setColorMode] = useState<"chromatic" | "department">("chromatic");

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Load cycles
  useEffect(() => {
    setIsLoading(true);
    api.get<SchedulingCycle[] | { items: SchedulingCycle[] }>("/api/v1/cycles")
      .then((data) => {
        const list = unwrapCycles(data);
        setCycles(list);
        if (list.length > 0) {
          setSelectedCycleId(list[0].id);
        } else {
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error("Error loading cycles:", err);
        setIsLoading(false);
      });
  }, []);

  // Load graph data for selected cycle
  const fetchGraphData = async (cycleId: string) => {
    if (!cycleId) return;
    setIsLoading(true);
    try {
      const [sumData, graphData] = await Promise.all([
        api.get<GraphSummary>(`/api/v1/cycles/${cycleId}/graph/summary`),
        api.get<RawGraphData>(`/api/v1/cycles/${cycleId}/graph/data`),
      ]);
      setSummary(sumData);
      setRawGraph(graphData);
      setIsGraphCreated(true);
    } catch (err) {
      console.error("Failed to load graph data:", err);
      setIsGraphCreated(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCycleId) {
      if (builtCycles[selectedCycleId]) {
        fetchGraphData(selectedCycleId);
      } else {
        setRawGraph(null);
        setSummary(null);
        setNodes([]);
        setEdges([]);
        setIsGraphCreated(false);
        setIsLoading(false);
      }
    }
  }, [selectedCycleId, builtCycles]);

  // Compute chromatic coloring (Welsh-Powell) if node.color is not pre-assigned
  const chromaticColors = useMemo(() => {
    if (!rawGraph || !rawGraph.nodes || rawGraph.nodes.length === 0) {
      return new Map<string, number>();
    }
    const hasPreassigned = rawGraph.nodes.some(
      (n) => typeof n.color === "number" && n.color > 0
    );
    if (hasPreassigned) {
      const map = new Map<string, number>();
      for (const n of rawGraph.nodes) {
        if (typeof n.color === "number" && n.color > 0) {
          map.set(n.id, n.color);
        }
      }
      return map;
    }
    return computeGreedyColoring(rawGraph.nodes, rawGraph.edges || []);
  }, [rawGraph]);

  // Function to resolve light color theme for any node
  const getNodeTheme = (node: RawGraphData["nodes"][0]): { theme: LightColorTheme; label: string } => {
    if (colorMode === "chromatic") {
      const colorNum = chromaticColors.get(node.id) || node.color || 1;
      const paletteIndex = (colorNum - 1) % LIGHT_COLOR_PALETTE.length;
      return {
        theme: LIGHT_COLOR_PALETTE[paletteIndex],
        label: `Slot ${colorNum}`,
      };
    } else {
      const dept = node.departmentCode || "GEN";
      const paletteIndex = getDepartmentIndex(dept, LIGHT_COLOR_PALETTE.length);
      return {
        theme: LIGHT_COLOR_PALETTE[paletteIndex],
        label: dept,
      };
    }
  };

  // Derive legend items
  const legendItems = useMemo(() => {
    if (!rawGraph || !rawGraph.nodes || rawGraph.nodes.length === 0) return [];

    if (colorMode === "chromatic") {
      const colorGroups = new Map<number, number>();
      for (const n of rawGraph.nodes) {
        const c = chromaticColors.get(n.id) || n.color || 1;
        colorGroups.set(c, (colorGroups.get(c) || 0) + 1);
      }
      return Array.from(colorGroups.entries())
        .sort((a, b) => a[0] - b[0])
        .slice(0, 10)
        .map(([colorNum, count]) => {
          const theme = LIGHT_COLOR_PALETTE[(colorNum - 1) % LIGHT_COLOR_PALETTE.length];
          return {
            key: `slot-${colorNum}`,
            label: `Slot ${colorNum}`,
            count,
            theme,
          };
        });
    } else {
      const deptGroups = new Map<string, number>();
      for (const n of rawGraph.nodes) {
        const d = n.departmentCode || "GEN";
        deptGroups.set(d, (deptGroups.get(d) || 0) + 1);
      }
      return Array.from(deptGroups.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([dept, count]) => {
          const theme = LIGHT_COLOR_PALETTE[getDepartmentIndex(dept, LIGHT_COLOR_PALETTE.length)];
          return {
            key: `dept-${dept}`,
            label: dept,
            count,
            theme,
          };
        });
    }
  }, [rawGraph, colorMode, chromaticColors]);

  // Compute Layout (Circular / Force Positioning with Light Colors)
  useEffect(() => {
    if (!rawGraph || !rawGraph.nodes) return;

    const filteredNodes = rawGraph.nodes.filter(
      (n) =>
        n.degree >= minDegreeFilter &&
        (searchTerm === "" ||
          n.subjectCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
          n.subjectName.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));
    const total = filteredNodes.length;
    const radius = Math.max(300, total * 35);
    const centerX = 500;
    const centerY = 400;

    const flowNodes: Node[] = filteredNodes.map((n, idx) => {
      const angle = (idx / (total || 1)) * 2 * Math.PI;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      const isSelected = selectedNodeId === n.id;
      const { theme, label } = getNodeTheme(n);
      const slotNum = chromaticColors.get(n.id) || n.color || 1;

      return {
        id: n.id,
        position: { x, y },
        data: {
          label: (
            <div
              style={{
                backgroundColor: theme.bg,
                borderColor: isSelected ? theme.borderActive : theme.border,
                borderWidth: isSelected ? "2px" : "1px",
              }}
              className={`p-2.5 rounded-lg shadow-sm text-xs transition-all relative overflow-hidden select-none cursor-pointer ${
                isSelected
                  ? "ring-4 ring-blue-300/60 shadow-md scale-105 z-20"
                  : "hover:shadow-md hover:scale-[1.02]"
              }`}
            >
              {/* Left accent colored stripe */}
              <div
                className="absolute top-0 left-0 bottom-0 w-1"
                style={{ backgroundColor: theme.accent }}
              />

              <div className="pl-1.5 space-y-1">
                <div className="flex items-center justify-between gap-1.5 font-bold">
                  <div className="flex items-center gap-1.5">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: theme.accent }}
                    />
                    <span className="text-slate-900 font-bold tracking-tight">
                      {n.subjectCode}
                    </span>
                  </div>
                  <span
                    className="text-[10px] font-semibold px-1.5 py-0.5 rounded border"
                    style={{
                      backgroundColor: theme.badgeBg,
                      color: theme.badgeText,
                      borderColor: theme.border,
                    }}
                  >
                    deg {n.degree}
                  </span>
                </div>

                <div className="text-[11px] font-medium text-slate-700 truncate max-w-[130px]">
                  {n.subjectName}
                </div>

                <div className="flex items-center justify-between pt-0.5 text-[9px] text-slate-500 font-medium">
                  <span>{n.departmentCode || "GEN"}</span>
                  <span
                    className="px-1 py-0.2 rounded font-semibold"
                    style={{
                      backgroundColor: theme.badgeBg,
                      color: theme.badgeText,
                    }}
                  >
                    {colorMode === "chromatic" ? `Slot ${slotNum}` : label}
                  </span>
                </div>
              </div>
            </div>
          ),
        },
      };
    });

    const flowEdges: Edge[] = (rawGraph.edges || [])
      .filter((e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target))
      .map((e, idx) => {
        const isIncident = selectedNodeId === e.source || selectedNodeId === e.target;
        return {
          id: `e-${idx}-${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
          animated: isIncident,
          style: {
            stroke: isIncident
              ? "#2563eb"
              : selectedNodeId
              ? "#e2e8f0"
              : "#cbd5e1",
            strokeWidth: isIncident
              ? Math.min(Math.max(e.weight, 2), 5)
              : Math.min(Math.max(e.weight / 2, 1), 3),
            opacity: selectedNodeId && !isIncident ? 0.35 : 1,
          },
        };
      });

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [rawGraph, minDegreeFilter, searchTerm, selectedNodeId, colorMode, chromaticColors]);

  const handleCreateOrRebuild = async () => {
    if (!selectedCycleId) return;
    setIsRebuilding(true);
    try {
      await api.post(`/api/v1/cycles/${selectedCycleId}/graph/build`);
      const [sumData, graphData] = await Promise.all([
        api.get<GraphSummary>(`/api/v1/cycles/${selectedCycleId}/graph/summary`),
        api.get<RawGraphData>(`/api/v1/cycles/${selectedCycleId}/graph/data`),
      ]);
      setSummary(sumData);
      setRawGraph(graphData);
      setIsGraphCreated(true);
      setBuiltCycles((prev) => ({ ...prev, [selectedCycleId]: true }));
      const cycleName = cycles.find((c) => c.id === selectedCycleId)?.name || selectedCycleId;
      setSuccessMsg(
        `Conflict graph successfully created for "${cycleName}"! Computed ${sumData.vertexCount} examination nodes and ${sumData.edgeCount} clash edges with clash-free light coloring.`
      );
      setTimeout(() => setSuccessMsg(null), 6000);
    } catch (err) {
      console.error("Error creating/rebuilding graph:", err);
    } finally {
      setIsRebuilding(false);
    }
  };

  const handleResetGraph = () => {
    if (!selectedCycleId) return;
    setBuiltCycles((prev) => ({ ...prev, [selectedCycleId]: false }));
    setIsGraphCreated(false);
    setRawGraph(null);
    setSummary(null);
    setNodes([]);
    setEdges([]);
    setSelectedNodeId(null);
    setSuccessMsg("Graph canvas reset. Click 'Create Conflict Graph' to generate the topology.");
    setTimeout(() => setSuccessMsg(null), 4000);
  };

  const handleExport = (format: "json" | "csv") => {
    if (!rawGraph) return;
    if (format === "json") {
      const blob = new Blob([JSON.stringify(rawGraph, null, 2)], {
        type: "application/json;charset=utf-8;",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `conflict-graph-${selectedCycleId || "cycle"}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } else {
      const rows = [
        "Source Exam,Target Exam,Shared Student Count",
        ...rawGraph.edges.map(
          (e) => `"${e.source}","${e.target}",${e.weight}`
        ),
      ].join("\r\n");
      const blob = new Blob([rows], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `conflict-graph-edges-${selectedCycleId || "cycle"}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  const selectedNodeInfo = useMemo(() => {
    if (!selectedNodeId || !rawGraph) return null;
    return rawGraph.nodes.find((n) => n.id === selectedNodeId) || null;
  }, [selectedNodeId, rawGraph]);

  const selectedNodeTheme = useMemo(() => {
    if (!selectedNodeInfo) return null;
    return getNodeTheme(selectedNodeInfo).theme;
  }, [selectedNodeInfo, colorMode, chromaticColors]);

  const conflictingNeighbors = useMemo(() => {
    if (!selectedNodeId || !rawGraph || !rawGraph.edges) return [];
    const neighbors: Array<{ id: string; subjectCode: string; subjectName: string; weight: number }> = [];

    for (const e of rawGraph.edges) {
      let nbrId: string | null = null;
      if (e.source === selectedNodeId) {
        nbrId = e.target;
      } else if (e.target === selectedNodeId) {
        nbrId = e.source;
      }

      if (nbrId) {
        const nbrNode = rawGraph.nodes.find((n) => n.id === nbrId);
        if (nbrNode) {
          neighbors.push({
            id: nbrNode.id,
            subjectCode: nbrNode.subjectCode,
            subjectName: nbrNode.subjectName,
            weight: e.weight,
          });
        }
      }
    }

    return neighbors.sort((a, b) => b.weight - a.weight);
  }, [selectedNodeId, rawGraph]);

  const activeCycle = cycles.find((c) => c.id === selectedCycleId);

  return (
    <div className="space-y-4">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div className="flex items-center gap-3">
          <Network className="w-5 h-5 text-blue-600 flex-shrink-0" />
          <div>
            <h1 className="text-base font-bold text-slate-900">Conflict Graph Visualizer G=(V,E)</h1>
            <p className="text-xs text-slate-500">
              Interactive conflict graph visualization and examination clash topology G=(V,E).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedCycleId}
            onChange={(e) => setSelectedCycleId(e.target.value)}
            disabled={cycles.length === 0}
            className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {cycles.length === 0 ? (
              <option value="">No cycles available</option>
            ) : (
              cycles.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))
            )}
          </select>

          {isGraphCreated ? (
            <>
              <Button
                variant="primary"
                size="sm"
                isLoading={isRebuilding}
                disabled={!selectedCycleId}
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                onClick={handleCreateOrRebuild}
              >
                Rebuild Graph
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!selectedCycleId || isRebuilding}
                leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                onClick={handleResetGraph}
              >
                Reset
              </Button>
            </>
          ) : (
            <Button
              variant="primary"
              size="sm"
              isLoading={isRebuilding}
              disabled={!selectedCycleId}
              leftIcon={<Sparkles className="w-3.5 h-3.5" />}
              onClick={handleCreateOrRebuild}
            >
              Create Conflict Graph
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            disabled={!selectedCycleId || !rawGraph || !isGraphCreated}
            leftIcon={<Download className="w-3.5 h-3.5" />}
            onClick={() => handleExport("csv")}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between shadow-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="font-medium">{successMsg}</span>
          </div>
          <button
            onClick={() => setSuccessMsg(null)}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-4"
          >
            &times;
          </button>
        </div>
      )}

      {/* Filter, Color Mode and Metrics Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Search, Degree Slider & Color Mode */}
        <div className="md:col-span-3 flex flex-col sm:flex-row items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl shadow-sm flex-wrap">
          <div className="relative flex-1 min-w-[180px] w-full sm:w-auto">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search vertex by course code (e.g. CS101)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Color Mode Selector */}
          <div className="flex items-center gap-1.5">
            <Palette className="w-4 h-4 text-blue-600 flex-shrink-0" />
            <label htmlFor="color-mode-select" className="text-xs text-slate-600 font-medium whitespace-nowrap">
              Colors:
            </label>
            <select
              id="color-mode-select"
              value={colorMode}
              onChange={(e) => setColorMode(e.target.value as "chromatic" | "department")}
              className="px-2.5 py-1 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-700"
            >
              <option value="chromatic">Chromatic Slot (Timeslot)</option>
              <option value="department">Academic Department</option>
            </select>
          </div>

          {/* Degree Filter Slider */}
          <div className="flex items-center gap-2 w-full sm:w-56">
            <Filter className="w-4 h-4 text-slate-400" />
            <label htmlFor="deg-slider" className="text-xs text-slate-600 whitespace-nowrap">
              Min Deg: <span className="font-bold">{minDegreeFilter}</span>
            </label>
            <input
              id="deg-slider"
              type="range"
              min={0}
              max={summary?.maxDegree || 20}
              value={minDegreeFilter}
              onChange={(e) => setMinDegreeFilter(Number(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>
        </div>

        {/* Compact Metrics Badge */}
        <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-sm flex items-center justify-around text-center text-xs">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">|V| Vertices</span>
            <span className="font-bold text-slate-900">{summary?.vertexCount || 0}</span>
          </div>
          <div className="h-6 w-px bg-slate-200" />
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">|E| Edges</span>
            <span className="font-bold text-slate-900">{summary?.edgeCount || 0}</span>
          </div>
          <div className="h-6 w-px bg-slate-200" />
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Density</span>
            <span className="font-bold text-slate-900">{((summary?.density || 0) * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Dynamic Color Legend */}
      {isGraphCreated && rawGraph && legendItems.length > 0 && (
        <div className="p-2.5 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 font-bold text-slate-700 mr-1 text-[11px]">
            <Palette className="w-3.5 h-3.5 text-blue-600" />
            <span>Legend ({colorMode === "chromatic" ? "Time Slots / Colors" : "Departments"}):</span>
          </div>
          {legendItems.map((item) => (
            <div
              key={item.key}
              className="flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[11px] font-medium transition-transform hover:scale-105"
              style={{
                backgroundColor: item.theme.bg,
                borderColor: item.theme.border,
                color: item.theme.badgeText,
              }}
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: item.theme.accent }}
              />
              <span className="font-semibold">{item.label}</span>
              <span className="opacity-75 text-[10px]">({item.count})</span>
            </div>
          ))}
          <span className="text-[10px] text-slate-400 italic ml-auto hidden sm:inline">
            Light pastel shading preserves complete text legibility
          </span>
        </div>
      )}

      {/* Main Graph Canvas Area */}
      <div className="relative w-full h-[620px] bg-slate-100 border border-slate-200 rounded-xl shadow-inner overflow-hidden flex items-center justify-center">
        {isLoading ? (
          <div className="p-8 w-full">
            <LoadingSkeleton rows={8} />
          </div>
        ) : cycles.length === 0 ? (
          <div className="p-8 max-w-md w-full">
            <EmptyState
              icon={<Network className="w-8 h-8 text-blue-600" />}
              title="No Scheduling Cycle Found"
              description="There are currently no examination cycles in the database. Please load the demonstration dataset in Settings or create a cycle to explore the conflict graph."
              actionLabel="Load Demo Data in Settings"
              onAction={() => navigate("/settings")}
            />
          </div>
        ) : (!isGraphCreated || !rawGraph || nodes.length === 0) ? (
          <div className="p-8 max-w-lg w-full text-center bg-white/95 backdrop-blur-sm border border-slate-200 rounded-2xl shadow-lg space-y-4 animate-fadeIn">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-inner">
              <Network className="w-8 h-8" />
            </div>
            <div>
              <span className="inline-block px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-amber-50 text-amber-700 border border-amber-200 mb-2">
                GRAPH NOT GENERATED YET
              </span>
              <h2 className="text-base font-bold text-slate-900">
                Create Conflict Graph G = (V, E)
              </h2>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                The conflict graph has not been generated for <strong className="text-slate-800">{activeCycle?.name || "this cycle"}</strong>. Create the conflict graph to compute student enrollment clash edges and enable automated clash-free exam scheduling with colored time slots.
              </p>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-left text-xs space-y-1.5 text-slate-600">
              <div className="flex justify-between">
                <span className="text-slate-500">Selected Cycle:</span>
                <span className="font-semibold text-slate-800 truncate max-w-[200px]">{activeCycle?.name || selectedCycleId}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Exam Period:</span>
                <span className="font-mono text-slate-700">{activeCycle?.startDate} &rarr; {activeCycle?.endDate}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Clash Computation:</span>
                <span className="font-semibold text-blue-600">Pairwise student enrollment overlap</span>
              </div>
            </div>
            <Button
              variant="primary"
              size="md"
              isLoading={isRebuilding}
              leftIcon={<Sparkles className="w-4 h-4" />}
              onClick={handleCreateOrRebuild}
              className="w-full justify-center shadow-sm"
            >
              {isRebuilding ? "Computing Conflict Topology..." : "Create Conflict Graph"}
            </Button>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            onPaneClick={() => setSelectedNodeId(null)}
            fitView
          >
            <Background color="#cbd5e1" gap={20} />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const raw = rawGraph?.nodes.find((n) => n.id === node.id);
                if (!raw) return "#94a3b8";
                return getNodeTheme(raw).theme.minimap;
              }}
              maskColor="rgba(241, 245, 249, 0.7)"
            />
          </ReactFlow>
        )}

        {/* Node Inspector Drawer */}
        {selectedNodeInfo && (
          <div className="absolute top-4 right-4 z-10 w-80 p-4 bg-white/95 backdrop-blur-md border border-slate-300 rounded-xl shadow-xl text-xs space-y-3 max-h-[560px] overflow-y-auto animate-fadeIn">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: selectedNodeTheme?.accent || "#2563eb" }}
                />
                <span className="font-bold text-slate-900 text-sm">{selectedNodeInfo.subjectCode}</span>
              </div>
              <Badge variant="info">Degree: {selectedNodeInfo.degree}</Badge>
            </div>

            <p className="text-slate-800 font-semibold text-xs leading-snug">{selectedNodeInfo.subjectName}</p>

            <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
              <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-400 block text-[9px] uppercase font-bold">Department</span>
                <span className="font-bold text-slate-800">{selectedNodeInfo.departmentCode || "General"}</span>
              </div>
              <div
                className="p-2 rounded-lg border"
                style={{
                  backgroundColor: selectedNodeTheme?.bg,
                  borderColor: selectedNodeTheme?.border,
                }}
              >
                <span className="text-slate-500 block text-[9px] uppercase font-bold">Chromatic Slot</span>
                <span className="font-bold" style={{ color: selectedNodeTheme?.badgeText }}>
                  Slot {chromaticColors.get(selectedNodeInfo.id) || selectedNodeInfo.color || 1}
                </span>
              </div>
            </div>

            {/* List of Conflicting Neighbor Exams */}
            <div className="pt-2">
              <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 mb-1.5">
                <span>Conflicting Exams ({conflictingNeighbors.length})</span>
                <span className="text-[10px] text-slate-400 font-normal">Shared Students</span>
              </div>
              {conflictingNeighbors.length === 0 ? (
                <p className="text-slate-400 text-[10px] italic">No conflicting courses (isolated node).</p>
              ) : (
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {conflictingNeighbors.map((nbr) => (
                    <div
                      key={nbr.id}
                      onClick={() => setSelectedNodeId(nbr.id)}
                      className="flex items-center justify-between p-1.5 rounded-lg border border-slate-200 hover:border-blue-400 hover:bg-blue-50/50 cursor-pointer transition-colors text-[11px]"
                    >
                      <div className="truncate max-w-[170px]">
                        <span className="font-bold text-slate-800">{nbr.subjectCode}</span>{" "}
                        <span className="text-slate-500 text-[10px] truncate">{nbr.subjectName}</span>
                      </div>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                        {nbr.weight} stu
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-1 border-t border-slate-200 text-slate-400 text-[10px] flex items-center gap-1">
              <Info className="w-3 h-3 flex-shrink-0" />
              <span>Adjacent nodes have different colors (zero exam clash).</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
