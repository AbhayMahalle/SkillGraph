import React, { useState, useEffect } from 'react';
import { 
  Target, Sparkles, CheckCircle, AlertCircle, 
  XCircle, ChevronRight, RefreshCw, BarChart2 
} from 'lucide-react';

interface SkillGapViewProps {
  roleId: string;
  allRoles: any[];
  onSelectRole: (roleId: string) => void;
  onNavigateTab: (tab: string) => void;
}

export const SkillGapView: React.FC<SkillGapViewProps> = ({
  roleId,
  allRoles,
  onSelectRole,
  onNavigateTab
}) => {
  const [gapData, setGapData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!roleId) return;
    setLoading(true);
    fetch(`/api/analysis/skill-gap/${roleId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
      .then((res) => res.json())
      .then((data) => {
        setGapData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [roleId]);

  // SVG Radar Chart Math
  const renderRadarChart = (radarData: any[]) => {
    if (!radarData || radarData.length === 0) return null;

    const size = 320;
    const center = size / 2;
    const radius = 110;
    const totalAxes = radarData.length;
    const angleSlice = (Math.PI * 2) / totalAxes;

    // Generate concentric grid rings (25%, 50%, 75%, 100%)
    const rings = [0.25, 0.5, 0.75, 1.0];

    // Calculate required polygon points
    const reqPoints = radarData.map((d, i) => {
      const r = (d.required_level / 100) * radius;
      const x = center + r * Math.cos(angleSlice * i - Math.PI / 2);
      const y = center + r * Math.sin(angleSlice * i - Math.PI / 2);
      return `${x},${y}`;
    }).join(' ');

    // Calculate current polygon points
    const currPoints = radarData.map((d, i) => {
      const r = (Math.max(10, d.current_level) / 100) * radius;
      const x = center + r * Math.cos(angleSlice * i - Math.PI / 2);
      const y = center + r * Math.sin(angleSlice * i - Math.PI / 2);
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg width={size} height={size} style={{ overflow: 'visible' }}>
        {/* Concentric rings */}
        {rings.map((ring, idx) => (
          <circle
            key={idx}
            cx={center}
            cy={center}
            r={radius * ring}
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeDasharray={idx < 3 ? '3,3' : undefined}
          />
        ))}

        {/* Radial Axis Lines */}
        {radarData.map((_, i) => {
          const x = center + radius * Math.cos(angleSlice * i - Math.PI / 2);
          const y = center + radius * Math.sin(angleSlice * i - Math.PI / 2);
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={x}
              y2={y}
              stroke="rgba(255, 255, 255, 0.12)"
            />
          );
        })}

        {/* Required Level Polygon (Dashed Purple) */}
        <polygon
          points={reqPoints}
          fill="rgba(139, 92, 246, 0.12)"
          stroke="#8b5cf6"
          strokeWidth="1.5"
          strokeDasharray="4,4"
        />

        {/* Current Level Polygon (Solid Cyan/Emerald) */}
        <polygon
          points={currPoints}
          fill="rgba(6, 182, 212, 0.25)"
          stroke="#06b6d4"
          strokeWidth="2"
        />

        {/* Data points & labels */}
        {radarData.map((d, i) => {
          const r = (Math.max(10, d.current_level) / 100) * radius;
          const x = center + r * Math.cos(angleSlice * i - Math.PI / 2);
          const y = center + r * Math.sin(angleSlice * i - Math.PI / 2);

          // Label position
          const labelR = radius + 22;
          const lx = center + labelR * Math.cos(angleSlice * i - Math.PI / 2);
          const ly = center + labelR * Math.sin(angleSlice * i - Math.PI / 2);

          return (
            <g key={i}>
              <circle cx={x} cy={y} r="4" fill="#38bdf8" />
              <text
                x={lx}
                y={ly}
                fill={d.current_level >= 50 ? '#38bdf8' : 'var(--text-muted)'}
                fontSize="11"
                fontWeight="600"
                textAnchor="middle"
                dominantBaseline="central"
              >
                {d.skill}
              </text>
            </g>
          );
        })}
      </svg>
    );
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 20px', color: 'var(--text-muted)' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
        <p>Calculating algorithmic skill gap and ML readiness prediction...</p>
      </div>
    );
  }

  if (!gapData) return null;

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      {/* Header & Role Switcher */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 16,
        marginBottom: 28
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span className="badge badge-purple">Skill Gap Analysis</span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>Employee: {gapData.employee_name}</span>
          </div>
          <h2 style={{ fontSize: '2.1rem' }}>Target: {gapData.role_title}</h2>
        </div>

        {/* Dropdown to switch roles */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Analyze different role:</span>
          <select
            className="input-field"
            value={roleId}
            onChange={(e) => onSelectRole(e.target.value)}
            style={{ width: 220, cursor: 'pointer' }}
          >
            {allRoles.map((r) => (
              <option key={r.role_id} value={r.role_id} style={{ background: '#1e293b' }}>
                {r.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 20,
        marginBottom: 32
      }}>
        <div className="glass-panel" style={{ padding: 22 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
            Current Role Match
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
            <h3 style={{ fontSize: '2.2rem', color: 'var(--accent-cyan)' }}>{gapData.match_score}%</h3>
            <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>{gapData.mobility_status}</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
            Weighted across {gapData.matched_skills.length + gapData.missing_skills.length} role competencies
          </p>
        </div>

        <div className="glass-panel" style={{ padding: 22 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
            Coverage Percentage
          </span>
          <h3 style={{ fontSize: '2.2rem', color: '#818cf8', marginBottom: 4 }}>{gapData.coverage_percentage}%</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {gapData.matched_skills.length} of {gapData.matched_skills.length + gapData.missing_skills.length} required competencies possessed
          </p>
        </div>

        <div className="glass-panel" style={{ padding: 22 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
            Projected Post-Upskilling Readiness
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
            <h3 style={{ fontSize: '2.2rem', color: '#34d399' }}>
              {gapData.readiness_prediction?.projected_readiness_pct}%
            </h3>
            <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>
              +{gapData.readiness_prediction?.readiness_gain_pct}% Gain
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
            ML Model verdict: <strong>{gapData.readiness_prediction?.transition_verdict}</strong>
          </p>
        </div>
      </div>

      {/* Main Analysis Body: Radar Chart + Categorized Skills */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 26 }}>
        {/* Radar Chart Panel */}
        <div className="glass-panel" style={{ padding: 30, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 4, alignSelf: 'flex-start' }}>Competency Radar Analysis</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 24, alignSelf: 'flex-start' }}>
            Current capability (Cyan solid) vs Target benchmark requirement (Purple dashed)
          </p>

          <div style={{ padding: '20px 0' }}>
            {renderRadarChart(gapData.radar_data)}
          </div>

          <div style={{ display: 'flex', gap: 20, marginTop: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem' }}>
              <span style={{ width: 12, height: 12, borderRadius: 2, background: '#06b6d4', display: 'inline-block' }} />
              <span>Current Capability</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem' }}>
              <span style={{ width: 12, height: 12, borderRadius: 2, border: '1px dashed #8b5cf6', background: 'rgba(139, 92, 246, 0.2)', display: 'inline-block' }} />
              <span>Required Benchmark (85%)</span>
            </div>
          </div>
        </div>

        {/* Detailed Competency Breakdown */}
        <div className="glass-panel" style={{ padding: 30 }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 4 }}>Competency Breakdown</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 20 }}>
            Categorized by match strength and immediate upskilling priority
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Matched Skills */}
            <div>
              <span style={{ fontSize: '0.8rem', color: '#34d399', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                <CheckCircle size={16} /> Matched Competencies ({gapData.matched_skills.length})
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {gapData.matched_skills.map((sk: any) => (
                  <div
                    key={sk.skill_name}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      background: 'rgba(16, 185, 129, 0.06)',
                      border: '1px solid rgba(16, 185, 129, 0.2)',
                      padding: '8px 14px',
                      borderRadius: 'var(--radius-sm)'
                    }}
                  >
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{sk.skill_name}</span>
                    <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>{sk.status}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Missing Skills */}
            <div>
              <span style={{ fontSize: '0.8rem', color: '#fb7185', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                <XCircle size={16} /> Critical Skill Gaps ({gapData.missing_skills.length})
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {gapData.missing_skills.map((sk: any) => (
                  <div
                    key={sk.skill_name}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      background: 'rgba(244, 63, 94, 0.06)',
                      border: '1px solid rgba(244, 63, 94, 0.2)',
                      padding: '8px 14px',
                      borderRadius: 'var(--radius-sm)'
                    }}
                  >
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{sk.skill_name}</span>
                    <span className="badge badge-rose" style={{ fontSize: '0.65rem' }}>Missing</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Action to Learning Path */}
            <div style={{ marginTop: 10, paddingTop: 16, borderTop: '1px solid var(--border-subtle)' }}>
              <button
                onClick={() => onNavigateTab('learning-path')}
                className="btn btn-primary"
                style={{ width: '100%' }}
              >
                Generate Prerequisite Learning Roadmap <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
