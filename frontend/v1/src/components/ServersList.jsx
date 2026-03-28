import styles from '../pages/Dashboard.module.css'

export default function ServersList({ servers, onSelectServer, loading }) {
  if (loading) {
    return <div className={styles.loading}><div className={styles.loadingBar} /></div>
  }

  if (servers.length === 0) {
    return (
      <div className={styles.empty}>
        <p className={styles.emptyTitle}>NO SERVERS</p>
        <p className={styles.emptySub}>You haven't joined any servers yet.</p>
      </div>
    )
  }

  return (
    <div className={styles.serversList}>
      {servers.map(server => (
        <button
          key={server.id}
          className={styles.serverCard}
          onClick={() => onSelectServer(server.id)}
        >
          <div className={styles.serverCardContent}>
            <h3 className={styles.serverCardName}>{server.name}</h3>
            <span className={styles.serverCardMembers}>{server.member_count || 0} members</span>
          </div>
          <span className={styles.arrow}>→</span>
        </button>
      ))}
    </div>
  )
}
