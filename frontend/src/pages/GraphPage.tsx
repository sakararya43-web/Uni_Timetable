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
import { Network, RefreshCw, Download, Filter, Search, Info, Sparkles, RotateCcw, CheckCircle2 } from "lucide-react";
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

  // Compute Layout (Circular / Force Positioning)
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

      return {
        id: n.id,
        position: { x, y },
        data: {
          label: (
            <div
              className={`p-2.5 rounded-lg border shadow-sm text-xs transition-all ${
                isSelected
                  ? "bg-blue-600 text-white border-blue-700 ring-4 ring-blue-200"
                  : "bg-white text-slate-800 border-slate-300 hover:border-blue-400"
              }`}
            >
              <div className="flex items-center justify-between gap-1 font-bold">
                <span>{n.subjectCode}</span>
                <span className="text-[10px] px-1.5 py-0.2 bg-slate-100 text-slate-700 rounded border">
                  deg {n.degree}
                </span>
              </div>
              <div className="text-[10px] opacity-80 truncate max-w-[120px] mt-0.5">{n.subjectName}</div>
            </div>
          ),
        },
      };
    });

    const flowEdges: Edge[] = (rawGraph.edges || [])
      .filter((e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target))
      .map((e, idx) => ({
        id: `e-${idx}-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        animated: selectedNodeId === e.source || selectedNodeId === e.target,
        style: {
          stroke: selectedNodeId === e.source || selectedNodeId === e.target ? "#2563eb" : "#cbd5e1",
          strokeWidth: Math.min(e.weight, 4),
        },
      }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [rawGraph, minDegreeFilter, searchTerm, selectedNodeId]);

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
      setSuccessMsg(`Conflict graph successfully created for "${cycleName}"! Computed ${sumData.vertexCount} examination nodes and ${sumData.edgeCount} clash edges.`);
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

      {/* Filter and Metrics Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Search & Degree Slider */}
        <div className="md:col-span-3 flex flex-col sm:flex-row items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search vertex by course code (e.g. CS101)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-64">
            <Filter className="w-4 h-4 text-slate-400" />
            <label htmlFor="deg-slider" className="text-xs text-slate-600 whitespace-nowrap">
              Min Degree: <span className="font-bold">{minDegreeFilter}</span>
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
                The conflict graph has not been generated for <strong className="text-slate-800">{activeCycle?.name || "this cycle"}</strong>. Create the conflict graph to compute student enrollment clash edges and enable automated clash-free exam scheduling.
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
            <MiniMap nodeColor="#94a3b8" />
          </ReactFlow>
        )}

        {/* Node Inspector Drawer */}
        {selectedNodeInfo && (
          <div className="absolute top-4 right-4 z-10 w-72 p-4 bg-white/95 backdrop-blur-sm border border-slate-300 rounded-xl shadow-lg text-xs space-y-2">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="font-bold text-slate-900 text-sm">{selectedNodeInfo.subjectCode}</span>
              <Badge variant="info">Degree: {selectedNodeInfo.degree}</Badge>
            </div>
            <p className="text-slate-600 font-medium">{selectedNodeInfo.subjectName}</p>
            <div className="text-slate-500 text-[11px] space-y-1 pt-1">
              <p>Department: {selectedNodeInfo.departmentCode || "General"}</p>
              <p className="flex items-center gap-1 text-slate-400 text-[10px]">
                <Info className="w-3 h-3" />
                Privacy preserved: Student identities omitted.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
