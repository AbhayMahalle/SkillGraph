import React from 'react';
import { 
  Network, ArrowRight, ShieldCheck, Cpu, 
  GitBranch, Sparkles, BarChart3, Database, CheckCircle2 
} from 'lucide-react';

interface LandingViewProps {
  onEnterEmployee: () => void;
  onEnterHR: () => void;
}

export const LandingView: React.FC<LandingViewProps> = ({ onEnterEmployee, onEnterHR }) => {
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
          background: 'rgba(99, 102, 241, 0.12)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          color: '#818cf8',
          fontSize: '0.85rem',
          fontWeight: 600,
          marginBottom: 20
        }}>
          <Sparkles size={16} /> Authentic Kaggle & O*NET 29.0 Data-Backed Talent Intelligence
        </div>

        <h1 style={{
          fontSize: '3.4rem',
          lineHeight: 1.15,
          fontWeight: 800,
          marginBottom: 20,
          letterSpacing: '-0.03em'
        }}>
          Transform Internal Mobility with <br />
          <span className="text-gradient">Predictive Skill Graph Intelligence</span>
        </h1>

        <p style={{
          fontSize: '1.2rem',
          color: 'var(--text-muted)',
          maxWidth: 780,
          margin: '0 auto 36px',
          lineHeight: 1.6
        }}>
          Beyond basic skill-tagging: Discover internal transition pathways, calculate prerequisite-aware
          learning roadmaps, simulate future readiness, and solve organizational headcount gaps.
        </p>

        {/* Dual Launch CTA */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, flexWrap: 'wrap' }}>
          <button 
            onClick={onEnterEmployee}
            className="btn btn-primary"
            style={{ padding: '14px 28px', fontSize: '1.05rem', borderRadius: 'var(--radius-lg)' }}
          >
            Launch Employee Mobility Portal <ArrowRight size={18} />
          </button>
          <button 
            onClick={onEnterHR}
            className="btn btn-cyan"
            style={{ padding: '14px 28px', fontSize: '1.05rem', borderRadius: 'var(--radius-lg)' }}
          >
            Launch HR Workforce Planning <BarChart3 size={18} />
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
        <div className="glass-panel" style={{ padding: 28 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'rgba(6, 182, 212, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-cyan)',
            marginBottom: 20
          }}>
            <Cpu size={24} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 10 }}>Multi-Factor Role Matching</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: 1.6 }}>
            Blends weighted skill coverage, proficiency level decay, and experience deltas to accurately rank realistic internal roles.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: 28 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'rgba(99, 102, 241, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-indigo)',
            marginBottom: 20
          }}>
            <GitBranch size={24} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 10 }}>Topological Learning DAGs</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: 1.6 }}>
            Prerequisite-aware course ordering ensures foundational skills (Linux, SQL) are mastered before advanced technologies (K8s, MLOps).
          </p>
        </div>

        <div className="glass-panel" style={{ padding: 28 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-emerald)',
            marginBottom: 20
          }}>
            <Sparkles size={24} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 10 }}>What-If Simulation Sandbox</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: 1.6 }}>
            Interactive scenario modeling where employees toggle prospective courses and watch transition feasibility recalculate in real-time.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: 28 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'rgba(139, 92, 246, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-purple)',
            marginBottom: 20
          }}>
            <Network size={24} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 10 }}>Knowledge Graph & Neo4j</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: 1.6 }}>
            2D canvas graph visualizer connecting Employees, Skills, Roles, and Courses with built-in Cypher script export for Neo4j deployment.
          </p>
        </div>
      </div>

      {/* Dataset Verification Proof */}
      <div className="glass-panel" style={{ padding: 32, borderColor: 'rgba(99, 102, 241, 0.3)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <span className="badge badge-emerald" style={{ marginBottom: 8 }}>Verified Datasets</span>
            <h3 style={{ fontSize: '1.4rem' }}>Built on 4 Authentic Organizational Data Sources</h3>
          </div>
          <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Zero synthetic mocking required</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 16, borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#38bdf8', fontWeight: 600, marginBottom: 4 }}>
              <CheckCircle2 size={16} /> Job Skill Set Dataset
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>1,167 real job postings across IT, Finance, Sales, HR with extracted skill requirements.</p>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 16, borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#38bdf8', fontWeight: 600, marginBottom: 4 }}>
              <CheckCircle2 size={16} /> Resume Dataset & Roles
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>324 canonical role definitions with experience thresholds and salary benchmarks.</p>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 16, borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#38bdf8', fontWeight: 600, marginBottom: 4 }}>
              <CheckCircle2 size={16} /> Candidate-Job Role
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>1,000 empirical employee records training the transition readiness ML classifier.</p>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: 16, borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#38bdf8', fontWeight: 600, marginBottom: 4 }}>
              <CheckCircle2 size={16} /> O*NET 29.0 Database
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>US Dept. of Labor standard taxonomy with 1,016 occupational profiles and tech skills.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
