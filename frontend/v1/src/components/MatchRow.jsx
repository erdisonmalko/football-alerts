import styles from '../pages/Dashboard.module.css'

function formatKickoff(dateStr) {
  const d = new Date(dateStr)
  return {
    date: d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' }),
    time: d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) + ' UTC',
  }
}

function timeUntil(dateStr) {
  const diff = new Date(dateStr) - new Date()
  if (diff <= 0) return null
  const days = Math.floor(diff / 86400000)
  const hours = Math.floor((diff % 86400000) / 3600000)
  const mins = Math.floor((diff % 3600000) / 60000)
  if (days >= 7) return `${days}d`
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h`
  return `${mins}m`
}

export default function MatchRow({ match, section }) {
  const { date, time } = formatKickoff(match.kickoff_utc)
  const isLive = section === 'live'
  const isFinished = section === 'finished'

  return (
    <div className={`${styles.matchRow} ${isLive ? styles.matchRowLive : ''} ${isFinished ? styles.matchRowFinished : ''}`}>
      <div className={styles.matchLeague}>
        <span className={styles.leagueCode}>{match.league_code}</span>
        {match.matchday && <span className={styles.matchday}>MD{match.matchday}</span>}
      </div>
      <div className={styles.matchTeams}>
        <span className={styles.teamName}>{match.home_team_name}</span>
        {(isLive || isFinished) && match.home_score !== null ? (
          <span className={styles.score}>{match.home_score} — {match.away_score}</span>
        ) : (
          <span className={styles.vs}>VS</span>
        )}
        <span className={styles.teamName}>{match.away_team_name}</span>
      </div>
      <div className={styles.matchMeta}>
        {isLive ? (
          <span className={styles.liveBadge}>● LIVE</span>
        ) : isFinished ? (
          <span className={styles.finishedBadge}>FINISHED</span>
        ) : (
          <>
            <span className={styles.kickoffDate}>{date}</span>
            <span className={styles.kickoffTime}>{time}</span>
          </>
        )}
        {!isLive && !isFinished && timeUntil(match.kickoff_utc) && (
          <span className={styles.countdown}>{timeUntil(match.kickoff_utc)}</span>
        )}
      </div>
    </div>
  )
}
