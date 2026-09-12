import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingView } from './components/LandingView';
import { EmployeeDashboard } from './components/EmployeeDashboard';
import { ProfileView } from './components/ProfileView';
import { RoleExplorer } from './components/RoleExplorer';
import { SkillGapView } from './components/SkillGapView';
import { LearningPathView } from './components/LearningPathView';
import { WhatIfSimulator } from './components/WhatIfSimulator';
import { SkillGraphVisualizer } from './components/SkillGraphVisualizer';
import { HRDashboard } from './components/HRDashboard';
import { DatasetsExplorer } from './components/DatasetsExplorer';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [allRoles, setAllRoles] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string>('ROL-001');
  const [loading, setLoading] = useState<boolean>(true);

  // Auto-login with Demo Employee on initial mount if not logged in
  const performDemoLogin = async (role = 'EMPLOYEE') => {
    setLoading(true);
    try {
      const res = await fetch('/api/auth/demo-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role })
      });
      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        setCurrentUser(data.user);
        await loadUserData(data.access_token);
      }
    } catch (err) {
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadUserData = async (token: string) => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };

      // 1. Roles list
      const rolesRes = await fetch('/api/roles');
      const rolesData = await rolesRes.json();
      setAllRoles(rolesData);

      // 2. Profile
      const profileRes = await fetch('/api/employees/profile', { headers });
      if (profileRes.ok) {
        const pData = await profileRes.json();
        setProfile(pData);
        if (pData.target_role_id) {
          setSelectedRoleId(pData.target_role_id);
        }
      }

      // 3. Recommendations
      const recRes = await fetch('/api/roles/recommendations', { headers });
      if (recRes.ok) {
        const rData = await recRes.json();
        setRecommendations(rData);
      }
    } catch (err) {
      console.error('Error loading data:', err);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetch('/api/auth/me', { headers: { 'Authorization': `Bearer ${token}` } })
        .then(res => {
          if (res.ok) return res.json();
          throw new Error('Token expired');
        })
        .then(user => {
          setCurrentUser(user);
          loadUserData(token).then(() => setLoading(false));
        })
        .catch(() => {
          performDemoLogin('EMPLOYEE');
        });
    } else {
      performDemoLogin('EMPLOYEE');
    }
  }, []);

  const handleSwitchUser = (newRole: string) => {
    performDemoLogin(newRole).then(() => {
      setActiveTab(newRole === 'HR' ? 'hr-dashboard' : 'dashboard');
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    performDemoLogin('EMPLOYEE').then(() => {
      setActiveTab('landing');
    });
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8' }}>
        <p style={{ fontFamily: 'Outfit', fontSize: '1.2rem', fontWeight: 600 }}>Initializing SkillGraph Platform...</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        onLogout={handleLogout}
        onSwitchUser={handleSwitchUser}
      />

      <main style={{ flex: 1 }}>
        {activeTab === 'landing' && (
          <LandingView
            onEnterEmployee={() => setActiveTab('dashboard')}
            onEnterHR={() => {
              handleSwitchUser('HR');
              setActiveTab('hr-dashboard');
            }}
          />
        )}

        {activeTab === 'dashboard' && (
          <EmployeeDashboard
            profile={profile}
            recommendations={recommendations}
            onSelectRole={(rid) => setSelectedRoleId(rid)}
            onNavigateTab={(tab) => setActiveTab(tab)}
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
            onSelectRole={(rid) => setSelectedRoleId(rid)}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'skill-gap' && (
          <SkillGapView
            roleId={selectedRoleId}
            allRoles={allRoles}
            onSelectRole={(rid) => setSelectedRoleId(rid)}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'learning-path' && (
          <LearningPathView
            roleId={selectedRoleId}
            allRoles={allRoles}
            onSelectRole={(rid) => setSelectedRoleId(rid)}
            onNavigateTab={(tab) => setActiveTab(tab)}
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

        {activeTab === 'hr-dashboard' && (
          <HRDashboard />
        )}

        {activeTab === 'datasets' && (
          <DatasetsExplorer />
        )}
      </main>

      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        padding: '24px',
        textAlign: 'center',
        fontSize: '0.82rem',
        color: 'var(--text-dim)',
        background: 'rgba(5, 8, 15, 0.8)'
      }}>
        SkillGraph — Predictive Internal Career Mobility & Workforce Planning System • Powered by Kaggle & O*NET 29.0
      </footer>
    </div>
  );
};
