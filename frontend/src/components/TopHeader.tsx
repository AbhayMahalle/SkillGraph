import React, { useState, useRef, useEffect } from 'react';
import { 
  Menu, Target, ChevronRight, User, 
  LogOut, Shield, ChevronDown, Sparkles
} from 'lucide-react';

interface TopHeaderProps {
  activeTab: string;
  onNavigateTab: (tab: string) => void;
  currentUser: any;
  profile: any;
  onLogout: () => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
  onOpenMobileMenu: () => void;
  sidebarCollapsed: boolean;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  activeTab,
  onNavigateTab,
  currentUser,
  profile,
  onLogout,
  onOpenAuth,
  onOpenMobileMenu,
  sidebarCollapsed
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Map active tab to human-readable breadcrumb and title
  const getTabMeta = (tab: string) => {
    switch (tab) {
      case 'dashboard':
        return { section: 'Workspace', title: 'Personal Overview' };
      case 'profile':
        return { section: 'Workspace', title: 'My Skills & Evidence' };
      case 'roles':
        return { section: 'Workspace', title: 'Career Explorer' };
      case 'skill-gap':
        return { section: 'Workspace', title: 'Skill Gap & Readiness' };
      case 'learning-path':
        return { section: 'Workspace', title: 'Learning Roadmap' };
      case 'simulator':
        return { section: 'Workspace', title: 'Career What-If Simulator' };
      case 'graph':
        return { section: 'Research', title: 'Skill Graph 2D Explorer' };
      case 'datasets':
        return { section: 'Research', title: 'Dataset Lineage & Audit' };
      case 'landing':
        return { section: 'Platform', title: 'SkillGraph Vision' };
      default:
        return { section: 'SkillGraph', title: 'Dashboard' };
    }
  };

  const meta = getTabMeta(activeTab);

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 40,
      height: 'var(--header-height)',
      background: '#ffffff',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      transition: 'left 0.2s ease'
    }}>
      {/* Left: Mobile hamburger + Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <button
          onClick={onOpenMobileMenu}
          className="btn-ghost"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 6,
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: 'transparent',
            cursor: 'pointer'
          }}
          title="Open Navigation"
        >
          <Menu size={20} color="var(--text-secondary)" />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>{meta.section}</span>
          <ChevronRight size={14} color="var(--text-dim)" />
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{meta.title}</span>
        </div>
      </div>

      {/* Right: Target Role quick indicator & User Menu */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Target role indicator if set */}
        {profile?.target_role_title && (
          <div 
            onClick={() => onNavigateTab('skill-gap')}
            style={{
              display: 'none', // Shown on md+ screens via inline check or style
              alignItems: 'center',
              gap: 8,
              padding: '4px 12px',
              borderRadius: 'var(--radius-md)',
              background: '#f8fafc',
              border: '1px solid var(--border-subtle)',
              cursor: 'pointer',
              fontSize: '0.82rem'
            }}
            title="Click to view skill gap analysis for your active target role"
          >
            <Target size={14} color="var(--accent-blue)" />
            <span style={{ color: 'var(--text-muted)' }}>Target:</span>
            <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{profile.target_role_title}</span>
          </div>
        )}

        {currentUser ? (
          /* User dropdown menu */
          <div style={{ position: 'relative' }} ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '4px 8px',
                borderRadius: 'var(--radius-md)',
                background: dropdownOpen ? '#f1f5f9' : 'transparent',
                border: '1px solid transparent',
                cursor: 'pointer'
              }}
            >
              <div style={{
                width: 30,
                height: 30,
                borderRadius: '50%',
                background: 'var(--primary)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 600,
                fontSize: '0.82rem'
              }}>
                {currentUser.full_name?.charAt(0) || 'U'}
              </div>
              <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-main)' }}>
                {currentUser.full_name}
              </span>
              <ChevronDown size={14} color="var(--text-muted)" />
            </button>

            {dropdownOpen && (
              <div style={{
                position: 'absolute',
                top: 'calc(100% + 6px)',
                right: 0,
                width: 220,
                background: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                padding: '6px',
                zIndex: 50
              }}>
                <div style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-subtle)', marginBottom: 4 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-main)' }}>
                    {currentUser.full_name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {currentUser.email}
                  </div>
                </div>

                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    onNavigateTab('profile');
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-sm)',
                    border: 'none',
                    background: 'transparent',
                    color: 'var(--text-secondary)',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <User size={15} color="var(--text-muted)" />
                  <span>My Profile & Skills</span>
                </button>

                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    onNavigateTab('skill-gap');
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-sm)',
                    border: 'none',
                    background: 'transparent',
                    color: 'var(--text-secondary)',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <Target size={15} color="var(--text-muted)" />
                  <span>Target Role Match</span>
                </button>

                <div style={{ borderTop: '1px solid var(--border-subtle)', margin: '4px 0' }} />

                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    onLogout();
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    width: '100%',
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-sm)',
                    border: 'none',
                    background: 'transparent',
                    color: 'var(--accent-rose)',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#fff1f2'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <LogOut size={15} />
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              onClick={() => onOpenAuth('login')}
              className="btn btn-secondary"
              style={{ fontSize: '0.82rem', padding: '6px 12px' }}
            >
              Sign In
            </button>
            <button
              onClick={() => onOpenAuth('register')}
              className="btn btn-primary"
              style={{ fontSize: '0.82rem', padding: '6px 14px' }}
            >
              Register
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
