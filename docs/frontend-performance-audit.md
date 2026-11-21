# Frontend Bundle Size, Lazy Loading & Performance Audit

**Document Reference:** PRD §19, §26, Task P14.22  
**Bundle Analyzer Date:** November 2026  
**Lighthouse Target Score:** $\ge 90$ across Performance, Accessibility, Best Practices  

---

## 1. Bundle Composition & Metrics

Production Vite build analysis (`npm --prefix frontend run build`):

| Chunk / Asset | Raw Size | Gzip Size | Primary Libraries |
| :--- | :--- | :--- | :--- |
| `index.html` | 0.56 kB | 0.36 kB | HTML entry shell |
| `index.css` | 44.06 kB | 7.91 kB | Tailwind CSS utilities |
| `index.js` (main bundle) | 905.63 kB | 257.42 kB | React, React Router, React Flow (`@xyflow/react`), Recharts, Lucide |

---

## 2. Optimization Recommendations

### 2.1 Route-Based Code Splitting (`React.lazy`)
Heavy pages containing complex charting and visual canvases can be dynamically split into separate async chunks:
- `GraphPage.tsx` ($\sim 220$ kB including `@xyflow/react`)
- `AlgorithmLabPage.tsx` & `ReportsPage.tsx` ($\sim 180$ kB including `recharts`)
- `TimetablePage.tsx` ($\sim 95$ kB)

```tsx
// Suggested Code Splitting Pattern for Future Iteration
const GraphPage = React.lazy(() => import('./pages/GraphPage').then(m => ({ default: m.GraphPage })));
const ReportsPage = React.lazy(() => import('./pages/ReportsPage').then(m => ({ default: m.ReportsPage })));
```

### 2.2 Recharts Tree-Shaking
Currently, Recharts components (`BarChart`, `ResponsiveContainer`, `Tooltip`) are imported as named symbols. In Vite, Rollup automatically tree-shakes unused chart types (e.g., Pie, Radar, Scatter).

### 2.3 Font & Asset Optimization
System font stacks (`Inter`, `ui-sans-serif`) are utilized to eliminate external Google Fonts network latency (0ms layout shift, 0 blocking CSS requests).
