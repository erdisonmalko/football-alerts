import { useState } from 'react'
import styles from './ServerLeaderboard.module.css'

export default function ServerLeaderboard({ leaderboard }) {
  const [showModal, setShowModal] = useState(false)

  if (!leaderboard) return null

  const topThree = leaderboard.entries?.slice(0, 3) || []
  const allEntries = leaderboard.entries || []

  return (
    <>
      <div className={styles.leaderboardSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>LEADERBOARD</h3>
          {allEntries.length > 3 && (
            <button
              className={styles.viewFullBtn}
              onClick={() => setShowModal(true)}
            >
              VIEW FULL
            </button>
          )}
        </div>

        {topThree.length > 0 ? (
          <div className={styles.leaderboardList}>
            {topThree.map((entry) => (
              <div key={entry.user_id} className={styles.leaderboardEntry}>
                <span className={styles.rank}>#{entry.rank}</span>
                <span className={styles.playerName}>
                  {entry.full_name || entry.email}
                </span>
                <span className={styles.stats}>
                  {entry.total_wins}W {entry.total_losses}L {entry.total_draws}D
                </span>
                <span className={styles.points}>{entry.total_points} pts</span>
              </div>
            ))}
          </div>
        ) : (
          <p className={styles.emptyText}>No leaderboard data yet.</p>
        )}
      </div>

      {showModal && (
        <div className={styles.overlay} onClick={() => setShowModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>Full Leaderboard</h2>
            <div className={styles.modalLeaderboardList}>
              {allEntries.map((entry) => (
                <div key={entry.user_id} className={styles.modalEntry}>
                  <span className={styles.rank}>#{entry.rank}</span>
                  <span className={styles.playerName}>
                    {entry.full_name || entry.email}
                  </span>
                  <span className={styles.stats}>
                    {entry.total_wins}W {entry.total_losses}L {entry.total_draws}D
                  </span>
                  <span className={styles.points}>{entry.total_points} pts</span>
                </div>
              ))}
            </div>
            <button
              className={styles.closeBtn}
              onClick={() => setShowModal(false)}
            >
              CLOSE
            </button>
          </div>
        </div>
      )}
    </>
  )
}