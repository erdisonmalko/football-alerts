import { useState } from 'react'
import Pagination from './Pagination'
import styles from '../pages/Dashboard.module.css'
import JoinPrivateServerModal from './JoinPrivateServerModal'
import { joinByInvite } from '../api/endpoints'

const SERVERS_PER_PAGE = 15

function MyServers({ servers, onSelectServer, currentPage = 1, onPageChange = () => {}, totalPages = 1 }) {
  const visibleServers = servers

  if (servers.length === 0) {
    return (
      <div className={styles.empty}>
        <p className={styles.emptyTitle}>NO SERVERS</p>
        <p className={styles.emptySub}>You haven't joined any servers yet. Discover public ones or create your own.</p>
      </div>
    )
  }

  return (
    <>
      <div className={styles.serversList}>
        {visibleServers.map(server => (
          <button
            key={server.id}
            className={styles.serverCard}
            onClick={() => onSelectServer(server.id)}
          >
            <div className={styles.serverCardContent}>
              <h3 className={styles.serverCardName}>{server.name}</h3>
              <span className={styles.serverCardMembers}>{server.member_count || 0} members</span>
            </div>
            {server.is_owner && (
              <span className={styles.arrow}>OWNER</span>
            )}
            <span className={styles.arrow}>→</span>
          </button>
        ))}
      </div>
      {totalPages > 1 && (
        <Pagination
          page={currentPage}
          totalPages={totalPages}
          onChange={onPageChange}
        />
      )}
    </>
  )
}



function DiscoverServers({ servers, onRequestJoin, onEnter, currentPage = 1, onPageChange = () => {}, totalPages = 1 }) {
  const [selectedServer, setSelectedServer] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)

  const visibleServers = servers

  if (servers.length === 0) {
    return (
      <div className={styles.empty}>
        <p className={styles.emptyTitle}>NO SERVERS</p>
        <p className={styles.emptySub}>No servers available yet.</p>
      </div>
    )
  }

  const handleRequest = (server) => {
    onRequestJoin(server)
  }

  const handleJoinPrivate = (server) => {
    setSelectedServer(server)
    setModalOpen(true)
  }

  const handleSubmitCode = async (code) => {
    const res = await joinByInvite(code, selectedServer.id)

    // optional: you can trigger refresh or optimistic UI here
    // e.g. refetch public servers or update state

    return res
  }

  return (
    <>
      <div className={styles.serversList}>
        {visibleServers.map(server => (
          <div key={server.id} className={styles.serverCard}>
            
            <div className={styles.serverCardContent}>
              <h3 className={styles.serverCardName}>{server.name}</h3>
              <span className={styles.serverCardMembers}>
                {server.member_count || 0} members
              </span>
            </div>

            {server.is_owner && (
              <span className={styles.arrow}>OWNER</span>
            )}

            <div className={styles.serverCardActions}>
              
              {server.is_member ? (
                <button
                  className={styles.serverActionBtn}
                  onClick={() => onEnter(server.id)}
                >
                  ENTER →
                </button>

              ) : server.has_pending_request ? (
                <span className={styles.serverPending}>REQUESTED</span>

              ) : (
                <button
                  className={styles.serverActionBtn}
                  onClick={() =>
                    server.is_public
                      ? handleRequest(server)
                      : handleJoinPrivate(server)
                  }
                >
                  {server.is_public ? 'JOIN' : 'ENTER CODE'}
                </button>
              )}

            </div>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <Pagination
          page={currentPage}
          totalPages={totalPages}
          onChange={onPageChange}
        />
      )}

      {/* SINGLE modal instance */}
      <JoinPrivateServerModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmitCode}
        serverName={selectedServer?.name}
      />
    </>
  )
}

export default function ServersList({
  servers,
  publicServers,
  loading,
  publicLoading,
  onSelectServer,
  onRequestJoin,
  onLeaveServer,
  onPageChange = () => {},
}) {
  const [subTab, setSubTab] = useState('mine')
  const [pageByTab, setPageByTab] = useState({ mine: 1, discover: 1 })

  const currentPage = pageByTab[subTab] || 1
  const handlePageChange = (nextPage) => {
    setPageByTab(prev => ({ ...prev, [subTab]: nextPage }))
    onPageChange(nextPage, subTab)
  }

  if (loading) {
    return <div className={styles.loading}><div className={styles.loadingBar} /></div>
  }

  return (
    <>
      <div className={styles.subTabs}>
        <button
          className={`${styles.subTab} ${subTab === 'mine' ? styles.subTabActive : ''}`}
          onClick={() => setSubTab('mine')}
        >
          MY SERVERS
          {servers.length > 0 && (
            <span className={`${styles.tabBadge} ${subTab === 'mine' ? styles.tabBadgeActive : ''}`}>
              {servers.length}
            </span>
          )}
        </button>
        <button
          className={`${styles.subTab} ${subTab === 'discover' ? styles.subTabActive : ''}`}
          onClick={() => setSubTab('discover')}
        >
          DISCOVER
        </button>
      </div>

      {subTab === 'mine' ? (
        <MyServers
          servers={servers?.items || []}
          totalPages={servers?.total_pages || 1}
          onSelectServer={onSelectServer}
          currentPage={currentPage}
          onPageChange={handlePageChange}
        />
      ) : publicLoading ? (
        <div className={styles.loading}><div className={styles.loadingBar} /></div>
      ) : (
        <DiscoverServers
          servers={publicServers?.items || []}
          totalPages={publicServers?.total_pages || 1}
          onRequestJoin={onRequestJoin}
          onEnter={onSelectServer}
          currentPage={currentPage}
          onPageChange={handlePageChange}
        />
      )}
    </>
  )
}