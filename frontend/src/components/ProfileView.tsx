import React, { useState } from 'react';
import { 
  UserCheck, Sparkles, Plus, Trash2, 
  FileText, CheckCircle2, RefreshCw, UploadCloud 
} from 'lucide-react';

interface ProfileViewProps {
  profile: any;
  allRoles: any[];
  onRefreshProfile: () => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({
  profile,
  allRoles,
  onRefreshProfile
}) => {
  const [targetRoleId, setTargetRoleId] = useState(profile?.target_role_id || 'ROL-001');
  const [bio, setBio] = useState(profile?.bio || '');
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillProf, setNewSkillProf] = useState('Intermediate');
  const [resumeText, setResumeText] = useState('');
  const [isParsing, setIsParsing] = useState(false);
  const [extractedResults, setExtractedResults] = useState<any[]>([]);
  const [statusMsg, setStatusMsg] = useState('');

  const handleSaveProfile = async () => {
    try {
      const res = await fetch('/api/employees/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          target_role_id: targetRoleId,
          bio: bio
        })
      });
      if (res.ok) {
        setStatusMsg('Profile updated successfully!');
        onRefreshProfile();
        setTimeout(() => setStatusMsg(''), 3000);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSkillName.trim()) return;
    try {
      const res = await fetch('/api/employees/skills', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          skill_name: newSkillName.trim(),
          proficiency: newSkillProf
        })
      });
      if (res.ok) {
        setNewSkillName('');
        onRefreshProfile();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteSkill = async (skillName: string) => {
    try {
      const res = await fetch(`/api/employees/skills/${encodeURIComponent(skillName)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (res.ok) {
        onRefreshProfile();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleParseResume = async () => {
    if (!resumeText.trim()) return;
    setIsParsing(true);
    try {
      const res = await fetch('/api/employees/resume-upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ text: resumeText })
      });
      const data = await res.json();
      if (data.extracted_skills) {
        setExtractedResults(data.extracted_skills);
        setStatusMsg(`Successfully extracted ${data.extracted_skills.length} skills from resume!`);
        onRefreshProfile();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsParsing(false);
    }
  };

  const sampleCloudResume = `Senior Cloud & DevOps Engineer with 4+ years architecting microservices on AWS (EC2, S3, RDS, VPC). Proficient in Docker containerization, Kubernetes cluster orchestration, Terraform infrastructure as code, CI/CD automation with GitHub Actions, Linux administration, and Python backend scripting.`;

  const sampleDataResume = `Data Scientist experienced in Python, SQL, Pandas, NumPy, Scikit-Learn machine learning, Deep Learning with PyTorch, Natural Language Processing (NLP), and large-scale data visualization.`;

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', padding: '30px 20px 60px' }}>
      <div style={{ marginBottom: 26 }}>
        <h2 style={{ fontSize: '2rem', marginBottom: 6 }}>Employee Profile & Resume Intelligence</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Manage your verified skill inventory, target career ambition, and extract skills from your resume with NLP.
        </p>
      </div>

      {statusMsg && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#34d399',
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          gap: 10
        }}>
          <CheckCircle2 size={18} /> {statusMsg}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 24 }}>
        {/* Left Column: Profile Info & Target Role */}
        <div className="glass-panel" style={{ padding: 26 }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 18, display: 'flex', alignItems: 'center', gap: 8 }}>
            <UserCheck size={20} color="#38bdf8" /> Professional Details
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ fontSize: '0.82rem', color: 'var(--text-dim)', display: 'block', marginBottom: 6 }}>Full Name</label>
              <input type="text" className="input-field" value={profile?.name || ''} disabled style={{ opacity: 0.8 }} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-dim)', display: 'block', marginBottom: 6 }}>Current Role</label>
                <input type="text" className="input-field" value={profile?.current_role || ''} disabled style={{ opacity: 0.8 }} />
              </div>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-dim)', display: 'block', marginBottom: 6 }}>Department</label>
                <input type="text" className="input-field" value={profile?.department || ''} disabled style={{ opacity: 0.8 }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-dim)', display: 'block', marginBottom: 6 }}>Experience</label>
                <input type="text" className="input-field" value={`${profile?.experience_years || 2} years`} disabled style={{ opacity: 0.8 }} />
              </div>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-dim)', display: 'block', marginBottom: 6 }}>Education</label>
                <input type="text" className="input-field" value={profile?.qualification || ''} disabled style={{ opacity: 0.8 }} />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.82rem', color: '#38bdf8', display: 'block', marginBottom: 6, fontWeight: 600 }}>
                Target Internal Role
              </label>
              <select
                className="input-field"
                value={targetRoleId}
                onChange={(e) => setTargetRoleId(e.target.value)}
                style={{ cursor: 'pointer' }}
              >
                {allRoles.map((r) => (
                  <option key={r.role_id} value={r.role_id} style={{ background: '#1e293b' }}>
                    {r.title} ({r.department})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.82rem', color: 'var(--text-dim)', display: 'block', marginBottom: 6 }}>Career Bio & Ambitions</label>
              <textarea
                className="input-field"
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Describe your current focus and target career direction..."
              />
            </div>

            <button onClick={handleSaveProfile} className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
              Save Profile Changes
            </button>
          </div>
        </div>

        {/* Middle Column: Skills Inventory */}
        <div className="glass-panel" style={{ padding: 26 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <h3 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircle2 size={20} color="#34d399" /> Verified Skills ({profile?.skills?.length || 0})
            </h3>
          </div>

          {/* Add Skill Form */}
          <form onSubmit={handleAddSkill} style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
            <input
              type="text"
              className="input-field"
              placeholder="Add skill (e.g. Docker, AWS)..."
              value={newSkillName}
              onChange={(e) => setNewSkillName(e.target.value)}
              style={{ flex: 2 }}
            />
            <select
              className="input-field"
              value={newSkillProf}
              onChange={(e) => setNewSkillProf(e.target.value)}
              style={{ flex: 1, minWidth: 110, cursor: 'pointer' }}
            >
              <option value="Beginner" style={{ background: '#1e293b' }}>Beginner</option>
              <option value="Intermediate" style={{ background: '#1e293b' }}>Intermediate</option>
              <option value="Advanced" style={{ background: '#1e293b' }}>Advanced</option>
              <option value="Expert" style={{ background: '#1e293b' }}>Expert</option>
            </select>
            <button type="submit" className="btn btn-cyan" style={{ padding: '0 14px' }}>
              <Plus size={18} />
            </button>
          </form>

          {/* Skills List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 380, overflowY: 'auto' }}>
            {profile?.skills?.map((sk: any) => (
              <div
                key={sk.skill_name}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-subtle)',
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-sm)'
                }}
              >
                <div>
                  <strong style={{ fontSize: '0.9rem', color: '#fff' }}>{sk.skill_name}</strong>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginLeft: 8 }}>
                    {sk.category}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={`badge ${
                    sk.proficiency === 'Expert' ? 'badge-amber' :
                    sk.proficiency === 'Advanced' ? 'badge-cyan' :
                    sk.proficiency === 'Intermediate' ? 'badge-purple' : 'badge-emerald'
                  }`} style={{ fontSize: '0.65rem' }}>
                    {sk.proficiency}
                  </span>
                  <button
                    onClick={() => handleDeleteSkill(sk.skill_name)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}
                    title="Remove skill"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: NLP Resume Parser */}
        <div className="glass-panel" style={{ padding: 26, gridColumn: 'span 1' }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sparkles size={20} color="#c084fc" /> NLP Resume Skill Extractor
          </h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 14 }}>
            Paste raw resume text or load samples. Our NLP parser matches n-grams and aliases against our 119 canonical skill ontology.
          </p>

          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button
              onClick={() => setResumeText(sampleCloudResume)}
              className="btn btn-secondary"
              style={{ fontSize: '0.74rem', padding: '4px 8px' }}
            >
              Load Cloud Resume
            </button>
            <button
              onClick={() => setResumeText(sampleDataResume)}
              className="btn btn-secondary"
              style={{ fontSize: '0.74rem', padding: '4px 8px' }}
            >
              Load Data Science Resume
            </button>
          </div>

          <textarea
            className="input-field"
            rows={5}
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste raw resume text or job description here..."
            style={{ marginBottom: 14, fontSize: '0.85rem' }}
          />

          <button
            onClick={handleParseResume}
            disabled={isParsing || !resumeText.trim()}
            className="btn btn-primary"
            style={{ width: '100%', marginBottom: 16 }}
          >
            {isParsing ? <RefreshCw size={16} className="animate-spin" /> : <UploadCloud size={16} />}
            {isParsing ? 'Extracting with NLP...' : 'Extract & Auto-Add Skills'}
          </button>

          {/* Results preview */}
          {extractedResults.length > 0 && (
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 8 }}>
                Extracted Canonical Entities ({extractedResults.length})
              </span>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {extractedResults.map((item) => (
                  <span key={item.skill_name} className="badge badge-emerald" style={{ fontSize: '0.72rem' }}>
                    {item.skill_name} ({Math.round(item.confidence * 100)}%)
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
