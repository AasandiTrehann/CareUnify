import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, ShieldCheck, User, Stethoscope, Mail, Lock, UserPlus, ArrowRight } from 'lucide-react';

const Logo = ({ size = 40 }) => (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', marginBottom: '30px' }}>
        <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#4de8f4" />
                    <stop offset="100%" stopColor="#2b58c5" />
                </linearGradient>
            </defs>
            <circle cx="50" cy="50" r="45" stroke="url(#logoGrad)" strokeWidth="3" opacity="0.6" />
            <path d="M50 75C50 75 30 65 24 50C18 35 28 22 40 22C45 22 50 26 50 26C50 26 55 22 60 22C72 22 82 35 76 50C70 65 50 75 50 75Z" stroke="url(#logoGrad)" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M43 32C43 32 45 28 50 28C55 28 57 32 57 32" stroke="url(#logoGrad)" strokeWidth="4" strokeLinecap="round" />
            <circle cx="50" cy="75" r="5" fill="url(#logoGrad)" />
            <circle cx="50" cy="75" r="2" fill="white" />
        </svg>
        <span style={{ fontWeight: 900, fontSize: '1.5rem', color: '#0070f3', letterSpacing: '-0.05em' }}>CareUnify</span>
    </div>
);

const Signup = () => {
    const [role, setRole] = useState('Doctor');
    const navigate = useNavigate();

    const handleSignup = (e) => {
        e.preventDefault();
        localStorage.setItem('userRole', role);
        localStorage.setItem('isAuthenticated', 'true');
        navigate('/dashboard');
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <div onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
                        <Logo />
                    </div>
                    <h2>Create <span className="text-primary">CareUnify</span> Account</h2>
                    <p>Register as a provider or patient to join the intelligence network.</p>
                </div>

                <div className="role-selector">
                    <button className={role === 'Doctor' ? 'active' : ''} onClick={() => setRole('Doctor')}>
                        <Stethoscope size={18} /> Provider
                    </button>
                    <button className={role === 'Patient' ? 'active' : ''} onClick={() => setRole('Patient')}>
                        <User size={18} /> Patient
                    </button>
                </div>

                <form onSubmit={handleSignup} className="auth-form">
                    <div className="input-group">
                        <UserPlus size={18} className="icon" />
                        <input type="text" placeholder="Full Legal Name" required />
                    </div>
                    <div className="input-group">
                        <Mail size={18} className="icon" />
                        <input type="email" placeholder="Email Address" required />
                    </div>
                    <div className="input-group">
                        <Lock size={18} className="icon" />
                        <input type="password" placeholder="Create Secure Password" required />
                    </div>
                    <button type="submit" className="btn-submit">Register Account <ArrowRight size={18} /></button>
                </form>

                <div className="auth-footer">
                    <p>Already have an account? <span onClick={() => navigate('/login')}>Sign in instead</span></p>
                    <div className="security-badge"><ShieldCheck size={14} /> Encrypted Identity Verification</div>
                </div>
            </div>

            <style dangerouslySetInnerHTML={{ __html: `
                .auth-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f8fafc; font-family: 'Inter', sans-serif; }
                .auth-card { width: 480px; padding: 3rem; background: white; border-radius: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.03); border: 1px solid #f1f5f9; }
                .auth-logo { background: #0070f3; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem; }
                .auth-header { text-align: center; margin-bottom: 2rem; }
                .auth-header h2 { font-size: 1.6rem; font-weight: 800; }
                .text-primary { color: #0070f3; }
                .role-selector { display: flex; background: #f1f5f9; padding: 6px; border-radius: 16px; margin-bottom: 2rem; gap: 6px; }
                .role-selector button { flex: 1; border: none; padding: 12px; border-radius: 12px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s; background: transparent; color: #64748b; }
                .role-selector button.active { background: white; color: #0070f3; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
                .input-group { position: relative; margin-bottom: 1rem; }
                .input-group .icon { position: absolute; left: 16px; top: 16px; color: #94a3b8; }
                .input-group input { width: 100%; padding: 14px 14px 14px 48px; border-radius: 14px; border: 1px solid #e2e8f0; outline: none; }
                .btn-submit { width: 100%; padding: 16px; border-radius: 14px; border: none; background: #0070f3; color: white; font-weight: 800; display: flex; align-items: center; justify-content: center; gap: 10px; cursor: pointer; transition: 0.3s; margin-top: 1rem; }
                .auth-footer { text-align: center; margin-top: 2rem; font-size: 0.9rem; color: #64748b; }
                .auth-footer span { color: #0070f3; font-weight: 700; cursor: pointer; }
                .security-badge { margin-top: 1.5rem; display: inline-flex; align-items: center; gap: 6px; font-size: 0.75rem; color: #10b981; font-weight: 800; background: #f0fdf4; padding: 6px 12px; border-radius: 50px; }
            ` }} />
        </div>
    );
};

export default Signup;
