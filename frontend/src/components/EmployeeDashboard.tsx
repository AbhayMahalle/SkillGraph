import React, { useState, useEffect } from 'react';
import { 
  Target, Sparkles, TrendingUp, Award, 
  ArrowRight, BookOpen, CheckCircle, ChevronRight,
  Briefcase, Compass, FileText, AlertCircle, RefreshCw
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
  const [readinessData, setReadinessData] = useState<any>(null);
  const [loadingReadiness, setLoadingReadiness] = useState<boolean>(false);

  const targetRoleId = profile?.target_role_id;
  const hasTargetRole = Boolean(targetRoleId);
  const targetRoleRec = recommendations.find(r => r.role_id === targetRoleId);

  useEffect(() => {
    if (!targetRoleId) {
      setReadinessData(null);
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) return;

    setLoadingReadiness(true);
    fetch(`/api/analysis/readiness/${encodeURIComponent(targetRoleId)}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Could not fetch readiness');
        return res.json();
      })
      .then(data => {
        setReadinessData(data);
        setLoadingReadiness(false);
      })
      .catch(() => {
        setReadinessData(null);
        setLoadingReadiness(false);
      });
  }, [targetRoleId]);

  const matchScore = targetRoleRec?.match_score != null 
    ? targetRoleRec.match_score 
    : (readinessData?.skill_match_score != null ? readinessData.skill_match_score : null);

  const readinessScore = readinessData?.readiness_score != null
    ? readinessData.readiness_score
    : (targetRoleRec?.projected_readiness_pct != null ? targetRoleRec.projected_readiness_pct : null);

  const readinessLevel = readinessData?.readiness_level || (
    readinessScore != null
      ? (readinessScore >= 85 ? 'High Feasibility' : readinessScore >= 70 ? 'Moderate Feasibility' : 'Long-Term Upskilling')
      : null
  );

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 20px 48px' }}>
      {/* Top Welcome Card */}
      <div className="saas-card" style={{
        padding: '24px 28px',
        marginBottom: 24,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 20
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
              Personal Career Workspace
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              ID: {profile?.employee_id || 'EMP-001'}
            </span>
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: 4 }}>
            Welcome back, {profile?.name || 'Professional'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Current: <strong>{profile?.current_role || 'Software Engineer'}</strong> • Department: <strong>{profile?.department || 'Engineering'}</strong>
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button 
            onClick={() => onNavigateTab(hasTargetRole ? 'skill-gap' : 'roles')}
            className="btn btn-primary"
          >
            <Target size={15} /> {hasTargetRole ? 'Analyze Target Gap' : 'Select Target Role'}
          </button>
          <button 
            onClick={() => onNavigateTab('profile')}
            className="btn btn-secondary"
          >
            <FileText size={15} /> Update Skills
          </button>
        </div>
      </div>

      {/* Metric Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 16,
        marginBottom: 28
      }}>
        {/* Designated Target Role Card */}
        <div className="saas-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Designated Target Role
            </span>
            <Target size={16} color="var(--accent-blue)" />
          </div>
          <h3 style={{ fontSize: '1.25rem', color: 'var(--text-main)', fontWeight: 600, marginBottom: 4 }}>
            {hasTargetRole 
              ? (profile?.target_role_title || readinessData?.target_role_title || targetRoleRec?.title || targetRoleId)
              : 'None Selected'}
          </h3>
          {hasTargetRole ? (
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              Department: {readinessData?.department || targetRoleRec?.department || 'Enterprise Architecture'}
            </p>
          ) : (
            <button 
              onClick={() => onNavigateTab('roles')}
              className="btn btn-secondary" 
              style={{ fontSize: '0.75rem', padding: '4px 10px', marginTop: 4 }}
            >
              Choose Target Role <ArrowRight size={12} />
            </button>
          )}
        </div>

        {/* Current Match */}
        <div className="saas-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Current Skill Match
            </span>
            <TrendingUp size={16} color="var(--accent-indigo)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 8 }}>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
              {matchScore != null ? `${matchScore}%` : '—'}
            </h3>
            <span className="badge badge-purple" style={{ fontSize: '0.68rem' }}>
              {hasTargetRole 
                ? (targetRoleRec?.mobility_status || (matchScore != null && matchScore >= 70 ? 'Ready for Transition' : 'Needs Upskilling'))
                : 'No Goal Selected'}
            </span>
          </div>
          <div style={{
            height: 4,
            background: 'var(--bg-muted)',
            borderRadius: 2,
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${matchScore || 0}%`,
              height: '100%',
              background: (matchScore || 0) >= 60 ? 'var(--accent-emerald)' : 'var(--accent-blue)',
              borderRadius: 2,
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        {/* Career Readiness */}
        <div className="saas-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Career Readiness
            </span>
            <Sparkles size={16} color="var(--accent-emerald)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
              {loadingReadiness ? (
                <RefreshCw size={20} className="animate-spin" />
              ) : (
                readinessScore != null ? `${readinessScore}%` : '—'
              )}
            </h3>
            {readinessLevel && (
              <span className={`badge ${readinessScore && readinessScore >= 80 ? 'badge-emerald' : 'badge-amber'}`} style={{ fontSize: '0.68rem' }}>
                {readinessLevel}
              </span>
            )}
            {!hasTargetRole && (
              <span className="badge badge-neutral" style={{ fontSize: '0.68rem' }}>
                Pending Goal
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {hasTargetRole ? 'Multi-factor practical capability' : 'Requires target role designation'}
          </p>
        </div>

        {/* Verified Skills */}
        <div className="saas-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Skills & Courses
            </span>
            <Award size={16} color="var(--accent-amber)" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: 4 }}>
              {profile?.skills?.length || 0}
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>demonstrated skills</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {profile?.completed_courses?.length || 0} completed curriculum courses
          </p>
        </div>
      </div>

      {/* Role Recommendations Table / Grid */}
      <div className="saas-card" style={{ padding: '24px 28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 2 }}>
              Top Internal Transition Opportunities
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Ranked by multi-factor algorithmic compatibility with your verified skills and experience
            </p>
          </div>
          <button 
            onClick={() => onNavigateTab('roles')}
            className="btn btn-secondary" 
            style={{ fontSize: '0.82rem' }}
          >
            <span>Browse All Roles</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {recommendations && recommendations.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {recommendations.slice(0, 5).map((rec) => {
              const isTarget = rec.role_id === profile?.target_role_id;
              return (
                <div
                  key={rec.role_id}
                  style={{
                    background: isTarget ? '#eff6ff' : '#ffffff',
                    border: isTarget ? '1px solid #bfdbfe' : '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: 16,
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ minWidth: 240 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>{rec.title}</h4>
                      {isTarget && (
                        <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>Current Target</span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {rec.department} • Experience: {rec.experience_years}y • Salary: {rec.salary_range}
                    </p>
                  </div>

                  {/* Match Score & Progress Bar */}
                  <div style={{ minWidth: 180, flex: 1, maxWidth: 260 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: 6 }}>
                      <span style={{ color: 'var(--text-secondary)' }}>
                        Match: <strong style={{ color: 'var(--text-main)' }}>{rec.match_score}%</strong>
                      </span>
                      <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
                        {rec.projected_readiness_pct != null ? `${rec.projected_readiness_pct}% Projected` : ''}
                      </span>
                    </div>
                    <div style={{
                      height: 4,
                      background: 'var(--bg-muted)',
                      borderRadius: 2,
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${rec.match_score}%`,
                        height: '100%',
                        background: rec.match_score >= 60 ? 'var(--accent-emerald)' : 'var(--accent-blue)',
                        borderRadius: 2
                      }} />
                    </div>
                  </div>

                  {/* Missing Skills Pill */}
                  <div style={{ minWidth: 200 }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>
                      Priority Missing Skills
                    </span>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {rec.missing_skills && rec.missing_skills.length > 0 ? (
                        <>
                          {rec.missing_skills.slice(0, 3).map((sk: string) => (
                            <span key={sk} className="badge badge-rose" style={{ fontSize: '0.68rem' }}>
                              {sk}
                            </span>
                          ))}
                          {rec.missing_skills.length > 3 && (
                            <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', alignSelf: 'center' }}>
                              +{rec.missing_skills.length - 3} more
                            </span>
                          )}
                        </>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>None missing</span>
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
                      style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                    >
                      View Gap
                    </button>
                    <button
                      onClick={() => {
                        onSelectRole(rec.role_id);
                        onNavigateTab('learning-path');
                      }}
                      className="btn btn-primary"
                      style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                    >
                      Roadmap <ChevronRight size={13} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '36px 20px', color: 'var(--text-muted)' }}>
            <AlertCircle size={28} style={{ margin: '0 auto 10px', color: 'var(--text-dim)' }} />
            <p style={{ fontWeight: 500, fontSize: '0.95rem', color: 'var(--text-main)', marginBottom: 4 }}>
              No Recommendations Generated Yet
            </p>
            <p style={{ fontSize: '0.85rem', marginBottom: 16 }}>
              Add personal competencies to your profile to receive personalized internal role matches.
            </p>
            <button onClick={() => onNavigateTab('profile')} className="btn btn-primary">
              Build Skill Profile
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
