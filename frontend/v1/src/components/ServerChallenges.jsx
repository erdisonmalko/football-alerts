import { useState, useEffect } from 'react'
import Pagination from './Pagination'
import styles from './ServerChallenges.module.css'
import ChallengeCard from './ChallengeCard'
import { getServerChallenges } from '../api/endpoints'

const ITEMS_PER_PAGE = 6
const STATUS_TABS = [
  { key: 'open', label: 'OPEN' },
  { key: 'pending', label: 'PENDING' },
  { key: 'settled', label: 'SETTLED' },
  { key: 'locked', label: 'LOCKED' },
]

export default function ServerChallenges({ serverId, onRefresh }) {
  const [activeTab, setActiveTab] = useState('open')
  const [pageByTab, setPageByTab] = useState({ open: 1, pending: 1, settled: 1, locked: 1 })
  const [dataByTab, setDataByTab] = useState({})
  const [loadingByTab, setLoadingByTab] = useState({})

  const currentPage = pageByTab[activeTab] || 1
  const tabData = dataByTab[activeTab] || { items: [], total: 0, page: 1, page_size: ITEMS_PER_PAGE, total_pages: 1 }

  useEffect(() => {
    let mounted = true
    const fetch = async () => {
      setLoadingByTab(prev => ({ ...prev, [activeTab]: true }))
      try {
        const res = await getServerChallenges(serverId, { page: currentPage, pageSize: ITEMS_PER_PAGE, status: activeTab })
        if (!mounted) return
        setDataByTab(prev => ({ ...prev, [activeTab]: res }))
      } catch (err) {
        console.error('Failed to fetch server challenges:', err)
      } finally {
        setLoadingByTab(prev => ({ ...prev, [activeTab]: false }))
      }
    }

    fetch()
    return () => { mounted = false }
  }, [serverId, activeTab, currentPage])

  const handleTabChange = (tabKey) => {
    setActiveTab(tabKey)
    setPageByTab(prev => ({ ...prev, [tabKey]: prev[tabKey] || 1 }))
  }

  const handlePageChange = (nextPage) => {
    setPageByTab(prev => ({ ...prev, [activeTab]: nextPage }))
  }

  const { items, total_pages: totalPages } = tabData

  return (
    <div className={styles.challengesSection}>
      <div className={styles.sectionHeader}>
        <h3 className={styles.sectionTitle}>ONGOING CHALLENGES</h3>
        <div className={styles.tabBar}>
          {STATUS_TABS.map(tab => (
            <button
              key={tab.key}
              type="button"
              className={`${styles.tabButton} ${activeTab === tab.key ? styles.activeTab : ''}`}
              onClick={() => handleTabChange(tab.key)}
            >
              {tab.label}
              <span className={styles.tabCount}> { (dataByTab[tab.key] && dataByTab[tab.key].total) || 0 }</span>
            </button>
          ))}
        </div>
      </div>

      {loadingByTab[activeTab] ? (
        <p className={styles.emptyText}>Loading…</p>
      ) : items && items.length > 0 ? (
        <>
          <div className={styles.challengesList}>
            {items.map(challenge => (
              <ChallengeCard
                key={challenge.id}
                challenge={challenge}
                tab="server"
                onRefresh={onRefresh}
              />
            ))}
          </div>

          <Pagination
            page={currentPage}
            totalPages={totalPages}
            onChange={handlePageChange}
          />
        </>
      ) : (
        <p className={styles.emptyText}>No {activeTab} challenges.</p>
      )}
    </div>
  )
}