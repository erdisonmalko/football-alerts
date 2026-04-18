import { useState } from 'react'
import ServerLeaderboard from './ServerLeaderboard'
import ServerChallenges from './ServerChallenges'
import styles from '../pages/Dashboard.module.css'

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
  const [editPublic, setEditPublic] = useState(serverDetails.is_public)

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Parent expects: serverId, name, isPublic
    await onUpdate(serverDetails.id, editName, editPublic);
    setIsEditing(false);
  };


  return (
    <div className={styles.serverDetail}>
      <div className={styles.topActions}>
        <button onClick={onBack} className={styles.backBtn}>← BACK</button>
        
        <div className={styles.rightActions}>
           {/* Only show Edit if the user is the owner */}
          {serverDetails.is_owner && (
            <button onClick={() => setIsEditing(true)} className={styles.editBtn}>EDIT</button>
          )}
          {/* <button onClick={() => setIsEditing(true)} className={styles.editBtn}>EDIT</button> */}
          <button onClick={onLeave} className={styles.leaveBtn}>LEAVE SERVER</button>
        </div>
      </div>
      
      <div className={styles.serverHeader}>
        <h2 className={styles.serverName}>{serverDetails.name}</h2>
        <span className={styles.memberCount}>{serverDetails.members?.length || 0} members</span>
      </div>

      {/* --- SIMPLE MODAL OVERLAY --- */}
      {isEditing && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h3>Update Server</h3>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Server Name</label>
                <input 
                  value={editName} 
                  onChange={(e) => setEditName(e.target.value)}
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label>
                  <input 
                    type="checkbox" 
                    checked={editPublic} 
                    onChange={(e) => setEditPublic(e.target.checked)} 
                  />
                  Public Server
                </label>
              </div>
              <div className={styles.modalActions}>
                <button type="button" onClick={() => setIsEditing(false)}>Cancel</button>
                <button type="submit" className={styles.saveBtn}>Save Changes</button>
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
