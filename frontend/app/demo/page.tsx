import Link from "next/link";
import { Icon } from "@/components/judge/RelayTrack";
import "./judge.css";

export const metadata = { title: "CareRelay | Start the demo" };

/**
 * The judge start page (Gate 1 `design/mocks/redesign/judge-intro.html`). Static: it reads
 * nothing and writes nothing. The evidence strip is the dated live result recorded in
 * `00-status.md` (16 October 2026), not a value measured by this page.
 */
export default function DemoIntro() {
  return (
    <div className="judge">
      <header className="stage-bar">
        <span className="wordmark">CareRelay</span>
        <span className="sim-note">Built for the NTU LKCMedicine challenge.</span>
      </header>
      <main className="intro">
        <section className="hero">
          <div>
            <h1>Mei has until 6pm.</h1>
            <p>Mei is 72 and fictional. Her plan says to get a same-day review before 6pm. CareRelay checks she understood it, helps her act on it, and never pretends help is arranged when it is not.</p>
            <div className="actions">
              <Link className="btn" href="/demo/stage">Start the demo</Link>
              <a className="textlink" href="#adp">See where Tencent ADP is used</a>
            </div>
          </div>
          <div className="hero-slip">
            <section className="slip" aria-label="Mei's example plan">
              <div className="slip-head"><strong>Mei&apos;s plan</strong><span>Fictional plan. No real care.</span></div>
              <dl className="slip-rows">
                <div><dt><Icon name="calendar" />What to do</dt><dd>Go to the clinic for a same-day review.</dd></div>
                <div><dt><Icon name="clock" />Before</dt><dd>6pm today</dd></div>
                <div><dt><Icon name="person" />Who acts</dt><dd>Mei</dd></div>
              </dl>
            </section>
            <span className="stamp">No one has agreed to help yet</span>
          </div>
        </section>

        <section className="section">
          <h2>What happens in the demo</h2>
          <p>Four steps, about three minutes. Colour shows who is acting at each step.</p>
          <ol className="journey-steps">
            <li className="s-mei"><span className="who">Mei</span><h3>She reads her plan</h3><p>What to do, by when, and who acts. Large text, one action at a time.</p></li>
            <li className="s-adp"><span className="who">Tencent ADP</span><h3>She says it back</h3><p>In her own words. ADP copies out what she said about the action, the time and who acts.</p></li>
            <li className="s-code"><span className="who">CareRelay code</span><h3>Code checks it</h3><p>Fixed rules compare her phrases with the plan. If she said 8pm, it asks about the time.</p></li>
            <li className="s-sim"><span className="who">Simulated provider</span><h3>The booking fails</h3><p>CareRelay keeps the 6pm deadline, says help is not arranged, and points to the nurse line.</p></li>
          </ol>
        </section>

        <section className="section" id="adp">
          <h2>Where Tencent ADP is used</h2>
          <p>ADP reads language. CareRelay&apos;s code makes every decision about the plan. That split is the safety design.</p>
          <div className="split">
            <div>
              <h3 className="yes"><Icon name="adp" />Tencent ADP does</h3>
              <ul>
                {["Read the words Mei confirmed", "Copy out her action, time and who acts",
                  "Flag doubt, “won't”, “or” and changed minds", "Refuse medical questions and injected instructions"].map(t => (
                  <li key={t}><span className="yes"><Icon name="yes" width={3} /></span><span>{t}</span></li>
                ))}
              </ul>
            </div>
            <div className="no-list">
              <h3>Tencent ADP never</h3>
              <ul>
                {["Sets the plan, the deadline or how urgent it is", "Grades whether Mei understood",
                  "Books, sends or closes anything", "Gets a second try if its reply is wrong"].map(t => (
                  <li key={t}><span className="no"><Icon name="no" width={3} /></span><span>{t}</span></li>
                ))}
              </ul>
            </div>
          </div>
          <div className="evidence">
            <b>8 of 8</b><span>recent live ADP calls gave the expected result</span>
            <b>5.1 to 6.2 s</b><span>click to settled screen</span>
          </div>
        </section>
      </main>
      <footer className="judge-credit">Built for the NTU LKCMedicine challenge</footer>
    </div>
  );
}
