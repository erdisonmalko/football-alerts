import styles from './ServerChallenges.module.css'
import ChallengeCard from './ChallengeCard'

export default function ServerChallenges({ challenges, onRefresh }) {
  return (
    <div className={styles.challengesSection}>
      <h3 className={styles.sectionTitle}>ONGOING CHALLENGES</h3>

      {challenges && challenges.length > 0 ? (
        <div className={styles.challengesList}>
          {challenges.map(challenge => (
            <ChallengeCard
              key={challenge.id}
              challenge={challenge}
              tab="server"          // 👈 important: special mode
              onRefresh={onRefresh} // 👈 so accept/decline updates list
            />
          ))}
        </div>
      ) : (
        <p className={styles.emptyText}>No ongoing challenges.</p>
      )}
    </div>
  )
}