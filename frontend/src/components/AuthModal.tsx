import React, { useState } from 'react';
import { 
  Network, Lock, Mail, User as UserIcon, 
  Briefcase, Building2, X, AlertCircle, 
  CheckCircle2, ArrowRight, Loader2
} from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (token: string, user: any) => void;
  initialMode?: 'login' | 'register';
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onAuthSuccess,
  initialMode = 'login'
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);

  // Sync mode whenever initialMode or isOpen changes
  React.useEffect(() => {
    setMode(initialMode);
    setErrorMessage('');
    setSuccessMessage('');
  }, [initialMode, isOpen]);
  
  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  
  // Register form state
  const [regFullName, setRegFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regDepartment, setRegDepartment] = useState('Engineering');
  const [regCurrentRole, setRegCurrentRole] = useState('Software Engineer');

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  if (!isOpen) return null;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!loginEmail.trim() || !loginPassword) {
      setErrorMessage('Please enter both your email address and password.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: loginEmail.trim().toLowerCase(),
          password: loginPassword
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Invalid email or password.');
      }

      setSuccessMessage('Authentication successful! Loading profile...');
      setTimeout(() => {
        onAuthSuccess(data.access_token, data.user);
        onClose();
      }, 400);
    } catch (err: any) {
      setErrorMessage(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!regFullName.trim()) {
      setErrorMessage('Please enter your full name.');
      return;
    }
    if (!regEmail.trim() || !regEmail.includes('@') || !regEmail.includes('.')) {
      setErrorMessage('Please enter a valid work email address.');
      return;
    }
    if (regPassword.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: regFullName.trim(),
          email: regEmail.trim().toLowerCase(),
          password: regPassword,
          department: regDepartment,
          current_role: regCurrentRole
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Registration failed. Email may already be in use.');
      }

      setSuccessMessage('Account and personal profile created successfully!');
      setTimeout(() => {
        onAuthSuccess(data.access_token, data.user);
        onClose();
      }, 500);
    } catch (err: any) {
      setErrorMessage(err.message || 'Could not complete registration.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div 
        className="modal-content"
        style={{
          maxWidth: 440,
          padding: '28px 32px',
          position: 'relative'
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 18,
            right: 18,
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: 4,
            borderRadius: 'var(--radius-sm)'
          }}
          title="Close modal"
        >
          <X size={18} />
        </button>

        {/* Modal Header */}
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 'var(--radius-md)',
            background: 'var(--primary)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px',
            boxShadow: 'var(--shadow-xs)'
          }}>
            <Network size={22} strokeWidth={2.2} />
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: 4 }}>
            {mode === 'login' ? 'Sign in to SkillGraph' : 'Create your account'}
          </h2>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
            {mode === 'login' 
              ? 'Access your career roadmap and skill gap intelligence'
              : 'Start your self-service career mobility journey'}
          </p>
        </div>

        {/* Segmented Mode Switcher */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-muted)',
          borderRadius: 'var(--radius-md)',
          padding: 3,
          marginBottom: 18
        }}>
          <button
            type="button"
            onClick={() => { setMode('login'); setErrorMessage(''); }}
            style={{
              flex: 1,
              padding: '7px 12px',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              background: mode === 'login' ? '#ffffff' : 'transparent',
              color: mode === 'login' ? 'var(--text-main)' : 'var(--text-muted)',
              boxShadow: mode === 'login' ? 'var(--shadow-xs)' : 'none',
              fontSize: '0.84rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setMode('register'); setErrorMessage(''); }}
            style={{
              flex: 1,
              padding: '7px 12px',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              background: mode === 'register' ? '#ffffff' : 'transparent',
              color: mode === 'register' ? 'var(--text-main)' : 'var(--text-muted)',
              boxShadow: mode === 'register' ? 'var(--shadow-xs)' : 'none',
              fontSize: '0.84rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div style={{
            background: 'var(--accent-rose-subtle)',
            border: '1px solid var(--accent-rose-border)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            color: 'var(--accent-rose)',
            fontSize: '0.82rem'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Success Alert */}
        {successMessage && (
          <div style={{
            background: 'var(--accent-emerald-subtle)',
            border: '1px solid var(--accent-emerald-border)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            color: 'var(--accent-emerald)',
            fontSize: '0.82rem'
          }}>
            <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Form Fields */}
        {mode === 'login' ? (
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 5, fontWeight: 500 }}>
                Work Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={15} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 11 }} />
                <input
                  type="email"
                  className="input-field"
                  placeholder="alex.rivera@skillgraph.internal"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  style={{ paddingLeft: 36 }}
                  required
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 5, fontWeight: 500 }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 11 }} />
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  style={{ paddingLeft: 36 }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 6, padding: '10px' }}
            >
              {isLoading ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
              {isLoading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 500 }}>
                Full Name
              </label>
              <div style={{ position: 'relative' }}>
                <UserIcon size={15} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 10 }} />
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. Jordan Smith"
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                  style={{ paddingLeft: 36 }}
                  required
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 500 }}>
                Work Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={15} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 10 }} />
                <input
                  type="email"
                  className="input-field"
                  placeholder="jordan.smith@skillgraph.internal"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  style={{ paddingLeft: 36 }}
                  required
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 500 }}>
                Password (min 8 characters)
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 10 }} />
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  style={{ paddingLeft: 36 }}
                  required
                  minLength={8}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Department
                </label>
                <select
                  className="input-field"
                  value={regDepartment}
                  onChange={(e) => setRegDepartment(e.target.value)}
                  style={{ cursor: 'pointer' }}
                >
                  <option value="Engineering">Engineering</option>
                  <option value="Data & AI">Data & AI</option>
                  <option value="Product">Product</option>
                  <option value="Design">Design</option>
                  <option value="Cloud & Platform">Cloud & Platform</option>
                  <option value="Security">Security</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Current Role
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. Software Engineer"
                  value={regCurrentRole}
                  onChange={(e) => setRegCurrentRole(e.target.value)}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 6, padding: '10px' }}
            >
              {isLoading ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
