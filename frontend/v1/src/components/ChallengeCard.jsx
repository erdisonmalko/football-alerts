import styles from './ChallengeCard.module.css'
import { acceptChallenge, declineChallenge } from '../api/endpoints'
import { parseApiError } from '../api/errorHandler'

import { useState } from 'react'

function formatTimeLeft(expiresAt) {
  const now = new Date()
  const end = new Date(expiresAt)
  const diff = Math.floor((end - now) / 1000)

  if (diff <= 0) return "Started"

  const hours = Math.floor(diff / 3600)
  const mins = Math.floor((diff % 3600) / 60)

  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins}m`
}

export default function ChallengeCard({ challenge, tab, onRefresh }) {
  const [loading, setLoading] = useState(false)
  const [prediction, setPrediction] = useState('')
  const [error, setError] = useState(null)
  const [responded, setResponded] = useState(null) // 'accepted' | 'declined'
  const isIncoming = tab === 'incoming'
  const isServer = tab === 'server'
  const myStatus = challenge.my_entry?.status
  const myPrediction = challenge.my_entry?.prediction
  const challengeStatus = challenge.status

  console.log("[ChallengeCard] details", { challenge, myStatus, challengeStatus })

  // Show actions when user has a pending entry
  const canRespond = myStatus === 'pending' && challengeStatus === 'open'
  const creator =
    challenge.entries?.find(e => e.user_id === challenge.created_by_id)?.full_name
    || "Unknown"


    const handleAccept = async () => {
        if (!prediction) {
            setError("Enter prediction (e.g. 2-1)")
            return
        }
        setLoading(true)
        try {
            await acceptChallenge(challenge.server_id, challenge.id, prediction)
            setResponded('accepted')
            onRefresh && onRefresh()
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to accept")
        } finally {
            setLoading(false)
        }
    }

    const handleDecline = async () => {
        setLoading(true)
        try {
            await declineChallenge(challenge.server_id, challenge.id)
            setResponded('declined')
            onRefresh && onRefresh()
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to decline")
        } finally {
            setLoading(false)
        }
    }

  return (
    <div className={styles.card}>
      {error && <p className={styles.error}>{error}</p>}

      {/* Header */}
      <div className={styles.header}>
        <span className={`${styles.status} ${styles[challenge.status]}`}>
          {challenge.status}
        </span>
        <span className={styles.stake}>{challenge.stake}</span>
      </div>

      {/* Match */}
      <div className={styles.match}>
        <span>{challenge.match.home_team_name}</span>
        <span className={styles.vs}>vs</span>
        <span>{challenge.match.away_team_name}</span>
      </div>

      {/* Meta */}
      <div className={styles.meta}>
        <span>by {creator}</span>
        <span className={styles.time}>
          {formatTimeLeft(challenge.expires_at)}
        </span>
      </div>

      {/* Predictions preview (keep your existing UI) */}
      <div className={styles.predictions}>
        {challenge.entries?.slice(0, 3).map(entry => (
          <div key={entry.id} className={styles.predictionRow}>
            <span className={styles.user}>
              {entry.full_name || entry.email}
            </span>
            <span className={styles.prediction}>
              {entry.prediction || "—"}
            </span>
          </div>
        ))}
      </div>

      {/* Participants */}
      <div className={styles.participants}>
        {challenge.entries?.length || 0} participants
      </div>

      {challenge.my_entry && (
        <div className={styles.myEntry}>
          <span className={`${styles.myStatus} ${styles[myStatus]}`}>
            {myStatus}
          </span>

          {myPrediction && (
            <span className={styles.myPrediction}>
              Your pick: {myPrediction}
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      {canRespond && (
            responded ? (
                <div className={`${styles.respondedMsg} ${styles[responded]}`}>
                {responded === 'accepted' ? '✓ Challenge Accepted' : '✕ Challenge Declined'}
                </div>
            ) : (
                <div className={styles.actions}>
                <input
                    placeholder="2-1"
                    value={prediction}
                    onChange={(e) => setPrediction(e.target.value)}
                    className={styles.input}
                />
                <button onClick={handleAccept} disabled={loading} className={styles.accept}>
                    ACCEPT
                </button>
                <button onClick={handleDecline} disabled={loading} className={styles.decline}>
                    DECLINE
                </button>
                </div>
            )
            )}
    </div>
  )
}