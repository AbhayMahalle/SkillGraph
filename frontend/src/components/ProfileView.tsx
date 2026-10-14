import React, { useState, useEffect, useRef } from 'react';
import { 
  UserCheck, Sparkles, Plus, Trash2, 
  FileText, CheckCircle2, RefreshCw, UploadCloud,
  Lock, KeyRound, AlertCircle, Save, Loader2,
  Upload, X, Check, Search, Shield, Info, FileUp, CheckSquare, Square
} from 'lucide-react';

interface CanonicalSkill {
  skill_id: string;
  name: string;
  category: string;
  aliases: string[];
}

interface UserSkill {
  id?: number;
  skill_id: string;
  skill_name: string;
  category: string;
  proficiency: string;
  verified: boolean;
  source: string;
  evidence?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

interface StagedCandidateSkill {
  skill_id: string;
  skill_name: string;
  category: string;
  confidence: number;
  evidence: string;
  proficiency: string;
  accepted: boolean;
}

interface ProfileViewProps {
  profile: any;
  allRoles: any[];
  onRefreshProfile: () => void;
}

const VALID_PROFICIENCIES = ['Beginner', 'Intermediate', 'Advanced', 'Expert'];

export const ProfileView: React.FC<ProfileViewProps> = ({
  profile,
  allRoles,
  onRefreshProfile
}) => {
  // 1. Profile editable fields
  const [fullName, setFullName] = useState(profile?.name || '');
  const [department, setDepartment] = useState(profile?.department || 'Engineering');
  const [experienceYears, setExperienceYears] = useState(profile?.experience_years?.toString() || '2');
  const [qualification, setQualification] = useState(profile?.qualification || "Bachelor's Degree");
  const [targetRoleId, setTargetRoleId] = useState(profile?.target_role_id || 'ROL-001');
  const [bio, setBio] = useState(profile?.bio || '');

  // 2. Canonical Catalog & Skill Management
  const [canonicalCatalog, setCanonicalCatalog] = useState<CanonicalSkill[]>([]);
  const [skillSearchQuery, setSkillSearchQuery] = useState('');
  const [selectedCanonicalSkill, setSelectedCanonicalSkill] = useState<CanonicalSkill | null>(null);
  const [newSkillProf, setNewSkillProf] = useState('Intermediate');
  const [newSkillEvidence, setNewSkillEvidence] = useState('');
  const [skillFilterQuery, setSkillFilterQuery] = useState('');
  const [isAddingSkill, setIsAddingSkill] = useState(false);
  const [editingSkillName, setEditingSkillName] = useState<string | null>(null);
  const [editingProficiency, setEditingProficiency] = useState<string>('Intermediate');

  // 3. Resume Upload & Processing State
  const [uploadMode, setUploadMode] = useState<'file' | 'text'>('file');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [resumeText, setResumeText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 4. Staged Candidate Skills Review Workflow
  const [stagedSkills, setStagedSkills] = useState<StagedCandidateSkill[]>([]);
  const [stagedMetadata, setStagedMetadata] = useState<{ filename: string | null; fileType: string | null } | null>(null);
  const [isConfirmingSkills, setIsConfirmingSkills] = useState(false);

  // 5. Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [pwdErrorMsg, setPwdErrorMsg] = useState('');
  const [pwdSuccessMsg, setPwdSuccessMsg] = useState('');

  // 6. UI feedback states
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Sync state when profile prop updates
  useEffect(() => {
    if (profile) {
      setFullName(profile.name || '');
      setDepartment(profile.department || 'Engineering');
      setExperienceYears(profile.experience_years?.toString() || '2');
      setQualification(profile.qualification || "Bachelor's Degree");
      setTargetRoleId(profile.target_role_id || 'ROL-001');
      setBio(profile.bio || '');
    }
  }, [profile]);

  // Load canonical skills catalog and check staged extractions on mount
  useEffect(() => {
    loadCanonicalCatalog();
    loadStagedExtractions();
  }, []);

  const loadCanonicalCatalog = async () => {
    try {
      const res = await fetch('/api/skills/catalog');
      if (res.ok) {
        const data = await res.json();
        setCanonicalCatalog(data);
      }
    } catch (err) {
      console.error('Failed to load canonical skills catalog:', err);
    }
  };

  const loadStagedExtractions = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const res = await fetch('/api/employees/resume/extracted', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.extracted_skills && data.extracted_skills.length > 0) {
          setStagedSkills(data.extracted_skills.map((s: any) => ({
            skill_id: s.skill_id,
            skill_name: s.skill_name,
            category: s.category || 'General',
            confidence: s.confidence || 0.85,
            evidence: s.evidence || '',
            proficiency: s.proficiency || 'Intermediate',
            accepted: true
          })));
          setStagedMetadata({
            filename: data.filename,
            fileType: data.file_type
          });
        }
      }
    } catch (err) {
      console.error('Failed to load staged extractions:', err);
    }
  };

  // Profile Save
  const handleSaveProfile = async () => {
    setErrorMsg('');
    setStatusMsg('');
    setIsSavingProfile(true);

    try {
      const expNum = parseInt(experienceYears, 10);
      const res = await fetch('/api/users/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          full_name: fullName.trim(),
          department: department.trim(),
          experience_years: isNaN(expNum) ? 1 : expNum,
          qualification: qualification.trim(),
          target_role_id: targetRoleId,
          bio: bio
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Could not update profile');
      }

      setStatusMsg('Profile updated and persisted successfully!');
      onRefreshProfile();
      setTimeout(() => setStatusMsg(''), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save profile changes.');
    } finally {
      setIsSavingProfile(false);
    }
  };

  // Password Change
  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdErrorMsg('');
    setPwdSuccessMsg('');

    if (!currentPassword) {
      setPwdErrorMsg('Please enter your current password.');
      return;
    }
    if (newPassword.length < 8) {
      setPwdErrorMsg('New password must be at least 8 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwdErrorMsg('New password and confirmation do not match.');
      return;
    }
    if (currentPassword === newPassword) {
      setPwdErrorMsg('New password cannot be the same as current password.');
      return;
    }

    setIsChangingPassword(true);
    try {
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to change password.');
      }

      setPwdSuccessMsg('Password changed successfully! Old password is now invalidated.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setPwdSuccessMsg(''), 5000);
    } catch (err: any) {
      setPwdErrorMsg(err.message || 'Error changing password.');
    } finally {
      setIsChangingPassword(false);
    }
  };

  // Canonical Skill Add / Update
  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    const skillName = selectedCanonicalSkill ? selectedCanonicalSkill.name : skillSearchQuery.trim();
    if (!skillName) return;

    setIsAddingSkill(true);
    setErrorMsg('');
    try {
      const res = await fetch('/api/employees/skills', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          skill_name: skillName,
          proficiency: newSkillProf,
          source: 'self_reported',
          evidence: newSkillEvidence.trim() || undefined
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to add skill.');
      }

      setSkillSearchQuery('');
      setSelectedCanonicalSkill(null);
      setNewSkillEvidence('');
      setStatusMsg(`Skill '${skillName}' successfully saved to profile.`);
      onRefreshProfile();
      setTimeout(() => setStatusMsg(''), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error adding skill.');
    } finally {
      setIsAddingSkill(false);
    }
  };

  // Inline Proficiency Update
  const handleUpdateSkillProficiency = async (skillName: string, newProf: string) => {
    try {
      const res = await fetch(`/api/employees/skills/${encodeURIComponent(skillName)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          proficiency: newProf
        })
      });

      if (res.ok) {
        setEditingSkillName(null);
        onRefreshProfile();
      }
    } catch (err) {
      console.error('Failed to update proficiency:', err);
    }
  };

  // Skill Deletion
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
      console.error('Failed to delete skill:', err);
    }
  };

  // File Validation
  const validateFile = (file: File): string | null => {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    const allowed = ['.pdf', '.docx', '.txt'];
    if (!allowed.includes(ext)) {
      return `Unsupported file format '${ext}'. Please upload a PDF (.pdf), Word document (.docx), or plain text (.txt) file.`;
    }
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the maximum allowed 10 MB limit.`;
    }
    if (file.size === 0) {
      return 'The uploaded file is empty. Please select a valid document.';
    }
    return null;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError('');
    setUploadSuccess('');
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const error = validateFile(file);
      if (error) {
        setUploadError(error);
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setUploadError('');
    setUploadSuccess('');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const error = validateFile(file);
      if (error) {
        setUploadError(error);
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
    }
  };

  // Execute Resume Upload & Skill Extraction
  const handleUploadResume = async () => {
    setUploadError('');
    setUploadSuccess('');

    if (uploadMode === 'file' && !selectedFile) {
      setUploadError('Please select a PDF, DOCX, or TXT resume file to upload.');
      return;
    }
    if (uploadMode === 'text' && !resumeText.trim()) {
      setUploadError('Please paste your resume text before running extraction.');
      return;
    }

    setIsUploading(true);
    try {
      let res: Response;
      const token = localStorage.getItem('token');

      if (uploadMode === 'file' && selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);

        res = await fetch('/api/employees/resume-upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });
      } else {
        res = await fetch('/api/employees/resume-upload', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ text: resumeText.trim() })
        });
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Resume analysis failed.');
      }

      if (data.extracted_skills && data.extracted_skills.length > 0) {
        setStagedSkills(data.extracted_skills.map((s: any) => ({
          skill_id: s.skill_id,
          skill_name: s.skill_name,
          category: s.category || 'General',
          confidence: s.confidence || 0.85,
          evidence: s.evidence || '',
          proficiency: s.proficiency || 'Intermediate',
          accepted: true
        })));
        setStagedMetadata({
          filename: data.filename,
          fileType: data.file_type
        });
        setUploadSuccess(`Identified ${data.total_extracted} candidate skill mentions from resume. Review below to accept, adjust, or reject before saving.`);
      } else {
        setUploadSuccess('Document processed successfully, but no matching ontology skills were detected. You may add personal skills manually.');
      }
    } catch (err: any) {
      setUploadError(err.message || 'Error processing resume file.');
    } finally {
      setIsUploading(false);
    }
  };

  // Toggle individual staged skill acceptance
  const toggleStagedSkill = (index: number) => {
    setStagedSkills(prev => prev.map((s, i) => i === index ? { ...s, accepted: !s.accepted } : s));
  };

  // Update proficiency in staged candidate skill
  const updateStagedProficiency = (index: number, prof: string) => {
    setStagedSkills(prev => prev.map((s, i) => i === index ? { ...s, proficiency: prof } : s));
  };

  // Select / Deselect All
  const setAllStagedAcceptance = (accepted: boolean) => {
    setStagedSkills(prev => prev.map(s => ({ ...s, accepted })));
  };

  // Confirm and Save Reviewed Skills
  const handleConfirmSkills = async () => {
    const acceptedList = stagedSkills.filter(s => s.accepted);
    if (acceptedList.length === 0) {
      setUploadError('Please select at least one skill to save to your profile, or click Discard.');
      return;
    }

    setIsConfirmingSkills(true);
    setUploadError('');
    try {
      const token = localStorage.getItem('token');
      const payload = {
        skills: stagedSkills.map(s => ({
          skill_name: s.skill_name,
          proficiency: s.proficiency,
          evidence: s.evidence,
          accepted: s.accepted
        }))
      };

      const res = await fetch('/api/employees/resume/confirm-skills', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to save confirmed skills.');
      }

      setStagedSkills([]);
      setStagedMetadata(null);
      setSelectedFile(null);
      setResumeText('');
      setUploadSuccess(`Successfully saved ${data.confirmed_count} reviewed skills to your personal profile.`);
      onRefreshProfile();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to confirm skills.');
    } finally {
      setIsConfirmingSkills(false);
    }
  };

  // Filter skills in inventory
  const userSkills: UserSkill[] = profile?.skills || [];
  const filteredUserSkills = userSkills.filter(sk => {
    if (!skillFilterQuery.trim()) return true;
    const q = skillFilterQuery.toLowerCase();
    return sk.skill_name.toLowerCase().includes(q) || sk.category.toLowerCase().includes(q);
  });

  // Filter canonical catalog suggestions
  const catalogSuggestions = canonicalCatalog.filter(cs => {
    if (!skillSearchQuery.trim()) return false;
    const q = skillSearchQuery.toLowerCase();
    return cs.name.toLowerCase().includes(q) || cs.aliases.some(a => a.toLowerCase().includes(q));
  }).slice(0, 8);

  const sampleCloudResume = `Senior Cloud & DevOps Engineer with 4+ years architecting microservices on AWS (EC2, S3, RDS, VPC). Proficient in Docker containerization, Kubernetes cluster orchestration, Terraform infrastructure as code, CI/CD automation with GitHub Actions, Linux administration, and Python backend scripting.`;
  const sampleDataResume = `Data Scientist experienced in Python, SQL, Pandas, NumPy, Scikit-Learn machine learning, Deep Learning with PyTorch, Natural Language Processing (NLP), and large-scale data visualization.`;

  return (
    <div style={{ maxWidth: 1300, margin: '0 auto', padding: '30px 20px 60px' }}>
      <div style={{ marginBottom: 26 }}>
        <h2 style={{ fontSize: '2rem', marginBottom: 6 }}>Personal Skill Profiling & Intelligence</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Manage your verified skill inventory, upload multi-format resumes (PDF/DOCX/TXT), review candidate skill mentions, and track provenance.
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

      {errorMsg && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          color: '#fb7185',
          padding: '12px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          gap: 10
        }}>
          <AlertCircle size={18} /> {errorMsg}
        </div>
      )}

      {/* Main Grid: 2 Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 24 }}>
        
        {/* COLUMN 1: Personal Skill Inventory & Catalog Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          
          {/* Card 1A: Personal Skills Inventory */}
          <div className="saas-card" style={{ padding: 26 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Shield size={19} color="#059669" /> Personal Skills Inventory ({userSkills.length})
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 2 }}>
                  Your authenticated talent profile and skill provenance records.
                </p>
              </div>
              <span className="badge badge-emerald" style={{ fontSize: '0.72rem' }}>
                {userSkills.filter(s => s.verified).length} Verified
              </span>
            </div>

            {/* Filter Search */}
            {userSkills.length > 5 && (
              <div style={{ position: 'relative', marginBottom: 14 }}>
                <Search size={14} color="var(--text-dim)" style={{ position: 'absolute', left: 12, top: 11 }} />
                <input
                  type="text"
                  placeholder="Filter your skills by name or category..."
                  value={skillFilterQuery}
                  onChange={(e) => setSkillFilterQuery(e.target.value)}
                  className="input-field"
                  style={{ paddingLeft: 34, fontSize: '0.84rem' }}
                />
              </div>
            )}

            {/* Skills List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 340, overflowY: 'auto', paddingRight: 4 }}>
              {filteredUserSkills.length > 0 ? (
                filteredUserSkills.map((sk) => (
                  <div
                    key={sk.skill_name}
                    style={{
                      background: '#ffffff',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px 14px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>{sk.skill_name}</strong>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                          {sk.category}
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {/* Inline proficiency editing */}
                        {editingSkillName === sk.skill_name ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <select
                              value={editingProficiency}
                              onChange={(e) => setEditingProficiency(e.target.value)}
                              className="input-field"
                              style={{ padding: '2px 6px', fontSize: '0.75rem', height: 28 }}
                            >
                              {VALID_PROFICIENCIES.map(p => (
                                <option key={p} value={p}>{p}</option>
                              ))}
                            </select>
                            <button
                              onClick={() => handleUpdateSkillProficiency(sk.skill_name, editingProficiency)}
                              className="btn btn-primary"
                              style={{ padding: '2px 6px', fontSize: '0.72rem', height: 28 }}
                              title="Save"
                            >
                              <Check size={14} />
                            </button>
                            <button
                              onClick={() => setEditingSkillName(null)}
                              className="btn btn-secondary"
                              style={{ padding: '2px 6px', fontSize: '0.72rem', height: 28 }}
                              title="Cancel"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => {
                              setEditingSkillName(sk.skill_name);
                              setEditingProficiency(sk.proficiency);
                            }}
                            className={`badge ${
                              sk.proficiency === 'Expert' ? 'badge-amber' :
                              sk.proficiency === 'Advanced' ? 'badge-cyan' :
                              sk.proficiency === 'Intermediate' ? 'badge-purple' : 'badge-emerald'
                            }`}
                            style={{ fontSize: '0.68rem', cursor: 'pointer', border: 'none' }}
                            title="Click to edit proficiency"
                          >
                            {sk.proficiency} ✎
                          </button>
                        )}

                        {/* Provenance Badge */}
                        <span
                          className={`badge ${sk.source === 'resume_extracted' ? 'badge-cyan' : 'badge-purple'}`}
                          style={{ fontSize: '0.62rem' }}
                        >
                          {sk.source === 'resume_extracted' ? 'Resume Mention' : 'Self-Reported'}
                        </span>

                        {/* Verified status flag */}
                        {!sk.verified && (
                          <span
                            className="badge badge-amber"
                            style={{ fontSize: '0.6rem' }}
                            title="Candidate skill extracted from resume, awaiting formal verification"
                          >
                            Candidate
                          </span>
                        )}

                        <button
                          onClick={() => handleDeleteSkill(sk.skill_name)}
                          style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', marginLeft: 4 }}
                          title="Remove skill from profile"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>

                    {/* Evidence Snippet if present */}
                    {sk.evidence && (
                      <div style={{
                        fontSize: '0.74rem',
                        color: 'var(--text-secondary)',
                        background: '#f8fafc',
                        padding: '4px 8px',
                        borderRadius: 4,
                        borderLeft: '2px solid #0284c7'
                      }}>
                        <span style={{ fontWeight: 600, color: '#0284c7' }}>Evidence: </span>
                        {sk.evidence}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.86rem' }}>
                  No skills match your filter. Use the form below or resume parser to build your skill profile.
                </div>
              )}
            </div>
          </div>

          {/* Card 1B: Add Skill from Canonical Catalog */}
          <div className="saas-card" style={{ padding: 26 }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Plus size={18} color="#0284c7" /> Add Canonical Skill
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 14 }}>
              Select skills from our 119 canonical skill ontology. Adding an existing skill updates your proficiency level in-place without creating duplicates.
            </p>

            <form onSubmit={handleAddSkill} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ position: 'relative' }}>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 500 }}>
                  Skill Name (Search 119 Canonical Skills)
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    className="input-field"
                    placeholder="Search canonical ontology (e.g. Docker, Python, AWS)..."
                    value={selectedCanonicalSkill ? selectedCanonicalSkill.name : skillSearchQuery}
                    onChange={(e) => {
                      setSelectedCanonicalSkill(null);
                      setSkillSearchQuery(e.target.value);
                    }}
                    required
                  />
                  {selectedCanonicalSkill && (
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedCanonicalSkill(null);
                        setSkillSearchQuery('');
                      }}
                      style={{ position: 'absolute', right: 10, top: 10, background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                {/* Autocomplete Dropdown */}
                {catalogSuggestions.length > 0 && !selectedCanonicalSkill && (
                  <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    background: '#ffffff',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    marginTop: 4,
                    zIndex: 20,
                    maxHeight: 180,
                    overflowY: 'auto',
                    boxShadow: 'var(--shadow-md)'
                  }}>
                    {catalogSuggestions.map(cs => (
                      <div
                        key={cs.skill_id}
                        onClick={() => {
                          setSelectedCanonicalSkill(cs);
                          setSkillSearchQuery(cs.name);
                        }}
                        style={{
                          padding: '8px 12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          cursor: 'pointer',
                          borderBottom: '1px solid var(--border-subtle)'
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-subtle)')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                      >
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 500 }}>{cs.name}</span>
                        <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>{cs.category}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 500 }}>
                    Proficiency
                  </label>
                  <select
                    className="input-field"
                    value={newSkillProf}
                    onChange={(e) => setNewSkillProf(e.target.value)}
                    style={{ cursor: 'pointer' }}
                  >
                    {VALID_PROFICIENCIES.map(p => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4, fontWeight: 500 }}>
                    Evidence / Context (Optional)
                  </label>
                  <input
                    type="text"
                    className="input-field"
                    placeholder="e.g. Production microservices deployment"
                    value={newSkillEvidence}
                    onChange={(e) => setNewSkillEvidence(e.target.value)}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isAddingSkill || (!selectedCanonicalSkill && !skillSearchQuery.trim())}
                className="btn btn-primary"
                style={{ alignSelf: 'flex-start', marginTop: 4, fontSize: '0.86rem' }}
              >
                {isAddingSkill ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                {isAddingSkill ? 'Saving...' : 'Add Skill to Profile'}
              </button>
            </form>
          </div>

          {/* Card 1C: Professional Profile Details */}
          <div className="saas-card" style={{ padding: 26 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <UserCheck size={18} color="#0284c7" /> Professional Details
              </h3>
              <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>
                ID: {profile?.employee_id || 'Personal'}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                  Full Name
                </label>
                <input 
                  type="text" 
                  className="input-field" 
                  value={fullName} 
                  onChange={(e) => setFullName(e.target.value)} 
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                    Department
                  </label>
                  <input 
                    type="text" 
                    className="input-field" 
                    value={department} 
                    onChange={(e) => setDepartment(e.target.value)} 
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                    Experience (Years)
                  </label>
                  <input 
                    type="number" 
                    min="0"
                    max="60"
                    className="input-field" 
                    value={experienceYears} 
                    onChange={(e) => setExperienceYears(e.target.value)} 
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                  Highest Qualification
                </label>
                <input 
                  type="text" 
                  className="input-field" 
                  value={qualification} 
                  onChange={(e) => setQualification(e.target.value)} 
                />
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-main)', display: 'block', marginBottom: 4, fontWeight: 600 }}>
                  Target Career Role
                </label>
                <select
                  className="input-field"
                  value={targetRoleId}
                  onChange={(e) => setTargetRoleId(e.target.value)}
                  style={{ cursor: 'pointer' }}
                >
                  {allRoles.map((r) => (
                    <option key={r.role_id} value={r.role_id}>
                      {r.title} ({r.department})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                  Career Bio & Goals
                </label>
                <textarea
                  className="input-field"
                  rows={2}
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Describe your current engineering focus..."
                  style={{ fontSize: '0.84rem' }}
                />
              </div>

              <button 
                onClick={handleSaveProfile} 
                disabled={isSavingProfile}
                className="btn btn-primary" 
                style={{ alignSelf: 'flex-start', marginTop: 4, fontSize: '0.84rem' }}
              >
                {isSavingProfile ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
                {isSavingProfile ? 'Saving...' : 'Save Profile Changes'}
              </button>
            </div>
          </div>
        </div>

        {/* COLUMN 2: Resume Intelligence Center & Security */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          
          {/* Card 2A: Resume Upload & Intelligence Processing */}
          <div className="saas-card" style={{ padding: 26 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Sparkles size={19} color="#7c3aed" /> Resume Intelligence Center
              </h3>
              <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
                NLP Parser v3
              </span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>
              Upload your resume in PDF, Word (DOCX), or plain text (TXT) format. Extracted candidate skills are staged for review and <strong>never</strong> automatically marked as verified expertise without your approval.
            </p>

            {uploadSuccess && (
              <div style={{
                background: '#ecfdf5',
                border: '1px solid #a7f3d0',
                color: '#047857',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                marginBottom: 16,
                fontSize: '0.82rem',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <CheckCircle2 size={16} /> {uploadSuccess}
              </div>
            )}

            {uploadError && (
              <div style={{
                background: '#fff1f2',
                border: '1px solid #fecdd3',
                color: '#be123c',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                marginBottom: 16,
                fontSize: '0.82rem',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <AlertCircle size={16} /> {uploadError}
              </div>
            )}

            {/* Mode Selector */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
              <button
                type="button"
                onClick={() => setUploadMode('file')}
                className={`btn ${uploadMode === 'file' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '6px 14px' }}
              >
                <FileUp size={14} /> Upload Document (PDF / DOCX / TXT)
              </button>
              <button
                type="button"
                onClick={() => setUploadMode('text')}
                className={`btn ${uploadMode === 'text' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '6px 14px' }}
              >
                <FileText size={14} /> Paste Text
              </button>
            </div>

            {uploadMode === 'file' ? (
              <div>
                {/* Drag and Drop Zone */}
                <div
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    border: `2px dashed ${dragActive ? '#0284c7' : 'var(--border-subtle)'}`,
                    borderRadius: 'var(--radius-md)',
                    padding: '30px 20px',
                    textAlign: 'center',
                    background: dragActive ? 'rgba(2, 132, 199, 0.05)' : '#f8fafc',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    marginBottom: 14
                  }}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                  />
                  <UploadCloud size={32} color={dragActive ? '#0284c7' : '#94a3b8'} style={{ margin: '0 auto 10px' }} />
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-main)', fontWeight: 500, marginBottom: 4 }}>
                    {selectedFile ? selectedFile.name : 'Click to select or drag & drop resume file'}
                  </p>
                  <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    Supported: PDF (.pdf), Word (.docx), Text (.txt) • Maximum 10 MB limit
                  </p>
                  {selectedFile && (
                    <div style={{ marginTop: 8 }}>
                      <span className="badge badge-cyan" style={{ fontSize: '0.72rem' }}>
                        {(selectedFile.size / 1024).toFixed(1)} KB • Ready for extraction
                      </span>
                    </div>
                  )}
                </div>

                <button
                  onClick={handleUploadResume}
                  disabled={isUploading || !selectedFile}
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                >
                  {isUploading ? <Loader2 size={16} className="animate-spin" /> : <UploadCloud size={16} />}
                  {isUploading ? 'Extracting Skills from Resume...' : 'Analyze Document & Detect Skills'}
                </button>
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <button
                    onClick={() => setResumeText(sampleCloudResume)}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.74rem', padding: '4px 8px' }}
                  >
                    Load Cloud Sample
                  </button>
                  <button
                    onClick={() => setResumeText(sampleDataResume)}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.74rem', padding: '4px 8px' }}
                  >
                    Load Data Science Sample
                  </button>
                </div>
                <textarea
                  className="input-field"
                  rows={4}
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  placeholder="Paste resume text or job description here..."
                  style={{ marginBottom: 12, fontSize: '0.84rem' }}
                />
                <button
                  onClick={handleUploadResume}
                  disabled={isUploading || !resumeText.trim()}
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                >
                  {isUploading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                  {isUploading ? 'Extracting Skills from Text...' : 'Analyze Text & Detect Skills'}
                </button>
              </div>
            )}
          </div>

          {/* Card 2B: Staged Candidate Skills Review & Confirmation Workflow */}
          {stagedSkills.length > 0 && (
            <div className="saas-card" style={{ padding: 26, border: '1px solid #c7d2fe' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, color: '#4338ca' }}>
                    <CheckSquare size={18} /> Candidate Skills Review ({stagedSkills.filter(s => s.accepted).length} of {stagedSkills.length} selected)
                  </h3>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    Source: {stagedMetadata?.filename || 'Uploaded Resume'} ({stagedMetadata?.fileType || 'Doc'})
                  </p>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    type="button"
                    onClick={() => setAllStagedAcceptance(true)}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.7rem', padding: '3px 8px' }}
                  >
                    Select All
                  </button>
                  <button
                    type="button"
                    onClick={() => setAllStagedAcceptance(false)}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.7rem', padding: '3px 8px' }}
                  >
                    Deselect All
                  </button>
                </div>
              </div>

              {/* Informative Disclaimer Alert */}
              <div style={{
                background: '#f0f9ff',
                border: '1px solid #bae6fd',
                color: '#0369a1',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.76rem',
                marginBottom: 14,
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <Info size={16} style={{ flexShrink: 0 }} />
                <span>
                  Extracted skills are unverified mentions. Review match confidence and context snippets, adjust proficiency levels, and confirm which skills to persist to your personal profile.
                </span>
              </div>

              {/* Candidate Skills Review Table */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 320, overflowY: 'auto', marginBottom: 16, paddingRight: 4 }}>
                {stagedSkills.map((sk, index) => (
                  <div
                    key={`${sk.skill_name}-${index}`}
                    style={{
                      background: sk.accepted ? '#f0fdf4' : '#ffffff',
                      border: `1px solid ${sk.accepted ? '#bbf7d0' : 'var(--border-subtle)'}`,
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px 12px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div
                        onClick={() => toggleStagedSkill(index)}
                        style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}
                      >
                        {sk.accepted ? (
                          <CheckSquare size={18} color="#10b981" />
                        ) : (
                          <Square size={18} color="var(--text-dim)" />
                        )}
                        <div>
                          <strong style={{ fontSize: '0.9rem', color: sk.accepted ? 'var(--text-main)' : 'var(--text-dim)' }}>
                            {sk.skill_name}
                          </strong>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginLeft: 8 }}>
                            {sk.category}
                          </span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        {/* Confidence score */}
                        <span className="badge badge-emerald" style={{ fontSize: '0.66rem' }}>
                          {Math.round(sk.confidence * 100)}% Match
                        </span>

                        {/* Proficiency selector */}
                        <select
                          value={sk.proficiency}
                          onChange={(e) => updateStagedProficiency(index, e.target.value)}
                          disabled={!sk.accepted}
                          className="input-field"
                          style={{
                            padding: '2px 8px',
                            fontSize: '0.76rem',
                            height: 28,
                            opacity: sk.accepted ? 1 : 0.5,
                            cursor: sk.accepted ? 'pointer' : 'not-allowed'
                          }}
                        >
                          {VALID_PROFICIENCIES.map(p => (
                            <option key={p} value={p}>{p}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Context evidence snippet */}
                    {sk.evidence && (
                      <div style={{
                        fontSize: '0.74rem',
                        color: 'var(--text-secondary)',
                        background: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        padding: '4px 8px',
                        borderRadius: 4,
                        fontStyle: 'italic',
                        marginLeft: 28
                      }}>
                        "{sk.evidence}"
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  type="button"
                  onClick={() => {
                    setStagedSkills([]);
                    setStagedMetadata(null);
                  }}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                >
                  Discard All
                </button>

                <button
                  type="button"
                  onClick={handleConfirmSkills}
                  disabled={isConfirmingSkills || stagedSkills.filter(s => s.accepted).length === 0}
                  className="btn btn-primary"
                  style={{ fontSize: '0.84rem', padding: '6px 16px' }}
                >
                  {isConfirmingSkills ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  {isConfirmingSkills ? 'Saving...' : `Save ${stagedSkills.filter(s => s.accepted).length} Confirmed Skills to Profile`}
                </button>
              </div>
            </div>
          )}

          {/* Card 2C: Password Security Settings */}
          <div className="saas-card" style={{ padding: 26 }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Lock size={18} color="#d97706" /> Change Password
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 14 }}>
              Update your account credentials. Secured with PBKDF2-HMAC-SHA256 cryptography.
            </p>

            {pwdSuccessMsg && (
              <div style={{
                background: '#ecfdf5',
                border: '1px solid #a7f3d0',
                color: '#047857',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                marginBottom: 12,
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <CheckCircle2 size={15} /> {pwdSuccessMsg}
              </div>
            )}

            {pwdErrorMsg && (
              <div style={{
                background: '#fff1f2',
                border: '1px solid #fecdd3',
                color: '#be123c',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                marginBottom: 12,
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <AlertCircle size={15} /> {pwdErrorMsg}
              </div>
            )}

            <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div>
                <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                  Current Password
                </label>
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                    New Password (min 8)
                  </label>
                  <input
                    type="password"
                    className="input-field"
                    placeholder="••••••••"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    className="input-field"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isChangingPassword}
                className="btn btn-secondary"
                style={{ alignSelf: 'flex-start', marginTop: 4, fontSize: '0.84rem' }}
              >
                {isChangingPassword ? <Loader2 size={15} className="animate-spin" /> : <KeyRound size={15} />}
                {isChangingPassword ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          </div>
        </div>

      </div>
    </div>
  );
};
