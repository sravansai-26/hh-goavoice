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
        const isComplete = state === 'complete' && index < 2;
        const isActive = state === 'processing' && index === 1;
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

function SystemStatus() {
  const services = [
    ['STT ADAPTER', 'READY', Mic],
    ['VECTOR INDEX', 'NOT CONNECTED', Database],
    ['RETRIEVER', 'STANDBY', Search],
    ['GENERATOR', 'STANDBY', Sparkles],
    ['GUARDRAILS', 'READY', ShieldCheck],
  ] as const;
  return (
    <div className="status-list">
      {services.map(([name, status, Icon]) => (
        <div className="status-row" key={name}><Icon size={14} /><span>{name}</span><em className={status === 'READY' ? 'status-ready' : ''}><i />{status}</em></div>
      ))}
    </div>
  );
}

function App() {
  const [recorderState, setRecorderState] = useState<RecorderState>('ready');
  const [pipelineState, setPipelineState] = useState<PipelineState>('idle');
  const [seconds, setSeconds] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [strategy, setStrategy] = useState('fixed');
  const [showArchitecture, setShowArchitecture] = useState(false);
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<any[]>([]);
  const [guardrail, setGuardrail] = useState<any>(null);
  const [latency, setLatency] = useState<any>(null);
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
      } else {
        setTranscript('Transcription failed: ' + (sttData.error?.message || 'Unknown error'));
        setPipelineState('idle');
        return;
      }
      
      // Auto-submit to RAG
      await submitQuery(sttData.transcript);
      
    } catch (error) {
      console.error(error);
      setPipelineState('idle');
    }
  };
  
  const submitQuery = async (queryToSubmit: string = transcript) => {
    if (!queryToSubmit) return;
    setPipelineState('processing');
    try {
      const API_BASE = import.meta.env.VITE_API_URL || '';
      const ragRes = await fetch(`${API_BASE}/api/rag/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryToSubmit, strategy }),
      });
      const ragData = await ragRes.json();
      setAnswer(ragData.answer);
      setSources(ragData.sources);
      setIsGrounded(ragData.grounded);
      setGuardrail(ragData.guardrail);
      setLatency(ragData.latency);
      setPipelineState('complete');
    } catch (error) {
      console.error(error);
      setPipelineState('idle');
    }
  };

  const resetRecording = () => {
    setRecorderState('ready');
    setPipelineState('idle');
    setTranscript('');
    setAnswer('');
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
        <div className="task-badge"><span>TASK</span><strong>02</strong></div>
      </header>

      <main>
        <section className="hero" id="ask">
          <div className="hero-copy">
            <div className="hero-kicker"><span className="live-dot" /> DEVELOPMENT MODE <span className="slash">/</span> BACKEND CONTRACT READY</div>
            <h1>Ask the<br /><i>knowledge base.</i></h1>
            <p className="hero-lede">A voice-enabled retrieval system built for HH Goa 2026. Speak naturally — we transcribe, retrieve, verify, then answer.</p>
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
              {recorderState === 'captured' ? <textarea value={transcript} onChange={(event) => setTranscript(event.target.value)} placeholder="Transcription will appear here when the STT adapter is connected." aria-label="Editable transcript" /> : <div className="empty-box"><Waves size={18} /><span>Your next question starts here.</span><small>Press the microphone above to capture audio.</small></div>}
              <div className="panel-footer"><span className="mono">POST /api/voice/transcribe</span>{recorderState === 'captured' && <button className="text-button" onClick={() => submitQuery(transcript)}>SUBMIT</button>}</div>
            </section>

            <section className="panel pipeline-panel">
              <SectionHeading eyebrow="ORCHESTRATION" title="The harness"><span className="connection-indicator"><i /> STANDBY</span></SectionHeading>
              <Pipeline state={pipelineState} />
              <div className="pipeline-note"><Terminal size={15} /><span>Structured stages, retries and typed responses — not a single prompt-in / text-out call.</span></div>
            </section>
          </div>

          <div className="right-column">
            <section className="answer-panel" id="answer">
              <div className="answer-top"><Label tone={isGrounded ? 'green' : 'pink'}>ANSWER</Label><span className="mono">GROUNDING / {isGrounded ? 'PASS' : 'FAIL'}</span></div>
              {answer ? (
                <h2>{answer}</h2>
              ) : (
                <>
                  <h2>Evidence before<br /><i>eloquence.</i></h2>
                  <p className="answer-empty">No answer generated yet. Connect the retrieval service to turn a spoken question into a grounded response.</p>
                </>
              )}
              <div className="guardrail-inline"><ShieldCheck size={18} /><div><strong>SAFE BY DEFAULT</strong><span>Answers only pass when supported by retrieved context.</span></div><LockKeyhole size={15} /></div>
            </section>

            <section className="panel inspector-panel" id="retrieval">
              <SectionHeading eyebrow="RETRIEVAL INSPECTOR" title="Evidence layer"><span className="active-chip"><i /> VECTOR SEARCH</span></SectionHeading>
              <div className="inspector-controls"><div><Label>CHUNK STRATEGY</Label><div className="select-wrap"><SlidersHorizontal size={15} /><select value={strategy} onChange={(event) => setStrategy(event.target.value)} aria-label="Chunk strategy"><option value="hybrid">Hybrid</option><option value="semantic">Semantic</option><option value="fixed">Fixed + overlap</option><option value="metadata">Metadata-aware</option></select><ChevronDown size={14} /></div></div><div className="inspector-metric"><Label>TOP K</Label><strong>5</strong></div><div className="inspector-metric"><Label>SCANNED</Label><strong>{sources.length}</strong></div></div>
              
              {sources.length > 0 ? (
                <div className="evidence-list" style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '300px', overflowY: 'auto' }}>
                  {sources.map((s, idx) => (
                    <div key={idx} style={{ padding: '0.75rem', background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span className="mono">{s.document_id || s.chunk_id}</span>
                        <span>SCORE: {s.score?.toFixed(4)}</span>
                      </div>
                      <p style={{ fontSize: '0.875rem', lineHeight: 1.5, margin: 0 }}>{s.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="evidence-empty"><FileText size={19} /><div><strong>No supporting context retrieved.</strong><span>Evidence cards will appear here after the MSMARCO-XI index is connected.</span></div></div>
              )}
              
              <div className="source-line"><Database size={14} /><span>MSMARCO-XI / AI4BHARAT</span><em>INDEX —</em></div>
            </section>
          </div>
        </section>

        <section className="engineering-section" id="performance">
          <SectionHeading eyebrow="ENGINEERING TELEMETRY" title="Make the system measurable"><span className="muted-note"><Activity size={15} /> Live metrics arrive from the backend</span></SectionHeading>
          <div className="telemetry-grid">
            <div className="latency-card"><div className="card-heading"><Gauge size={18} /><Label tone="yellow">LATENCY / MS</Label></div><div className="big-metrics"><div><span>P50</span><strong>—</strong></div><div><span>P70</span><strong>—</strong></div><div><span>P100</span><strong>—</strong></div></div><div className="timeline"><span>0</span><div><i /><i /><i /><i /></div><span>200ms TARGET</span></div></div>
            <div className="benchmark-card"><div className="card-heading"><Clock3 size={18} /><Label tone="pink">BENCHMARK RUN</Label></div><div className="benchmark-title"><strong>—</strong><span>QUERIES MEASURED</span></div><div className="benchmark-row"><span>AVERAGE</span><b>—</b><span>FASTEST</span><b>—</b><span>SLOWEST</span><b>—</b></div><div className="card-caption">Run a representative test set to populate P50 / P70 / P100.</div></div>
          </div>
          <div className="stages-bar"><span>STAGE LATENCY</span>{['STT', 'QUERY', 'RETRIEVAL', 'GROUNDING', 'GENERATION', 'TOTAL'].map((stage) => <div key={stage}><b>{stage}</b><strong>{latency ? latency[`${stage.toLowerCase()}_ms`] || 0 : '—'}</strong><small>ms</small></div>)}</div>
        </section>

        <section className="lower-grid">
          <section className="panel strategy-panel"><SectionHeading eyebrow="INDEX DESIGN" title="Chunking strategy explorer"><span className="mono">4 STRATEGIES</span></SectionHeading><div className="strategy-list">{strategies.map((item, index) => <div className={`strategy-row strategy-${item.color}`} key={item.name}><span className="strategy-index">0{index + 1}</span><div><strong>{item.name}</strong><small>{item.detail}</small></div><span className="strategy-value">—</span><ArrowUpRight size={16} /></div>)}</div><div className="table-header"><span>STRATEGY</span><span>CHUNKS</span><span>AVG SIZE</span><span>SCORE</span><span>LATENCY</span></div></section>
          <section className="panel system-panel" id="system"><SectionHeading eyebrow="RUNTIME" title="System status"><span className="connection-indicator"><i /> DEVELOPMENT</span></SectionHeading><SystemStatus /><div className="dataset-card"><div><Label tone="yellow">KNOWLEDGE SOURCE</Label><strong>MSMARCO-XI</strong><span>AI4BHARAT · Hugging Face dataset</span></div><ArrowUpRight size={17} /></div><button className="architecture-button" onClick={() => setShowArchitecture((value) => !value)}>{showArchitecture ? 'HIDE' : 'VIEW'} SYSTEM CONTRACT <ArrowDown size={15} /></button>{showArchitecture && <div className="architecture-popover"><code>VOICE → SARVAM STT → QUERY VALIDATION → {strategy.toUpperCase()} RETRIEVAL → GROUNDING → GENERATION → SAFETY</code></div>}</section>
        </section>
      </main>

      <footer><div className="footer-brand"><span>RAG</span><b>//</b><span>GOA</span></div><span>VOICE INTELLIGENCE LAB / TASK 02</span><span className="footer-right"><WifiOff size={13} /> API CONTRACTS READY · LIVE SERVICES NOT CONNECTED</span></footer>
    </div>
  );
}

export default App;
