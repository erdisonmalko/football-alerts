import { useState } from 'react'
import { createChallenge } from '../api/endpoints'
import { parseApiError } from '../api/errorHandler'

export default function CreateChallenge({ serverId, members = [], matches = [], onCreated }) {
const [matchId, setMatchId] = useState('')
const [stake, setStake] = useState('')
const [prediction, setPrediction] = useState('')
const [inviteAll, setInviteAll] = useState(true)
const [selectedUsers, setSelectedUsers] = useState([])
const [loading, setLoading] = useState(false)
const [error, setError] = useState('')

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
            invited_user_ids: inviteAll ? [] : selectedUsers
        }

            const res = await createChallenge(serverId, payload)

            if (onCreated) onCreated(res)

            // reset
            setMatchId('')
            setStake('')
            setPrediction('')
            setSelectedUsers([])

            } catch (err) {
            setError(parseApiError(err))
            } finally {
            setLoading(false)
            }
        }

return ( 
<div> <h3>Create Challenge</h3>

  <form onSubmit={handleSubmit}>

    {/* Match */}
    <div>
      <label>Match</label>
      <select value={matchId} onChange={e => setMatchId(e.target.value)} required>
        <option value="">Select match</option>
        {matches.map(m => (
          <option key={m.id} value={m.id}>
            {m.home_team} vs {m.away_team}
          </option>
        ))}
      </select>
    </div>

    {/* Prediction */}
    <div>
      <label>Prediction</label>
      <input
        value={prediction}
        onChange={e => setPrediction(e.target.value)}
        placeholder="2-1"
        required
      />
    </div>

    {/* Stake */}
    <div>
      <label>Stake</label>
      <input
        value={stake}
        onChange={e => setStake(e.target.value)}
        placeholder="e.g. Coffee"
        required
      />
    </div>

    {/* Invite mode */}
    <div>
      <label>
        <input
          type="checkbox"
          checked={inviteAll}
          onChange={() => setInviteAll(!inviteAll)}
        />
        Invite all members
      </label>
    </div>

    {/* Select users */}
    {!inviteAll && (
      <div>
        <label>Invite users</label>
        {members.map(u => (
          <div key={u.user_id}>
            <label>
              <input
                type="checkbox"
                checked={selectedUsers.includes(u.user_id)}
                onChange={() => toggleUser(u.user_id)}
              />
              {u.full_name}
            </label>
          </div>
        ))}
      </div>
    )}

    {error && <p style={{ color: 'red' }}>{error}</p>}

    <button disabled={loading}>
      {loading ? 'Creating...' : 'Create'}
    </button>

  </form>
</div>
)}
