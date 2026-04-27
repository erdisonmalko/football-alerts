import { useState, useEffect, useCallback } from 'react'
import { createChallenge, getMyMatches } from '../api/endpoints'
import { parseApiError } from '../api/errorHandler'
import styles from './CreateChallenge.module.css'

export default function CreateChallenge({ serverId, members = [], onCreated, onClose }) {
  const [matchOptions, setMatchOptions] = useState([])
  const [loadingMatches, setLoadingMatches] = useState(false)
  const [matchId, setMatchId] = useState('')
  const [stake, setStake] = useState('')
  const [prediction, setPrediction] = useState('')
  const [inviteAll, setInviteAll] = useState(true)
  const [selectedUsers, setSelectedUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchMatches = useCallback(async () => {
    setLoadingMatches(true)
    try {
      const data = await getMyMatches()
      const allMatches = [
        ...(data.live || []),
        ...(data.upcoming || []),
      ]
      setMatchOptions(allMatches)
    } catch (err) {
      console.error('Failed to fetch matches:', err)
    } finally {
      setLoadingMatches(false)
    }
  }, [])

  useEffect(() => {
    fetchMatches()
  }, [fetchMatches])

  const toggleUser = (id) => {
    setSelectedUsers(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        match_id: Number(matchId),
        stake,
        prediction,
        invited_user_ids: inviteAll ? [] : selectedUsers,
      }
      const res = await createChallenge(serverId, payload)
      if (onCreated) onCreated(res)
      onClose()
    } catch (err) {
      setError(parseApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>

        <div className={styles.header}>
          <h2>CREATE CHALLENGE</h2>
          <button className={styles.close} onClick={onClose}>×</button>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label>MATCH</label>
            <select
              className={styles.select}
              value={matchId}
              onChange={e => setMatchId(e.target.value)}
              required
            >
              <option value="">
                {loadingMatches ? 'Loading...' : 'Select a match'}
              </option>
              {matchOptions.map(m => (
                <option key={m.id} value={m.id}>
                  {m.home_team_name} vs {m.away_team_name}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.formGroup}>
            <label>YOUR PREDICTION</label>
            <input
              type="text"
              value={prediction}
              onChange={e => setPrediction(e.target.value)}
              placeholder="e.g. 2-1"
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label>STAKE</label>
            <input
              type="text"
              value={stake}
              onChange={e => setStake(e.target.value)}
              placeholder="e.g. Coffee"
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label>INVITE</label>
            <div className={styles.radioGroup}>
              <label className={`${styles.radioLabel} ${inviteAll ? styles.radioLabelActive : ''}`}>
                <input
                  type="radio"
                  checked={inviteAll}
                  onChange={() => setInviteAll(true)}
                />
                <span className={styles.radioText}>
                  <strong>All members</strong>
                </span>
              </label>
              <label className={`${styles.radioLabel} ${!inviteAll ? styles.radioLabelActive : ''}`}>
                <input
                  type="radio"
                  checked={!inviteAll}
                  onChange={() => setInviteAll(false)}
                />
                <span className={styles.radioText}>
                  <strong>Select members</strong>
                </span>
              </label>
            </div>
          </div>

          {!inviteAll && members.length > 0 && (
            <div className={styles.formGroup}>
              <label>MEMBERS</label>
              <div className={styles.memberList}>
                {members.map(u => (
                  <label key={u.user_id} className={`${styles.memberItem} ${selectedUsers.includes(u.user_id) ? styles.memberItemActive : ''}`}>
                    <input
                      type="checkbox"
                      checked={selectedUsers.includes(u.user_id)}
                      onChange={() => toggleUser(u.user_id)}
                    />
                    <span>{u.full_name || `User #${u.user_id}`}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {error && <p className={styles.error}>{error}</p>}
        </form>

        <div className={styles.footer}>
          <button className={styles.cancelBtn} onClick={onClose} disabled={loading}>
            CANCEL
          </button>
          <button
            className={styles.createBtn}
            onClick={handleSubmit}
            disabled={loading || !matchId || !stake || !prediction}
          >
            {loading ? 'CREATING...' : 'CREATE CHALLENGE'}
          </button>
        </div>

      </div>
    </div>
  )
}