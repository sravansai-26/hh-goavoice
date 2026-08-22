import { useEffect, useRef, useState, type ReactNode } from 'react';
import {
  Activity,
  ArrowDown,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleAlert,
  Clock3,
  Database,
  FileText,
  Gauge,
  GitBranch,
  Layers3,
  Loader2,
  LockKeyhole,
  Mic,
  MicOff,
  Pause,
  Play,
  Radio,
  RotateCcw,
  Search,
  Server,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Square,
  Terminal,
  Waves,
  WifiOff,
  X,
  Zap,
} from 'lucide-react';

type RecorderState = 'ready' | 'recording' | 'captured' | 'denied';
type PipelineState = 'idle' | 'processing' | 'complete';

const pipeline = [
  ['01', 'VOICE', 'Capture audio'],
  ['02', 'TRANSCRIBE', 'Sarvam adapter'],
  ['03', 'CHUNK', 'Strategy selector'],
  ['04', 'RETRIEVE', 'Vector search'],
  ['05', 'GROUND', 'Evidence check'],
  ['06', 'GENERATE', 'Safe response'],
];

const strategies = [
  { name: 'Fixed + overlap', detail: 'Token windows with controlled overlap', color: 'yellow' },
  { name: 'Semantic', detail: 'Boundary-aware document splitting', color: 'cream' },
  { name: 'Metadata-aware', detail: 'Structure and source-aware chunks', color: 'pink' },
  { name: 'Hybrid', detail: 'Candidate strategy for production', color: 'green' },
];

function Label({ children, tone = 'muted' }: { children: ReactNode; tone?: 'muted' | 'yellow' | 'pink' | 'green' }) {
  return <span className={`label label-${tone}`}>{children}</span>;
}

function SectionHeading({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <div className="section-heading">
      <div>
        <Label tone="yellow">{eyebrow}</Label>
        <h2>{title}</h2>
      </div>
      {children}
    </div>
  );
}

function Waveform({ active }: { active: boolean }) {
  return (
    <div className={`waveform ${active ? 'waveform-active' : ''}`} aria-label={active ? 'Live audio waveform' : 'Idle audio waveform'}>
      {Array.from({ length: 34 }).map((_, index) => <span key={index} style={{ '--i': index } as React.CSSProperties} />)}
    </div>
  );
}

function Pipeline({ state }: { state: PipelineState }) {
  return (
    <div className="pipeline" aria-label="Voice to answer pipeline">
      {pipeline.map(([number, name, detail], index) => {
        const isComplete = state === 'complete';
        const isActive = state === 'processing';
        return (
          <div className="pipeline-step" key={name}>
            <div className={`pipeline-node ${isComplete ? 'node-complete' : ''} ${isActive ? 'node-active' : ''}`}>
              {isComplete ? <Check size={15} strokeWidth={3} /> : <span>{number}</span>}
            </div>
            <div className="pipeline-copy"><strong>{name}</strong><small>{detail}</small></div>
            {index < pipeline.length - 1 && <div className={`pipeline-line ${isComplete ? 'line-complete' : ''}`} />}
          </div>
        );
      })}
    </div>
  );
}

function SystemStatus({ isConnected, state }: { isConnected: boolean; state: PipelineState }) {
  const services = [
    ['STT ADAPTER', 'READY', Mic],
    ['VECTOR INDEX', isConnected ? 'CONNECTED' : 'NOT CONNECTED', Database],
    ['RETRIEVER', state === 'processing' ? 'ACTIVE' : 'STANDBY', Search],
    ['GENERATOR', state === 'processing' ? 'ACTIVE' : 'STANDBY', Sparkles],
    ['GUARDRAILS', 'READY', ShieldCheck],
  ] as const;
  return (
    <div className="status-list">
      {services.map(([name, status, Icon]) => (
        <div className="status-row" key={name as string}><Icon size={14} /><span>{name as string}</span><em className={status !== 'NOT CONNECTED' && status !== 'STANDBY' ? 'status-ready' : ''}><i />{status as string}</em></div>
      ))}
    </div>
  );
}

function App() {
  const [recorderState, setRecorderState] = useState<RecorderState>('ready');
  const [pipelineState, setPipelineState] = useState<PipelineState>('idle');
  const [seconds, setSeconds] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [strategy, setStrategy] = useState('hybrid');
  const [showArchitecture, setShowArchitecture] = useState(false);
  
  const [language, setLanguage] = useState<any>(null);
  const [queryInfo, setQueryInfo] = useState<any>(null);
  const [answerData, setAnswerData] = useState<any>(null);
  
  const [sources, setSources] = useState<any[]>([]);
  const [guardrail, setGuardrail] = useState<any>(null);
  const [latency, setLatency] = useState<any>(null);
  const [latencyHistory, setLatencyHistory] = useState<number[]>([]);
  const [isGrounded, setIsGrounded] = useState<boolean>(true);
  
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const audioChunks = useRef<BlobPart[]>([]);

  useEffect(() => {
    if (recorderState !== 'recording') return;
    const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [recorderState]);

  useEffect(() => () => stream.current?.getTracks().forEach((track) => track.stop()), []);

  const startRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setRecorderState('denied');
      return;
    }
    try {
      stream.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream.current);
      audioChunks.current = [];
      setTranscript('');
      
      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };
      
      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        await processAudio(audioBlob);
      };
      
      mediaRecorder.current.start();
      setSeconds(0);
      setRecorderState('recording');
    } catch {
      setRecorderState('denied');
    }
  };

  const stopRecording = () => {
    mediaRecorder.current?.stop();
    stream.current?.getTracks().forEach((track) => track.stop());
    setRecorderState('captured');
    setPipelineState('processing');
  };

  const processAudio = async (audioBlob: Blob) => {
    setPipelineState('processing');
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');
      
      const API_BASE = import.meta.env.VITE_API_URL || '';
      const sttRes = await fetch(`${API_BASE}/api/voice/transcribe`, {
        method: 'POST',
        body: formData,
      });
      
      const sttData = await sttRes.json();
      if (sttData.success) {
        setTranscript(sttData.transcript);
        setLanguage({ detected: sttData.language, name: 'Detected Language' });
        setQueryInfo({ english: sttData.error?.english_transcript });
        setPipelineState('idle');
      } else {
        setTranscript('Transcription failed: ' + (sttData.error?.message || 'Unknown error'));
        setPipelineState('idle');
        return;
      }
    } catch (error) {
      console.error(error);
      setPipelineState('idle');
    }
  };
  
  const submitQuery = async (queryToSubmit: string = transcript, detectedLang: string = "hi") => {
    if (!queryToSubmit) return;
    setPipelineState('processing');
    setSources([]);
    setAnswerData(null);
    setQueryInfo(null);
    setGuardrail(null);
    setLatency(null);
    try {
      const API_BASE = import.meta.env.VITE_API_URL || '';
      const ragRes = await fetch(`${API_BASE}/api/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryToSubmit, strategy, language: detectedLang }),
      });
      
      const ragData = await ragRes.json();
      
      if (!ragRes.ok) {
        throw new Error(ragData.detail || 'RAG Query failed');
      }
      
      setLanguage(ragData.language);
      setQueryInfo(ragData.query);
      setAnswerData(ragData.answer);
      setSources(ragData.sources || []);
      setIsGrounded(ragData.grounded || false);
      setGuardrail(ragData.guardrail);
      setLatency(ragData.latency);
      setLatencyHistory((prev) => [...prev, ragData.latency.total_ms]);
      setPipelineState('complete');
    } catch (error: any) {
      console.error(error);
      setAnswerData({ primary: `Error: ${error.message}`, english: "" });
      setSources([]);
      setPipelineState('complete');
    }
  };

  const resetRecording = () => {
    setRecorderState('ready');
    setPipelineState('idle');
    setTranscript('');
    setLanguage(null);
    setQueryInfo(null);
    setAnswerData(null);
    setSources([]);
    setLatency(null);
    setSeconds(0);
  };

  const formatTime = (value: number) => `00:${String(value).padStart(2, '0')}`;
  const isBusy = recorderState === 'recording';

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#ask" aria-label="RAG Goa home"><span>RAG</span><b>//</b><span>GOA</span></a>
        <div className="brand-subtitle">VOICE INTELLIGENCE LAB <span>/</span> HH GOA 2026</div>
        <nav aria-label="Primary navigation">
          {[['ASK', '#ask'], ['RETRIEVAL', '#retrieval'], ['PERFORMANCE', '#performance'], ['SYSTEM', '#system']].map(([name, href], index) => <a className={index === 0 ? 'active' : ''} href={href} key={name}>{name}</a>)}
        </nav>
        <img src="/hackerhouse.svg" alt="Hacker House" className="hackerhouse-logo" />
      </header>

      <main>
        <section className="hero" id="ask">
          <div className="hero-copy">
            <div className="hero-kicker"><span className="live-dot" /> LIVE RAG PIPELINE <span className="slash">/</span> CONNECTED</div>
            <h1>Ask the<br /><i>knowledge base.</i></h1>
            <p className="hero-lede">A voice-enabled retrieval system built for HH Goa 2026. Speak naturally in any language — we translate, retrieve, verify, and answer.</p>
            <div className="flow-caption"><span>SPEAK NATURALLY</span><ArrowDown size={14} /><span>WE RETRIEVE</span><ArrowDown size={14} /><span>WE VERIFY</span><ArrowDown size={14} /><span>WE ANSWER</span></div>
          </div>
          <div className={`voice-console ${isBusy ? 'console-listening' : ''}`}>
            <div className="console-top"><Label tone={isBusy ? 'pink' : 'yellow'}>{isBusy ? 'LISTENING' : recorderState === 'captured' ? 'AUDIO CAPTURED' : 'VOICE INPUT'}</Label><span className="mono">{formatTime(seconds)}</span></div>
            <div className="mic-stage">
              <div className="mic-orbit orbit-one" /><div className="mic-orbit orbit-two" />
              <button className="mic-button" onClick={isBusy ? stopRecording : startRecording} aria-label={isBusy ? 'Stop recording' : 'Start recording'}>
                {isBusy ? <Square size={28} fill="currentColor" /> : recorderState === 'denied' ? <MicOff size={36} /> : <Mic size={40} />}
              </button>
            </div>
            <div className="console-bottom">
              <div><strong>{isBusy ? 'STOP RECORDING' : recorderState === 'denied' ? 'MICROPHONE UNAVAILABLE' : recorderState === 'captured' ? 'READY TO PROCESS' : 'ASK WITH VOICE'}</strong><span>{recorderState === 'denied' ? 'Permission or browser support required' : isBusy ? 'Speak your question clearly' : 'Press the microphone to begin'}</span></div>
              {recorderState === 'captured' && <button className="icon-button" onClick={resetRecording} aria-label="Retry recording"><RotateCcw size={16} /></button>}
            </div>
            <Waveform active={isBusy} />
          </div>
        </section>

        <section className="signal-strip" aria-label="System promise">
          <div><span>01</span><strong>CAPTURE</strong><small>Voice in</small></div><div><span>02</span><strong>RETRIEVE</strong><small>Evidence out</small></div><div><span>03</span><strong>GROUND</strong><small>Nothing invented</small></div><div><span>04</span><strong>MEASURE</strong><small>Every millisecond</small></div>
        </section>

        <section className="workspace-grid">
          <div className="left-column">
            <section className="panel transcript-panel" id="transcript">
              <SectionHeading eyebrow="VOICE → TEXT" title="Your question"><Label tone={recorderState === 'captured' ? 'green' : 'muted'}>{recorderState === 'captured' ? 'CAPTURED' : 'WAITING'}</Label></SectionHeading>
              
              {recorderState === 'captured' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1, padding: '0 24px', position: 'relative' }}>
                  <div style={{ background: 'var(--dark)', border: '1px solid rgba(244,240,223,.1)', borderRadius: '6px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <Label tone="yellow">PRIMARY TRANSCRIPT</Label>
                      {language && <span style={{ fontSize: '10px', color: 'var(--yellow)', textTransform: 'uppercase' }}>{language.name}</span>}
                    </div>
                    {pipelineState === 'processing' && !transcript ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', color: 'var(--yellow)' }}>
                        <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
                        <span style={{ fontSize: '14px', letterSpacing: '0.04em' }}>Converting speech to text...</span>
                      </div>
                    ) : (
                      <textarea 
                        value={transcript} 
                        onChange={(event) => setTranscript(event.target.value)} 
                        style={{ background: 'transparent', border: 'none', color: 'var(--cream)', width: '100%', fontSize: '15px', resize: 'none', outline: 'none', padding: 0 }}
                        rows={3}
                        aria-label="Editable transcript" 
                      />
                    )}
                  </div>
                </div>
              ) : (
                <div className="empty-box"><Waves size={18} /><span>Your next question starts here.</span><small>Press the microphone above to capture audio.</small></div>
              )}
              
              <div className="panel-footer">
                <span className="mono">POST /api/voice/transcribe</span>
                {recorderState === 'captured' && (
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="text-button" onClick={() => window.location.reload()} style={{ color: 'var(--muted)', cursor: 'pointer', zIndex: 10 }}>CLEAR</button>
                    <button className="text-button submit-pulse" onClick={() => submitQuery(transcript, language?.detected || 'hi')} style={{ zIndex: 10 }}>SUBMIT</button>
                  </div>
                )}
              </div>
            </section>

            <section className="panel pipeline-panel">
              <SectionHeading eyebrow="ORCHESTRATION" title="The harness"><span className="connection-indicator"><i /> STANDBY</span></SectionHeading>
              <Pipeline state={pipelineState} />
              <div className="pipeline-note"><Terminal size={15} /><span>Structured stages, retries and typed responses — not a single prompt-in / text-out call.</span></div>
            </section>
          </div>

          <div className="right-column">
            <section className="answer-panel" id="answer">
              <div className="answer-top">
                <Label tone={isGrounded ? 'green' : 'pink'}>ANSWER</Label>
                <span className="mono">GROUNDING / {isGrounded ? 'PASS' : 'FAIL'}</span>
              </div>
              
              {answerData ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', flex: 1 }}>
                  <div>
                    <h4 style={{ fontSize: '11px', letterSpacing: '0.08em', color: 'var(--yellow)', marginBottom: '10px', textTransform: 'uppercase' }}>{language?.name || 'ANSWER'} — PRIMARY</h4>
                    <h2 style={{ margin: 0, fontSize: 'clamp(20px, 2.5vw, 24px)', lineHeight: 1.3 }}>{answerData.primary}</h2>
                  </div>
                </div>
              ) : pipelineState === 'processing' && transcript ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px', flex: 1, padding: '40px 0' }}>
                  <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--yellow)' }} />
                  <p style={{ margin: 0, fontSize: '14px', color: 'var(--yellow)', letterSpacing: '0.05em' }}>Retrieving context & generating answer...</p>
                </div>
              ) : (
                <>
                  <h2>Evidence before<br /><i>eloquence.</i></h2>
                  <p className="answer-empty">No answer generated yet. Connect the retrieval service to turn a spoken question into a grounded response.</p>
                </>
              )}
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: 'auto', paddingTop: '32px', position: 'relative', zIndex: 10 }}>
                <div className="guardrail-inline" style={{ margin: 0, paddingTop: 0, border: 'none' }}><ShieldCheck size={18} /><div><strong>SAFE BY DEFAULT</strong><span>Answers only pass when supported by retrieved context.</span></div><LockKeyhole size={15} /></div>
              </div>
            </section>

            <section className="panel architecture-panel" style={{ background: 'var(--dark)', color: '#ffffff', border: '1px solid rgba(244,240,223,.2)' }}>
              <div className="section-heading">
                <div>
                  <Label tone="yellow">INFRASTRUCTURE</Label>
                  <h2 style={{ color: '#ffffff' }}>Model Infrastructure</h2>
                </div>
                <span className="active-chip"><i /> ONLINE</span>
              </div>
              
              <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(255,255,255,0.06)', padding: '14px', borderRadius: '6px', border: '1px solid rgba(244,240,223,.15)' }}>
                  <Radio size={20} color="var(--pink)" />
                  <div>
                    <strong style={{ display: 'block', fontSize: '13px', letterSpacing: '0.04em', color: '#ffffff' }}>SARVAM ENGINE</strong>
                    <span style={{ fontSize: '12px', color: '#d0d8cb' }}>High-fidelity Indic language speech recognition</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(255,255,255,0.06)', padding: '14px', borderRadius: '6px', border: '1px solid rgba(244,240,223,.15)' }}>
                  <Database size={20} color="var(--yellow)" />
                  <div>
                    <strong style={{ display: 'block', fontSize: '13px', letterSpacing: '0.04em', color: '#ffffff' }}>QDRANT · VECTOR SEARCH</strong>
                    <span style={{ fontSize: '12px', color: '#d0d8cb' }}>Semantic retrieval from MSMARCO-XI database</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(255,255,255,0.06)', padding: '14px', borderRadius: '6px', border: '1px solid rgba(244,240,223,.15)' }}>
                  <Sparkles size={20} color="var(--green)" />
                  <div>
                    <strong style={{ display: 'block', fontSize: '13px', letterSpacing: '0.04em', color: '#ffffff' }}>GEMINI FLASH · GENERATION</strong>
                    <span style={{ fontSize: '12px', color: '#d0d8cb' }}>Evidence-grounded multilingual reasoning</span>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </section>

        <section className="engineering-section" id="performance">
          <SectionHeading eyebrow="ENGINEERING TELEMETRY" title="Make the system measurable"><span className="muted-note"><Activity size={15} /> Live metrics arrive from the backend</span></SectionHeading>
          <div className="telemetry-grid">
            <div className="latency-card"><div className="card-heading"><Gauge size={18} /><Label tone="yellow">LATENCY / MS</Label></div><div className="big-metrics"><div><span>CURRENT</span><strong>{latency ? latency.total_ms : '—'}</strong></div><div><span>TARGET</span><strong>200</strong></div><div><span>STATUS</span><strong>{latency ? (latency.total_ms <= 200 ? 'PASS' : 'FAIL') : '—'}</strong></div></div><div className="timeline"><span>0</span><div><i /><i /><i /><i /></div><span>200ms TARGET</span></div></div>
            <div className="benchmark-card">
              <div className="card-heading"><Clock3 size={18} /><Label tone="pink">BENCHMARK RUN</Label></div>
              <div className="benchmark-title">
                <strong>{latencyHistory.length}</strong><span>QUERIES MEASURED</span>
              </div>
              <div className="benchmark-row">
                <span>AVERAGE</span><b>{latencyHistory.length ? (latencyHistory.reduce((a,b)=>a+b,0)/latencyHistory.length).toFixed(0) : '—'}</b>
                <span>FASTEST</span><b>{latencyHistory.length ? Math.min(...latencyHistory) : '—'}</b>
                <span>SLOWEST</span><b>{latencyHistory.length ? Math.max(...latencyHistory) : '—'}</b>
              </div>
              <div className="card-caption">Aggregating real-time latency across current session.</div>
            </div>
          </div>
          <div className="stages-bar"><span>STAGE LATENCY</span>{['STT', 'RETRIEVAL', 'GROUNDING', 'GENERATION', 'TOTAL'].map((stage) => <div key={stage}><b>{stage}</b><strong>{latency ? latency[`${stage.toLowerCase()}_ms`] || 0 : '—'}</strong><small>ms</small></div>)}</div>
        </section>

        <section className="lower-grid">
          <section className="panel strategy-panel">
            <SectionHeading eyebrow="INDEX DESIGN" title="Chunking strategy explorer"><span className="mono">4 STRATEGIES</span></SectionHeading>
            <div className="strategy-list">
              {strategies.map((item, index) => {
                const isSelected = item.name.toLowerCase().includes(strategy) || (strategy === 'fixed' && item.name.includes('Fixed'));
                const score = isSelected && sources.length > 0 ? (sources.reduce((acc: number, s: any) => acc + (s.score || 0), 0) / sources.length).toFixed(4) : '—';
                const lat = isSelected && latency ? latency.retrieval_ms + 'ms' : '—';
                return (
                  <div 
                    className={`strategy-row ${isSelected ? `strategy-${item.color}` : ''}`} 
                    key={item.name} 
                    style={{ opacity: isSelected ? 1 : 0.4, cursor: 'pointer' }}
                    onClick={() => {
                      if (item.name.includes('Fixed')) setStrategy('fixed');
                      else if (item.name.includes('Semantic')) setStrategy('semantic');
                      else if (item.name.includes('Metadata')) setStrategy('metadata');
                      else if (item.name.includes('Hybrid')) setStrategy('hybrid');
                    }}
                  >
                    <span className="strategy-index">0{index + 1}</span>
                    <div><strong>{item.name}</strong><small>{item.detail}</small></div>
                    <span className="strategy-value">{score}</span>
                    <span className="strategy-value" style={{ width: '40px', textAlign: 'right' }}>{lat}</span>
                    <ArrowUpRight size={16} style={{ opacity: isSelected ? 1 : 0 }} />
                  </div>
                );
              })}
            </div>
            <div className="table-header"><span>STRATEGY</span><span style={{flex: 2}}>DESCRIPTION</span><span>SCORE</span><span>LATENCY</span></div>
          </section>
          <section className="panel system-panel" id="system"><SectionHeading eyebrow="RUNTIME" title="System status"><span className="connection-indicator"><i /> DEVELOPMENT</span></SectionHeading><SystemStatus isConnected={sources.length > 0} state={pipelineState} /><div className="dataset-card"><div><Label tone="yellow">KNOWLEDGE SOURCE</Label><strong>MSMARCO-XI</strong><span>AI4BHARAT · Hugging Face dataset</span></div><ArrowUpRight size={17} /></div><button className="architecture-button" onClick={() => setShowArchitecture((value) => !value)}>{showArchitecture ? 'HIDE' : 'VIEW'} SYSTEM CONTRACT <ArrowDown size={15} /></button>{showArchitecture && <div className="architecture-popover"><code>VOICE → SARVAM STT → MULTILINGUAL ADAPTER → {strategy.toUpperCase()} RETRIEVAL → GROUNDING → GENERATION → SAFETY</code></div>}</section>
        </section>
      </main>
      <footer>
        <div className="footer-brand"><span>RAG</span><b>//</b><span>GOA</span></div>
        <span>
          Designed and Developed by <strong>Team SyntheticMinds</strong> — <a href="https://buildwithsravan.dev" target="_blank" rel="noreferrer" style={{ color: 'var(--yellow)', textDecoration: 'none' }}>Sravan Sai Vuppula</a> (Founder & Lead Developer at <a href="https://sailyfspot.blogspot.com" target="_blank" rel="noreferrer" style={{ color: 'var(--yellow)', textDecoration: 'none' }}>LYFSpot</a>) and <strong>Sai Balaji</strong> (Software Engineer Intern at HealthTech Mastery Academy) for Hacker House Goa by 2:47 pm studio.
        </span>
        <span className="footer-right"><Activity size={13} /> PRODUCTION READY · SERVICES CONNECTED</span>
      </footer>
    </div>
  );
}

export default App;
