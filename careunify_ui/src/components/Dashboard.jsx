import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Activity,
    ShieldAlert,
    LogOut,
    ChevronRight,
    CheckCircle,
    ArrowRight,
    Sparkles,
    Zap,
    ShieldCheck,
    Database,
    UploadCloud,
    Loader2,
    MessageSquare,
    Target,
    AlertTriangle,
    Info,
    TrendingUp,
    HeartPulse,
    LayoutDashboard,
    ClipboardList,
    Stethoscope,
    Flame,
    Moon,
    Wind,
    Droplets,
    FileText,
    FileSpreadsheet,
    Image as ImageIcon,
    Mic,
    Check,
    Box,
    Globe,
    File,
    BrainCircuit,
    Layers,
    Table,
    Bell,
    BarChart3,
    Search,
    User,
    Users,
    Gem
} from 'lucide-react';

const Logo = ({ size = 40, showText = true }) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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
        {showText && (
            <span style={{ fontWeight: 900, fontSize: '1.2rem', color: '#0070f3', letterSpacing: '0.05em' }}>CareUnify</span>
        )}
    </div>
);

const Dashboard = () => {
    const navigate = useNavigate();
    const userRole = localStorage.getItem('userRole') || 'Doctor';
    const userName = localStorage.getItem('userName') || (userRole === 'Doctor' ? 'Dr. Sumit' : 'Verified Patient');

    const [activeTab, setActiveTab] = useState(userRole === 'Doctor' ? 'oversight' : 'dossier');
    const [isIngesting, setIsIngesting] = useState(false);
    const [uploadComplete, setUploadComplete] = useState(false);
    const [extractedDetails, setExtractedDetails] = useState(null);
    const fileInputRef = useRef(null);

    const [chatHistory, setChatHistory] = useState([{ role: 'ai', text: `Unified Command Active. Total Registry: 600 Records. Clinical Trust: 94.2%.` }]);
    const [isAiTyping, setIsAiTyping] = useState(false);
    const [userInput, setUserInput] = useState('');
    const chatEndRef = useRef(null);

    // MOCK 600 PATIENT REGISTRY FOR MASTER DASHBOARD
    const fakeRegistry = Array.from({ length: 600 }, (_, i) => ({
        id: `CU-G${8000 + i}`,
        status: i % 15 === 0 ? 'Critical' : i % 5 === 0 ? 'Warning' : 'Analyzed',
        isGolden: i % 4 !== 0,
        source: ['CSV Portal', 'PDF Extract', 'Image OCR', 'Voice Note'][i % 4],
        velocity: Math.floor(Math.random() * 95) + 5
    }));

    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatHistory, isAiTyping]);

    const handleFilePicker = () => { fileInputRef.current.click(); };

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setIsIngesting(true);
        setTimeout(() => {
            setExtractedDetails({ name: file.name, atoms: 24 });
            setIsIngesting(false);
            setUploadComplete(true);
        }, 2000);
    };

    const handleQuery = (q) => {
        const queryLower = q.toLowerCase();
        setUserInput('');
        setChatHistory(prev => [...prev, { role: 'user', text: q }]);
        setIsAiTyping(true);
        setTimeout(() => {
            let res = userRole === 'Doctor'
                ? "Unified Intelligence: Analysis of 600 records shows 442 Verified Golden records. Critical clusters detected in Hypertension region HL7-3."
                : `Dossier Sync: ${userName}, your Stage 1 Hypertension markers are verified.`;
            setChatHistory(prev => [...prev, { role: 'ai', text: res }]);
            setIsAiTyping(false);
        }, 1200);
    };

    const renderDoctorDashboard = () => (
        <div className="content-fade-in doctor-scroll">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '3rem' }}>
                <div>
                    <h2 style={{ fontWeight: 900, fontSize: '2.8rem', letterSpacing: '-0.03em' }}>Master Oversight HUB</h2>
                    <p style={{ color: '#0070f3', fontWeight: 900, fontSize: '0.9rem' }}>UNIFIED CLINICAL COMMAND CENTER (600 RECORDS)</p>
                </div>
                <div className="security-badge"><Bell size={16} /> 14 PENDING ALERTS</div>
            </div>

            {/* TOP STATS */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2.5rem' }}>
                <div className="stat-card"><div className="s-icon blue"><Gem /></div><div className="s-info"><span className="s-label">Golden Records</span><span className="s-val">442</span></div></div>
                <div className="stat-card"><div className="s-icon orange"><Database /></div><div className="s-info"><span className="s-label">Total Pool</span><span className="s-val">600</span></div></div>
                <div className="stat-card"><div className="s-icon red"><ShieldAlert /></div><div className="s-info"><span className="s-label">Critical Risks</span><span className="s-val">42</span></div></div>
                <div className="stat-card"><div className="s-icon green"><Activity /></div><div className="s-info"><span className="s-label">Trust Index</span><span className="s-val">94.2%</span></div></div>
            </div>

            {/* HEAT MAP & ALERTS ROW */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '2rem', marginBottom: '2.5rem' }}>
                <div className="glass-premium" style={{ padding: '2.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                        <h3 style={{ fontWeight: 900, display: 'flex', alignItems: 'center', gap: '12px' }}><Layers color="#0070f3" size={24} /> Population Disease HeatMap</h3>
                        <div className="legend"><span>High</span><span>Med</span><span>Low</span></div>
                    </div>
                    <div className="heatmap-grid">
                        {Array.from({ length: 24 }).map((_, i) => (
                            <div key={i} className={`h-cell c-${i % 3}`}></div>
                        ))}
                    </div>
                </div>
                <div className="glass-premium" style={{ padding: '2.5rem' }}>
                    <h3 style={{ fontWeight: 900, marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '10px' }}><AlertTriangle color="#ef4444" size={22} /> Critical Risk Alerts</h3>
                    <div className="alert-list">
                        {[
                            { p: 'Patient #CU-G8015', a: 'Hypertension Spike (180/110)' },
                            { p: 'Patient #CU-G8030', a: 'HbA1c Conflict Found' },
                            { p: 'Source HL7-3', a: 'Sync Latency Drift' }
                        ].map((a, i) => (
                            <div key={i} className="alert-item">
                                <div style={{ flex: 1 }}><strong>{a.p}</strong><p style={{ fontSize: '0.75rem', color: '#ef4444', fontWeight: 700 }}>{a.a}</p></div>
                                <ArrowRight size={14} color="#64748b" />
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* UNIFIED GLOBAL REGISTRY TABLE */}
            <div className="glass-premium" style={{ padding: '2.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2.5rem', alignItems: 'center' }}>
                    <h3 style={{ fontWeight: 900, display: 'flex', alignItems: 'center', gap: '12px' }}><Table color="#0070f3" size={24} /> Global Patient Report Registry (600 Records)</h3>
                    <div className="search-bar"><Search size={16} /> <input type="text" placeholder="Filter 600 golden records..." /></div>
                </div>
                <div className="table-container">
                    <table className="clinical-table">
                        <thead>
                            <tr><th>Report ID</th><th>Status</th><th>Analyzed Risk</th><th>Ingestion Source</th><th>Verification Tier</th></tr>
                        </thead>
                        <tbody>
                            {fakeRegistry.slice(0, 100).map((row, i) => (
                                <tr key={i}>
                                    <td><strong>{row.id}</strong></td>
                                    <td><span className="badge s-badge">{row.status}</span></td>
                                    <td><span className={`badge r-badge ${row.status === 'Critical' ? 'critical' : row.status === 'Warning' ? 'warning' : 'stable'}`}>{row.status === 'Analyzed' ? 'Stable' : row.status}</span></td>
                                    <td style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 700 }}>{row.source}</td>
                                    <td>{row.isGolden ? <span className="badge g-badge"><Gem size={10} /> VERIFIED GOLDEN</span> : <span className="badge p-badge">PENDING CLASH</span>}</td>
                                </tr>
                            ))}
                            <tr><td colSpan="5" style={{ padding: '3rem', textAlign: 'center', fontWeight: 900, color: '#64748b', background: '#f8fafc' }}>... SYNCING ADDITIONAL 500 RECORDS TO MASTER DASHBOARD ...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );

    const renderPatientDashboard = () => (
        <div className="content-fade-in patient-scroll">
            <h2 style={{ fontWeight: 900, fontSize: '2.8rem', letterSpacing: '-0.03em', marginBottom: '0.5rem' }}>My Health Dossier</h2>
            <p style={{ color: '#0070f3', fontWeight: 900, fontSize: '0.9rem', marginBottom: '3.5rem' }}>VERIFIED RECORD FOR: {userName?.toUpperCase()}</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '1.5rem' }}>
                <div className="p-card"><div className="p-icon blue"><HeartPulse /></div><h3>Hypertension Cluster</h3><p>Verified. Stage 1.</p></div>
                <div className="p-card"><div className="p-icon pink"><Activity /></div><h3>Diabetes Indicators</h3><p>Verified. HbA1c 6.8.</p></div>
                <div className="p-card"><div className="p-icon green"><Database /></div><h3>Lipid Cluster</h3><p>Verified. High LDL-C.</p></div>
            </div>
        </div>
    );

    return (
        <div className="layout">
            <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={handleFileUpload} accept="*" />
            <aside className="sidebar">
                <div style={{ padding: '0 0.5rem', marginBottom: '4rem' }}><Logo size={32} /></div>
                <nav>
                    {userRole === 'Doctor' ? (
                        <>
                            <div className={`nav-item ${activeTab === 'oversight' ? 'active' : ''}`} onClick={() => setActiveTab('oversight')}><LayoutDashboard size={20} /> Oversight HUB</div>
                            <div className={`nav-item ${activeTab === 'intelligence' ? 'active' : ''}`} onClick={() => setActiveTab('intelligence')}><Sparkles size={20} /> Registry Intel</div>
                            <div className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}><UploadCloud size={20} /> Ingestion Hub</div>
                        </>
                    ) : (
                        <>
                            <div className={`nav-item ${activeTab === 'dossier' ? 'active' : ''}`} onClick={() => setActiveTab('dossier')}><ClipboardList size={20} /> My Dossier</div>
                            <div className={`nav-item ${activeTab === 'intelligence' ? 'active' : ''}`} onClick={() => setActiveTab('intelligence')}><MessageSquare size={20} /> Ask AI Partner</div>
                            <div className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}><UploadCloud size={20} /> My Reports</div>
                        </>
                    )}
                </nav>
                <div style={{ marginTop: 'auto' }}><div className="nav-item logout" onClick={() => { localStorage.clear(); navigate('/login'); }}><LogOut size={20} /> Sign Out</div></div>
            </aside>
            <main className="main">
                <header style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3.5rem', alignItems: 'center' }}>
                    <Logo size={28} />
                    <div className="identity-pill"><div className="avatar">{userName[0] || 'U'}</div><div style={{ textAlign: 'left' }}><strong>{userName}</strong><p>{userRole.toUpperCase()}</p></div></div>
                </header>

                {activeTab === 'oversight' && renderDoctorDashboard()}
                {activeTab === 'dossier' && renderPatientDashboard()}

                {activeTab === 'intelligence' && (
                    <div className="content-fade-in chat-layout" style={{ height: 'calc(100vh - 250px)' }}>
                        <div className="glass-premium chat-container">
                            <div className="chat-header">
                                <h3 style={{ fontWeight: 900 }}><BrainCircuit size={18} color="#0070f3" /> {userRole === 'Doctor' ? 'Registry Intelligence Engine' : 'AI Health Partner'}</h3>
                                <div className="dot-label"><div className="dot"></div> ONLINE</div>
                            </div>
                            <div className="chat-body">
                                {chatHistory.map((c, i) => (<div key={i} className={`bubble-${c.role}`}>{c.text}</div>))}
                                {isAiTyping && <div className="loader"><span></span><span></span><span></span></div>}
                                <div ref={chatEndRef}></div>
                            </div>
                            <form onSubmit={(e) => { e.preventDefault(); handleQuery(userInput); }} className="chat-footer">
                                <input type="text" placeholder={userRole === 'Doctor' ? "Analyze 600 Golden Records..." : "Ask your partner..."} value={userInput} onChange={e => setUserInput(e.target.value)} />
                                <button type="submit"><ArrowRight size={20} /></button>
                            </form>
                        </div>
                    </div>
                )}

                {activeTab === 'upload' && (
                    <div className="content-fade-in">
                        <h2 style={{ fontWeight: 900, marginBottom: '2.5rem', fontSize: '2.2rem' }}>Unified Ingestion Hub</h2>
                        <div className="glass-premium" style={{ padding: '6rem', border: '3.5rem dashed #e2e8f0', borderRadius: '60px', textAlign: 'center' }}>
                            {isIngesting ? <div className="ingest-pulse"><Loader2 size={64} className="spin" color="#0070f3" /><p style={{ marginTop: '2rem', fontWeight: 900 }}>SYNCING TO GOLDEN REGISTRY...</p></div> : (
                                <>
                                    <h3 style={{ fontSize: '2.2rem', fontWeight: 900, marginBottom: '4rem' }}>Universal Source Ingestion</h3>
                                    <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
                                        {['CSV', 'PDF', 'IMAGE', 'VOICE', 'WORD'].map(t => (
                                            <button key={t} className="btn-v-large" onClick={handleFilePicker}><span>{t}</span></button>
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                )}
            </main>

            <style dangerouslySetInnerHTML={{
                __html: `
                @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
                * { margin:0; padding:0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }
                body { background: #fbfcfe; color: #1e293b; }
                .layout { display: flex; height: 100vh; width: 100vw; }
                .sidebar { width: 300px; background: white; border-right: 1px solid #f1f5f9; padding: 3rem 1.5rem; display:flex; flex-direction:column; }
                .main { flex: 1; padding: 3.5rem 5rem; overflow-y: auto; }
                .nav-item { display: flex; align-items: center; gap: 16px; padding: 18px 22px; border-radius: 20px; color: #64748b; font-weight: 800; cursor: pointer; margin-bottom: 8px; transition: 0.2s; }
                .nav-item.active { background: #0070f3; color: white; box-shadow: 0 12px 24px rgba(0,112,243,0.25); }
                .stat-card { background:white; padding:1.8rem; border-radius:28px; border:1px solid #f1f5f9; display:flex; align-items:center; gap:15px; box-shadow:0 8px 30px rgba(0,0,0,0.02); }
                .s-label { font-size:0.75rem; font-weight:800; color:#64748b; display:block; }
                .s-val { font-size:1.6rem; font-weight:900; }
                .s-icon { width:50px; height:50px; border-radius:14px; display:flex; align-items:center; justify-content:center; }
                .s-icon.blue { background:#eff6ff; color:#0070f3; } .s-icon.orange { background:#fff7ed; color:#f59e0b; } .s-icon.red { background:#fef2f2; color:#ef4444; } .s-icon.green { background:#f0fdf4; color:#10b981; }
                
                .heatmap-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }
                .h-cell { height: 40px; border-radius: 8px; }
                .c-1 { background: #eff6ff; } .c-2 { background: #60a5fa; } .c-0 { background: #1d4ed8; }
                .legend { display:flex; gap:10px; font-size:0.7rem; font-weight:900; }
                
                .alert-item { padding:1.2rem; background:#fef2f2; border-radius:18px; display:flex; align-items:center; gap:15px; margin-bottom:12px; border:1px solid #fee2e2; }
                
                .table-container { max-height: 500px; overflow-y: auto; margin-top: 1rem; }
                .clinical-table { width: 100%; border-collapse: collapse; }
                .clinical-table th { text-align: left; padding: 1.2rem; background: #f8fafc; color: #64748b; font-size: 0.75rem; font-weight: 800; border-bottom: 2px solid #f1f5f9; position: sticky; top: 0; z-index: 10; }
                .clinical-table td { padding: 1.2rem; font-weight: 700; font-size: 0.9rem; border-bottom: 1px solid #f1f5f9; }
                
                .badge { padding: 4px 12px; border-radius: 50px; font-size: 0.65rem; font-weight: 900; width:fit-content; }
                .s-badge { background: #f1f5f9; color: #0f172a; }
                .r-badge.critical { background: #fef2f2; color: #ef4444; }
                .r-badge.warning { background: #fff7ed; color: #f59e0b; }
                .r-badge.stable { background: #f0fdf4; color: #10b981; }
                .g-badge { background: #eff6ff; color: #0070f3; display:flex; align-items:center; gap:6px; }
                .p-badge { background: #f8fafc; color: #64748b; }

                .glass-premium { background: white; border-radius: 40px; border: 1px solid #f1f5f9; box-shadow: 0 10px 40px rgba(0,0,0,0.02); }
                .p-card { background:white; padding:2rem; border-radius:32px; border:1px solid #f1f5f9; }
                .p-icon { width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; margin-bottom:1.5rem; }
                .p-icon.blue { background:#eff6ff; color:#0070f3; } .p-icon.pink { background:#fdf2f8; color:#db2777; } .p-icon.green { background:#f0fdf4; color:#10b981; }
                
                .chat-container { display:flex; flex-direction:column; height: 100%; overflow:hidden; }
                .chat-header { padding:2rem; border-bottom:1px solid #f1f5f9; display:flex; justifyContent:space-between; }
                .chat-body { flex:1; padding:2.5rem; overflow-y:auto; display:flex; flex-direction:column; gap:1.5rem; }
                .bubble-user { background:#0070f3; color:white; padding:1.4rem 2rem; border-radius:28px 28px 4px 28px; align-self:flex-end; font-weight:600; font-size:1rem; }
                .bubble-ai { background:#f1f5f9; color:#0f172a; padding:1.4rem 2rem; border-radius:28px 28px 28px 4px; align-self:flex-start; font-weight:600; font-size:1rem; line-height:1.6; }
                .chat-footer { padding:2rem; border-top:1px solid #f1f5f9; display:flex; gap:15px; align-items:center; }
                .chat-footer input { flex:1; padding:18px; border-radius:20px; border:1px solid #e2e8f0; outline:none; font-weight:600; font-size:1rem; }
                .btn-v-large { background:white; border:1px solid #f1f5f9; padding:20px 40px; border-radius:25px; font-weight:900; font-size:1rem; cursor:pointer; transition:0.3s; }
                .identity-pill { display: flex; align-items: center; gap: 14px; background: white; padding: 10px 22px 10px 10px; border-radius: 60px; border: 1px solid #f1f5f9; }
                .avatar { width: 42px; height: 42px; border-radius: 50%; background: #0070f3; color: white; display:flex; align-items:center; justify-content:center; font-weight:900; }
                .dot-label { font-size:0.7rem; font-weight:900; color:#10b981; display:flex; align-items:center; gap:10px; }
                .dot { width:10px; height:10px; background:#10b981; border-radius:50%; box-shadow:0 0 15px #10b981; }
                .content-fade-in { animation: fadeIn 0.4s ease-out; }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
                .spin { animation: spin 2s linear infinite; }
                .ingest-pulse { animation: pulse 2s infinite; }
            ` }} />
        </div>
    );
};

export default Dashboard;
