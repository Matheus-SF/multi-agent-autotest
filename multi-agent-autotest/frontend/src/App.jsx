import { useState, useRef } from "react";

const API_URL = "https://friendly-trout-r47rw4px56qjcx7xp-8080.app.github.dev/api";

export default function App() {
  const [files, setFiles] = useState([]);
  const [threshold, setThreshold] = useState(80);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef();

  const handleFiles = (incoming) => {
    const pyFiles = Array.from(incoming).filter((f) => f.name.endsWith(".py"));
    setFiles((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...pyFiles.filter((f) => !names.has(f.name))];
    });
  };

  const removeFile = (name) =>
    setFiles((prev) => prev.filter((f) => f.name !== name));

  const handleSubmit = async () => {
    if (!files.length) return;
    setLoading(true);
    setReport(null);
    setError(null);

    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("threshold", threshold);
    form.append("max_iterations", 5);

    try {
      const res = await fetch(`${API_URL}/analyze`, { method: "POST", body: form });
      if (!res.ok) throw new Error((await res.json()).detail);
      setReport(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const coverageColor = (pct) => {
    if (pct >= 80) return "var(--green)";
    if (pct >= 50) return "var(--amber)";
    return "var(--red)";
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
          --bg:        #0f1318;
          --surface:   #151a21;
          --surface2:  #1c2330;
          --border:    #252d3a;
          --border2:   #2e3848;
          --text:      #cdd6e0;
          --muted:     #4e5f72;
          --accent:    #4d9de0;
          --accent-dim:#1a3a56;
          --green:     #4caf82;
          --amber:     #d4a94a;
          --red:       #c05c5c;
          --shadow:    0 4px 24px rgba(0,0,0,.35);
        }

        body {
          font-family: 'IBM Plex Sans', sans-serif;
          background: var(--bg);
          color: var(--text);
          min-height: 100vh;
          font-size: 14px;
        }

        .shell {
          display: grid;
          grid-template-columns: 300px 1fr;
          min-height: 100vh;
        }

        /* ── SIDEBAR ── */
        .sidebar {
          background: var(--surface);
          border-right: 1px solid var(--border);
          padding: 36px 24px;
          display: flex;
          flex-direction: column;
          gap: 32px;
          position: sticky;
          top: 0;
          height: 100vh;
          overflow-y: auto;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 10px;
          padding-bottom: 24px;
          border-bottom: 1px solid var(--border);
        }
        .logo-icon {
          width: 32px; height: 32px;
          background: var(--accent-dim);
          border: 1px solid var(--accent);
          border-radius: 6px;
          display: flex; align-items: center; justify-content: center;
          font-size: 15px;
        }
        .logo-text {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 13px;
          font-weight: 500;
          color: var(--text);
          line-height: 1.3;
        }
        .logo-text small {
          display: block;
          font-size: 10px;
          color: var(--muted);
          font-weight: 400;
        }

        /* SECTION LABEL */
        .section-label {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          letter-spacing: .12em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 10px;
        }

        /* DROPZONE */
        .dropzone {
          border: 1px dashed var(--border2);
          border-radius: 8px;
          padding: 24px 16px;
          text-align: center;
          cursor: pointer;
          transition: border-color .2s, background .2s;
        }
        .dropzone:hover, .dropzone.over {
          border-color: var(--accent);
          background: var(--accent-dim);
        }
        .dropzone-icon { font-size: 24px; margin-bottom: 8px; display: block; opacity: .6; }
        .dropzone p { font-size: 12px; color: var(--muted); line-height: 1.6; }
        .dropzone strong { color: var(--accent); font-weight: 500; }

        /* FILE LIST */
        .file-list { display: flex; flex-direction: column; gap: 6px; }
        .file-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: var(--surface2);
          border: 1px solid var(--border);
          border-radius: 6px;
          padding: 8px 12px;
          animation: fadeUp .15s ease;
        }
        .file-item span {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          color: var(--text);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 190px;
        }
        .file-item button {
          background: none; border: none; cursor: pointer;
          color: var(--muted); font-size: 15px;
          padding: 0 0 0 8px; flex-shrink: 0;
          transition: color .15s;
        }
        .file-item button:hover { color: var(--red); }

        /* THRESHOLD */
        .threshold-row { display: flex; align-items: center; gap: 12px; }
        input[type=range] {
          flex: 1; accent-color: var(--accent);
          cursor: pointer; height: 2px;
        }
        .threshold-val {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 18px;
          font-weight: 500;
          color: var(--accent);
          min-width: 44px;
          text-align: right;
        }

        /* BUTTON */
        .btn {
          width: 100%;
          padding: 12px;
          background: var(--accent);
          color: #0a1520;
          border: none;
          border-radius: 7px;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 12px;
          font-weight: 500;
          letter-spacing: .06em;
          cursor: pointer;
          transition: opacity .2s, transform .15s;
          margin-top: auto;
        }
        .btn:hover:not(:disabled) { opacity: .85; transform: translateY(-1px); }
        .btn:disabled { opacity: .3; cursor: not-allowed; }

        /* ── MAIN ── */
        .main {
          padding: 48px 52px;
          display: flex;
          flex-direction: column;
          gap: 36px;
        }

        .main-header {
          border-bottom: 1px solid var(--border);
          padding-bottom: 28px;
        }
        .main-header h1 {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 20px;
          font-weight: 500;
          color: var(--text);
          margin-bottom: 8px;
        }
        .main-header p {
          font-size: 13px;
          color: var(--muted);
          line-height: 1.7;
          max-width: 520px;
          font-weight: 300;
        }

        /* PIPELINE STEPS */
        .pipeline {
          display: flex;
          align-items: center;
          gap: 0;
          flex-wrap: wrap;
          gap: 4px;
        }
        .step {
          display: flex;
          align-items: center;
          gap: 8px;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 6px;
          padding: 8px 14px;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          color: var(--muted);
        }
        .step.active { border-color: var(--accent); color: var(--accent); background: var(--accent-dim); }
        .step-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
        .step-arrow { color: var(--border2); font-size: 16px; padding: 0 2px; }

        /* EMPTY */
        .empty {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 12px;
          color: var(--muted);
          text-align: center;
          padding: 80px 0;
        }
        .empty-icon { font-size: 40px; opacity: .25; }
        .empty p { font-size: 13px; font-weight: 300; max-width: 260px; line-height: 1.7; }

        /* LOADER */
        .loader {
          display: flex; flex-direction: column;
          align-items: center; gap: 20px;
          padding: 80px 0; color: var(--muted);
        }
        .loader-bar {
          width: 200px; height: 2px;
          background: var(--border);
          border-radius: 2px;
          overflow: hidden;
        }
        .loader-bar::after {
          content: '';
          display: block;
          height: 100%;
          width: 40%;
          background: var(--accent);
          border-radius: 2px;
          animation: slide 1.4s infinite ease-in-out;
        }
        .loader p { font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: .06em; }

        /* REPORT */
        .report { display: flex; flex-direction: column; gap: 24px; animation: fadeUp .3s ease; }

        /* COVERAGE HERO */
        .coverage-hero {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 28px 32px;
          display: flex;
          align-items: center;
          gap: 36px;
        }
        .coverage-ring { position: relative; width: 88px; height: 88px; flex-shrink: 0; }
        .coverage-ring svg { transform: rotate(-90deg); }
        .ring-bg { fill: none; stroke: var(--border2); stroke-width: 7; }
        .ring-fill { fill: none; stroke-width: 7; stroke-linecap: round; }
        .ring-label {
          position: absolute; inset: 0;
          display: flex; flex-direction: column;
          align-items: center; justify-content: center;
        }
        .ring-label strong {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 18px; font-weight: 500; line-height: 1;
        }
        .ring-label small { font-size: 9px; color: var(--muted); letter-spacing: .08em; margin-top: 2px; }

        .coverage-meta h2 {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 16px; font-weight: 500; margin-bottom: 6px;
        }
        .coverage-meta p { font-size: 13px; color: var(--muted); line-height: 1.6; font-weight: 300; }
        .meta-pills { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }
        .pill {
          padding: 4px 10px;
          border-radius: 4px;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          border: 1px solid var(--border2);
          color: var(--muted);
          background: var(--surface2);
        }
        .pill.accent { border-color: var(--accent); color: var(--accent); background: var(--accent-dim); }

        /* CARDS GRID */
        .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 24px;
        }
        .card h3 {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px; letter-spacing: .12em;
          text-transform: uppercase; color: var(--muted);
          margin-bottom: 16px;
        }

        /* UNCOVERED */
        .uncovered-list { display: flex; flex-direction: column; gap: 8px; }
        .uncovered-file {
          background: var(--surface2);
          border: 1px solid var(--border);
          border-radius: 6px;
          padding: 10px 14px;
        }
        .uncovered-file .fname {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px; font-weight: 500;
          color: var(--text); margin-bottom: 8px;
        }
        .lines { display: flex; flex-wrap: wrap; gap: 5px; }
        .line-badge {
          background: rgba(192,92,92,.12);
          border: 1px solid rgba(192,92,92,.25);
          color: var(--red);
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px; padding: 2px 7px;
          border-radius: 3px;
        }

        /* CODE */
        .code-wrap { grid-column: 1 / -1; }
        .code-block {
          background: #0a0e13;
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 24px;
          overflow-x: auto;
          max-height: 420px;
        }
        .code-block pre {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 12px; line-height: 1.75;
          color: #8bacc8; white-space: pre-wrap; word-break: break-all;
        }

        /* ERROR */
        .error-box {
          background: rgba(192,92,92,.08);
          border: 1px solid rgba(192,92,92,.25);
          border-radius: 8px; padding: 16px 20px;
          color: var(--red); font-size: 13px; line-height: 1.6;
          font-family: 'IBM Plex Mono', monospace;
        }

        @keyframes slide {
          0%   { transform: translateX(-100%); }
          50%  { transform: translateX(250%); }
          100% { transform: translateX(250%); }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 860px) {
          .shell { grid-template-columns: 1fr; }
          .sidebar { position: static; height: auto; }
          .main { padding: 28px 20px; }
          .cards { grid-template-columns: 1fr; }
          .coverage-hero { flex-direction: column; }
        }
      `}</style>

      <div className="shell">
        {/* SIDEBAR */}
        <aside className="sidebar">
          <div className="logo">
            <div className="logo-icon">🧪</div>
            <div className="logo-text">
              autotest
              <small>multi-agent · pytest</small>
            </div>
          </div>

          <div>
            <p className="section-label">Arquivos</p>
            <div
              className={`dropzone${dragOver ? " over" : ""}`}
              onClick={() => inputRef.current.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
            >
              <span className="dropzone-icon">📂</span>
              <p>Arraste arquivos <strong>.py</strong> aqui<br />ou clique para selecionar</p>
              <input
                ref={inputRef} type="file" accept=".py" multiple
                style={{ display: "none" }}
                onChange={(e) => handleFiles(e.target.files)}
              />
            </div>
          </div>

          {files.length > 0 && (
            <div>
              <p className="section-label">{files.length} arquivo{files.length > 1 ? "s" : ""} selecionado{files.length > 1 ? "s" : ""}</p>
              <div className="file-list">
                {files.map((f) => (
                  <div className="file-item" key={f.name}>
                    <span>{f.name}</span>
                    <button onClick={() => removeFile(f.name)}>×</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="section-label">Threshold de cobertura</p>
            <div className="threshold-row">
              <input
                type="range" min={50} max={100} step={5}
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
              />
              <span className="threshold-val">{threshold}%</span>
            </div>
          </div>

          <button className="btn" disabled={!files.length || loading} onClick={handleSubmit}>
            {loading ? "ANALISANDO..." : "GERAR TESTES →"}
          </button>
        </aside>

        {/* MAIN */}
        <main className="main">
          <div className="main-header">
            <h1>// multi-agent-autotest</h1>
            <p>
              Envie seus arquivos Python, defina o threshold e os agentes
              analisam, geram, executam e iteram os testes até atingir a meta de cobertura.
            </p>
          </div>

          {/* PIPELINE VISUAL */}
          <div className="pipeline">
            {["analyzer", "writer", "executor", "reviewer"].map((s, i) => (
              <>
                <div className={`step ${loading ? "active" : ""}`} key={s}>
                  <span className="step-dot" />
                  {s}
                </div>
                {i < 3 && <span className="step-arrow" key={`a${i}`}>→</span>}
              </>
            ))}
          </div>

          {!loading && !report && !error && (
            <div className="empty">
              <span className="empty-icon">⬡</span>
              <p>Adicione arquivos .py na barra lateral para iniciar a análise.</p>
            </div>
          )}

          {loading && (
            <div className="loader">
              <div className="loader-bar" />
              <p>AGENTS RUNNING...</p>
            </div>
          )}

          {error && <div className="error-box">// ERROR: {error}</div>}

          {report && (
            <div className="report">
              <div className="coverage-hero">
                <CoverageRing pct={report.coverage_pct} color={coverageColor(report.coverage_pct)} />
                <div className="coverage-meta">
                  <h2>{report.coverage_pct >= threshold ? "// threshold reached" : "// partial coverage"}</h2>
                  <p>{report.review_reason}</p>
                  <div className="meta-pills">
                    <span className="pill accent">{report.coverage_pct}% covered</span>
                    <span className="pill">{report.iteration} iteration{report.iteration !== 1 ? "s" : ""}</span>
                    <span className="pill">{files.length} file{files.length > 1 ? "s" : ""}</span>
                  </div>
                </div>
              </div>

              <div className="cards">
                {Object.keys(report.uncovered_lines || {}).length > 0 && (
                  <div className="card">
                    <h3>Linhas não cobertas</h3>
                    <div className="uncovered-list">
                      {Object.entries(report.uncovered_lines).map(([file, lines]) => (
                        <div className="uncovered-file" key={file}>
                          <div className="fname">{file}</div>
                          <div className="lines">
                            {lines.map((l) => <span className="line-badge" key={l}>L{l}</span>)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="card code-wrap">
                  <h3>Testes gerados</h3>
                  <div className="code-block">
                    <pre>{report.tests_code}</pre>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  );
}

function CoverageRing({ pct, color }) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  return (
    <div className="coverage-ring">
      <svg width="88" height="88" viewBox="0 0 88 88">
        <circle className="ring-bg" cx="44" cy="44" r={r} />
        <circle
          className="ring-fill" cx="44" cy="44" r={r}
          stroke={color} strokeDasharray={circ} strokeDashoffset={offset}
        />
      </svg>
      <div className="ring-label">
        <strong style={{ color }}>{pct}%</strong>
        <small>COV</small>
      </div>
    </div>
  );
}