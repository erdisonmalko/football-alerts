import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import styles from './Landing.module.css'

const LEAGUES = [
  { code: 'PL',  name: 'Premier League',  country: 'England' },
  { code: 'PD',  name: 'La Liga',         country: 'Spain'   },
  { code: 'SA',  name: 'Serie A',         country: 'Italy'   },
  { code: 'BL1', name: 'Bundesliga',      country: 'Germany' },
  { code: 'FL1', name: 'Ligue 1',         country: 'France'  },
  { code: 'CL',  name: 'Champions League',country: 'Europe'  },
  { code: 'EL',  name: 'Europa League',   country: 'Europe'  },
  { code: 'PPL', name: 'Primeira Liga',   country: 'Portugal'},
  { code: 'DED', name: 'Eredivisie',      country: 'Netherlands'},
]

const TICKER_MATCHES = [
  'Arsenal vs Chelsea', 'Real Madrid vs Barcelona', 'Inter vs AC Milan',
  'Bayern vs Dortmund', 'PSG vs Lyon', 'Man City vs Liverpool',
  'Juventus vs Roma', 'Atletico vs Sevilla', 'Ajax vs PSV',
  'Porto vs Benfica', 'Napoli vs Lazio', 'Leicester vs Villa',
]

const FEATURES = [
  {
    label: '01',
    title: 'THREE ALERTS PER MATCH',
    desc: '1 week, 3 days, and 6 hours before every kickoff. Plan ahead, clear your calendar, then get the final nudge.',
  },
  {
    label: '02',
    title: 'SUBSCRIBE YOUR WAY',
    desc: 'Follow an entire league, a specific club, or a single match you spotted elsewhere. Any combination works.',
  },
  {
    label: '03',
    title: 'EMAIL — NO APP NEEDED',
    desc: 'Alerts land in your inbox. No notifications to enable, no app to keep updated, no account to check.',
  },
  {
    label: '04',
    title: 'ALWAYS UP TO DATE',
    desc: 'Match schedules sync automatically. Reschedules update in the background so your reminders stay accurate.',
  },
]

export default function Landing() {
  const tickerRef = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Stagger entrance animations
    const t = setTimeout(() => setVisible(true), 80)
    return () => clearTimeout(t)
  }, [])

  const doubled = [...TICKER_MATCHES, ...TICKER_MATCHES]

  return (
    <div className={styles.page}>

      {/* ── NAV ── */}
      <nav className={styles.nav}>
        <div className={styles.navLogo}>
          <span className={styles.navMark}>FA</span>
          <span className={styles.navWordmark}>FOOTBALL<br />ALERTS</span>
        </div>
        <div className={styles.navActions}>
          <Link to="/login" className={styles.navLogin}>SIGN IN</Link>
          <Link to="/register" className={styles.navRegister}>GET STARTED</Link>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className={styles.hero}>
        {/* Scrolling match ticker background */}
        <div className={styles.tickerBg} aria-hidden="true">
          {[0, 1, 2].map(row => (
            <div key={row} className={`${styles.tickerRow} ${row % 2 === 1 ? styles.tickerRowReverse : ''}`}>
              {doubled.map((m, i) => (
                <span key={i} className={styles.tickerItem}>{m}</span>
              ))}
            </div>
          ))}
        </div>

        {/* Gradient overlay so ticker fades behind content */}
        <div className={styles.heroOverlay} />

        <div className={`${styles.heroContent} ${visible ? styles.heroVisible : ''}`}>
          <p className={styles.heroPre}>EMAIL ALERTS FOR FOOTBALL FANS</p>
          <h1 className={styles.heroTitle}>
            NEVER<br />
            MISS<br />
            <span className={styles.heroAccent}>KICKOFF</span>
          </h1>
          <p className={styles.heroSub}>
            Subscribe to your leagues and teams. Get email reminders 1 week,
            3 days, and 6 hours before every match.
          </p>
          <div className={styles.heroCtas}>
            <Link to="/register" className={styles.ctaPrimary}>CREATE FREE ACCOUNT</Link>
            <Link to="/login" className={styles.ctaSecondary}>SIGN IN</Link>
          </div>
        </div>

        {/* Bottom rule */}
        <div className={styles.heroRule} />
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className={styles.section}>
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <span className={styles.sectionTag}>HOW IT WORKS</span>
            <h2 className={styles.sectionTitle}>THREE STEPS,<br />ZERO EFFORT</h2>
          </div>

          <div className={styles.steps}>
            <div className={styles.step}>
              <span className={styles.stepNum}>01</span>
              <div className={styles.stepConnector} />
              <h3 className={styles.stepTitle}>CREATE AN ACCOUNT</h3>
              <p className={styles.stepDesc}>Register with your email. Takes under a minute.</p>
            </div>
            <div className={styles.step}>
              <span className={styles.stepNum}>02</span>
              <div className={styles.stepConnector} />
              <h3 className={styles.stepTitle}>PICK YOUR LEAGUES & TEAMS</h3>
              <p className={styles.stepDesc}>Subscribe to any combination of leagues, clubs, or individual matches.</p>
            </div>
            <div className={styles.step}>
              <span className={styles.stepNum}>03</span>
              <div className={styles.stepConnector} />
              <h3 className={styles.stepTitle}>CHECK YOUR INBOX</h3>
              <p className={styles.stepDesc}>We handle the schedule. You just watch the game.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className={`${styles.section} ${styles.sectionDark}`}>
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <span className={styles.sectionTag}>FEATURES</span>
            <h2 className={styles.sectionTitle}>BUILT FOR FANS<br />WHO WATCH FOOTBALL,<br />NOT APPS</h2>
          </div>

          <div className={styles.features}>
            {FEATURES.map(f => (
              <div key={f.label} className={styles.feature}>
                <span className={styles.featureNum}>{f.label}</span>
                <h3 className={styles.featureTitle}>{f.title}</h3>
                <p className={styles.featureDesc}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── LEAGUES ── */}
      <section className={styles.section}>
        <div className={styles.container}>
          <div className={styles.sectionHead}>
            <span className={styles.sectionTag}>COVERAGE</span>
            <h2 className={styles.sectionTitle}>9 LEAGUES<br />SUPPORTED</h2>
          </div>

          <div className={styles.leagueGrid}>
            {LEAGUES.map((lg, i) => (
              <div key={lg.code} className={styles.leagueCard}>
                <span className={styles.leagueIdx}>{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <p className={styles.leagueName}>{lg.name}</p>
                  <p className={styles.leagueCountry}>{lg.country}</p>
                </div>
                <span className={styles.leagueCode}>{lg.code}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── BOTTOM CTA ── */}
      <section className={styles.ctaSection}>
        <div className={styles.container}>
          <p className={styles.ctaTag}>FREE. NO CREDIT CARD.</p>
          <h2 className={styles.ctaBig}>READY FOR<br />THE NEXT MATCH?</h2>
          <Link to="/register" className={styles.ctaPrimary}>CREATE YOUR ACCOUNT</Link>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className={styles.footer}>
        <div className={styles.container}>
          <div className={styles.footerInner}>
            <div className={styles.footerBrand}>
              <span className={styles.navMark} style={{ width: 28, height: 28, fontSize: '0.75rem' }}>FA</span>
              <span className={styles.footerName}>Football Alerts</span>
            </div>
            <p className={styles.footerNote}>
              Match data provided by football-data.org
            </p>
            <div className={styles.footerLinks}>
              <Link to="/login" className={styles.footerLink}>Sign In</Link>
              <Link to="/register" className={styles.footerLink}>Register</Link>
            </div>
          </div>
        </div>
      </footer>

    </div>
  )
}