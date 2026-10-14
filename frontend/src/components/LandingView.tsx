import React from 'react';
import { 
  Network, ArrowRight, Cpu, 
  GitBranch, Sparkles, CheckCircle2 
} from 'lucide-react';

interface LandingViewProps {
  onEnterCareerHub: () => void;
}

export const LandingView: React.FC<LandingViewProps> = ({ onEnterCareerHub }) => {
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '40px 20px 80px' }}>
      {/* Hero Section */}
      <div style={{ textAlign: 'center', marginBottom: 60 }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 16px',
          borderRadius: 9999,
          background: '#eef2ff',
          border: '1px solid #c7d2fe',
          color: '#4338ca',
          fontSize: '0.85rem',
          fontWeight: 600,
          marginBottom: 20
        }}>
          <Sparkles size={16} /> Authentic Kaggle & O*NET 29.0 Data-Backed Talent Intelligence
        </div>

        <h1 style={{
          fontSize: '3.2rem',
          lineHeight: 1.15,
          fontWeight: 800,
          marginBottom: 20,
          color: 'var(--text-main)',
          letterSpacing: '-0.03em'
        }}>
          Accelerate Your Career Transition with <br />
          <span style={{ color: '#4f46e5' }}>Predictive Skill Graph Intelligence</span>
        </h1>

        <p style={{
          fontSize: '1.15rem',
          color: 'var(--text-muted)',
          maxWidth: 780,
          margin: '0 auto 36px',
          lineHeight: 1.6
        }}>
          An AI-driven, self-service platform for individual career development: Discover internal transition
          pathways, analyze skill gaps against target roles, follow prerequisite-aware learning roadmaps,
          and simulate future readiness.
        </p>

        {/* Focused Self-Service CTA */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16 }}>
          <button 
            onClick={onEnterCareerHub}
            className="btn btn-primary"
            style={{ padding: '12px 28px', fontSize: '1rem', borderRadius: 'var(--radius-md)' }}
          >
            Explore Career Pathways <ArrowRight size={18} />
          </button>
        </div>
      </div>

      {/* Core Architectural Pillars */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: 24,
        marginBottom: 60
      }}>
        <div className="saas-card" style={{ padding: 28 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: '#e0f2fe',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#0284c7',
            marginBottom: 18
          }}>
            <Cpu size={22} />
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 8 }}>Multi-Factor Role Matching</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', lineHeight: 1.6 }}>
            Blends weighted skill coverage, proficiency level evaluation, and experience thresholds to accurately identify reachable career pathways.
          </p>
        </div>

        <div className="saas-card" style={{ padding: 28 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: '#eef2ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#4f46e5',
            marginBottom: 18
          }}>
            <GitBranch size={22} />
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 8 }}>Topological Learning DAGs</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', lineHeight: 1.6 }}>
            Prerequisite-aware course ordering ensures foundational skills (Linux, SQL) are mastered before advanced dependencies (Kubernetes, MLOps).
          </p>
        </div>

        <div className="saas-card" style={{ padding: 28 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: '#ecfdf5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#059669',
            marginBottom: 18
          }}>
            <Sparkles size={22} />
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 8 }}>Career Sandbox Simulation</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', lineHeight: 1.6 }}>
            Interactive scenario modeling where you toggle prospective courses and watch skill match and transition feasibility update in real time.
          </p>
        </div>

        <div className="saas-card" style={{ padding: 28 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: '#f5f3ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#7c3aed',
            marginBottom: 18
          }}>
            <Network size={22} />
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: 8 }}>2D Interactive SkillGraph</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', lineHeight: 1.6 }}>
            Interactive network canvas mapping relationships between skills, roles, prerequisite courses, and career transitions.
          </p>
        </div>
      </div>

      {/* Dataset Verification Proof */}
      <div className="saas-card" style={{ padding: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <span className="badge badge-emerald" style={{ marginBottom: 8 }}>Verified Datasets</span>
            <h3 style={{ fontSize: '1.3rem', fontWeight: 600, color: 'var(--text-main)' }}>Built on 4 Authentic Organizational Data Sources</h3>
          </div>
          <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Empirically grounded talent intelligence</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
          <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', padding: 16, borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#0284c7', fontWeight: 600, marginBottom: 4 }}>
              <CheckCircle2 size={16} /> Job Skill Set Dataset
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>1,167 real job postings with empirical skill distributions and descriptions.</p>
          </div>

          <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', padding: 16, borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#0284c7', fontWeight: 600, marginBottom: 4 }}>
              <CheckCircle2 size={16} /> Resume Dataset & Roles
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>324 canonical role profiles with experience thresholds and salary benchmarks.</p>
          </div>

          <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', padding: 16, borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#0284c7', fontWeight: 600, marginBottom: 4 }}>
              <CheckCircle2 size={16} /> Candidate-Job Role
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>1,000 employee profile records mapping skill sets and career transitions.</p>
          </div>

          <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', padding: 16, borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#0284c7', fontWeight: 600, marginBottom: 4 }}>
              <CheckCircle2 size={16} /> O*NET 29.0 Database
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>US Dept. of Labor taxonomy providing 1,016 occupational definitions and tech skills.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
