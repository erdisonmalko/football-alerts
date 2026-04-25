import { useState } from 'react'
import ServerLeaderboard from './ServerLeaderboard'
import ServerChallenges from './ServerChallenges'
import styles from '../pages/Dashboard.module.css'
import { regenerateInviteCode } from '../api/endpoints'

export default function ServerDetail({ 
  serverDetails, 
  leaderboard, 
  challenges, 
  onBack, 
  onLeave, 
  onUpdate // Ensure this is passed in
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState(serverDetails.name)
  const [editPublic, setEditPublic] = useState(!!serverDetails.is_public)
  const [copied, setCopied] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [inviteCode, setInviteCode] = useState(serverDetails.invite_code)

  const handleRegenerateInvite = async () => {
    setRegenerating(true)

    try {
      const res = await regenerateInviteCode(serverDetails.id)

      // backend returns { invite_code }
      setInviteCode(res.invite_code)

      // optional UX: auto-copy new code
      await navigator.clipboard.writeText(res.invite_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)

    } catch (err) {
      console.warn('Failed to regenerate invite code', err)
    } finally {
      setRegenerating(false)
    }
  }
  const handleCopyInvite = async () => {
    try {
      await navigator.clipboard.writeText(inviteCode)
      setCopied(true)

      setTimeout(() => setCopied(false), 1500)
    } catch (err) {
      console.warn('Clipboard copy failed', err)
    }
  }
    const handleSubmit = async (e) => {
    e.preventDefault();
    // Parent expects: serverId, name, isPublic
    await onUpdate(serverDetails.id, editName, !!editPublic);
    setIsEditing(false);
  };


  return (
    <div className={styles.serverDetail}>
      <div className={styles.topActions}>
        <button onClick={onBack} className={styles.backBtn}>← BACK</button>
      </div>
      
      <div className={styles.serverHeader}>
        {/* 1. Identity */}
        <div className={styles.headerTop}>
          <h2 className={styles.serverName}>{serverDetails.name}</h2>

          <span className={styles.memberCount}>
            {serverDetails.members?.length || 0} members
          </span>
        </div>
        {/* 3. Actions */}
      {serverDetails.is_owner && (
          <div className={styles.ownerControls}>
            <button onClick={() => setIsEditing(true)} className={styles.editBtn}>
              EDIT SERVER
            </button>

            <button onClick={handleCopyInvite} className={styles.inviteBtn}>
              {copied ? 'COPIED!' : 'COPY CODE'}
            </button>
          </div>
        )}

        <button onClick={onLeave} className={styles.leaveBtn}>
          LEAVE SERVER
        </button>
      </div>

      {/* --- SIMPLE MODAL OVERLAY --- */}
      {isEditing && (
        <div className={styles.overlay}>
          <div className={styles.modal}>

            <h3 className={styles.title}>Edit Server</h3>
            <p className={styles.subtitle}>
              Update server settings
            </p>

            <form onSubmit={handleSubmit}>

              <div className={styles.formGroup}>
                <label className={styles.label}>Server Name</label>
                <input 
                  value={editName} 
                  onChange={(e) => setEditName(e.target.value)}
                  className={styles.input}
                  placeholder="Enter server name"
                />
              </div>

              <div className={styles.formGroupRow}>
                <label className={styles.checkboxLabel}>
                  <input 
                    type="checkbox" 
                    checked={editPublic} 
                    onChange={(e) => setEditPublic(e.target.checked)} 
                  />
                  <span>Public Server</span>
                </label>
              </div>

              <div className={styles.actions}>
                <button
                  type="button"
                  className={styles.secondary}
                  onClick={() => setIsEditing(false)}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className={styles.primary}
                >
                  Save Changes
                </button>
              </div>

            </form>
          </div>
        </div>
      )}

      <ServerLeaderboard leaderboard={leaderboard} />
      <ServerChallenges challenges={challenges} />
    </div>
  )
}
