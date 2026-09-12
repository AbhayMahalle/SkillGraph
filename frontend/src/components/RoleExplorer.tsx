import React, { useState } from 'react';
import { Search, Target, Briefcase, ChevronRight, Sparkles } from 'lucide-react';

interface RoleExplorerProps {
  roles: any[];
  onSelectRole: (roleId: string) => void;
  onNavigateTab: (tab: string) => void;
  targetRoleId?: string;
}

export const RoleExplorer: React.FC<RoleExplorerProps> = ({
  roles,
  onSelectRole,
  onNavigateTab,
  targetRoleId
}) => {
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('All');

  const departments = ['All', 'Engineering', 'Infrastructure', 'Data Science', 'AI Engineering', 'Information Security'];

  const filteredRoles = roles.filter((r) => {
    const matchesSearch = 
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.department.toLowerCase().includes(search.toLowerCase()) ||
      r.required_skills?.some((sk: string) => sk.toLowerCase().includes(search.toLowerCase()));

    const matchesDept = selectedDept === 'All' || r.department === selectedDept;
    return matchesSearch && matchesDept;
  });

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: '2rem', marginBottom: 6 }}>Organizational Role Architecture</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Explore canonical enterprise roles, required competencies, salary bands, and open headcount requisitions.
        </p>
      </div>

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
            placeholder="Search roles, departments, or skills (e.g. AWS, React)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 42 }}
          />
        </div>

        {/* Dept Pills */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {departments.map((dept) => (
            <button
              key={dept}
              onClick={() => setSelectedDept(dept)}
              style={{
                padding: '6px 14px',
                borderRadius: 9999,
                border: '1px solid',
                borderColor: selectedDept === dept ? 'var(--accent-indigo)' : 'var(--border-subtle)',
                background: selectedDept === dept ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                color: selectedDept === dept ? '#818cf8' : 'var(--text-muted)',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {dept}
            </button>
          ))}
        </div>
      </div>

      {/* Roles Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
        gap: 22
      }}>
        {filteredRoles.map((role) => {
          const isCurrentTarget = role.role_id === targetRoleId;
          return (
            <div
              key={role.role_id}
              className="glass-panel"
              style={{
                padding: 24,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                borderColor: isCurrentTarget ? 'rgba(99, 102, 241, 0.5)' : undefined,
                background: isCurrentTarget ? 'rgba(30, 41, 65, 0.85)' : undefined
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <div>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: 2 }}>{role.title}</h3>
                    <span style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>{role.department}</span>
                  </div>
                  {isCurrentTarget ? (
                    <span className="badge badge-cyan" style={{ fontSize: '0.68rem' }}>Target Role</span>
                  ) : (
                    <span className="badge badge-emerald" style={{ fontSize: '0.68rem' }}>
                      {role.openings} Openings
                    </span>
                  )}
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 14 }}>
                  {role.description}
                </p>

                <div style={{ display: 'flex', gap: 14, fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: 16 }}>
                  <span>Exp: <strong style={{ color: '#fff' }}>{role.experience_years} yrs</strong></span>
                  <span>Salary: <strong style={{ color: '#fff' }}>{role.salary_range}</strong></span>
                </div>

                {/* Skills tags */}
                <div style={{ marginBottom: 20 }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: 6 }}>
                    Required Competencies ({role.required_skills?.length || 0})
                  </span>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {role.required_skills?.slice(0, 6).map((sk: string) => (
                      <span key={sk} className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
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
              <div style={{ display: 'flex', gap: 10, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
                <button
                  onClick={() => {
                    onSelectRole(role.role_id);
                    onNavigateTab('skill-gap');
                  }}
                  className="btn btn-secondary"
                  style={{ flex: 1, fontSize: '0.82rem' }}
                >
                  <Sparkles size={14} /> Analyze Gap
                </button>
                <button
                  onClick={() => {
                    onSelectRole(role.role_id);
                    onNavigateTab('learning-path');
                  }}
                  className="btn btn-primary"
                  style={{ flex: 1, fontSize: '0.82rem' }}
                >
                  Roadmap <ChevronRight size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
