import { useCountUp } from "../hooks.js";
import { IconArrow, IconGithub, IconTerminal } from "./icons.jsx";

function Stat({ value, label, accent }) {
  const n = useCountUp(value, true);
  return (
    <div className="stat">
      <div className={`stat-num ${accent ? "accent" : ""}`}>{n}</div>
      <div className="stat-lab">{label}</div>
    </div>
  );
}

export default function Hero({ data }) {
  const t = data.totals;
  return (
    <header className="hero wrap" id="overview">
      <div className="hero-grid">
        <div>
          <span className="eyebrow"><IconTerminal width={15} height={15} /> attack &amp; defend ML</span>
          <h1>
            I break and harden <span className="grad">machine-learning systems</span>.
          </h1>
          <p className="hero-lead">
            A data-scientist's pivot into ML security — {t.projects} self-contained, reproducible
            projects spanning detection engineering, adversarial robustness, model privacy, LLM
            red-teaming, and ML supply-chain. Each one runs offline and is grounded in MITRE
            ATLAS / OWASP. The results below are generated from real runs, not mocked up.
          </p>
          <div className="hero-cta">
            <a className="btn btn-primary" href="#results">See the results <IconArrow /></a>
            <a className="btn" href={data.repoUrl} target="_blank" rel="noreferrer">
              <IconGithub /> Source code
            </a>
          </div>
          <p className="byline">Built &amp; maintained by Nick Lampl · data refreshed {data.generatedAt}</p>
        </div>

        <div className="hero-side">
          <div className="term" aria-hidden="true">
            <div className="term-bar">
              <span className="term-dot" style={{ background: "#f87171" }} />
              <span className="term-dot" style={{ background: "#f0b429" }} />
              <span className="term-dot" style={{ background: "#22c55e" }} />
              <span className="term-title">~/p1-fgsm-mnist — make attack</span>
            </div>
            <div className="term-body">
              <div className="cmd">make attack</div>
              <div className="out">training SmallCNN on MNIST (2 epochs, CPU)…</div>
              <div className="out">clean test accuracy: <span className="ok">98.7%</span></div>
              <div className="out">FGSM eps=0.30 → accuracy: <span className="warn">9.3%</span></div>
              <div className="ok">OK wrote results/metrics.json + figures</div>
            </div>
          </div>
        </div>
      </div>

      <div className="stats">
        <Stat value={t.projects} label="projects" />
        <Stat value={t.projects} label="passing tests" accent />
        <Stat value={t.tracks} label="tracks" />
        <Stat value={t.figures} label="result figures" />
      </div>
    </header>
  );
}
