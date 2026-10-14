import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopHeader } from './components/TopHeader';
import { LandingView } from './components/LandingView';
import { EmployeeDashboard } from './components/EmployeeDashboard';
import { ProfileView } from './components/ProfileView';
import { RoleExplorer } from './components/RoleExplorer';
import { SkillGapView } from './components/SkillGapView';
import { LearningPathView } from './components/LearningPathView';
import { WhatIfSimulator } from './components/WhatIfSimulator';
import { SkillGraphVisualizer } from './components/SkillGraphVisualizer';
import { DatasetsExplorer } from './components/DatasetsExplorer';
import { AuthModal } from './components/AuthModal';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [allRoles, setAllRoles] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string>('ROL-001');
  const [loading, setLoading] = useState<boolean>(true);

  // Sidebar and navigation states
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    return localStorage.getItem('skillgraph_sidebar_collapsed') === 'true';
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  // Auth modal state
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  // Protected tabs requiring user authentication
  const protectedTabs = ['dashboard', 'profile', 'skill-gap', 'learning-path', 'simulator'];

  const handleToggleSidebar = () => {
    setSidebarCollapsed(prev => {
      const next = !prev;
      localStorage.setItem('skillgraph_sidebar_collapsed', String(next));
      return next;
    });
  };

  const loadUserData = async (token: string) => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };

      // 1. User profile
      const profileRes = await fetch('/api/employees/profile', { headers });
      if (profileRes.ok) {
        const pData = await profileRes.json();
        setProfile(pData);
        if (pData.target_role_id) {
          setSelectedRoleId(pData.target_role_id);
        }
      }

      // 2. Recommendations
      const recRes = await fetch('/api/roles/recommendations', { headers });
      if (recRes.ok) {
        const rData = await recRes.json();
        setRecommendations(rData);
      }
    } catch (err) {
      console.error('Error loading private user data:', err);
    }
  };

  const loadPublicRoles = async () => {
    try {
      const rolesRes = await fetch('/api/roles');
      if (rolesRes.ok) {
        const rolesData = await rolesRes.json();
        setAllRoles(rolesData);
        if (rolesData.length > 0 && !selectedRoleId) {
          setSelectedRoleId(rolesData[0].role_id);
        }
      }
    } catch (err) {
      console.error('Error loading public roles catalog:', err);
    }
  };

  // Restore session on mount if valid token exists
  useEffect(() => {
    const initializeAuth = async () => {
      setLoading(true);
      await loadPublicRoles();

      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await fetch('/api/users/me', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setCurrentUser(data);
            setActiveTab('dashboard'); // Default authenticated users to dashboard overview
            await loadUserData(token);
          } else {
            // Token expired, malformed, or invalidated
            localStorage.removeItem('token');
            setCurrentUser(null);
            setProfile(null);
          }
        } catch (err) {
          console.error('Error restoring session:', err);
          localStorage.removeItem('token');
          setCurrentUser(null);
          setProfile(null);
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const handleNavigate = (tab: string) => {
    if (protectedTabs.includes(tab) && !currentUser) {
      // User must be authenticated to view protected features
      setAuthMode('login');
      setAuthModalOpen(true);
      return;
    }
    setActiveTab(tab);
  };

  const handleAuthSuccess = async (token: string, user: any) => {
    localStorage.setItem('token', token);
    setCurrentUser(user);
    await loadUserData(token);
    setActiveTab('dashboard');
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }
    localStorage.removeItem('token');
    setCurrentUser(null);
    setProfile(null);
    setRecommendations([]);
    setActiveTab('landing');
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-app)',
        color: 'var(--text-main)',
        gap: 12
      }}>
        <div style={{
          width: 36,
          height: 36,
          border: '3px solid var(--border-subtle)',
          borderTopColor: 'var(--primary)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite'
        }} />
        <p style={{ fontSize: '0.92rem', fontWeight: 500, color: 'var(--text-muted)' }}>
          Initializing SkillGraph Platform...
        </p>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-app)' }}>
      {/* SaaS Collapsible Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={handleNavigate}
        currentUser={currentUser}
        onLogout={handleLogout}
        onOpenAuth={(mode) => {
          setAuthMode(mode);
          setAuthModalOpen(true);
        }}
        collapsed={sidebarCollapsed}
        onToggleCollapse={handleToggleSidebar}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main SaaS Content Column */}
      <div className="app-content-column" style={{
        marginLeft: sidebarCollapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
      }}>
        {/* Top Header */}
        <TopHeader
          activeTab={activeTab}
          onNavigateTab={handleNavigate}
          currentUser={currentUser}
          profile={profile}
          onLogout={handleLogout}
          onOpenAuth={(mode) => {
            setAuthMode(mode);
            setAuthModalOpen(true);
          }}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
          sidebarCollapsed={sidebarCollapsed}
        />

        {/* Dynamic Page Views */}
        <main style={{ flex: 1, paddingBottom: 40 }}>
          {activeTab === 'landing' && (
            <LandingView
              onEnterCareerHub={() => {
                if (currentUser) {
                  setActiveTab('dashboard');
                } else {
                  setAuthMode('login');
                  setAuthModalOpen(true);
                }
              }}
            />
          )}

          {activeTab === 'dashboard' && (
            <EmployeeDashboard
              profile={profile}
              recommendations={recommendations}
              onSelectRole={(rid) => setSelectedRoleId(rid)}
              onNavigateTab={handleNavigate}
            />
          )}

          {activeTab === 'profile' && (
            <ProfileView
              profile={profile}
              allRoles={allRoles}
              onRefreshProfile={() => {
                const token = localStorage.getItem('token');
                if (token) loadUserData(token);
              }}
            />
          )}

          {activeTab === 'roles' && (
            <RoleExplorer
              roles={allRoles}
              targetRoleId={profile?.target_role_id}
              currentUser={currentUser}
              onRefreshProfile={() => {
                const token = localStorage.getItem('token');
                if (token) loadUserData(token);
              }}
              onSelectRole={(rid) => setSelectedRoleId(rid)}
              onNavigateTab={handleNavigate}
            />
          )}

          {activeTab === 'skill-gap' && (
            <SkillGapView
              roleId={selectedRoleId}
              allRoles={allRoles}
              targetRoleId={profile?.target_role_id}
              currentUser={currentUser}
              onRefreshProfile={() => {
                const token = localStorage.getItem('token');
                if (token) loadUserData(token);
              }}
              onSelectRole={(rid) => setSelectedRoleId(rid)}
              onNavigateTab={handleNavigate}
            />
          )}

          {activeTab === 'learning-path' && (
            <LearningPathView
              roleId={selectedRoleId}
              allRoles={allRoles}
              onSelectRole={(rid) => setSelectedRoleId(rid)}
              onNavigateTab={handleNavigate}
            />
          )}

          {activeTab === 'simulator' && (
            <WhatIfSimulator
              initialRoleId={selectedRoleId}
              allRoles={allRoles}
            />
          )}

          {activeTab === 'graph' && (
            <SkillGraphVisualizer />
          )}

          {activeTab === 'datasets' && (
            <DatasetsExplorer />
          )}
        </main>

        <footer style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '20px 24px',
          textAlign: 'center',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          background: 'var(--bg-surface)'
        }}>
          SkillGraph — AI-Powered Self-Service Career Development & Skill Gap Intelligence • Light SaaS Edition
        </footer>
      </div>

      {/* Global Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
        initialMode={authMode}
      />
    </div>
  );
};
