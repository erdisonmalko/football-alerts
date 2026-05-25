import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import ServerLeaderboard from './ServerLeaderboard'
import ServerChallenges from './ServerChallenges'
import CreateChallenge from './CreateChallenge'
import ConfirmationDialog from './ConfirmationDialog'
import styles from './ServerDetails.module.css'
import { regenerateInviteCode } from '../api/endpoints'

export default function ServerDetail({
  serverDetails,
  leaderboard,
  onRefresh,
  onBack,
  onLeave,
  onUpdate,
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  const [editName, setEditName] = useState(serverDetails.name)
  const [editPublic, setEditPublic] = useState(!!serverDetails.is_public)

  const [inviteCode, setInviteCode] = useState(serverDetails.invite_code)
  const [copied, setCopied] = useState(false)
  const [regenerating, setRegenerating] = useState(false)

  const [showCreateChallenge, setShowCreateChallenge] = useState(false)
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const menuRef = useRef(null)
  
  // Close menu on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleCopyInvite = async () => {
    if (!inviteCode) return
    await navigator.clipboard.writeText(inviteCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const handleRegenerateInvite = async () => {
    setRegenerating(true)
    try {
      const res = await regenerateInviteCode(serverDetails.id)
      setInviteCode(res.invite_code)
      await navigator.clipboard.writeText(res.invite_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } finally {
      setRegenerating(false)
    }
  }
  const navigate = useNavigate()

  const confirmLeave = async () => {
    setLeaving(true)
    try {
      await onLeave()
    } finally {
      setLeaving(false)
    }
  }
  const handleSubmit = async (e) => {
    e.preventDefault()
    await onUpdate(editName, editPublic)
    setIsEditing(false)
  }

  return (
    <div className={styles.serverDetail}>
      {/* Top bar */}
      <div className={styles.topBar}>
        <button onClick={() => navigate('/servers')} className={styles.backBtn}>
          ← BACK
        </button>

        {/* 3-dot menu */}
        <div className={styles.menuWrapper} ref={menuRef}>
          <button
              className={styles.menuBtn}
              onClick={() => setMenuOpen(prev => !prev)}
            >
              ⚙️
            </button>

          {menuOpen && (
            <div className={styles.dropdownMenu}>
              {serverDetails.is_owner && (
                <>
                  <button
                    className={styles.menuItem}
                    onClick={() => {
                      setIsEditing(true)
                      setMenuOpen(false)
                    }}
                  >
                    Edit Server
                  </button>

                  <button
                    className={styles.menuItem}
                    onClick={handleCopyInvite}
                  >
                    {copied ? 'Copied!' : 'Copy Invite Code'}
                  </button>

                  <button
                    className={styles.menuItem}
                    onClick={handleRegenerateInvite}
                    disabled={regenerating}
                  >
                    {regenerating ? 'Regenerating...' : 'Regenerate Code'}
                  </button>

                  <div className={styles.menuDivider} />
                </>
              )}

              <button
                className={`${styles.menuItem} ${styles.menuItemDanger}`}
                onClick={() => setShowLeaveConfirm(true)}
              >
                Leave Server
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Identity (clean now) */}
      <div className={styles.serverIdentity}>
        <h2 className={styles.serverName}>{serverDetails.name}</h2>

        <div className={styles.metaRow}>
          <span className={styles.isPublic}>
            {serverDetails.is_public ? 'Public Server' : 'Private Server'}
          </span>

          <span className={styles.memberCount}>
            {serverDetails.members?.length || 0} members
          </span>
        </div>
      </div>

      {/* Edit Modal */}
      {isEditing && (
        <div className={styles.overlay}>
          <div className={styles.modal}>
            <h3 className={styles.title}>Edit Server</h3>
            <p className={styles.subtitle}>Update server settings</p>

            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Server Name</label>
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className={styles.input}
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

                <button type="submit" className={styles.primary}>
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ServerLeaderboard leaderboard={leaderboard} />
      <button
        className={styles.challengeBtn}
        onClick={() => setShowCreateChallenge(true)}
      >
        + CHALLENGE
      </button>
      <ServerChallenges serverId={serverDetails.id} onRefresh={onRefresh} />
      
      {showCreateChallenge && (
        <CreateChallenge
          serverId={serverDetails.id}
          members={serverDetails.members || []}
          onCreated={() => {
            setShowCreateChallenge(false)
            if (onRefresh) onRefresh()
          }}
          onClose={() => setShowCreateChallenge(false)}
        />
      )}

      <ConfirmationDialog
        isOpen={showLeaveConfirm}
        title="Leave Server"
        description="This action is irreversible. You will lose access to this server, including its challenges, leaderboard, and members. You will need a new invite to join again."
        confirmLabel={leaving ? 'Leaving...' : 'Leave Server'}
        cancelLabel="Cancel"
        isLoading={leaving}
        confirmVariant="danger"
        onConfirm={confirmLeave}
        onCancel={() => setShowLeaveConfirm(false)}
      />
    </div>
  )
}