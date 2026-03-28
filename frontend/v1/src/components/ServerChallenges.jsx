import styles from '../pages/Dashboard.module.css'

export default function ServerChallenges({ challenges }) {
  return (
    <div className={styles.challengesSection}>
      <h3 className={styles.sectionTitle}>ONGOING CHALLENGES</h3>
      {challenges && challenges.length > 0 ? (
        <div className={styles.challengesList}>
          {challenges.map(challenge => (
            <div key={challenge.id} className={styles.challengeCard}>
              <div className={styles.challengeHeader}>
                <span className={styles.challengeStatus}>{challenge.status}</span>
                <span className={styles.stake}>{challenge.stake}</span>
              </div>
              <div className={styles.matchInfo}>
                <span className={styles.homeTeam}>{challenge.match.home_team_name}</span>
                <span className={styles.vs}>vs</span>
                <span className={styles.awayTeam}>{challenge.match.away_team_name}</span>
              </div>
              <div className={styles.participants}>
                <span className={styles.createdBy}>
                  {/* find creator name from entries */}
                  {challenge.entries?.find(e => e.user_id === challenge.created_by_id)?.full_name
                    || challenge.entries?.find(e => e.user_id === challenge.created_by_id)?.email
                    || `User ${challenge.created_by_id}`}
                </span>
                <span className={styles.participantCount}>
                  {challenge.entries?.length || 0} participants
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className={styles.emptyText}>No ongoing challenges.</p>
      )}
    </div>
  )
}