import React, { useState, useEffect } from 'react';
import { 
  Sparkles, CheckCircle2, ArrowRight, TrendingUp, 
  BookOpen, PlusCircle, RefreshCw, Zap 
} from 'lucide-react';

interface WhatIfSimulatorProps {
  initialRoleId: string;
  allRoles: any[];
}

export const WhatIfSimulator: React.FC<WhatIfSimulatorProps> = ({
  initialRoleId,
  allRoles
}) => {
  const [targetRoleId, setTargetRoleId] = useState(initialRoleId || 'ROL-001');
  const [toggledSkills, setToggledSkills] = useState<string[]>(['AWS', 'Docker']);
  const [toggledCourses, setToggledCourses] = useState<string[]>(['CRS-006', 'CRS-007']);
  const [coursesCatalog, setCoursesCatalog] = useState<any[]>([]);
  const [simResult, setSimResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Available skills to toggle
  const availableToggleSkills = [
    'AWS', 'Docker', 'Kubernetes', 'Terraform', 'CI/CD', 
    'Machine Learning', 'Deep Learning', 'PyTorch', 'MLOps',
    'React', 'TypeScript', 'FastAPI', 'PostgreSQL', 'System Design'
  ];

  // Fetch course catalog
  useEffect(() => {
    fetch('/data/processed/course_catalog.json')
      .then(res => res.json())
      .then(data => setCoursesCatalog(data))
      .catch(() => {
        // Fallback default courses
        setCoursesCatalog([
          { course_id: 'CRS-006', title: 'Cloud Computing Foundations with AWS', duration_weeks: 5 },
          { course_id: 'CRS-007', title: 'Docker Containers & Microservices', duration_weeks: 4 },
          { course_id: 'CRS-008', title: 'Kubernetes Container Orchestration at Scale', duration_weeks: 5 },
          { course_id: 'CRS-009', title: 'CI/CD Automation & Terraform IaC', duration_weeks: 4 }
        ]);
      });
  }, []);

  // Run simulation API
  useEffect(() => {
    if (!targetRoleId) return;
    setLoading(true);
    fetch('/api/analysis/what-if', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        target_role_id: targetRoleId,
        additional_skills: toggledSkills,
        completed_course_ids: toggledCourses
      })
    })
      .then((res) => res.json())
      .then((data) => {
        setSimResult(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [targetRoleId, toggledSkills, toggledCourses]);

  const toggleSkill = (skill: string) => {
    if (toggledSkills.includes(skill)) {
      setToggledSkills(toggledSkills.filter(s => s !== skill));
    } else {
      setToggledSkills([...toggledSkills, skill]);
    }
  };

  const toggleCourse = (courseId: string) => {
    if (toggledCourses.includes(courseId)) {
      setToggledCourses(toggledCourses.filter(c => c !== courseId));
    } else {
      setToggledCourses([...toggledCourses, courseId]);
    }
  };

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span className="badge badge-cyan">Predictive Talent Mobility</span>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>Interactive AI Sandbox</span>
        </div>
        <h2 style={{ fontSize: '2.1rem' }}>What-If Career Transition Simulator</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Toggle prospective courses and skills to simulate real-time readiness impact, match score surges, and unlocked roles.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 26 }}>
        {/* Left Panel: Simulation Controls */}
        <div className="glass-panel" style={{ padding: 28 }}>
          <div style={{ marginBottom: 22 }}>
            <label style={{ fontSize: '0.82rem', color: '#38bdf8', fontWeight: 600, display: 'block', marginBottom: 6 }}>
              Select Target Role Scenario
            </label>
            <select
              className="input-field"
              value={targetRoleId}
              onChange={(e) => setTargetRoleId(e.target.value)}
              style={{ cursor: 'pointer' }}
            >
              {allRoles.map((r) => (
                <option key={r.role_id} value={r.role_id} style={{ background: '#1e293b' }}>
                  {r.title} ({r.department})
                </option>
              ))}
            </select>
          </div>

          {/* Toggle Prospective Skills */}
          <div style={{ marginBottom: 26 }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 10 }}>
              Simulate Acquired Skills (Click to toggle)
            </span>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {availableToggleSkills.map((sk) => {
                const isActive = toggledSkills.includes(sk);
                return (
                  <button
                    key={sk}
                    onClick={() => toggleSkill(sk)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      padding: '6px 12px',
                      borderRadius: 9999,
                      border: '1px solid',
                      borderColor: isActive ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                      background: isActive ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                      color: isActive ? '#38bdf8' : 'var(--text-muted)',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {isActive ? <CheckCircle2 size={13} color="#38bdf8" /> : <PlusCircle size={13} />}
                    {sk}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Toggle Prospective Courses */}
          <div>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 10 }}>
              Simulate Completed Training Courses
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 260, overflowY: 'auto' }}>
              {coursesCatalog.slice(0, 8).map((c) => {
                const isActive = toggledCourses.includes(c.course_id);
                return (
                  <div
                    key={c.course_id}
                    onClick={() => toggleCourse(c.course_id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid',
                      borderColor: isActive ? 'var(--accent-indigo)' : 'var(--border-subtle)',
                      background: isActive ? 'rgba(99, 102, 241, 0.14)' : 'rgba(255, 255, 255, 0.02)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => {}}
                      style={{ cursor: 'pointer' }}
                    />
                    <div style={{ flex: 1 }}>
                      <strong style={{ fontSize: '0.88rem', color: '#fff', display: 'block' }}>{c.title}</strong>
                      <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                        {c.course_id} • {c.duration_weeks} Weeks
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Panel: Real-Time Simulation Results */}
        <div className="glass-panel" style={{ padding: 28, position: 'relative' }}>
          {loading && (
            <div style={{
              position: 'absolute',
              top: 14,
              right: 14,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: '0.78rem',
              color: 'var(--accent-cyan)'
            }}>
              <RefreshCw size={14} className="animate-spin" /> Recalculating...
            </div>
          )}

          <h3 style={{ fontSize: '1.35rem', marginBottom: 4 }}>Live Transition Feasibility</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 24 }}>
            Direct comparison: Baseline status vs Simulated upskilling profile
          </p>

          {simResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Score Surge Comparison */}
              <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                padding: 20,
                borderRadius: 'var(--radius-md)',
                display: 'grid',
                gridTemplateColumns: '1fr auto 1fr',
                alignItems: 'center',
                gap: 16,
                textAlign: 'center'
              }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Baseline Match</span>
                  <h4 style={{ fontSize: '2rem', color: 'var(--text-muted)' }}>{simResult.baseline?.match_score}%</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{simResult.baseline?.mobility_status}</span>
                </div>

                <div style={{ color: 'var(--accent-cyan)' }}>
                  <ArrowRight size={26} />
                  <span className="badge badge-emerald" style={{ fontSize: '0.68rem', display: 'block', marginTop: 4 }}>
                    +{simResult.deltas?.match_gain}%
                  </span>
                </div>

                <div>
                  <span style={{ fontSize: '0.75rem', color: '#38bdf8', textTransform: 'uppercase', fontWeight: 600 }}>Simulated Match</span>
                  <h4 style={{ fontSize: '2.2rem', color: 'var(--accent-cyan)' }}>{simResult.simulated?.match_score}%</h4>
                  <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>
                    {simResult.simulated?.mobility_status}
                  </span>
                </div>
              </div>

              {/* Readiness Prediction Gauge */}
              <div style={{
                background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(99, 102, 241, 0.1))',
                border: '1px solid rgba(6, 182, 212, 0.3)',
                padding: 22,
                borderRadius: 'var(--radius-md)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Zap size={18} color="#38bdf8" />
                    <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>ML Predicted Readiness</span>
                  </div>
                  <strong style={{ fontSize: '1.6rem', color: '#34d399' }}>
                    {simResult.simulated?.projected_readiness_pct}%
                  </strong>
                </div>

                <div style={{
                  height: 8,
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: 4,
                  overflow: 'hidden',
                  marginBottom: 10
                }}>
                  <div style={{
                    width: `${simResult.simulated?.projected_readiness_pct}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #06b6d4, #10b981)',
                    borderRadius: 4,
                    transition: 'width 0.4s ease'
                  }} />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  <span>Verdict: <strong style={{ color: '#fff' }}>{simResult.simulated?.readiness_verdict}</strong></span>
                  <span>Skills closed: <strong style={{ color: '#34d399' }}>{simResult.deltas?.skills_closed}</strong></span>
                </div>
              </div>

              {/* Remaining missing skills */}
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>
                  Remaining Missing Competencies ({simResult.simulated?.missing_skills?.length || 0})
                </span>
                {simResult.simulated?.missing_skills?.length === 0 ? (
                  <div style={{ color: '#34d399', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <CheckCircle2 size={16} /> 100% Competency coverage achieved in this scenario!
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {simResult.simulated?.missing_skills?.map((sk: string) => (
                      <span key={sk} className="badge badge-rose" style={{ fontSize: '0.72rem' }}>
                        {sk}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
