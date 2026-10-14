import React from 'react';
import { 
  LayoutDashboard, UserCheck, Compass, Target, 
  GraduationCap, Sparkles, Network, Database, 
  ChevronLeft, ChevronRight, LogOut, LogIn, 
  UserPlus, User, X, Home
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentUser: any;
  onLogout: () => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onLogout,
  onOpenAuth,
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile
}) => {
  // Main Career & Skill Navigation
  const mainNavItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard, authRequired: true },
    { id: 'profile', label: 'My Skills', icon: UserCheck, authRequired: true },
    { id: 'roles', label: 'Career Explorer', icon: Compass, authRequired: false },
    { id: 'skill-gap', label: 'Skill Gap Analysis', icon: Target, authRequired: true },
    { id: 'learning-path', label: 'Learning Roadmap', icon: GraduationCap, authRequired: true },
    { id: 'simulator', label: 'Career Simulator', icon: Sparkles, authRequired: true },
  ];

  // Research & Analytics Navigation
  const researchNavItems = [
    { id: 'graph', label: 'Skill Graph 2D', icon: Network, authRequired: false },
    { id: 'datasets', label: 'Dataset Lineage', icon: Database, authRequired: false },
  ];

  const handleNavClick = (tabId: string, authRequired: boolean) => {
    if (authRequired && !currentUser) {
      onOpenAuth('login');
    } else {
      setActiveTab(tabId);
    }
    if (mobileOpen) {
      onCloseMobile();
    }
  };

  const renderNavGroup = (title: string, items: typeof mainNavItems) => (
    <div style={{ marginBottom: 20 }}>
      {!collapsed && (
        <div style={{
          fontSize: '0.7rem',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: 'var(--text-dim)',
          padding: '0 12px',
          marginBottom: 6
        }}>
          {title}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id, item.authRequired)}
              title={collapsed ? item.label : undefined}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                width: '100%',
                padding: collapsed ? '10px 0' : '9px 12px',
                justifyContent: collapsed ? 'center' : 'flex-start',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                background: isActive ? '#f1f5f9' : 'transparent',
                color: isActive ? 'var(--text-main)' : 'var(--text-secondary)',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                position: 'relative',
                textAlign: 'left'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = '#f8fafc';
                  e.currentTarget.style.color = 'var(--text-main)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
            >
              {isActive && (
                <div style={{
                  position: 'absolute',
                  left: 0,
                  top: '15%',
                  bottom: '15%',
                  width: 3,
                  background: 'var(--primary)',
                  borderRadius: '0 2px 2px 0'
                }} />
              )}
              <Icon 
                size={18} 
                color={isActive ? 'var(--primary)' : 'var(--text-muted)'} 
                strokeWidth={isActive ? 2.2 : 1.8}
              />
              {!collapsed && (
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.label}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div 
          onClick={onCloseMobile}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.4)',
            backdropFilter: 'blur(2px)',
            zIndex: 90,
            transition: 'opacity 0.2s ease'
          }}
        />
      )}

      {/* Sidebar Container */}
      <aside 
        className={`sidebar-shell ${mobileOpen ? 'mobile-open' : ''}`}
        style={{
          width: collapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
        }}
      >
        {/* Brand / Logo Area */}
        <div style={{
          height: 'var(--header-height)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          padding: collapsed ? '0' : '0 16px',
          borderBottom: '1px solid var(--border-subtle)'
        }}>
          <div 
            onClick={() => {
              setActiveTab(currentUser ? 'dashboard' : 'landing');
              if (mobileOpen) onCloseMobile();
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              cursor: 'pointer',
              userSelect: 'none'
            }}
          >
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-md)',
              background: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: 'var(--shadow-xs)'
            }}>
              <Network size={18} strokeWidth={2.2} />
            </div>
            {!collapsed && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{
                  fontWeight: 700,
                  fontSize: '1rem',
                  letterSpacing: '-0.02em',
                  color: 'var(--text-main)'
                }}>
                  SkillGraph
                </span>
                <span style={{
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  padding: '1px 5px',
                  borderRadius: 4,
                  background: 'var(--bg-muted)',
                  color: 'var(--text-muted)'
                }}>
                  SaaS
                </span>
              </div>
            )}
          </div>

          {/* Mobile close button */}
          {mobileOpen && (
            <button
              onClick={onCloseMobile}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: 4
              }}
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Scrollable Navigation Body */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: collapsed ? '16px 8px' : '16px 12px'
        }}>
          {/* Landing / Product Link */}
          <div style={{ marginBottom: 16 }}>
            <button
              onClick={() => {
                setActiveTab('landing');
                if (mobileOpen) onCloseMobile();
              }}
              title={collapsed ? 'Product Vision' : undefined}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                width: '100%',
                padding: collapsed ? '9px 0' : '8px 12px',
                justifyContent: collapsed ? 'center' : 'flex-start',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                background: activeTab === 'landing' ? '#f1f5f9' : 'transparent',
                color: activeTab === 'landing' ? 'var(--text-main)' : 'var(--text-secondary)',
                fontSize: '0.85rem',
                fontWeight: activeTab === 'landing' ? 600 : 500,
                cursor: 'pointer'
              }}
            >
              <Home size={17} color={activeTab === 'landing' ? 'var(--primary)' : 'var(--text-muted)'} />
              {!collapsed && <span>Product Vision</span>}
            </button>
          </div>

          {/* Navigation Groups */}
          {renderNavGroup('Career Workspace', mainNavItems)}
          {renderNavGroup('Research & Lineage', researchNavItems)}
        </div>

        {/* Footer Account Section */}
        <div style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: collapsed ? '12px 8px' : '12px 14px',
          background: 'var(--bg-subtle)'
        }}>
          {currentUser ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div 
                onClick={() => {
                  setActiveTab('profile');
                  if (mobileOpen) onCloseMobile();
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  cursor: 'pointer',
                  padding: collapsed ? '6px 0' : '6px 8px',
                  borderRadius: 'var(--radius-md)',
                  justifyContent: collapsed ? 'center' : 'flex-start'
                }}
                title={collapsed ? `${currentUser.full_name} (${currentUser.email})` : undefined}
              >
                <div style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: 'var(--primary)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  flexShrink: 0
                }}>
                  {currentUser.full_name?.charAt(0) || 'U'}
                </div>
                {!collapsed && (
                  <div style={{ flex: 1, minWidth: 0, lineHeight: 1.25 }}>
                    <div style={{
                      fontWeight: 600,
                      fontSize: '0.84rem',
                      color: 'var(--text-main)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {currentUser.full_name}
                    </div>
                    <div style={{
                      fontSize: '0.72rem',
                      color: 'var(--text-muted)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {currentUser.email}
                    </div>
                  </div>
                )}
              </div>

              {!collapsed && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 6 }}>
                  <button
                    onClick={() => {
                      setActiveTab('profile');
                      if (mobileOpen) onCloseMobile();
                    }}
                    className="btn btn-ghost"
                    style={{ fontSize: '0.78rem', padding: '4px 8px', gap: 4 }}
                  >
                    <User size={13} /> Settings
                  </button>

                  <button
                    onClick={onLogout}
                    className="btn btn-ghost"
                    style={{ fontSize: '0.78rem', padding: '4px 8px', color: 'var(--accent-rose)', gap: 4 }}
                    title="Sign Out"
                  >
                    <LogOut size={13} /> Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                onClick={() => {
                  onOpenAuth('login');
                  if (mobileOpen) onCloseMobile();
                }}
                className="btn btn-primary"
                style={{
                  width: '100%',
                  fontSize: '0.82rem',
                  padding: collapsed ? '8px 0' : '8px 12px',
                  justifyContent: 'center'
                }}
                title={collapsed ? 'Sign In' : undefined}
              >
                <LogIn size={15} />
                {!collapsed && <span>Sign In</span>}
              </button>
              {!collapsed && (
                <button
                  onClick={() => {
                    onOpenAuth('register');
                    if (mobileOpen) onCloseMobile();
                  }}
                  className="btn btn-secondary"
                  style={{ width: '100%', fontSize: '0.82rem', padding: '7px 12px' }}
                >
                  <UserPlus size={15} /> Create Account
                </button>
              )}
            </div>
          )}

          {/* Desktop Collapse Toggle */}
          <div style={{
            display: 'flex',
            justifyContent: collapsed ? 'center' : 'flex-end',
            marginTop: 8,
            paddingTop: 6,
            borderTop: '1px solid var(--border-subtle)'
          }}>
            <button
              onClick={onToggleCollapse}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-dim)',
                cursor: 'pointer',
                padding: 4,
                borderRadius: 4,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: '0.72rem'
              }}
              title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            >
              {collapsed ? <ChevronRight size={16} /> : (
                <>
                  <ChevronLeft size={14} />
                  <span>Collapse</span>
                </>
              )}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
