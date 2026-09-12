import React from 'react';
import { 
  Network, Compass, Target, GraduationCap, 
  Sparkles, Users, Database, LogOut, UserCheck
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentUser: any;
  onLogout: () => void;
  onSwitchUser: (role: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onLogout,
  onSwitchUser
}) => {
  const isHR = currentUser?.role === 'HR';

  const employeeNav = [
    { id: 'dashboard', label: 'Dashboard', icon: Compass },
    { id: 'profile', label: 'My Skills & Resume', icon: UserCheck },
    { id: 'roles', label: 'Role Explorer', icon: Target },
    { id: 'skill-gap', label: 'Skill Gap & Readiness', icon: Sparkles },
    { id: 'learning-path', label: 'Learning Roadmap', icon: GraduationCap },
    { id: 'simulator', label: 'What-If Sandbox', icon: Sparkles },
    { id: 'graph', label: 'SkillGraph 2D', icon: Network },
  ];

  const hrNav = [
    { id: 'hr-dashboard', label: 'Workforce Overview', icon: Users },
    { id: 'roles', label: 'Role Architecture', icon: Target },
    { id: 'graph', label: 'SkillGraph 2D', icon: Network },
    { id: 'datasets', label: 'Dataset Explorer', icon: Database },
  ];

  const navItems = isHR ? hrNav : employeeNav;

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      background: 'rgba(10, 13, 20, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '0 24px'
    }}>
      <div style={{
        maxWidth: 1400,
        margin: '0 auto',
        height: 70,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 20
      }}>
        {/* Brand */}
        <div 
          onClick={() => setActiveTab('landing')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            background: 'linear-gradient(135deg, #06b6d4, #6366f1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--glow-cyan)'
          }}>
            <Network size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.03em', color: '#fff' }}>
                Skill<span style={{ color: 'var(--accent-cyan)' }}>Graph</span>
              </span>
              <span className="badge badge-cyan" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>AI Talent</span>
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Predictive Internal Mobility</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 4, overflowX: 'auto' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  background: isActive ? 'rgba(99, 102, 241, 0.18)' : 'transparent',
                  color: isActive ? '#38bdf8' : 'var(--text-muted)',
                  fontSize: '0.86rem',
                  fontWeight: isActive ? 600 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  borderBottom: isActive ? '2px solid #38bdf8' : '2px solid transparent',
                  whiteSpace: 'nowrap'
                }}
              >
                <Icon size={16} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* User Info & Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: 10
          }}>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: isHR ? 'linear-gradient(135deg, #f43f5e, #f59e0b)' : 'linear-gradient(135deg, #06b6d4, #6366f1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.85rem'
            }}>
              {currentUser?.full_name?.charAt(0) || 'U'}
            </div>
            <div style={{ lineHeight: 1.2 }}>
              <p style={{ fontSize: '0.82rem', fontWeight: 600, color: '#fff' }}>{currentUser?.full_name}</p>
              <span className={`badge ${isHR ? 'badge-amber' : 'badge-emerald'}`} style={{ fontSize: '0.62rem', padding: '1px 5px' }}>
                {currentUser?.role === 'HR' ? 'HR Director' : 'Employee'}
              </span>
            </div>
          </div>

          {/* Quick Switcher Button */}
          <button
            onClick={() => onSwitchUser(isHR ? 'EMPLOYEE' : 'HR')}
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '6px 10px' }}
            title={`Switch to ${isHR ? 'Employee view' : 'HR Admin view'}`}
          >
            Switch to {isHR ? 'Employee' : 'HR Admin'}
          </button>

          <button
            onClick={onLogout}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-dim)',
              cursor: 'pointer',
              padding: 8,
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Log out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </header>
  );
};
