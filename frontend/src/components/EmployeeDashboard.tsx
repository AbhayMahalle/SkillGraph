import React from 'react';
import { 
  Target, Sparkles, TrendingUp, Award, 
  ArrowRight, BookOpen, CheckCircle, ChevronRight 
} from 'lucide-react';

interface EmployeeDashboardProps {
  profile: any;
  recommendations: any[];
  onSelectRole: (roleId: string) => void;
  onNavigateTab: (tab: string) => void;
}

export const EmployeeDashboard: React.FC<EmployeeDashboardProps> = ({
  profile,
  recommendations,
  onSelectRole,
  onNavigateTab
}) => {
  const targetRoleRec = recommendations.find(r => r.role_id === profile?.target_role_id) || recommendations[0];

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      {/* Top Banner */}
      <div className="glass-panel" style={{
        padding: 32,
        marginBottom: 30,
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9))',
        border: '1px solid rgba(99, 102, 241, 0.25)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 20
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <span className="badge badge-cyan">Employee Career Hub</span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>ID: {profile?.employee_id}</span>
          </div>
          <h2 style={{ fontSize: '2rem', marginBottom: 6 }}>
            Welcome back, {profile?.name}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Current: <strong style={{ color: '#fff' }}>{profile?.current_role}</strong> • Department: <strong style={{ color: '#fff' }}>{profile?.department}</strong>
          </p>
        </div>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button 
            onClick={() => onNavigateTab('simulator')}
            className="btn btn-primary"
          >
            <Sparkles size={16} /> Open What-If Simulator
          </button>
          <button 
            onClick={() => onNavigateTab('profile')}
            className="btn btn-secondary"
          >
            Update Resume & Skills
          </button>
        </div>
      </div>

      {/* Metric Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 20,
        marginBottom: 36
      }}>
        {/* Target Role Card */}
        <div className="glass-panel" style={{ padding: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
              Designated Target Role
            </span>
            <Target size={18} color="#38bdf8" />
          </div>
          <h3 style={{ fontSize: '1.35rem', color: '#fff', marginBottom: 4 }}>
            {profile?.target_role_title || targetRoleRec?.title || 'Cloud Engineer'}
          </h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            {targetRoleRec?.openings || 5} open internal requisitions
          </p>
        </div>

        {/* Current Match */}
        <div className="glass-panel" style={{ padding: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
              Current Skill Match
            </span>
            <TrendingUp size={18} color="#818cf8" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
            <h3 style={{ fontSize: '1.9rem', color: '#818cf8' }}>
              {targetRoleRec?.match_score || 41.2}%
            </h3>
            <span className="badge badge-purple" style={{ fontSize: '0.68rem' }}>
              {targetRoleRec?.mobility_status || 'Needs Upskilling'}
            </span>
          </div>
          <div style={{
            height: 6,
            background: 'rgba(255, 255, 255, 0.08)',
            borderRadius: 3,
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${targetRoleRec?.match_score || 41}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
              borderRadius: 3
            }} />
          </div>
        </div>

        {/* Projected Readiness */}
        <div className="glass-panel" style={{ padding: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
              Projected Readiness
            </span>
            <Sparkles size={18} color="#34d399" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
            <h3 style={{ fontSize: '1.9rem', color: '#34d399' }}>
              {targetRoleRec?.projected_readiness_pct || 90.5}%
            </h3>
            <span className="badge badge-emerald" style={{ fontSize: '0.68rem' }}>High Feasibility</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            After completing 5 topological roadmap courses
          </p>
        </div>

        {/* Verified Skills */}
        <div className="glass-panel" style={{ padding: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
              Verified Skill Inventory
            </span>
            <Award size={18} color="#fbbf24" />
          </div>
          <h3 style={{ fontSize: '1.9rem', color: '#fbbf24', marginBottom: 4 }}>
            {profile?.skills?.length || 6}
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {profile?.completed_courses?.length || 3} courses completed
          </p>
        </div>
      </div>

      {/* Role Recommendations Table / Grid */}
      <div className="glass-panel" style={{ padding: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h3 style={{ fontSize: '1.35rem', marginBottom: 4 }}>Top Internal Transition Opportunities</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
              Ranked by multi-factor algorithmic compatibility with your verified skills and experience
            </p>
          </div>
          <button 
            onClick={() => onNavigateTab('roles')}
            className="btn btn-secondary" 
            style={{ fontSize: '0.85rem' }}
          >
            Browse All 96 Roles <ArrowRight size={15} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {recommendations.slice(0, 5).map((rec) => {
            const isTarget = rec.role_id === profile?.target_role_id;
            return (
              <div
                key={rec.role_id}
                style={{
                  background: isTarget ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                  border: isTarget ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '18px 22px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 16,
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ minWidth: 260 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <h4 style={{ fontSize: '1.15rem' }}>{rec.title}</h4>
                    {isTarget && (
                      <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>Current Target</span>
                    )}
                  </div>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    {rec.department} • Salary Range: {rec.salary_range} • {rec.openings} Openings
                  </p>
                </div>

                {/* Score & Bar */}
                <div style={{ minWidth: 200, flex: 1, maxWidth: 300 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: 6 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Match: <strong style={{ color: '#fff' }}>{rec.match_score}%</strong></span>
                    <span style={{ color: '#34d399' }}>Projected: <strong>{rec.projected_readiness_pct}%</strong></span>
                  </div>
                  <div style={{
                    height: 6,
                    background: 'rgba(255, 255, 255, 0.08)',
                    borderRadius: 3,
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${rec.match_score}%`,
                      height: '100%',
                      background: rec.match_score >= 60 ? 'linear-gradient(90deg, #10b981, #06b6d4)' : 'linear-gradient(90deg, #f59e0b, #6366f1)',
                      borderRadius: 3
                    }} />
                  </div>
                </div>

                {/* Missing Skills Pill */}
                <div style={{ minWidth: 220 }}>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>
                    Top Missing Skills
                  </span>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {rec.missing_skills.slice(0, 3).map((sk: string) => (
                      <span key={sk} className="badge badge-rose" style={{ fontSize: '0.7rem' }}>
                        {sk}
                      </span>
                    ))}
                    {rec.missing_skills.length > 3 && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', alignSelf: 'center' }}>
                        +{rec.missing_skills.length - 3} more
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => {
                      onSelectRole(rec.role_id);
                      onNavigateTab('skill-gap');
                    }}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                  >
                    View Gap
                  </button>
                  <button
                    onClick={() => {
                      onSelectRole(rec.role_id);
                      onNavigateTab('learning-path');
                    }}
                    className="btn btn-primary"
                    style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                  >
                    Roadmap <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
