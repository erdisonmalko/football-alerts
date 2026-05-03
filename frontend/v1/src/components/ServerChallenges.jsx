import { useMemo, useState, useEffect } from 'react'
import Pagination from './Pagination'
import styles from './ServerChallenges.module.css'
import ChallengeCard from './ChallengeCard'

const ITEMS_PER_PAGE = 6
const STATUS_TABS = [
  { key: 'open', label: 'OPEN' },
  { key: 'pending', label: 'PENDING' },
  { key: 'settled', label: 'SETTLED' },
  { key: 'locked', label: 'LOCKED' },
]

export default function ServerChallenges({ challenges = [], onRefresh }) {
  const [activeTab, setActiveTab] = useState('open')
  const [pageByTab, setPageByTab] = useState({ open: 1, pending: 1, settled: 1, locked: 1 })

  const tabCounts = useMemo(() => {
    return challenges.reduce(
      (counts, challenge) => {
        if (STATUS_TABS.some(tab => tab.key === challenge.status)) {
          counts[challenge.status] = (counts[challenge.status] || 0) + 1
        }
        return counts
      },
      { open: 0, pending: 0, settled: 0, locked: 0 }
    )
  }, [challenges])

  const filteredChallenges = useMemo(
    () => challenges.filter(challenge => challenge.status === activeTab),
    [challenges, activeTab]
  )

  const totalPages = Math.max(1, Math.ceil(filteredChallenges.length / ITEMS_PER_PAGE))
  const currentPage = pageByTab[activeTab] || 1
  const visibleChallenges = useMemo(
    () => filteredChallenges.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE),
    [filteredChallenges, currentPage]
  )

  useEffect(() => {
    if (currentPage > totalPages) {
      setPageByTab(prev => ({ ...prev, [activeTab]: totalPages }))
    }
  }, [activeTab, currentPage, totalPages])

  const handleTabChange = (tabKey) => {
    setActiveTab(tabKey)
    setPageByTab(prev => ({ ...prev, [tabKey]: prev[tabKey] || 1 }))
  }

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
              <span className={styles.tabCount}> {tabCounts[tab.key]}</span>
            </button>
          ))}
        </div>
      </div>

      {filteredChallenges.length > 0 ? (
        <>
          <div className={styles.challengesList}>
            {visibleChallenges.map(challenge => (
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
            onChange={(nextPage) => setPageByTab(prev => ({ ...prev, [activeTab]: nextPage }))}
          />
        </>
      ) : (
        <p className={styles.emptyText}>No {activeTab} challenges.</p>
      )}
    </div>
  )
}