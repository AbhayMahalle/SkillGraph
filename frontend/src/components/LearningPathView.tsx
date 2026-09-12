import React, { useState, useEffect } from 'react';
import { 
  GraduationCap, Clock, CheckCircle2, 
  ArrowRight, Sparkles, RefreshCw, GitCommit 
} from 'lucide-react';

interface LearningPathViewProps {
  roleId: string;
  allRoles: any[];
  onSelectRole: (roleId: string) => void;
  onNavigateTab: (tab: string) => void;
}

export const LearningPathView: React.FC<LearningPathViewProps> = ({
  roleId,
  allRoles,
  onSelectRole,
  onNavigateTab
}) => {
  const [pathData, setPathData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!roleId) return;
    setLoading(true);
    fetch(`/api/analysis/learning-path/${roleId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
      .then((res) => res.json())
      .then((data) => {
        setPathData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [roleId]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 20px', color: 'var(--text-muted)' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px' }} />
        <p>Traversing Course Prerequisite DAG and computing topological roadmap...</p>
      </div>
    );
  }

  if (!pathData) return null;

  const milestones = pathData.learning_path?.milestones || [];
  const totalWeeks = pathData.learning_path?.total_estimated_weeks || 0;

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '30px 20px 60px' }}>
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
            <span className="badge badge-emerald">Topological DAG Roadmap</span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>Prerequisite Validated</span>
          </div>
          <h2 style={{ fontSize: '2.1rem' }}>Upskilling Path: {pathData.target_role_title}</h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
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
          <button 
            onClick={() => onNavigateTab('simulator')}
            className="btn btn-primary"
            style={{ fontSize: '0.85rem' }}
          >
            <Sparkles size={15} /> Simulate Impact
          </button>
        </div>
      </div>

      {/* Summary Banner */}
      <div className="glass-panel" style={{
        padding: 24,
        marginBottom: 36,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 20
      }}>
        <div>
          <h4 style={{ fontSize: '1.1rem', marginBottom: 4 }}>Roadmap Summary</h4>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            Closing <strong style={{ color: '#fb7185' }}>{pathData.missing_skills?.length || 0} skill gaps</strong> with strictly ordered prerequisite progression.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 24 }}>
          <div style={{ textAlign: 'center' }}>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block' }}>Required Courses</span>
            <strong style={{ fontSize: '1.6rem', color: '#fff' }}>{milestones.length}</strong>
          </div>
          <div style={{ textAlign: 'center' }}>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block' }}>Estimated Timeline</span>
            <strong style={{ fontSize: '1.6rem', color: 'var(--accent-cyan)' }}>{totalWeeks} Weeks</strong>
          </div>
        </div>
      </div>

      {/* Topological Timeline */}
      <div style={{ position: 'relative', paddingLeft: 30 }}>
        {/* Continuous vertical line */}
        <div style={{
          position: 'absolute',
          left: 14,
          top: 20,
          bottom: 20,
          width: 2,
          background: 'linear-gradient(180deg, #06b6d4 0%, #6366f1 50%, #8b5cf6 100%)'
        }} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {milestones.map((step: any, idx: number) => (
            <div
              key={step.course_id}
              className="glass-panel"
              style={{
                position: 'relative',
                padding: 24,
                borderLeft: '4px solid #06b6d4'
              }}
            >
              {/* Timeline marker node */}
              <div style={{
                position: 'absolute',
                left: -32,
                top: 24,
                width: 18,
                height: 18,
                borderRadius: '50%',
                background: '#06b6d4',
                boxShadow: '0 0 10px #06b6d4',
                border: '3px solid #0a0d14'
              }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span className="badge badge-cyan" style={{ fontSize: '0.68rem' }}>Step {step.step_order}</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>{step.provider}</span>
                  </div>
                  <h3 style={{ fontSize: '1.25rem', color: '#fff' }}>{step.title}</h3>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={`badge ${
                    step.level === 'Beginner' ? 'badge-emerald' :
                    step.level === 'Intermediate' ? 'badge-purple' : 'badge-amber'
                  }`} style={{ fontSize: '0.68rem' }}>
                    {step.level}
                  </span>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={14} /> {step.duration_weeks} wks (Cum: {step.cumulative_weeks} wks)
                  </span>
                </div>
              </div>

              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: 14 }}>
                {step.description}
              </p>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, paddingTop: 12, borderTop: '1px solid var(--border-subtle)' }}>
                {/* Skills taught */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Skills Acquired:</span>
                  {step.skills_taught.map((sk: string) => (
                    <span key={sk} className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>
                      +{sk}
                    </span>
                  ))}
                </div>

                {/* Prerequisites */}
                {step.prerequisites.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    <span>Requires:</span>
                    {step.prerequisites.map((pre: string) => (
                      <span key={pre} style={{ color: '#818cf8', fontWeight: 600 }}>{pre}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
