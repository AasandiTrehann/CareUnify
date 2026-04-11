import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    Activity, 
    ArrowRight, 
    ShieldCheck, 
    Zap, 
    Database, 
    Cpu, 
    MousePointer2, 
    Sparkles, 
    Fingerprint, 
    LineChart,
    ChevronDown
} from 'lucide-react';

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="landing-container">
            {/* NAV BAR */}
            <nav className="glass-nav">
                <div className="logo" style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
                    <div className="logo-icon"><Activity size={20} color="white" /></div>
                    <span>CareUnify</span>
                </div>
                <div className="nav-links">
                    <button className="btn-login" onClick={() => navigate('/login')}>Enter Platform</button>
                </div>
            </nav>

            {/* HERO SECTION */}
            <header className="hero">
                <div className="hero-content">
                    <div className="badge-new"><Sparkles size={14} /> Phase 3 Intelligence is Live</div>
                    <h1>One Patient. One Record. <br /><span className="text-gradient">Infinite Intelligence.</span></h1>
                    <p>The first AI-Native Master Patient Index that resolves clinical fragmentation through Three-Layer Matching and Grounded RAG Intelligence.</p>
                    <div className="hero-btns">
                        <button className="btn-main" onClick={() => navigate('/login')}>Launch Hub <ArrowRight size={18} /></button>
                    </div>
                </div>
                
                {/* FLOATING CARDS DECO */}
                <div className="hero-visual">
                    <div className="float-card c1"><Database size={24} /> <span>5.1k FHIR Atoms</span></div>
                    <div className="float-card c2"><Fingerprint size={24} /> <span>98.2% Precision</span></div>
                    <div className="float-card c3"><Zap size={24} /> <span>Real-time RAG</span></div>
                    <div className="hero-glow"></div>
                </div>
            </header>

            {/* FEATURES GRID */}
            <section id="features" className="features">
                <div className="section-head">
                    <p className="sub">THE ARCHITECTURE</p>
                    <h2>Built for Clinical Truth</h2>
                </div>
                <div className="grid">
                    <div className="feature-card">
                        <div className="f-icon"><Zap color="#0070f3" /></div>
                        <h3>Multimodal Ingestion</h3>
                        <p>Automatically normalize PDF, HL7, and FHIR records into a unified clinical data lake.</p>
                    </div>
                    <div className="feature-card">
                        <div className="f-icon"><Cpu color="#0070f3" /></div>
                        <h3>XGBoost Resolution</h3>
                        <p>Three-layer identity resolution (Fuzzy, Phonetic, Rule-Based) with high-trust auto-merging.</p>
                    </div>
                    <div className="feature-card">
                        <div className="f-icon"><ShieldCheck color="#0070f3" /></div>
                        <h3>Grounded RAG</h3>
                        <p>A clinician-first AI assistant grounded in Master Patient Index provenance. Zero hallucinations.</p>
                    </div>
                </div>
            </section>

            {/* CTA FOOTER */}
            <footer className="footer-cta">
                <div className="cta-box">
                    <h2>Ready to unify your clinical data?</h2>
                    <p>Deploy the CareUnify Intelligence Hub in minutes and start building Golden Identities.</p>
                    <button className="btn-main white" onClick={() => navigate('/login')}>Get Started Now</button>
                </div>
                <div className="footer-bottom">
                    <p>© 2026 CareUnify Platform. Clinical Intelligence. Unified.</p>
                </div>
            </footer>

            <style dangerouslySetInnerHTML={{ __html: `
                @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
                
                :root {
                    --primary: #0070f3;
                    --dark: #0f172a;
                    --text: #334155;
                }

                * { margin:0; padding:0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }
                body { background: #fcfcfd; color: var(--dark); overflow-x: hidden; scroll-behavior: smooth; }

                .landing-container { display: flex; flex-direction: column; }

                /* NAV */
                .glass-nav { 
                    display: flex; justify-content: space-between; align-items: center; 
                    padding: 1.5rem 5%; position: fixed; width: 100%; top: 0; 
                    background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); 
                    z-index: 1000; border-bottom: 1px solid rgba(0,0,0,0.05);
                }
                .logo { display:flex; align-items:center; gap:10px; font-weight:800; font-size:1.2rem; color:var(--primary); }
                .logo-icon { background: var(--primary); padding: 8px; border-radius: 12px; }
                .nav-links { display:flex; align-items:center; gap:2.5rem; }
                .nav-links a { text-decoration: none; color: var(--text); font-weight: 700; font-size: 0.9rem; transition: 0.2s; }
                .nav-links a:hover { color: var(--primary); }
                .btn-login { background: var(--dark); color: white; padding: 10px 24px; border-radius: 12px; border: none; font-weight: 800; cursor: pointer; transition: 0.3s; }
                .btn-login:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }

                /* HERO */
                .hero { 
                    padding: 10rem 5% 5rem; display: flex; align-items: center; 
                    min-height: 90vh; background: radial-gradient(circle at top right, #f0f7ff 0%, #ffffff 50%);
                }
                .hero-content { flex: 1; max-width: 700px; }
                .badge-new { display: inline-flex; align-items: center; gap: 8px; background: #f0f7ff; color: var(--primary); padding: 6px 16px; border-radius: 50px; font-weight: 800; font-size: 0.75rem; margin-bottom: 1.5rem; }
                .hero h1 { font-size: 4.5rem; font-weight: 900; line-height: 1.1; margin-bottom: 2rem; color: #020617; }
                .text-gradient { background: linear-gradient(90deg, #0070f3, #00c2ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
                .hero p { font-size: 1.25rem; color: var(--text); line-height: 1.6; margin-bottom: 3rem; max-width: 600px; }
                .hero-btns { display: flex; gap: 1rem; }
                .btn-main { background: var(--primary); color: white; padding: 16px 32px; border-radius: 14px; border: none; font-weight: 800; display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 1rem; transition: 0.3s; }
                .btn-main:hover { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(0,112,243,0.3); }
                .btn-alt { background: white; border: 1px solid #e2e8f0; padding: 16px 32px; border-radius: 14px; font-weight: 700; cursor: pointer; }

                /* VISUAL */
                .hero-visual { flex: 1; position: relative; height: 500px; display: flex; justify-content: center; align-items: center; }
                .hero-glow { position: absolute; width: 400px; height: 400px; background: var(--primary); filter: blur(150px); opacity: 0.1; z-index: -1; }
                .float-card { 
                    background: white; border-radius: 20px; padding: 16px 24px; 
                    display: flex; align-items: center; gap: 15px; font-weight: 800; 
                    box-shadow: 0 20px 40px rgba(0,0,0,0.06); border: 1px solid #f1f5f9;
                    position: absolute; animation: float 6s ease-in-out infinite;
                }
                .c1 { top: 10%; right: 10%; color: #0070f3; animation-delay: 0s; }
                .c2 { bottom: 20%; left: 10%; color: #10b981; animation-delay: 1s; }
                .c3 { top: 40%; left: 30%; color: #f59e0b; animation-delay: 0.5s; }
                
                @keyframes float { 
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-20px); }
                }

                /* FEATURES */
                .features { padding: 8rem 5%; background: white; }
                .section-head { text-align: center; margin-bottom: 5rem; }
                .sub { color: var(--primary); font-weight: 800; font-size: 0.8rem; letter-spacing: 0.1rem; margin-bottom: 1rem; }
                .section-head h2 { font-size: 3rem; font-weight: 900; }
                .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2.5rem; }
                .feature-card { padding: 3rem; border-radius: 30px; background: #f8fafc; border: 1px solid #f1f5f9; transition: 0.3s; }
                .feature-card:hover { background: white; transform: translateY(-10px); box-shadow: 0 20px 50px rgba(0,0,0,0.05); }
                .f-icon { width: 50px; height: 50px; background: white; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin-bottom: 2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
                .feature-card h3 { font-size: 1.4rem; font-weight: 800; margin-bottom: 1.25rem; }
                .feature-card p { font-size: 1rem; color: var(--text); line-height: 1.6; }

                /* FOOTER CTA */
                .footer-cta { padding: 8rem 5% 4rem; }
                .cta-box { background: var(--dark); padding: 5rem; border-radius: 40px; text-align: center; color: white; position: relative; }
                .cta-box h2 { font-size: 3rem; font-weight: 900; margin-bottom: 1.5rem; }
                .cta-box p { font-size: 1.2rem; color: #94a3b8; margin-bottom: 3rem; }
                .btn-main.white { background: white; color: var(--dark); margin: 0 auto; }
                .footer-bottom { margin-top: 5rem; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 2rem; color: #94a3b8; font-size: 0.9rem; }
            ` }} />
        </div>
    );
};

export default LandingPage;
