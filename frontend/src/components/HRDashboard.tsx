import React, { useState, useEffect } from 'react';
import { 
  Users, TrendingUp, AlertTriangle, UserCheck, 
  Search, ArrowRight, ShieldAlert, Sparkles, RefreshCw 
} from 'lucide-react';

export const HRDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [talentPool, setTalentPool] = useState<any[]>([]);
  const [selectedRoleCandidates, setSelectedRoleCandidates] = useState<any>(null);
  const [activeRoleModal, setActiveRoleModal] = useState<string | null>(null);
  const [searchEmp, setSearchEmp] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/hr/analytics', { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } }).then(r => r.json()),
      fetch('/api/hr/talent-pool', { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } }).then(r => r.json())
    ])
      .then(([aData, tData]) => {
        setAnalytics(aData);
        setTalentPool(tData);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const handleOpenCandidateFinder = (roleId: string, roleTitle: string) => {
    setActiveRoleModal(roleTitle);
    fetch(`/api/hr/candidates-for-role/${roleId}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
      .then(res => res.json())
      .then(data => setSelectedRoleCandidates(data))
      .catch(err => console.error(err));
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 20px', color: 'var(--text-muted)' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
        <p>Loading enterprise workforce analytics & talent pipeline...</p>
      </div>
    );
  }

  const summary = analytics?.workforce_summary || {};
  const roleDemands = analytics?.role_demands || [];
  const shortages = analytics?.top_skill_shortages || [];

  const filteredTalent = talentPool.filter(e => 
    e.name.toLowerCase().includes(searchEmp.toLowerCase()) ||
    e.current_role.toLowerCase().includes(searchEmp.toLowerCase()) ||
    e.department.toLowerCase().includes(searchEmp.toLowerCase()) ||
    e.skills.some((s: string) => s.toLowerCase().includes(searchEmp.toLowerCase()))
  );

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span className="badge badge-amber">Executive View</span>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>People Analytics & Strategic Talent Planning</span>
        </div>
        <h2 style={{ fontSize: '2.1rem' }}>Workforce Planning & Internal Mobility Dashboard</h2>
      </div>

      {/* Top Level KPIs */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: 18,
        marginBottom: 32
      }}>
        <div className="glass-panel" style={{ padding: 20 }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Total Headcount</span>
          <h3 style={{ fontSize: '2rem', color: '#fff', margin: '4px 0' }}>{summary.total_headcount || 142}</h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Across 5 business units</p>
        </div>

        <div className="glass-panel" style={{ padding: 20 }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Open Positions</span>
          <h3 style={{ fontSize: '2rem', color: 'var(--accent-cyan)', margin: '4px 0' }}>{summary.open_positions || 28}</h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Q4 Targeted Hires: {summary.projected_q4_hires || 35}</p>
        </div>

        <div className="glass-panel" style={{ padding: 20 }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Internal Mobility Target</span>
          <h3 style={{ fontSize: '2rem', color: '#34d399', margin: '4px 0' }}>{summary.internal_mobility_target_pct || 65}%</h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Target internal fill rate</p>
        </div>

        <div className="glass-panel" style={{ padding: 20 }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Active in Upskilling</span>
          <h3 style={{ fontSize: '2rem', color: '#fbbf24', margin: '4px 0' }}>{summary.upskilling_active_employees || 46}</h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Enrolled in learning paths</p>
        </div>
      </div>

      {/* Grid: Future Demand vs Critical Skill Shortages */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: 26, marginBottom: 36 }}>
        {/* Future Role Requisitions */}
        <div className="glass-panel" style={{ padding: 26 }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 6 }}>Priority Future Headcount Gaps</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 18 }}>
            Roles with high urgency requiring immediate internal feeder matching
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {roleDemands.map((rd: any) => (
              <div
                key={rd.role_title}
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                  padding: '16px 18px',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 12,
                  flexWrap: 'wrap'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <strong style={{ fontSize: '1.05rem', color: '#fff' }}>{rd.role_title}</strong>
                    <span className={`badge ${
                      rd.priority === 'Critical' ? 'badge-rose' :
                      rd.priority === 'High' ? 'badge-amber' : 'badge-cyan'
                    }`} style={{ fontSize: '0.65rem' }}>
                      {rd.priority} Priority
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Current: {rd.current_headcount} • Target: {rd.projected_demand} (Deficit: <strong style={{ color: '#fb7185' }}>-{rd.gap}</strong>)
                  </p>
                </div>

                <button
                  onClick={() => handleOpenCandidateFinder(
                    rd.role_title === 'Cloud Engineer' ? 'ROL-001' :
                    rd.role_title === 'Data Scientist' ? 'ROL-002' : 'ROL-003',
                    rd.role_title
                  )}
                  className="btn btn-primary"
                  style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                >
                  <Sparkles size={14} /> Find Internal Candidates
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Organization Skill Shortages */}
        <div className="glass-panel" style={{ padding: 26 }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 6 }}>Critical Competency Shortages</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 18 }}>
            Aggregated skill deficits blocking strategic organizational transitions
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {shortages.map((s: any) => (
              <div key={s.skill} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ minWidth: 140 }}>
                  <strong style={{ fontSize: '0.9rem', color: '#fff' }}>{s.skill}</strong>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', display: 'block' }}>{s.category}</span>
                </div>

                {/* Progress bar of deficit */}
                <div style={{ flex: 1, height: 6, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(100, s.missing_count * 4.5)}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #f59e0b, #f43f5e)',
                    borderRadius: 3
                  }} />
                </div>

                <span className="badge badge-rose" style={{ fontSize: '0.7rem', minWidth: 75, textAlign: 'center' }}>
                  -{s.missing_count} Needed
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Internal Talent Pool Directory */}
      <div className="glass-panel" style={{ padding: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h3 style={{ fontSize: '1.3rem', marginBottom: 4 }}>Internal Talent Pool Inventory</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              All enterprise staff with verified skill competencies and career transition goals
            </p>
          </div>
          <div style={{ position: 'relative', width: 280 }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
            <input
              type="text"
              className="input-field"
              placeholder="Search talent or skills..."
              value={searchEmp}
              onChange={(e) => setSearchEmp(e.target.value)}
              style={{ paddingLeft: 38, fontSize: '0.85rem' }}
            />
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-dim)' }}>
                <th style={{ padding: '10px 14px' }}>Employee</th>
                <th style={{ padding: '10px 14px' }}>Current Role</th>
                <th style={{ padding: '10px 14px' }}>Department</th>
                <th style={{ padding: '10px 14px' }}>Target Ambition</th>
                <th style={{ padding: '10px 14px' }}>Top Skills</th>
              </tr>
            </thead>
            <tbody>
              {filteredTalent.map((emp) => (
                <tr key={emp.employee_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                  <td style={{ padding: '12px 14px', fontWeight: 600, color: '#fff' }}>
                    {emp.name}
                    <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-dim)' }}>{emp.email}</span>
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>{emp.current_role} ({emp.experience_years} yrs)</td>
                  <td style={{ padding: '12px 14px' }}>
                    <span className="badge badge-cyan" style={{ fontSize: '0.68rem' }}>{emp.department}</span>
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--accent-purple)', fontWeight: 500 }}>
                    {emp.target_role || 'Not Set'}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {emp.skills.slice(0, 4).map((s: string) => (
                        <span key={s} className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>{s}</span>
                      ))}
                      {emp.skills.length > 4 && (
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>+{emp.skills.length - 4}</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal / Overlay: Ranked Candidates for Role */}
      {activeRoleModal && selectedRoleCandidates && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: 20
        }}>
          <div className="glass-panel" style={{
            maxWidth: 750,
            width: '100%',
            maxHeight: '85vh',
            overflowY: 'auto',
            padding: 30,
            background: '#111827',
            borderColor: 'var(--accent-indigo)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 }}>
              <div>
                <span className="badge badge-cyan" style={{ marginBottom: 4 }}>Internal Mobility Feeder Pool</span>
                <h3 style={{ fontSize: '1.4rem' }}>Candidates for: {activeRoleModal}</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  Ranked by algorithmic readiness and skill coverage
                </p>
              </div>
              <button
                onClick={() => {
                  setActiveRoleModal(null);
                  setSelectedRoleCandidates(null);
                }}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {selectedRoleCandidates.ranked_candidates?.map((c: any, rank: number) => (
                <div
                  key={c.employee_id}
                  style={{
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 18px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 16,
                    flexWrap: 'wrap'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>#{rank + 1}</span>
                      <strong style={{ fontSize: '1.05rem', color: '#fff' }}>{c.name}</strong>
                      <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>{c.mobility_status}</span>
                    </div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      Current: {c.current_role} ({c.department})
                    </p>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      {c.match_score}% Match
                    </div>
                    <span style={{ fontSize: '0.78rem', color: '#34d399' }}>
                      Projected Readiness: {c.projected_readiness}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
