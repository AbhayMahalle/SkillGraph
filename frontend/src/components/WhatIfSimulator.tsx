import React, { useState, useEffect } from 'react';
import { 
  Sparkles, CheckCircle2, ArrowRight, TrendingUp, 
  BookOpen, PlusCircle, RefreshCw, Zap, AlertCircle,
  ShieldAlert, Sliders, Check, Info, Award, X
} from 'lucide-react';

interface WhatIfSimulatorProps {
  initialRoleId: string;
  allRoles: any[];
}

interface SimulatedSkill {
  skill_name: string;
  proficiency: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
}

export const WhatIfSimulator: React.FC<WhatIfSimulatorProps> = ({
  initialRoleId,
  allRoles
}) => {
  const [targetRoleId, setTargetRoleId] = useState(initialRoleId || (allRoles[0]?.role_id || 'ROL-001'));
  const [roleDetails, setRoleDetails] = useState<any>(null);
  const [hypotheticalSkills, setHypotheticalSkills] = useState<SimulatedSkill[]>([]);
  const [toggledCourses, setToggledCourses] = useState<string[]>([]);
  const [coursesCatalog, setCoursesCatalog] = useState<any[]>([]);
  const [simResult, setSimResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [gapLoading, setGapLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch course catalog on mount from canonical API
  useEffect(() => {
    fetch('/api/courses')
      .then(res => {
        if (!res.ok) throw new Error('API fetch failed');
        return res.json();
      })
      .then(data => setCoursesCatalog(data))
      .catch(() => {
        fetch('/data/processed/course_catalog.json')
          .then(res => res.json())
          .then(data => setCoursesCatalog(data))
          .catch(() => setCoursesCatalog([]));
      });
  }, []);

  // 2. Fetch role gap details when target role changes
  useEffect(() => {
    if (!targetRoleId) return;
    setGapLoading(true);
    const token = localStorage.getItem('token');
    fetch(`/api/analysis/skill-gap/${targetRoleId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to load target role skill gaps');
        return res.json();
      })
      .then(data => {
        setRoleDetails(data);
        // Pre-populate with first missing skill if available and no hypothetical skills selected yet
        if (hypotheticalSkills.length === 0 && data.all_gaps && data.all_gaps.length > 0) {
          const firstGap = data.all_gaps[0];
          setHypotheticalSkills([{
            skill_name: firstGap.skill_name,
            proficiency: 'Advanced'
          }]);
        }
      })
      .catch(err => {
        console.error('Error fetching role details:', err);
      })
      .finally(() => {
        setGapLoading(false);
      });
  }, [targetRoleId]);

  // 3. Trigger what-if simulation when hypothetical changes occur
  useEffect(() => {
    if (!targetRoleId) return;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem('token');
    const payload = {
      target_role_id: targetRoleId,
      skills: hypotheticalSkills,
      completed_course_ids: toggledCourses
    };

    fetch('/api/analysis/what-if', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })
      .then(async res => {
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Simulation failed (${res.status})`);
        }
        return res.json();
      })
      .then(data => {
        setSimResult(data);
      })
      .catch(err => {
        console.error('Simulation error:', err);
        setError(err.message || 'Error computing simulation.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [targetRoleId, hypotheticalSkills, toggledCourses]);

  const handleToggleGapSkill = (skillName: string, defaultLevel: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert' = 'Advanced') => {
    const existingIndex = hypotheticalSkills.findIndex(s => s.skill_name.toLowerCase() === skillName.toLowerCase());
    if (existingIndex >= 0) {
      setHypotheticalSkills(hypotheticalSkills.filter((_, idx) => idx !== existingIndex));
    } else {
      setHypotheticalSkills([...hypotheticalSkills, { skill_name: skillName, proficiency: defaultLevel }]);
    }
  };

  const handleUpdateSkillProficiency = (skillName: string, newProf: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert') => {
    setHypotheticalSkills(hypotheticalSkills.map(s => {
      if (s.skill_name.toLowerCase() === skillName.toLowerCase()) {
        return { ...s, proficiency: newProf };
      }
      return s;
    }));
  };

  const toggleCourse = (courseId: string) => {
    if (toggledCourses.includes(courseId)) {
      setToggledCourses(toggledCourses.filter(c => c !== courseId));
    } else {
      setToggledCourses([...toggledCourses, courseId]);
    }
  };

  const handleResetSimulation = () => {
    setHypotheticalSkills([]);
    setToggledCourses([]);
  };

  const roleGaps = roleDetails?.all_gaps || [];

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '24px 20px 80px' }}>
      {/* Header Banner */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 16,
        marginBottom: 24
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span className="badge badge-cyan" style={{ fontSize: '0.72rem' }}>Phase 6 Sandbox</span>
            <span className="badge badge-purple" style={{ fontSize: '0.72rem' }}>Non-Persistent</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Zero Profile Alteration</span>
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 700, margin: '0 0 6px' }}>
            Career Readiness & What-If Simulation
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0, maxWidth: 720 }}>
            Hypothetically adjust competencies, close skill gaps, and simulate training course completions to forecast realistic transition readiness without modifying your persistent profile.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <select
            className="input-field"
            value={targetRoleId}
            onChange={(e) => {
              setTargetRoleId(e.target.value);
              setHypotheticalSkills([]);
              setToggledCourses([]);
            }}
            style={{ width: 240, cursor: 'pointer' }}
          >
            {allRoles.map((r) => (
              <option key={r.role_id} value={r.role_id}>
                {r.title} ({r.department})
              </option>
            ))}
          </select>

          {(hypotheticalSkills.length > 0 || toggledCourses.length > 0) && (
            <button
              onClick={handleResetSimulation}
              className="btn btn-secondary"
              style={{ fontSize: '0.84rem' }}
              title="Reset all hypothetical adjustments"
            >
              Reset Scenarios
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Controls vs Results */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: 24 }}>
        
        {/* Left Column: Interactive Scenario Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          
          {/* Card 1: Missing & Partial Skills Adjuster */}
          <div className="saas-card" style={{ padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Sliders size={18} style={{ color: '#0284c7' }} />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: 0, color: 'var(--text-main)' }}>
                  Target Role Skill Gaps ({roleGaps.length})
                </h3>
              </div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                Click to toggle into scenario
              </span>
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>
              Select missing or partially met competencies to simulate acquiring them or elevating your proficiency level.
            </p>

            {gapLoading ? (
              <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)' }}>
                <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px' }} />
                <p style={{ fontSize: '0.84rem' }}>Loading target role requirements...</p>
              </div>
            ) : roleGaps.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#10b981', background: '#f0fdf4', borderRadius: 'var(--radius-md)' }}>
                <CheckCircle2 size={24} style={{ margin: '0 auto 6px' }} />
                <p style={{ margin: 0, fontWeight: 600, fontSize: '0.88rem' }}>No skill gaps! You meet 100% of requirements for this role.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {roleGaps.map((gap: any) => {
                  const isSimulated = hypotheticalSkills.some(s => s.skill_name.toLowerCase() === gap.skill_name.toLowerCase());
                  const simulatedProf = hypotheticalSkills.find(s => s.skill_name.toLowerCase() === gap.skill_name.toLowerCase())?.proficiency || 'Advanced';

                  return (
                    <div
                      key={gap.skill_name}
                      style={{
                        padding: '12px 14px',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid',
                        borderColor: isSimulated ? '#7dd3fc' : 'var(--border-subtle)',
                        background: isSimulated ? '#f0f9ff' : '#ffffff',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                        <div
                          onClick={() => handleToggleGapSkill(gap.skill_name, 'Advanced')}
                          style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', flex: 1 }}
                        >
                          <input
                            type="checkbox"
                            checked={isSimulated}
                            onChange={() => {}}
                            style={{ cursor: 'pointer' }}
                          />
                          <div>
                            <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>
                              {gap.skill_name}
                            </strong>
                            <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginTop: 2 }}>
                              <span className={`badge ${gap.classification === 'missing' ? 'badge-rose' : 'badge-amber'}`} style={{ fontSize: '0.65rem' }}>
                                {gap.status || gap.classification}
                              </span>
                              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                                Required: {gap.required_proficiency || 'Intermediate'}
                              </span>
                              {gap.demonstrated_proficiency && (
                                <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                                  • Current: {gap.demonstrated_proficiency}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Interactive Proficiency Level Selector */}
                        {isSimulated && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            {(['Beginner', 'Intermediate', 'Advanced', 'Expert'] as const).map((lvl) => (
                              <button
                                key={lvl}
                                onClick={() => handleUpdateSkillProficiency(gap.skill_name, lvl)}
                                style={{
                                  fontSize: '0.7rem',
                                  padding: '3px 8px',
                                  borderRadius: 4,
                                  border: '1px solid',
                                  borderColor: simulatedProf === lvl ? '#0284c7' : 'var(--border-subtle)',
                                  background: simulatedProf === lvl ? '#0284c7' : '#ffffff',
                                  color: simulatedProf === lvl ? '#ffffff' : 'var(--text-secondary)',
                                  fontWeight: simulatedProf === lvl ? 600 : 400,
                                  cursor: 'pointer'
                                }}
                              >
                                {lvl.slice(0, 3)}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Card 2: Prospective Training Courses */}
          <div className="saas-card" style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <BookOpen size={18} style={{ color: '#4f46e5' }} />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, margin: 0, color: 'var(--text-main)' }}>
                Simulate Course Completions ({toggledCourses.length} active)
              </h3>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 14 }}>
              Toggle curriculum courses to simulate acquiring their taught skills into your hypothetical profile.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 260, overflowY: 'auto' }}>
              {coursesCatalog.slice(0, 8).map((c) => {
                const isChecked = toggledCourses.includes(c.course_id);
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
                      borderColor: isChecked ? '#c7d2fe' : 'var(--border-subtle)',
                      background: isChecked ? '#f5f3ff' : '#ffffff',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => {}}
                      style={{ cursor: 'pointer' }}
                    />
                    <div style={{ flex: 1 }}>
                      <strong style={{ fontSize: '0.86rem', color: 'var(--text-main)', display: 'block' }}>
                        {c.title}
                      </strong>
                      <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                        {c.course_id} • {c.duration_weeks} wks • Teaches: {c.skills_taught?.join(', ')}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Comparative Results & Explainability */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          
          {/* Main Results Card */}
          <div className="saas-card" style={{ padding: 24, position: 'relative' }}>
            {loading && (
              <div style={{
                position: 'absolute',
                top: 14,
                right: 14,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: '0.78rem',
                color: '#0284c7'
              }}>
                <RefreshCw size={13} className="animate-spin" /> Recalculating...
              </div>
            )}

            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', margin: '0 0 4px' }}>
              Transition Feasibility Forecast
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: 20 }}>
              Live comparison of baseline profile vs hypothetical scenario.
            </p>

            {error ? (
              <div style={{ padding: 16, background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: 'var(--radius-md)', color: '#be123c', fontSize: '0.88rem' }}>
                <AlertCircle size={18} style={{ display: 'inline', marginRight: 6 }} />
                {error}
              </div>
            ) : simResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                
                {/* 2x2 Metric Comparison Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: 16
                }}>
                  {/* Metric 1: Role Match Score */}
                  <div style={{
                    background: '#f8fafc',
                    border: '1px solid var(--border-subtle)',
                    padding: 16,
                    borderRadius: 'var(--radius-md)',
                    textAlign: 'center'
                  }}>
                    <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                      Role Match Score
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                      <span style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
                        {simResult.baseline?.match_score}%
                      </span>
                      <ArrowRight size={18} style={{ color: '#0284c7' }} />
                      <span style={{ fontSize: '1.6rem', fontWeight: 700, color: '#0284c7' }}>
                        {simResult.simulated?.match_score}%
                      </span>
                    </div>
                    <span className="badge badge-emerald" style={{ fontSize: '0.7rem', marginTop: 4 }}>
                      +{simResult.deltas?.match_gain}% Gain
                    </span>
                  </div>

                  {/* Metric 2: Career Readiness Score */}
                  <div style={{
                    background: '#ffffff',
                    border: '1px solid #bae6fd',
                    padding: 16,
                    borderRadius: 'var(--radius-md)',
                    textAlign: 'center',
                    boxShadow: 'var(--shadow-sm)'
                  }}>
                    <span style={{ fontSize: '0.74rem', color: '#0369a1', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                      Career Readiness Score
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                      <span style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
                        {simResult.baseline?.readiness_score}%
                      </span>
                      <ArrowRight size={18} style={{ color: '#059669' }} />
                      <span style={{ fontSize: '1.6rem', fontWeight: 700, color: '#059669' }}>
                        {simResult.simulated?.readiness_score}%
                      </span>
                    </div>
                    <span className={`badge ${simResult.deltas?.readiness_gain >= 0 ? 'badge-emerald' : 'badge-amber'}`} style={{ fontSize: '0.7rem', marginTop: 4 }}>
                      {simResult.deltas?.readiness_gain >= 0 ? '+' : ''}{simResult.deltas?.readiness_gain}% Delta
                    </span>
                  </div>
                </div>

                {/* Verdict Transition Banner */}
                <div style={{
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 10
                }}>
                  <div>
                    <span style={{ fontSize: '0.74rem', color: '#166534', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                      Hypothetical Transition Status:
                    </span>
                    <strong style={{ fontSize: '0.95rem', color: '#15803d' }}>
                      {simResult.simulated?.readiness_level || simResult.simulated?.readiness_verdict}
                    </strong>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#166534' }}>
                    Skills Closed: <strong>{simResult.deltas?.skills_closed}</strong> of {simResult.baseline?.missing_count}
                  </div>
                </div>

                {/* Simulation Assumptions Callout */}
                <div style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: 'var(--radius-md)',
                  padding: 14
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                    <Sparkles size={15} style={{ color: '#0284c7' }} />
                    <strong style={{ fontSize: '0.84rem', color: 'var(--text-main)' }}>
                      Scenario Assumptions ({simResult.assumptions?.length || 0}):
                    </strong>
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 20, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {simResult.assumptions?.map((ass: string, idx: number) => (
                      <li key={idx} style={{ marginBottom: 4 }}>{ass}</li>
                    ))}
                  </ul>
                </div>

                {/* Contributing Factors Comparison */}
                {simResult.simulated?.contributing_factors && (
                  <div>
                    <h4 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 10 }}>
                      Readiness Factor Breakdown (Hypothetical):
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {simResult.simulated.contributing_factors.map((f: any) => (
                        <div
                          key={f.factor}
                          style={{
                            padding: '10px 12px',
                            background: '#ffffff',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-sm)',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            fontSize: '0.8rem'
                          }}
                        >
                          <div>
                            <strong style={{ color: 'var(--text-main)', display: 'block' }}>{f.factor}</strong>
                            <span style={{ color: 'var(--text-dim)', fontSize: '0.74rem' }}>{f.explanation}</span>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <span style={{ fontWeight: 700, color: '#0284c7' }}>{f.score_pct}%</span>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', display: 'block' }}>Weight: {f.weight_pct}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>

          {/* Explainability & Limitations Notice Card */}
          <div className="saas-card" style={{ padding: 20, borderLeft: '4px solid #0284c7', background: '#f8fafc' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <Info size={18} style={{ color: '#0284c7', marginTop: 2, flexShrink: 0 }} />
              <div>
                <h4 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)', margin: '0 0 4px' }}>
                  Model Methodology & Limitations
                </h4>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0 0 8px', lineHeight: 1.5 }}>
                  <strong>Role Match</strong> measures lexical and keyword overlap against role requirements. <strong>Career Readiness</strong> incorporates competency priority, verification provenance, and prerequisite fulfillment.
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', margin: 0, lineHeight: 1.4 }}>
                  {simResult?.limitations || 'Assessments are transparent deterministic heuristics and should be paired with practical reviews.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
