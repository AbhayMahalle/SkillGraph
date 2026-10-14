import React, { useState, useEffect } from 'react';
import { 
  Target, Sparkles, CheckCircle, AlertCircle, 
  XCircle, ChevronRight, RefreshCw, Info, ShieldCheck, 
  Check, Loader2, Award, FileText, Layers, TrendingUp
} from 'lucide-react';

interface SkillGapViewProps {
  roleId: string;
  allRoles: any[];
  onSelectRole: (roleId: string) => void;
  onNavigateTab: (tab: string) => void;
  targetRoleId?: string;
  currentUser?: any;
  onRefreshProfile?: () => void;
}

export const SkillGapView: React.FC<SkillGapViewProps> = ({
  roleId,
  allRoles,
  onSelectRole,
  onNavigateTab,
  targetRoleId,
  currentUser,
  onRefreshProfile
}) => {
  const [gapData, setGapData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [activeFilter, setActiveFilter] = useState<'all' | 'met' | 'partially_met' | 'missing'>('all');
  
  // Set target role state
  const [isSettingTarget, setIsSettingTarget] = useState(false);
  const [targetSuccessMsg, setTargetSuccessMsg] = useState('');
  const [targetErrorMsg, setTargetErrorMsg] = useState('');

  const fetchGapAnalysis = () => {
    if (!roleId) return;
    setLoading(true);
    setError(null);
    const token = localStorage.getItem('token');
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    fetch(`/api/analysis/skill-gap/${roleId}`, { headers })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Failed to load skill gap analysis (HTTP ${res.status})`);
        }
        return res.json();
      })
      .then((data) => {
        setGapData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Skill gap fetch error:', err);
        setError(err.message || 'Failed to retrieve skill gap analysis');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchGapAnalysis();
  }, [roleId]);

  // Handle setting current target role
  const handleSetTargetRole = async () => {
    if (!currentUser) {
      setTargetErrorMsg('Please sign in to persist this role as your career goal.');
      setTimeout(() => setTargetErrorMsg(''), 4000);
      return;
    }

    setIsSettingTarget(true);
    setTargetSuccessMsg('');
    setTargetErrorMsg('');

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/employees/target-role', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ target_role_id: roleId, role_id: roleId })
      });

      if (res.ok) {
        setTargetSuccessMsg(`Target role updated to "${gapData?.role_title || roleId}"!`);
        if (onRefreshProfile) {
          onRefreshProfile();
        }
        setTimeout(() => setTargetSuccessMsg(''), 4000);
      } else {
        const errData = await res.json().catch(() => ({}));
        setTargetErrorMsg(errData.detail || 'Could not update target role');
        setTimeout(() => setTargetErrorMsg(''), 5000);
      }
    } catch (err: any) {
      setTargetErrorMsg(err.message || 'Network error while updating target role');
      setTimeout(() => setTargetErrorMsg(''), 5000);
    } finally {
      setIsSettingTarget(false);
    }
  };

  // Helper for priority badge colors
  const getPriorityBadgeClass = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'critical':
        return 'badge-rose';
      case 'high':
        return 'badge-amber';
      case 'medium':
        return 'badge-cyan';
      default:
        return 'badge-purple';
    }
  };

  // Helper for status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Ready for Internal Transition':
        return <span className="badge badge-emerald"><CheckCircle size={12} /> {status}</span>;
      case 'Potential Internal Candidate':
        return <span className="badge badge-cyan"><Sparkles size={12} /> {status}</span>;
      default:
        return <span className="badge badge-amber"><AlertCircle size={12} /> {status}</span>;
    }
  };

  // SVG Radar Chart Math
  const renderRadarChart = (radarData: any[]) => {
    if (!radarData || radarData.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
          No competency radar metrics available for this role.
        </div>
      );
    }

    const size = 320;
    const center = size / 2;
    const radius = 105;
    const totalAxes = radarData.length;
    const angleSlice = (Math.PI * 2) / totalAxes;
    const rings = [0.25, 0.5, 0.75, 1.0];

    const reqPoints = radarData.map((d, i) => {
      const r = (d.required_level / 100) * radius;
      const x = center + r * Math.cos(angleSlice * i - Math.PI / 2);
      const y = center + r * Math.sin(angleSlice * i - Math.PI / 2);
      return `${x},${y}`;
    }).join(' ');

    const currPoints = radarData.map((d, i) => {
      const r = (Math.max(10, d.current_level) / 100) * radius;
      const x = center + r * Math.cos(angleSlice * i - Math.PI / 2);
      const y = center + r * Math.sin(angleSlice * i - Math.PI / 2);
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg width={size} height={size} style={{ overflow: 'visible' }}>
        {rings.map((ring, idx) => (
          <circle
            key={idx}
            cx={center}
            cy={center}
            r={radius * ring}
            fill="none"
            stroke="#e2e8f0"
            strokeDasharray={idx < 3 ? '3,3' : undefined}
          />
        ))}

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
              stroke="#e2e8f0"
            />
          );
        })}

        <polygon
          points={reqPoints}
          fill="rgba(124, 58, 237, 0.08)"
          stroke="#7c3aed"
          strokeWidth="1.5"
          strokeDasharray="4,4"
        />

        <polygon
          points={currPoints}
          fill="rgba(37, 99, 235, 0.15)"
          stroke="#2563eb"
          strokeWidth="2"
        />

        {radarData.map((d, i) => {
          const r = (Math.max(10, d.current_level) / 100) * radius;
          const x = center + r * Math.cos(angleSlice * i - Math.PI / 2);
          const y = center + r * Math.sin(angleSlice * i - Math.PI / 2);

          const labelR = radius + 22;
          const lx = center + labelR * Math.cos(angleSlice * i - Math.PI / 2);
          const ly = center + labelR * Math.sin(angleSlice * i - Math.PI / 2);

          return (
            <g key={i}>
              <circle cx={x} cy={y} r="4" fill="#2563eb" />
              <text
                x={lx}
                y={ly}
                fill={d.current_level >= 50 ? '#0f172a' : 'var(--text-secondary)'}
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
        <p style={{ fontSize: '1.1rem', fontWeight: 600 }}>Calculating Personalized Skill Gap & Explainable Match...</p>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginTop: 6 }}>
          Benchmarking personal competencies against canonical role requirements
        </p>
      </div>
    );
  }

  if (error || !gapData) {
    return (
      <div style={{ maxWidth: 700, margin: '80px auto', padding: 30 }} className="glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: '#fb7185', marginBottom: 12 }}>
          <AlertCircle size={24} />
          <h3 style={{ fontSize: '1.2rem' }}>Failed to Load Skill Gap Analysis</h3>
        </div>
        <p style={{ color: 'var(--text-muted)', marginBottom: 20 }}>{error || 'No gap analysis available for this role.'}</p>
        <button onClick={fetchGapAnalysis} className="btn btn-primary">
          <RefreshCw size={16} /> Retry Analysis
        </button>
      </div>
    );
  }

  const isCurrentTarget = (targetRoleId === roleId);
  const metSkills = gapData.met_skills || [];
  const partiallyMetSkills = gapData.partially_met_skills || [];
  const missingSkills = gapData.missing_skills || [];
  const explanation = gapData.explanation || {};
  const summary = gapData.summary || {
    met_count: metSkills.length,
    partially_met_count: partiallyMetSkills.length,
    missing_count: missingSkills.length,
    total_required: metSkills.length + partiallyMetSkills.length + missingSkills.length
  };

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      {/* Toast Feedback */}
      {targetSuccessMsg && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.2)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          color: '#34d399',
          padding: '12px 20px',
          borderRadius: 'var(--radius-md)',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontSize: '0.9rem'
        }}>
          <CheckCircle size={18} />
          <span>{targetSuccessMsg}</span>
        </div>
      )}

      {targetErrorMsg && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.2)',
          border: '1px solid rgba(244, 63, 94, 0.4)',
          color: '#fb7185',
          padding: '12px 20px',
          borderRadius: 'var(--radius-md)',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontSize: '0.9rem'
        }}>
          <AlertCircle size={18} />
          <span>{targetErrorMsg}</span>
        </div>
      )}

      {/* Header & Role Switcher */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: 20,
        marginBottom: 28,
        paddingBottom: 20,
        borderBottom: '1px solid var(--border-subtle)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
            <span className="badge badge-purple">Phase 4 Skill Gap Intelligence</span>
            {isCurrentTarget ? (
              <span className="badge badge-emerald" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <Check size={12} /> Active Career Target
              </span>
            ) : (
              <span className="badge badge-cyan">Exploratory Target</span>
            )}
            <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
              Profile: <strong>{gapData.employee_name || 'Authenticated User'}</strong>
            </span>
          </div>

          <h2 style={{ fontSize: '2.2rem', marginBottom: 6 }}>
            {gapData.role_title}
          </h2>

          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap', fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            <span><strong>Department:</strong> {gapData.department}</span>
            <span>•</span>
            <span><strong>Experience Required:</strong> {gapData.experience_years} years</span>
            <span>•</span>
            <span><strong>Salary Benchmark:</strong> {gapData.salary_range || 'Competitive'}</span>
          </div>
        </div>

        {/* Action Controls & Role Switcher */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {!isCurrentTarget ? (
              <button
                onClick={handleSetTargetRole}
                disabled={isSettingTarget}
                className="btn btn-primary"
                style={{ fontSize: '0.85rem', padding: '8px 16px' }}
                title="Persist this role as your active career target"
              >
                {isSettingTarget ? <Loader2 size={16} className="animate-spin" /> : <Target size={16} />}
                Set as Career Target
              </button>
            ) : (
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#34d399',
                fontSize: '0.85rem',
                fontWeight: 600
              }}>
                <CheckCircle size={16} /> Current Target Role
              </div>
            )}

            <button
              onClick={() => onNavigateTab('roles')}
              className="btn btn-secondary"
              style={{ fontSize: '0.85rem', padding: '8px 16px' }}
            >
              Browse Catalog
            </button>
          </div>

          {/* Quick Dropdown Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Switch Role:</span>
            <select
              className="input-field"
              value={roleId}
              onChange={(e) => onSelectRole(e.target.value)}
              style={{ width: 220, fontSize: '0.85rem', padding: '6px 10px', cursor: 'pointer' }}
            >
              {allRoles.map((r) => (
                <option key={r.role_id} value={r.role_id}>
                  {r.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 18,
        marginBottom: 28
      }}>
        {/* Match Score Card */}
        <div className="saas-card" style={{ padding: 22, position: 'relative' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
              Personalized Match Score
            </span>
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              style={{
                background: showExplanation ? '#e0e7ff' : '#f8fafc',
                border: '1px solid ' + (showExplanation ? '#c7d2fe' : 'var(--border-subtle)'),
                borderRadius: 'var(--radius-sm)',
                padding: '4px 8px',
                color: showExplanation ? '#3730a3' : 'var(--text-secondary)',
                fontSize: '0.75rem',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                cursor: 'pointer'
              }}
              title="Click to view explainability breakdown and formula"
            >
              <Info size={13} /> {showExplanation ? 'Hide Math' : 'Explain'}
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginTop: 8 }}>
            <h3 style={{ fontSize: '2.4rem', fontWeight: 700, color: '#0284c7' }}>{gapData.match_score}%</h3>
            {getStatusBadge(gapData.mobility_status)}
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 6 }}>
            Deterministic scoring across {summary.total_required} required competencies & experience delta
          </p>
        </div>

        {/* Competency Coverage Card */}
        <div className="saas-card" style={{ padding: 22 }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
            Competency Coverage
          </span>
          <h3 style={{ fontSize: '2.4rem', fontWeight: 700, color: '#4f46e5', marginBottom: 4 }}>
            {gapData.coverage_percentage}%
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <strong>{metSkills.length + partiallyMetSkills.length}</strong> of <strong>{summary.total_required}</strong> competencies demonstrated
          </p>
        </div>

        {/* Met Competencies */}
        <div className="saas-card" style={{ padding: 22 }}>
          <span style={{ fontSize: '0.78rem', color: '#059669', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
            Fully Met Competencies
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
            <h3 style={{ fontSize: '2.4rem', fontWeight: 700, color: '#059669' }}>{summary.met_count}</h3>
            <span className="badge badge-emerald" style={{ fontSize: '0.72rem' }}>
              Satisfies Benchmark
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
            Demonstrated proficiency meets or exceeds required benchmark
          </p>
        </div>

        {/* Gaps Breakdown (Partially Met + Missing) */}
        <div className="saas-card" style={{ padding: 22 }}>
          <span style={{ fontSize: '0.78rem', color: '#e11d48', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
            Upskilling Gaps
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
            <h3 style={{ fontSize: '2.4rem', fontWeight: 700, color: '#e11d48' }}>
              {summary.partially_met_count + summary.missing_count}
            </h3>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <div><strong style={{ color: '#d97706' }}>{summary.partially_met_count}</strong> Partial</div>
              <div><strong style={{ color: '#e11d48' }}>{summary.missing_count}</strong> Missing</div>
            </div>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
            Identified areas requiring targeted development or verification
          </p>
        </div>
      </div>

      {/* Explainable Calculation Accordion / Panel */}
      {showExplanation && (
        <div style={{
          padding: 24,
          marginBottom: 28,
          borderRadius: 'var(--radius-lg)',
          border: '1px solid #c7d2fe',
          background: '#f8fafc',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Sparkles size={18} color="#4f46e5" />
              <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#312e81' }}>Explainable Match Calculation Methodology</h4>
            </div>
            <button
              onClick={() => setShowExplanation(false)}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem', padding: '2px 6px' }}
            >
              ✕
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 18, fontSize: '0.86rem' }}>
            <div style={{ background: '#ffffff', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>Mathematical Formula</div>
              <code style={{ display: 'block', background: '#f1f5f9', padding: 8, borderRadius: 6, color: '#0369a1', fontSize: '0.78rem', marginBottom: 8, border: '1px solid #e2e8f0' }}>
                {explanation.scoring_formula || 'Composite = min(100, Coverage × ExpFactor × 100)'}
              </code>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: 1.5 }}>
                Weights proficiency depth, canonical importance weights, and experience delta without arbitrary rankings.
              </p>
            </div>

            <div style={{ background: '#ffffff', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>Experience Alignment</div>
              <ul style={{ color: 'var(--text-muted)', paddingLeft: 18, fontSize: '0.82rem', lineHeight: 1.6 }}>
                <li>Employee Experience: <strong>{gapData.experience_years ? (gapData.experience_years + (explanation.experience_delta || 0)) : 'N/A'} yrs</strong></li>
                <li>Role Required: <strong>{gapData.experience_years} yrs</strong> (Delta: {explanation.experience_delta >= 0 ? `+${explanation.experience_delta}` : explanation.experience_delta} yrs)</li>
                <li>Alignment Multiplier: <strong>{explanation.experience_factor}x</strong></li>
                <li>Catalog Benchmark Level: <strong>{explanation.role_experience_benchmark}</strong></li>
              </ul>
            </div>

            <div style={{ background: '#ffffff', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>Provenance & Evidence Guardrail</div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: 1.5 }}>
                {explanation.unverified_penalty_applied ? (
                  <span style={{ color: '#b45309' }}>
                    <ShieldCheck size={14} style={{ display: 'inline', marginRight: 4 }} />
                    {explanation.unverified_skills_count} candidate resume mention(s) detected. As required by policy, unverified claims are discounted by 1 level and 15% to avoid treating resume text as verified expertise.
                  </span>
                ) : (
                  <span style={{ color: '#047857' }}>
                    <CheckCircle size={14} style={{ display: 'inline', marginRight: 4 }} />
                    All demonstrated competencies have verified or self-reported evidence. No unverified discount was necessary.
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Analysis Body: Categorized Skills + Radar Chart */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: 26 }}>
        {/* Left Column: Categorized Competencies */}
        <div className="saas-card" style={{ padding: 28 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18, flexWrap: 'wrap', gap: 10 }}>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 4 }}>Skill-Gap Breakdown</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Classified by requirement fulfillment, proficiency gap, and upskilling priority
              </p>
            </div>

            {/* Filter Pills */}
            <div style={{ display: 'flex', gap: 6, background: '#f1f5f9', padding: 4, borderRadius: 'var(--radius-md)' }}>
              <button
                onClick={() => setActiveFilter('all')}
                style={{
                  background: activeFilter === 'all' ? '#ffffff' : 'transparent',
                  border: 'none',
                  color: activeFilter === 'all' ? 'var(--text-main)' : 'var(--text-muted)',
                  borderRadius: 6,
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  fontWeight: activeFilter === 'all' ? 600 : 500,
                  boxShadow: activeFilter === 'all' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
                  cursor: 'pointer'
                }}
              >
                All ({summary.total_required})
              </button>
              <button
                onClick={() => setActiveFilter('met')}
                style={{
                  background: activeFilter === 'met' ? '#ffffff' : 'transparent',
                  border: 'none',
                  color: activeFilter === 'met' ? '#047857' : 'var(--text-muted)',
                  borderRadius: 6,
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  fontWeight: activeFilter === 'met' ? 600 : 500,
                  boxShadow: activeFilter === 'met' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
                  cursor: 'pointer'
                }}
              >
                Met ({summary.met_count})
              </button>
              <button
                onClick={() => setActiveFilter('partially_met')}
                style={{
                  background: activeFilter === 'partially_met' ? '#ffffff' : 'transparent',
                  border: 'none',
                  color: activeFilter === 'partially_met' ? '#b45309' : 'var(--text-muted)',
                  borderRadius: 6,
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  fontWeight: activeFilter === 'partially_met' ? 600 : 500,
                  boxShadow: activeFilter === 'partially_met' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
                  cursor: 'pointer'
                }}
              >
                Partial ({summary.partially_met_count})
              </button>
              <button
                onClick={() => setActiveFilter('missing')}
                style={{
                  background: activeFilter === 'missing' ? '#ffffff' : 'transparent',
                  border: 'none',
                  color: activeFilter === 'missing' ? '#e11d48' : 'var(--text-muted)',
                  borderRadius: 6,
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  fontWeight: activeFilter === 'missing' ? 600 : 500,
                  boxShadow: activeFilter === 'missing' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
                  cursor: 'pointer'
                }}
              >
                Missing ({summary.missing_count})
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Met Skills List */}
            {(activeFilter === 'all' || activeFilter === 'met') && metSkills.length > 0 && (
              <div>
                <span style={{ fontSize: '0.8rem', color: '#059669', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                  <CheckCircle size={15} /> Met Competencies ({metSkills.length})
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {metSkills.map((sk: any) => (
                    <div
                      key={sk.skill_name}
                      style={{
                        background: '#ffffff',
                        border: '1px solid #d1fae5',
                        borderLeft: '4px solid #10b981',
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-md)',
                        boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-main)' }}>{sk.skill_name}</span>
                          <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>Met</span>
                        </div>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <span style={{ fontSize: '0.75rem', color: '#047857', background: '#ecfdf5', padding: '2px 8px', borderRadius: 4, fontWeight: 500, border: '1px solid #a7f3d0' }}>
                            Demonstrated: {sk.current_proficiency} (L{sk.demonstrated_level})
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', background: '#f1f5f9', padding: '2px 8px', borderRadius: 4, border: '1px solid #e2e8f0' }}>
                            Req: {sk.required_proficiency}
                          </span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6, fontSize: '0.78rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>{sk.reason}</span>
                        {sk.source && (
                          <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>
                            {sk.verified ? '✓ Verified Evidence' : `Source: ${sk.source}`}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Partially Met Skills List */}
            {(activeFilter === 'all' || activeFilter === 'partially_met') && partiallyMetSkills.length > 0 && (
              <div style={{ marginTop: activeFilter === 'all' ? 8 : 0 }}>
                <span style={{ fontSize: '0.8rem', color: '#d97706', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                  <AlertCircle size={15} /> Partially Met Competencies ({partiallyMetSkills.length})
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {partiallyMetSkills.map((sk: any) => (
                    <div
                      key={sk.skill_name}
                      style={{
                        background: '#ffffff',
                        border: '1px solid #fef3c7',
                        borderLeft: '4px solid #f59e0b',
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-md)',
                        boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-main)' }}>{sk.skill_name}</span>
                          <span className={`badge ${getPriorityBadgeClass(sk.priority)}`} style={{ fontSize: '0.65rem' }}>
                            {sk.priority} Priority Gap
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <span style={{ fontSize: '0.75rem', color: '#b45309', background: '#fffbeb', padding: '2px 8px', borderRadius: 4, fontWeight: 500, border: '1px solid #fde68a' }}>
                            Current: {sk.current_proficiency} (L{sk.demonstrated_level})
                          </span>
                          <span style={{ fontSize: '0.75rem', color: '#4338ca', background: '#eef2ff', padding: '2px 8px', borderRadius: 4, border: '1px solid #c7d2fe' }}>
                            Req: {sk.required_proficiency}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: '#be123c', background: '#fff1f2', padding: '2px 8px', borderRadius: 4, fontWeight: 500, border: '1px solid #fecdd3' }}>
                            Gap: -{sk.gap} Level
                          </span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6, fontSize: '0.78rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>{sk.reason}</span>
                        {sk.source && (
                          <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>
                            {sk.verified ? '✓ Verified' : `Unverified (${sk.source})`}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Missing Skills List */}
            {(activeFilter === 'all' || activeFilter === 'missing') && missingSkills.length > 0 && (
              <div style={{ marginTop: activeFilter === 'all' ? 8 : 0 }}>
                <span style={{ fontSize: '0.8rem', color: '#e11d48', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                  <XCircle size={15} /> Missing Competencies ({missingSkills.length})
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {missingSkills.map((sk: any) => (
                    <div
                      key={sk.skill_name}
                      style={{
                        background: '#ffffff',
                        border: '1px solid #ffe4e6',
                        borderLeft: '4px solid #f43f5e',
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-md)',
                        boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-main)' }}>{sk.skill_name}</span>
                          <span className={`badge ${getPriorityBadgeClass(sk.priority)}`} style={{ fontSize: '0.65rem' }}>
                            {sk.priority} Priority Gap
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: '#f8fafc', padding: '2px 8px', borderRadius: 4, border: '1px solid #e2e8f0' }}>
                            No Recorded Evidence
                          </span>
                          <span style={{ fontSize: '0.75rem', color: '#4338ca', background: '#eef2ff', padding: '2px 8px', borderRadius: 4, border: '1px solid #c7d2fe' }}>
                            Target: {sk.required_proficiency}
                          </span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6, fontSize: '0.78rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>{sk.reason}</span>
                        <span style={{ color: 'var(--text-dim)' }}>Weight: {sk.importance_weight || sk.weight || 1.0}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state for filtered skills */}
            {((activeFilter === 'met' && metSkills.length === 0) ||
              (activeFilter === 'partially_met' && partiallyMetSkills.length === 0) ||
              (activeFilter === 'missing' && missingSkills.length === 0)) && (
              <div style={{ textAlign: 'center', padding: '30px 20px', color: 'var(--text-dim)' }}>
                No competencies found matching the "{activeFilter}" filter.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Competency Radar & Action Hub */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Radar Chart Panel */}
          <div className="saas-card" style={{ padding: 28, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 4, alignSelf: 'flex-start' }}>Competency Radar Analysis</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 20, alignSelf: 'flex-start' }}>
              Current capability (Cyan solid) vs Target benchmark requirement (Purple dashed)
            </p>

            <div style={{ padding: '16px 0' }}>
              {renderRadarChart(gapData.radar_data)}
            </div>

            <div style={{ display: 'flex', gap: 20, marginTop: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                <span style={{ width: 12, height: 12, borderRadius: 2, background: '#0284c7', display: 'inline-block' }} />
                <span>Current Capability</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                <span style={{ width: 12, height: 12, borderRadius: 2, border: '1px dashed #7c3aed', background: 'rgba(124, 58, 237, 0.15)', display: 'inline-block' }} />
                <span>Required Benchmark</span>
              </div>
            </div>
          </div>

          {/* Action Card: Next Steps */}
          <div className="saas-card" style={{ padding: 24 }}>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Award size={18} color="#4f46e5" /> Career Development Actions
            </h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>
              Bridge your high-priority competency gaps with personalized course paths and career comparisons.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                onClick={() => onNavigateTab('learning-path')}
                className="btn btn-primary"
                style={{ width: '100%', justifyContent: 'space-between' }}
              >
                <span>View Learning Roadmap</span>
                <ChevronRight size={16} />
              </button>

              <button
                onClick={() => onNavigateTab('roles')}
                className="btn btn-secondary"
                style={{ width: '100%', justifyContent: 'space-between' }}
              >
                <span>Compare Target Roles</span>
                <Layers size={16} />
              </button>

              <button
                onClick={() => onNavigateTab('profile')}
                className="btn btn-secondary"
                style={{ width: '100%', justifyContent: 'space-between' }}
              >
                <span>Update Personal Skills & Evidence</span>
                <FileText size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
