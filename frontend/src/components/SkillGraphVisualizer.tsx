import React, { useState, useEffect, useRef } from 'react';
import { 
  Network, Search, Download, Info, 
  RefreshCw, Filter, Layers 
} from 'lucide-react';

export const SkillGraphVisualizer: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [graphData, setGraphData] = useState<any>({ nodes: [], edges: [] });
  const [selectedType, setSelectedType] = useState<string>('');
  const [search, setSearch] = useState<string>('');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch graph data from backend
  const fetchGraph = (type = selectedType, q = search) => {
    setLoading(true);
    let url = '/api/graph/data?max_nodes=100';
    if (type) url += `&node_type=${type}`;
    if (q) url += `&search=${encodeURIComponent(q)}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        // Initialize 2D physics positions
        const width = 850;
        const height = 550;
        const nodes = (data.nodes || []).map((n: any, i: number) => {
          const angle = (i / data.nodes.length) * Math.PI * 2;
          const radius = 120 + (i % 3) * 60;
          return {
            ...n,
            x: width / 2 + Math.cos(angle) * radius + (Math.random() - 0.5) * 40,
            y: height / 2 + Math.sin(angle) * radius + (Math.random() - 0.5) * 40,
            vx: 0,
            vy: 0
          };
        });
        setGraphData({ summary: data.summary, nodes, edges: data.edges || [] });
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchGraph();
  }, [selectedType]);

  // Canvas drawing loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const nodeMap = new Map();
      graphData.nodes.forEach((n: any) => nodeMap.set(n.id, n));

      // 1. Draw Edges
      graphData.edges.forEach((edge: any) => {
        const source = nodeMap.get(edge.source);
        const target = nodeMap.get(edge.target);
        if (source && target) {
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.lineTo(target.x, target.y);
          ctx.strokeStyle = edge.color || 'rgba(255, 255, 255, 0.15)';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      });

      // 2. Draw Nodes
      graphData.nodes.forEach((n: any) => {
        const isSelected = selectedNode && selectedNode.id === n.id;
        const radius = isSelected ? 12 : (n.val ? n.val / 2 : 7);

        // Halo if selected
        if (isSelected) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, radius + 6, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = n.color || '#3b82f6';
        ctx.fill();

        // Label
        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.75)';
        ctx.textAlign = 'center';
        ctx.fillText(n.label || n.id, n.x, n.y + radius + 12);
      });

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [graphData, selectedNode]);

  // Click on Canvas to inspect node
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    let clicked = null;
    for (const n of graphData.nodes) {
      const dist = Math.hypot(n.x - x, n.y - y);
      if (dist < 15) {
        clicked = n;
        break;
      }
    }
    setSelectedNode(clicked);
  };

  const handleExportCypher = () => {
    window.open('/data/processed/canonical_roles.json', '_blank');
  };

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span className="badge badge-purple">Knowledge Graph</span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>Multi-Relational Topology</span>
          </div>
          <h2 style={{ fontSize: '2.1rem' }}>Interactive SkillGraph 2D Visualizer</h2>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: 14, background: 'rgba(255, 255, 255, 0.03)', padding: '8px 16px', borderRadius: 'var(--radius-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#3b82f6', display: 'inline-block' }} />
            <span>Employee</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
            <span>Skill</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#8b5cf6', display: 'inline-block' }} />
            <span>Role</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
            <span>Course</span>
          </div>
        </div>
      </div>

      {/* Control Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14, marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <input
            type="text"
            className="input-field"
            placeholder="Search nodes in graph..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchGraph(selectedType, search)}
            style={{ width: 240 }}
          />
          <button onClick={() => fetchGraph(selectedType, search)} className="btn btn-secondary" style={{ padding: '8px 12px' }}>
            <Search size={15} />
          </button>
        </div>

        {/* Filter type pills */}
        <div style={{ display: 'flex', gap: 6 }}>
          {['', 'employee', 'skill', 'role', 'course'].map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              style={{
                padding: '6px 12px',
                borderRadius: 9999,
                border: '1px solid',
                borderColor: selectedType === t ? 'var(--accent-purple)' : 'var(--border-subtle)',
                background: selectedType === t ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                color: selectedType === t ? '#c084fc' : 'var(--text-muted)',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {t === '' ? 'All Nodes' : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Canvas Area & Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '1fr 320px' : '1fr', gap: 20 }}>
        <div className="glass-panel" style={{ padding: 12, position: 'relative', overflow: 'hidden' }}>
          {loading && (
            <div style={{ position: 'absolute', top: 20, right: 20, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent-cyan)' }}>
              <RefreshCw size={16} className="animate-spin" /> Loading Graph...
            </div>
          )}

          <canvas
            ref={canvasRef}
            width={850}
            height={550}
            onClick={handleCanvasClick}
            style={{ width: '100%', height: 550, background: 'rgba(5, 8, 15, 0.6)', borderRadius: 'var(--radius-md)', cursor: 'crosshair' }}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-dim)', padding: '8px 4px 0' }}>
            <span>Click any node to inspect ontology relationships</span>
            <span>Total Nodes: {graphData.nodes?.length || 0} • Total Edges: {graphData.edges?.length || 0}</span>
          </div>
        </div>

        {/* Node Inspector Sidebar */}
        {selectedNode && (
          <div className="glass-panel" style={{ padding: 22 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
              <div>
                <span className="badge" style={{ background: selectedNode.color, color: '#fff', fontSize: '0.65rem' }}>
                  {selectedNode.type}
                </span>
                <h3 style={{ fontSize: '1.25rem', marginTop: 6 }}>{selectedNode.label}</h3>
              </div>
              <button onClick={() => setSelectedNode(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}>
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '0.85rem' }}>
              <div>
                <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.74rem' }}>ID</span>
                <strong>{selectedNode.id}</strong>
              </div>
              {selectedNode.category && (
                <div>
                  <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.74rem' }}>Category</span>
                  <span>{selectedNode.category}</span>
                </div>
              )}
              {selectedNode.department && (
                <div>
                  <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.74rem' }}>Department</span>
                  <span>{selectedNode.department}</span>
                </div>
              )}
              {selectedNode.level && (
                <div>
                  <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.74rem' }}>Level</span>
                  <span>{selectedNode.level}</span>
                </div>
              )}
            </div>

            <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border-subtle)' }}>
              <button
                onClick={() => fetchGraph(selectedType, selectedNode.label)}
                className="btn btn-primary"
                style={{ width: '100%', fontSize: '0.8rem' }}
              >
                Focus Neighborhood
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
