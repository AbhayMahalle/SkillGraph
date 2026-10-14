import React from 'react';
import { 
  Network, Compass, Target, GraduationCap, 
  Sparkles, Database, LogOut, UserCheck, 
  LogIn, UserPlus, Shield
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentUser: any;
  onLogout: () => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onLogout,
  onOpenAuth
}) => {
  // Navigation tabs for authenticated users
  const authNavItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Compass },
    { id: 'profile', label: 'My Skills & Security', icon: UserCheck },
    { id: 'roles', label: 'Role Explorer', icon: Target },
    { id: 'skill-gap', label: 'Skill Gap & Readiness', icon: Sparkles },
    { id: 'learning-path', label: 'Learning Roadmap', icon: GraduationCap },
    { id: 'simulator', label: 'Career Sandbox', icon: Sparkles },
    { id: 'graph', label: 'SkillGraph 2D', icon: Network },
    { id: 'datasets', label: 'Dataset Lineage', icon: Database },
  ];

  // Navigation tabs for unauthenticated public visitors
  const publicNavItems = [
    { id: 'landing', label: 'Platform Vision', icon: Compass },
    { id: 'roles', label: 'Role Explorer', icon: Target },
    { id: 'graph', label: 'SkillGraph 2D', icon: Network },
    { id: 'datasets', label: 'Dataset Lineage', icon: Database },
  ];

  const currentNavItems = currentUser ? authNavItems : publicNavItems;

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      background: 'rgba(10, 13, 20, 0.88)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
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
            <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Self-Service Career Intelligence</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 4, overflowX: 'auto' }}>
          {currentNavItems.map((item) => {
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

        {/* Authentication State and Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {currentUser ? (
            <>
              {/* Authenticated User Badge & Profile shortcut */}
              <div 
                onClick={() => setActiveTab('profile')}
                style={{
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '6px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  cursor: 'pointer',
                  transition: 'background 0.2s ease'
                }}
                title="View and edit your personal profile"
              >
                <div style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #06b6d4, #6366f1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  color: '#ffffff'
                }}>
                  {currentUser?.full_name?.charAt(0) || 'U'}
                </div>
                <div style={{ lineHeight: 1.2 }}>
                  <p style={{ fontSize: '0.82rem', fontWeight: 600, color: '#fff' }}>
                    {currentUser?.full_name}
                  </p>
                  <span className="badge badge-emerald" style={{ fontSize: '0.62rem', padding: '1px 5px' }}>
                    Personal Profile
                  </span>
                </div>
              </div>

              {/* Sign Out Button */}
              <button
                onClick={onLogout}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '7px 12px',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: '0.82rem',
                  fontWeight: 500,
                  transition: 'all 0.2s ease'
                }}
                title="Sign out of current account"
              >
                <LogOut size={16} />
                <span>Sign Out</span>
              </button>
            </>
          ) : (
            <>
              {/* Unauthenticated Actions */}
              <button
                onClick={() => onOpenAuth('login')}
                className="btn btn-secondary"
                style={{ fontSize: '0.85rem', padding: '8px 14px', gap: 6 }}
              >
                <LogIn size={16} />
                <span>Sign In</span>
              </button>
              <button
                onClick={() => onOpenAuth('register')}
                className="btn btn-primary"
                style={{ fontSize: '0.85rem', padding: '8px 16px', gap: 6 }}
              >
                <UserPlus size={16} />
                <span>Register</span>
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
