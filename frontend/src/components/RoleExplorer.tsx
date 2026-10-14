import React, { useState } from 'react';
import { 
  Search, Target, Briefcase, ChevronRight, Sparkles, 
  Check, CheckCircle2, Scale, X, AlertCircle, Loader2, Award
} from 'lucide-react';

interface RoleExplorerProps {
  roles: any[];
  onSelectRole: (roleId: string) => void;
  onNavigateTab: (tab: string) => void;
  targetRoleId?: string;
  currentUser?: any;
  onRefreshProfile?: () => void;
}

export const RoleExplorer: React.FC<RoleExplorerProps> = ({
  roles,
  onSelectRole,
  onNavigateTab,
  targetRoleId,
  currentUser,
  onRefreshProfile
}) => {
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('All');
  const [settingTargetId, setSettingTargetId] = useState<string | null>(null);
  const [targetSuccessMsg, setTargetSuccessMsg] = useState('');
  const [targetErrorMsg, setTargetErrorMsg] = useState('');

  // Role Comparison State
  const [compareRoleIds, setCompareRoleIds] = useState<string[]>([]);
  const [isComparing, setIsComparing] = useState(false);
  const [compareModalOpen, setCompareModalOpen] = useState(false);
  const [compareData, setCompareData] = useState<any>(null);
  const [compareError, setCompareError] = useState('');

  const departments = ['All', 'Engineering', 'Infrastructure', 'Data Science', 'AI Engineering', 'Information Security'];

  const filteredRoles = roles.filter((r) => {
    const matchesSearch = 
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.department.toLowerCase().includes(search.toLowerCase()) ||
      r.required_skills?.some((sk: string) => sk.toLowerCase().includes(search.toLowerCase()));

    const matchesDept = selectedDept === 'All' || r.department === selectedDept;
    return matchesSearch && matchesDept;
  });

  // Handle Set Target Role
  const handleSetTargetRole = async (role: any) => {
    if (!currentUser) {
      setTargetErrorMsg('Please sign in to select and persist your career target role.');
      setTimeout(() => setTargetErrorMsg(''), 4000);
      return;
    }

    setSettingTargetId(role.role_id);
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
        body: JSON.stringify({ target_role_id: role.role_id })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to update target role');
      }

      setTargetSuccessMsg(`Target role updated to '${role.title}'. Profile synchronized.`);
      if (onRefreshProfile) onRefreshProfile();
      setTimeout(() => setTargetSuccessMsg(''), 4000);
    } catch (err: any) {
      setTargetErrorMsg(err.message || 'Error updating target role');
      setTimeout(() => setTargetErrorMsg(''), 4000);
    } finally {
      setSettingTargetId(null);
    }
  };

  // Toggle role in comparison selection
  const toggleRoleComparison = (roleId: string) => {
    setCompareRoleIds(prev => {
      if (prev.includes(roleId)) {
        return prev.filter(id => id !== roleId);
      }
      if (prev.length >= 4) {
        setTargetErrorMsg('You can compare a maximum of 4 roles simultaneously.');
        setTimeout(() => setTargetErrorMsg(''), 3000);
        return prev;
      }
      return [...prev, roleId];
    });
  };

  // Execute comparison API
  const handleOpenComparison = async () => {
    if (compareRoleIds.length < 2) {
      setTargetErrorMsg('Please select at least 2 roles to compare.');
      setTimeout(() => setTargetErrorMsg(''), 3000);
      return;
    }

    setIsComparing(true);
    setCompareError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/roles/compare?role_ids=${compareRoleIds.join(',')}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to compare roles');
      }
      setCompareData(data);
      setCompareModalOpen(true);
    } catch (err: any) {
      setCompareError(err.message || 'Error fetching comparison data.');
      setTimeout(() => setCompareError(''), 4000);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: '2rem', marginBottom: 6 }}>Organizational Role Architecture</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Explore 96 canonical enterprise roles, designated skill competencies, and salary bands. Select and persist your designated career target.
        </p>
      </div>

      {targetSuccessMsg && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#34d399',
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 10
        }}>
          <CheckCircle2 size={18} /> {targetSuccessMsg}
        </div>
      )}

      {targetErrorMsg && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          color: '#fb7185',
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 10
        }}>
          <AlertCircle size={18} /> {targetErrorMsg}
        </div>
      )}

      {/* Search & Filters */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 16,
        marginBottom: 28
      }}>
        {/* Search */}
        <div style={{ position: 'relative', minWidth: 280, flex: 1, maxWidth: 450 }}>
          <Search size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
          <input
            type="text"
            className="input-field"
            placeholder="Search roles, departments, or skills (e.g. AWS, React, Python)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 42 }}
          />
        </div>

        {/* Dept Pills */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {departments.map((dept) => {
            const isSelected = selectedDept === dept;
            return (
              <button
                key={dept}
                onClick={() => setSelectedDept(dept)}
                style={{
                  padding: '5px 12px',
                  borderRadius: 9999,
                  border: '1px solid',
                  borderColor: isSelected ? 'var(--primary)' : 'var(--border-subtle)',
                  background: isSelected ? 'var(--primary)' : '#ffffff',
                  color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  fontSize: '0.8rem',
                  fontWeight: isSelected ? 600 : 500,
                  cursor: 'pointer',
                  boxShadow: 'var(--shadow-xs)',
                  transition: 'all 0.15s ease'
                }}
              >
                {dept}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sticky Bottom Comparison Bar if any selected */}
      {compareRoleIds.length > 0 && (
        <div style={{
          position: 'sticky',
          top: 'calc(var(--header-height) + 12px)',
          zIndex: 30,
          background: '#ffffff',
          border: '1px solid var(--accent-blue)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 20px',
          marginBottom: 20,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: 'var(--shadow-lg)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Scale size={18} color="var(--accent-blue)" />
            <span style={{ fontSize: '0.86rem', color: 'var(--text-main)', fontWeight: 600 }}>
              {compareRoleIds.length} Role{compareRoleIds.length > 1 ? 's' : ''} Selected for Side-by-Side Comparison
            </span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              (Select 2 to 4 roles)
            </span>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => setCompareRoleIds([])}
              className="btn btn-secondary"
              style={{ fontSize: '0.78rem', padding: '5px 12px' }}
            >
              Clear
            </button>
            <button
              onClick={handleOpenComparison}
              disabled={isComparing || compareRoleIds.length < 2}
              className="btn btn-primary"
              style={{ fontSize: '0.8rem', padding: '6px 16px' }}
            >
              {isComparing ? <Loader2 size={14} className="animate-spin" /> : <Scale size={14} />}
              Compare Roles
            </button>
          </div>
        </div>
      )}

      {/* Roles Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
        gap: 18
      }}>
        {filteredRoles.map((role) => {
          const isCurrentTarget = role.role_id === targetRoleId;
          const isCompared = compareRoleIds.includes(role.role_id);
          const isSettingThis = settingTargetId === role.role_id;

          return (
            <div
              key={role.role_id}
              className="saas-card"
              style={{
                padding: 22,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                borderColor: isCurrentTarget ? 'var(--accent-blue)' : isCompared ? 'var(--accent-indigo)' : undefined,
                background: isCurrentTarget ? '#eff6ff' : isCompared ? '#f8fafc' : '#ffffff',
                boxShadow: isCurrentTarget ? 'var(--shadow-md)' : undefined
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <div>
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 2 }}>{role.title}</h3>
                    <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>{role.department}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                    {isCurrentTarget && (
                      <span className="badge badge-cyan" style={{ fontSize: '0.68rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Target size={11} /> Target Role
                      </span>
                    )}
                    <span className="badge badge-emerald" style={{ fontSize: '0.66rem' }}>
                      {role.openings} Openings
                    </span>
                  </div>
                </div>

                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 14 }}>
                  {role.description}
                </p>

                <div style={{ display: 'flex', gap: 14, fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 16 }}>
                  <span>Exp: <strong style={{ color: 'var(--text-main)' }}>{role.experience_years} yrs</strong></span>
                  <span>Salary: <strong style={{ color: 'var(--text-main)' }}>{role.salary_range}</strong></span>
                </div>

                {/* Skills tags */}
                <div style={{ marginBottom: 18 }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 6, fontWeight: 600 }}>
                    Required Competencies ({role.required_skills?.length || 0})
                  </span>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {role.required_skills?.slice(0, 6).map((sk: string) => (
                      <span key={sk} className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                        {sk}
                      </span>
                    ))}
                    {(role.required_skills?.length || 0) > 6 && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', alignSelf: 'center' }}>
                        +{(role.required_skills?.length || 0) - 6} more
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', gap: 8 }}>
                  {/* Set as Target Role Button */}
                  <button
                    onClick={() => handleSetTargetRole(role)}
                    disabled={isCurrentTarget || isSettingThis}
                    className={`btn ${isCurrentTarget ? 'btn-secondary' : 'btn-primary'}`}
                    style={{ flex: 1, fontSize: '0.78rem', padding: '6px 10px' }}
                  >
                    {isSettingThis ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : isCurrentTarget ? (
                      <><Check size={13} /> Current Target</>
                    ) : (
                      <><Target size={13} /> Set as Target</>
                    )}
                  </button>

                  {/* Compare Toggle */}
                  <button
                    onClick={() => toggleRoleComparison(role.role_id)}
                    className="btn btn-secondary"
                    style={{
                      fontSize: '0.78rem',
                      padding: '6px 10px',
                      borderColor: isCompared ? 'var(--accent-blue)' : undefined,
                      color: isCompared ? 'var(--accent-blue)' : undefined,
                      background: isCompared ? '#eff6ff' : undefined
                    }}
                    title="Compare with other roles"
                  >
                    <Scale size={14} /> {isCompared ? 'Compared' : 'Compare'}
                  </button>
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => {
                      onSelectRole(role.role_id);
                      onNavigateTab('skill-gap');
                    }}
                    className="btn btn-secondary"
                    style={{ flex: 1, fontSize: '0.78rem', padding: '6px 10px' }}
                  >
                    <Sparkles size={14} /> Analyze Gap
                  </button>
                  <button
                    onClick={() => {
                      onSelectRole(role.role_id);
                      onNavigateTab('learning-path');
                    }}
                    className="btn btn-secondary"
                    style={{ flex: 1, fontSize: '0.78rem', padding: '6px 10px' }}
                  >
                    Roadmap <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Role Comparison Modal */}
      {/* Role Comparison Modal */}
      {compareModalOpen && compareData && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: 1040, padding: '26px 30px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-main)' }}>
                  <Scale size={20} color="var(--accent-blue)" /> Multi-Role Side-by-Side Comparison
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                  Personalized compatibility comparison against your authenticated skills inventory.
                </p>
              </div>
              <button
                onClick={() => setCompareModalOpen(false)}
                className="btn btn-secondary"
                style={{ padding: '6px 10px' }}
              >
                <X size={16} />
              </button>
            </div>

            {/* Comparison Grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${compareData.compared_roles.length}, 1fr)`,
              gap: 16,
              marginBottom: 20
            }}>
              {compareData.compared_roles.map((cr: any) => (
                <div
                  key={cr.role_id}
                  style={{
                    background: cr.role_id === targetRoleId ? '#eff6ff' : '#f8fafc',
                    border: cr.role_id === targetRoleId ? '1px solid var(--accent-blue)' : '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: 18,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>{cr.title}</h4>
                      {cr.role_id === targetRoleId && (
                        <span className="badge badge-cyan" style={{ fontSize: '0.62rem' }}>Target</span>
                      )}
                    </div>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: 12 }}>
                      {cr.department} • {cr.salary_range}
                    </span>

                    {/* Match Score Card */}
                    <div style={{
                      background: '#ffffff',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: 12,
                      marginBottom: 14,
                      textAlign: 'center'
                    }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 2, fontWeight: 600 }}>
                        Compatibility Score
                      </span>
                      <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
                        {cr.match_score}%
                      </div>
                      <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>
                        {cr.mobility_status}
                      </span>
                    </div>

                    {/* Metrics Breakdown */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.8rem', marginBottom: 14 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Coverage:</span>
                        <strong style={{ color: 'var(--text-main)' }}>{cr.coverage_percentage}%</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--accent-emerald)' }}>Fully Met Skills:</span>
                        <strong style={{ color: 'var(--accent-emerald)' }}>{cr.met_count}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--accent-amber)' }}>Partially Met:</span>
                        <strong style={{ color: 'var(--accent-amber)' }}>{cr.partially_met_count}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--accent-rose)' }}>Missing Skills:</span>
                        <strong style={{ color: 'var(--accent-rose)' }}>{cr.missing_count}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Openings:</span>
                        <strong style={{ color: 'var(--text-main)' }}>{cr.openings}</strong>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 12 }}>
                    <button
                      onClick={() => {
                        handleSetTargetRole(cr);
                        setCompareModalOpen(false);
                      }}
                      disabled={cr.role_id === targetRoleId}
                      className="btn btn-primary"
                      style={{ fontSize: '0.78rem', padding: '6px' }}
                    >
                      {cr.role_id === targetRoleId ? 'Current Target' : 'Make Target Role'}
                    </button>
                    <button
                      onClick={() => {
                        onSelectRole(cr.role_id);
                        onNavigateTab('skill-gap');
                        setCompareModalOpen(false);
                      }}
                      className="btn btn-secondary"
                      style={{ fontSize: '0.78rem', padding: '6px' }}
                    >
                      Inspect Gap
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Common Skills Insights */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div style={{
                background: '#f8fafc',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: 14
              }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
                  Common Required Competencies ({compareData.common_required_skills.length})
                </span>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {compareData.common_required_skills.length > 0 ? (
                    compareData.common_required_skills.map((sk: string) => (
                      <span key={sk} className="badge badge-purple" style={{ fontSize: '0.72rem' }}>
                        {sk}
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No overlapping skills required across all selected roles.</span>
                  )}
                </div>
              </div>

              <div style={{
                background: '#f8fafc',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: 14
              }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--accent-rose)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
                  Common Missing Competencies ({compareData.common_missing_skills.length})
                </span>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {compareData.common_missing_skills.length > 0 ? (
                    compareData.common_missing_skills.map((sk: string) => (
                      <span key={sk} className="badge badge-rose" style={{ fontSize: '0.72rem' }}>
                        {sk}
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No common missing competencies across these roles.</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
