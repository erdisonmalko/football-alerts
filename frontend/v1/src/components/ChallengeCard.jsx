import styles from './ChallengeCard.module.css'
import { acceptChallenge, declineChallenge } from '../api/endpoints'
import { parseApiError } from '../api/errorHandler'

import { useState } from 'react'

function formatTimeLeft(expiresAt) {
  const now = new Date()
  const end = new Date(expiresAt)
  const diff = Math.floor((end - now) / 1000)

  if (diff <= 0) return 'Started'

  const hours = Math.floor(diff / 3600)
  const mins = Math.floor((diff % 3600) / 60)

  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins}m`
}

function formatKickoff(kickoffUtc) {
  const date = new Date(kickoffUtc)
  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function getMatchResult(match) {
  if (match.status !== 'FINISHED' || match.home_score == null || match.away_score == null) {
    return null
  }
  return `${match.home_score}-${match.away_score}`
}

function getOutcomeLabel(entry) {
  if (!entry?.result) return null
  return entry.result === 'draw'
    ? 'Draw'
    : entry.result === 'win'
    ? 'Win'
    : entry.result === 'lose'
    ? 'Lose'
    : null
}

export default function ChallengeCard({ challenge, tab, onRefresh }) {
  const [loading, setLoading] = useState(false)
  const [prediction, setPrediction] = useState('')
  const [error, setError] = useState(null)
  const [responded, setResponded] = useState(null) // 'accepted' | 'declined'
  const [showParticipants, setShowParticipants] = useState(false)
  const isIncoming = tab === 'incoming'
  const isServer = tab === 'server'
  const myStatus = challenge.my_entry?.status
  const myPrediction = challenge.my_entry?.prediction
  const challengeStatus = challenge.status
  const match = challenge.match || {}
  const matchResult = getMatchResult(match)
  const userOutcome = getOutcomeLabel(challenge.my_entry)
  const participants = challenge.entries?.length || 0

  console.log('[ChallengeCard] details', { challenge, myStatus, challengeStatus })

  // Show actions when user has a pending entry
  const canRespond = myStatus === 'pending' && challengeStatus === 'open'
  const creator =
    challenge.entries?.find(e => e.user_id === challenge.created_by_id)?.full_name
    || 'Unknown'


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
        <span>{match.league_name || match.league_code || 'League'}</span>
        <span className={styles.time}>
          {challenge.status === 'open' || challenge.status === 'locked'
            ? formatTimeLeft(challenge.expires_at)
            : 'Settled'}
        </span>
      </div>

      <div className={styles.matchMeta}>
        <span className={styles.matchStatus}>{match.status}</span>
        <span className={styles.kickoff}>{formatKickoff(match.kickoff_utc)}</span>
        {matchResult && <span className={styles.matchOutcome}>Final {matchResult}</span>}
      </div>

      {/* Predictions preview (keep your existing UI) */}
      <div className={styles.predictions}>
        {challenge.entries?.slice(0, 3).map(entry => (
          <div key={entry.id} className={styles.predictionRow}>
            <span className={styles.user}>
              {entry.full_name || entry.email}
            </span>
            <span className={styles.prediction}>
              {entry.prediction || '—'}
            </span>
          </div>
        ))}
      </div>

      {/* Participants */}
      <div className={styles.participantsRow}>
        <div className={styles.participants}>
          {participants} participants
        </div>
        {participants > 3 && (
          <button
            className={styles.viewAllBtn}
            onClick={() => setShowParticipants(true)}
          >
            View all
          </button>
        )}
      </div>

      {challenge.my_entry && (
        <div className={styles.myEntry}>
          <div className={styles.myEntryLeft}>
            <span className={`${styles.myStatus} ${styles[myStatus]}`}>
              {myStatus}
            </span>
            {userOutcome && (
              <span className={`${styles.outcomeBadge} ${styles[userOutcome.toLowerCase()]}`}>
                {userOutcome}
              </span>
            )}
          </div>

          <div className={styles.myDetails}>
            {myPrediction && (
              <span className={styles.myPrediction}>
                Your pick: {myPrediction}
              </span>
            )}
            {challenge.my_entry.points_earned != null && (
              <span className={styles.myOutcome}>
                {challenge.my_entry.points_earned} pts
              </span>
            )}
          </div>
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

      {showParticipants && (
        <div className={styles.overlay} onClick={() => setShowParticipants(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h3 className={styles.modalTitle}>Participants</h3>
            <div className={styles.modalList}>
              {challenge.entries?.map(entry => (
                <div key={entry.id} className={styles.modalRow}>
                  <span className={styles.modalUser}>
                    {entry.full_name || entry.email}
                  </span>
                  <span className={styles.modalPrediction}>
                    {entry.prediction || '—'}
                  </span>
                  <span className={`${styles.modalStatus} ${styles[entry.status]}`}>
                    {entry.status}
                  </span>
                  <span className={styles.modalPoints}>
                    {entry.points_earned != null ? `${entry.points_earned} pts` : '—'}
                  </span>
                </div>
              ))}
            </div>
            <button className={styles.closeBtn} onClick={() => setShowParticipants(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}