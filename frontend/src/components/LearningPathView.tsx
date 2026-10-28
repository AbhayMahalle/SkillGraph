import React, { useState, useEffect } from 'react';
import { 
  GraduationCap, Clock, CheckCircle2, Circle, 
  PlayCircle, AlertCircle, Sparkles, RefreshCw, 
  ArrowRight, ShieldAlert, BookOpen, Check, Target
} from 'lucide-react';

interface PrerequisiteDetail {
  course_id: string;
  title: string;
  is_completed: boolean;
  is_in_roadmap: boolean;
}

interface Milestone {
  step_order: number;
  course_id: string;
  title: string;
  provider: string;
  duration_weeks: number;
  level: string;
  description: string;
  skills_taught: string[];
  targeted_skills: string[];
  prerequisites: string[];
  prerequisites_detail?: PrerequisiteDetail[];
  prerequisite_for: string[];
  reason: string;
  cumulative_weeks: number;
  status: 'not_started' | 'in_progress' | 'completed';
  progress_pct: number;
}

interface UnaddressedGap {
  skill_name: string;
  classification: string;
  priority: string;
  importance_weight: number;
  required_proficiency: string;
  demonstrated_proficiency: string;
  reason: string;
}

interface RoadmapData {
  target_role_id: string;
  target_role_title: string;
  target_role_department?: string;
  match_score?: number;
  coverage_percentage?: number;
  mobility_status?: string;
  total_courses: number;
  total_estimated_weeks: number;
  completed_courses_count: number;
  in_progress_courses_count: number;
  not_started_courses_count: number;
  overall_progress_pct: number;
  skills_covered: string[];
  targeted_skills_covered: string[];
  unaddressed_gaps: UnaddressedGap[];
  milestones: Milestone[];
  message?: string;
}

interface LearningPathViewProps {
  roleId: string;
  allRoles: any[];
  targetRoleId?: string;
  onSelectRole: (roleId: string) => void;
  onNavigateTab: (tab: string) => void;
  onRefreshProfile?: () => void;
}

export const LearningPathView: React.FC<LearningPathViewProps> = ({
  roleId,
  allRoles,
  onSelectRole,
  onNavigateTab,
  onRefreshProfile
}) => {
  const [roadmapData, setRoadmapData] = useState<RoadmapData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [updatingCourseId, setUpdatingCourseId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'not_started' | 'in_progress' | 'completed'>('all');

  const fetchRoadmap = async (targetId: string, isRefresh: boolean = false) => {
    if (!targetId) {
      setLoading(false);
      return;
    }

    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setErrorMessage(null);

    try {
      const token = localStorage.getItem('token');
      const url = isRefresh ? '/api/roadmap/refresh' : `/api/roadmap?role_id=${encodeURIComponent(targetId)}`;
      const options: RequestInit = {
        method: isRefresh ? 'POST' : 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      };

      if (isRefresh) {
        options.body = JSON.stringify({ target_role_id: targetId });
      }

      const res = await fetch(url, options);

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to fetch roadmap (${res.status})`);
      }

      const data: RoadmapData = await res.json();
      setRoadmapData(data);
    } catch (err: any) {
      console.error('Roadmap fetch error:', err);
      setErrorMessage(err.message || 'Error generating personalized learning roadmap.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (roleId) {
      fetchRoadmap(roleId, false);
    } else {
      setLoading(false);
    }
  }, [roleId]);

  const handleUpdateProgress = async (courseId: string, newStatus: string, progressPct?: number) => {
    setUpdatingCourseId(courseId);
    try {
      const token = localStorage.getItem('token');
      const payload: any = { status: newStatus };
      if (progressPct !== undefined) {
        payload.progress_pct = progressPct;
      } else if (newStatus === 'completed') {
        payload.progress_pct = 100;
      } else if (newStatus === 'not_started') {
        payload.progress_pct = 0;
      } else if (newStatus === 'in_progress') {
        payload.progress_pct = 50;
      }

      const res = await fetch(`/api/roadmap/courses/${encodeURIComponent(courseId)}/progress`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to update course progress.');
      }

      const result = await res.json();

      // Update state with updated milestone and roadmap summary
      setRoadmapData(prev => {
        if (!prev) return prev;
        const updatedMilestones = prev.milestones.map(m => {
          if (m.course_id === courseId) {
            return {
              ...m,
              status: result.course_status as any,
              progress_pct: result.progress_pct
            };
          }
          return m;
        });

        return {
          ...prev,
          milestones: updatedMilestones,
          overall_progress_pct: result.roadmap_summary.overall_progress_pct,
          completed_courses_count: result.roadmap_summary.completed_courses_count,
          in_progress_courses_count: result.roadmap_summary.in_progress_courses_count,
          not_started_courses_count: result.roadmap_summary.not_started_courses_count
        };
      });

      if (newStatus === 'completed' && onRefreshProfile) {
        onRefreshProfile();
      }
    } catch (err: any) {
      console.error('Course progress update failed:', err);
      setActionError(err.message || 'Error updating course progress.');
      setTimeout(() => setActionError(null), 5000);
    } finally {
      setUpdatingCourseId(null);
    }
  };

  // State: No target role selected
  if (!roleId) {
    return (
      <div style={{ maxWidth: 800, margin: '60px auto', padding: '0 20px', textAlign: 'center' }}>
        <div className="saas-card" style={{ padding: 48 }}>
          <Target size={48} style={{ color: '#0284c7', margin: '0 auto 16px' }} />
          <h2 style={{ fontSize: '1.6rem', marginBottom: 12 }}>No Target Role Selected</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: 24, fontSize: '0.95rem' }}>
            To generate a deterministic, prerequisite-aware learning roadmap, please select your desired career target role.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
            <select
              className="input-field"
              style={{ maxWidth: 260 }}
              onChange={(e) => onSelectRole(e.target.value)}
              defaultValue=""
            >
              <option value="" disabled>Choose a Target Role...</option>
              {allRoles.map((r) => (
                <option key={r.role_id} value={r.role_id}>{r.title}</option>
              ))}
            </select>
            <button className="btn btn-primary" onClick={() => onNavigateTab('roles')}>
              Explore Roles Catalog
            </button>
          </div>
        </div>
      </div>
    );
  }

  // State: Loading
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '120px 20px', color: 'var(--text-muted)' }}>
        <RefreshCw size={36} className="animate-spin" style={{ margin: '0 auto 16px', color: '#0284c7' }} />
        <h3 style={{ fontSize: '1.25rem', color: 'var(--text-main)', marginBottom: 8 }}>
          Computing Personalized Learning Roadmap...
        </h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>
          Traversing Course Prerequisite DAG, ranking skill gap priorities, and ordering curriculum milestones.
        </p>
      </div>
    );
  }

  // State: Error
  if (errorMessage) {
    return (
      <div style={{ maxWidth: 700, margin: '60px auto', padding: '0 20px' }}>
        <div className="saas-card" style={{ padding: 36, borderLeft: '4px solid #e11d48' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <AlertCircle size={28} style={{ color: '#e11d48' }} />
            <h3 style={{ fontSize: '1.2rem', color: '#e11d48', margin: 0 }}>Roadmap Generation Notice</h3>
          </div>
          <p style={{ color: 'var(--text-main)', fontSize: '0.95rem', marginBottom: 20 }}>
            {errorMessage}
          </p>
          <div style={{ display: 'flex', gap: 12 }}>
            <button className="btn btn-primary" onClick={() => fetchRoadmap(roleId, false)}>
              <RefreshCw size={15} /> Retry
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigateTab('roles')}>
              Select Another Role
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!roadmapData) return null;

  const milestones = roadmapData.milestones || [];
  const totalWeeks = roadmapData.total_estimated_weeks || 0;
  const unaddressed = roadmapData.unaddressed_gaps || [];

  const filteredMilestones = milestones.filter(m => {
    if (statusFilter === 'all') return true;
    return m.status === statusFilter;
  });

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 20px 80px' }}>
      {actionError && (
        <div style={{
          background: '#fff1f2',
          border: '1px solid #fecdd3',
          color: '#e11d48',
          padding: '12px 16px',
          borderRadius: 'var(--radius-md)',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontSize: '0.88rem'
        }}>
          <AlertCircle size={18} />
          <span>{actionError}</span>
        </div>
      )}

      {/* Top Banner & Role Selection Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 16,
        marginBottom: 24
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span className="badge badge-emerald" style={{ fontSize: '0.72rem' }}>
              Phase 5 DAG Roadmap
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              Deterministic Topological Order
            </span>
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 700, margin: 0 }}>
            Curriculum Path: {roadmapData.target_role_title}
          </h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <select
            className="input-field"
            value={roleId}
            onChange={(e) => onSelectRole(e.target.value)}
            style={{ width: 230, cursor: 'pointer' }}
          >
            {allRoles.map((r) => (
              <option key={r.role_id} value={r.role_id}>
                {r.title}
              </option>
            ))}
          </select>

          <button 
            onClick={() => fetchRoadmap(roleId, true)}
            className="btn btn-secondary"
            disabled={refreshing}
            style={{ fontSize: '0.84rem' }}
            title="Recalculate roadmap from updated skills and course catalog"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            {refreshing ? 'Refreshing...' : 'Regenerate'}
          </button>

          <button 
            onClick={() => onNavigateTab('simulator')}
            className="btn btn-primary"
            style={{ fontSize: '0.84rem' }}
          >
            <Sparkles size={14} /> Simulate
          </button>
        </div>
      </div>

      {/* Overview KPI Cards */}
      <div className="saas-card" style={{ padding: '20px 24px', marginBottom: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 18 }}>
          <div>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, margin: '0 0 4px', color: 'var(--text-main)' }}>
              Personalized Learning Plan
            </h4>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', margin: 0 }}>
              Tailored to your current skills, verified evidence, and prerequisite dependencies.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Overall Progress:
            </span>
            <span style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0284c7' }}>
              {roadmapData.overall_progress_pct}%
            </span>
          </div>
        </div>

        {/* Progress Track */}
        <div style={{
          width: '100%',
          height: 8,
          background: 'var(--border-subtle)',
          borderRadius: 4,
          overflow: 'hidden',
          marginBottom: 20
        }}>
          <div style={{
            width: `${Math.min(100, Math.max(0, roadmapData.overall_progress_pct))}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #0284c7 0%, #10b981 100%)',
            transition: 'width 0.4s ease'
          }} />
        </div>

        {/* 4 Metrics Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: 16,
          paddingTop: 14,
          borderTop: '1px solid var(--border-subtle)'
        }}>
          <div>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: 2 }}>
              Total Courses
            </span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)' }}>
              {roadmapData.total_courses}
            </strong>
          </div>

          <div>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: 2 }}>
              Estimated Duration
            </span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0284c7' }}>
              {totalWeeks} Weeks
            </strong>
          </div>

          <div>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: 2 }}>
              Completed / In Progress
            </span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 700, color: '#10b981' }}>
              {roadmapData.completed_courses_count} <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>/ {roadmapData.in_progress_courses_count}</span>
            </strong>
          </div>

          <div>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', display: 'block', marginBottom: 2 }}>
              Gaps Addressed
            </span>
            <strong style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)' }}>
              {roadmapData.targeted_skills_covered?.length || 0}
            </strong>
          </div>
        </div>
      </div>

      {/* Unaddressed Gaps Alert */}
      {unaddressed.length > 0 && (
        <div className="saas-card" style={{
          padding: '18px 22px',
          marginBottom: 28,
          borderLeft: '4px solid #f59e0b',
          background: '#fffbeb'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <ShieldAlert size={22} style={{ color: '#d97706', marginTop: 2, flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#92400e', margin: '0 0 6px' }}>
                Skills Requiring External Learning ({unaddressed.length})
              </h4>
              <p style={{ fontSize: '0.84rem', color: '#b45309', margin: '0 0 12px' }}>
                The following skills required for this role are not currently taught by courses in our catalog. Mentor-guided projects, certifications, or self-study are recommended.
              </p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {unaddressed.map((u) => (
                  <span
                    key={u.skill_name}
                    className="badge"
                    style={{
                      background: '#fef3c7',
                      color: '#92400e',
                      border: '1px solid #fde68a',
                      fontSize: '0.76rem'
                    }}
                    title={u.reason}
                  >
                    {u.skill_name} ({u.priority})
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Milestone Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setStatusFilter('all')}
            className={`btn ${statusFilter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            All Milestones ({milestones.length})
          </button>
          <button
            onClick={() => setStatusFilter('not_started')}
            className={`btn ${statusFilter === 'not_started' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            Not Started ({roadmapData.not_started_courses_count})
          </button>
          <button
            onClick={() => setStatusFilter('in_progress')}
            className={`btn ${statusFilter === 'in_progress' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            In Progress ({roadmapData.in_progress_courses_count})
          </button>
          <button
            onClick={() => setStatusFilter('completed')}
            className={`btn ${statusFilter === 'completed' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            Completed ({roadmapData.completed_courses_count})
          </button>
        </div>

        <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>
          Showing {filteredMilestones.length} of {milestones.length} courses
        </span>
      </div>

      {/* When 0 milestones needed */}
      {milestones.length === 0 && (
        <div className="saas-card" style={{ padding: 48, textAlign: 'center' }}>
          <CheckCircle2 size={48} style={{ color: '#10b981', margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '1.4rem', marginBottom: 8, color: 'var(--text-main)' }}>
            All Skill Requirements Met!
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', maxWidth: 520, margin: '0 auto 20px' }}>
            {roadmapData.message || 'You currently possess all demonstrated skills required for this career target.'}
          </p>
          <button className="btn btn-primary" onClick={() => onNavigateTab('simulator')}>
            Simulate Advanced Career Paths
          </button>
        </div>
      )}

      {/* Topological Timeline Cards */}
      {filteredMilestones.length > 0 && (
        <div style={{ position: 'relative', paddingLeft: 30 }}>
          {/* Continuous vertical timeline connector line */}
          <div style={{
            position: 'absolute',
            left: 14,
            top: 24,
            bottom: 24,
            width: 2,
            background: 'linear-gradient(180deg, #0284c7 0%, #6366f1 100%)'
          }} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {filteredMilestones.map((step) => {
              const isUpdating = updatingCourseId === step.course_id;
              const isCompleted = step.status === 'completed';
              const isInProgress = step.status === 'in_progress';

              const markerColor = isCompleted ? '#10b981' : isInProgress ? '#0284c7' : '#94a3b8';

              return (
                <div
                  key={step.course_id}
                  className="saas-card"
                  style={{
                    position: 'relative',
                    padding: '22px 24px',
                    borderLeft: `4px solid ${markerColor}`,
                    transition: 'all 0.2s ease'
                  }}
                >
                  {/* Timeline Node Marker */}
                  <div style={{
                    position: 'absolute',
                    left: -32,
                    top: 24,
                    width: 18,
                    height: 18,
                    borderRadius: '50%',
                    background: markerColor,
                    border: '3px solid #ffffff',
                    boxShadow: `0 0 0 2px ${markerColor}`
                  }} />

                  {/* Header row */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    flexWrap: 'wrap',
                    gap: 12,
                    marginBottom: 10
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <span className="badge badge-cyan" style={{ fontSize: '0.68rem', fontWeight: 600 }}>
                          Step {step.step_order}
                        </span>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                          {step.provider}
                        </span>
                        <span className={`badge ${
                          isCompleted ? 'badge-emerald' : isInProgress ? 'badge-purple' : 'badge-amber'
                        }`} style={{ fontSize: '0.68rem' }}>
                          {isCompleted ? 'Completed' : isInProgress ? 'In Progress' : 'Not Started'}
                        </span>
                      </div>
                      <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                        {step.title}
                      </h3>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span className={`badge ${
                        step.level === 'Beginner' ? 'badge-emerald' :
                        step.level === 'Intermediate' ? 'badge-purple' : 'badge-amber'
                      }`} style={{ fontSize: '0.68rem' }}>
                        {step.level}
                      </span>
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Clock size={14} /> {step.duration_weeks} wks (Cum: {step.cumulative_weeks} wks)
                      </span>
                    </div>
                  </div>

                  {/* Course description */}
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: 14 }}>
                    {step.description}
                  </p>

                  {/* Explainable Rationale Callout Box */}
                  <div style={{
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: 'var(--radius-md)',
                    padding: '10px 14px',
                    marginBottom: 16,
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 8,
                    fontSize: '0.82rem',
                    color: '#334155'
                  }}>
                    <Sparkles size={16} style={{ color: '#0284c7', flexShrink: 0, marginTop: 1 }} />
                    <div>
                      <strong style={{ color: 'var(--text-main)' }}>Why this course: </strong>
                      {step.reason}
                    </div>
                  </div>

                  {/* Middle row: Skills and Prerequisites */}
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10,
                    paddingTop: 12,
                    borderTop: '1px solid var(--border-subtle)',
                    marginBottom: 16
                  }}>
                    {/* Skills targeted */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
                        Skills Addressed:
                      </span>
                      {step.targeted_skills.map((sk) => (
                        <span key={sk} className="badge badge-emerald" style={{ fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                          <Check size={11} /> {sk} (Gap Targeted)
                        </span>
                      ))}
                      {step.skills_taught
                        .filter(sk => !step.targeted_skills.includes(sk))
                        .map((sk) => (
                          <span key={sk} className="badge" style={{ fontSize: '0.7rem', background: '#f1f5f9', color: '#475569' }}>
                            +{sk}
                          </span>
                        ))}
                    </div>

                    {/* Prerequisites and Dependents */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, fontSize: '0.76rem' }}>
                      {step.prerequisites.length > 0 && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ color: 'var(--text-dim)' }}>Prerequisites:</span>
                          {step.prerequisites.map((pre) => (
                            <span key={pre} style={{
                              fontWeight: 600,
                              color: '#4f46e5',
                              background: '#eef2ff',
                              padding: '2px 6px',
                              borderRadius: 4
                            }}>
                              {pre}
                            </span>
                          ))}
                        </div>
                      )}

                      {step.prerequisite_for.length > 0 && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#0284c7' }}>
                          <span style={{ color: 'var(--text-dim)' }}>Enables downstream:</span>
                          <span style={{ fontWeight: 600 }}>{step.prerequisite_for.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Progress Controls Row */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: 14,
                    paddingTop: 12,
                    borderTop: '1px solid var(--border-subtle)',
                    background: '#fdfdfe',
                    margin: '0 -24px -22px',
                    padding: '12px 24px',
                    borderBottomLeftRadius: 'var(--radius-lg)',
                    borderBottomRightRadius: 'var(--radius-lg)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 600 }}>
                        Progress:
                      </span>
                      <div style={{
                        width: 100,
                        height: 6,
                        background: '#e2e8f0',
                        borderRadius: 3,
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${step.progress_pct}%`,
                          height: '100%',
                          background: isCompleted ? '#10b981' : '#0284c7'
                        }} />
                      </div>
                      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-main)' }}>
                        {step.progress_pct}%
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {step.status !== 'not_started' && (
                        <button
                          onClick={() => handleUpdateProgress(step.course_id, 'not_started', 0)}
                          disabled={isUpdating}
                          className="btn btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                        >
                          Reset
                        </button>
                      )}

                      {step.status !== 'in_progress' && (
                        <button
                          onClick={() => handleUpdateProgress(step.course_id, 'in_progress', 50)}
                          disabled={isUpdating}
                          className="btn btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '4px 10px', color: '#0284c7' }}
                        >
                          <PlayCircle size={13} /> In Progress
                        </button>
                      )}

                      {!isCompleted ? (
                        <button
                          onClick={() => handleUpdateProgress(step.course_id, 'completed', 100)}
                          disabled={isUpdating}
                          className="btn btn-primary"
                          style={{ fontSize: '0.75rem', padding: '4px 12px' }}
                        >
                          <CheckCircle2 size={13} /> Mark Completed
                        </button>
                      ) : (
                        <span className="badge badge-emerald" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                          <Check size={12} /> Finished
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
