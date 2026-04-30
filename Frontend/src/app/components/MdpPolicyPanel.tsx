import { useMemo, useState } from 'react'
import apiClient from '../../services/api'
import GreenButton from './GreenButton'
import SectionHeader from './SectionHeader'

type MdpPolicyPanelProps = {
	mdpIds: string[]
}

type MdpResult = {
	mdpId: string
	expectedScore: number | null
	clubId: string | null
	targetX: number | null
	targetY: number | null
	error: string | null
}

type PolicyResponse = {
	club_ids?: string[] | null
	policy: {
		club_idx: number
		target_x: number
		target_y: number
	} | null
}

type ValueResponse = {
	value: number | null
}

const DEFAULT_X = '0'
const DEFAULT_Y = '25'

function toDisplayScore(value: number | null | undefined) {
	if (value === null || value === undefined) return null
	return Math.abs(value)
}

const MdpPolicyPanel = ({ mdpIds }: MdpPolicyPanelProps) => {
	const [xValue, setXValue] = useState(DEFAULT_X)
	const [yValue, setYValue] = useState(DEFAULT_Y)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [results, setResults] = useState<MdpResult[]>([])

	const selectedCount = mdpIds?.length ?? 0

	const parsedState = useMemo(() => {
		const x = Number(xValue)
		const y = Number(yValue)
		if (!Number.isFinite(x) || !Number.isFinite(y)) return null
		return { x, y }
	}, [xValue, yValue])

	const handleGetPolicy = async () => {
		if (!mdpIds || mdpIds.length === 0) {
			setError('No mdp_ids selected. Select one or more mdp_ids from the sidebar.')
			return
		}

		if (!parsedState) {
			setError('Enter a valid X and Y location.')
			return
		}

		setLoading(true)
		setError(null)
		setResults([])

		try {
			const collected = await Promise.all(
				mdpIds.map(async (mdpId) => {
					try {
						const [valueResponse, policyResponse] = await Promise.all([
							apiClient.post('/mdp/value', {
								mdp_id: mdpId,
								state: parsedState,
							}) as Promise<ValueResponse>,
							apiClient.post('/mdp/policy', {
								mdp_id: mdpId,
								state: parsedState,
							}) as Promise<PolicyResponse>,
						])

						const policy = policyResponse?.policy
						const score = toDisplayScore(valueResponse?.value)
						const clubIds = policyResponse?.club_ids ?? []
						const clubId = policy && typeof policy.club_idx === 'number' ? clubIds[policy.club_idx] ?? null : null

						return {
							mdpId,
							expectedScore: score,
							clubId,
							targetX: policy?.target_x ?? null,
							targetY: policy?.target_y ?? null,
							error: null,
						}
					} catch (mdpError: any) {
						const message = mdpError?.message ?? 'Failed to load policy.'
						return {
							mdpId,
							expectedScore: null,
							clubId: null,
							targetX: null,
							targetY: null,
							error: message,
						}
					}
				}),
			)

			setResults(collected)
		} catch (requestError: any) {
			setError(requestError?.message ?? String(requestError))
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="mdp-policy-panel">
			<SectionHeader
				mainText="MDP Policy Lookup"
				subText="Select one or more mdp_ids, enter a hole location, then fetch expected score, optimal club, and target per model."
			/>

			<div className="mdp-policy-panel__controls">
				<label className="field">
					<span className="field__label">X</span>
					<input
						className="field__input"
						type="number"
						value={xValue}
						onChange={(e) => setXValue(e.target.value)}
						placeholder="Enter x"
					/>
				</label>

				<label className="field">
					<span className="field__label">Y</span>
					<input
						className="field__input"
						type="number"
						value={yValue}
						onChange={(e) => setYValue(e.target.value)}
						placeholder="Enter y"
					/>
				</label>
			</div>

			<div className="mdp-policy-panel__actions">
				<GreenButton onClick={handleGetPolicy} disabled={loading || selectedCount === 0}>
					{loading ? 'Loading...' : 'Get Policy'}
				</GreenButton>
				<div className="mdp-policy-panel__selected">{selectedCount} mdp_ids selected</div>
			</div>

			{error ? <div className="mdp-policy-panel__error">{error}</div> : null}

			{results.length > 0 ? (
				<div className="mdp-policy-panel__results">
					<div className="mdp-policy-panel__results-title">Policy Results</div>
					{results.map((result) => (
						<div key={result.mdpId} className="mdp-policy-panel__result-row">
							<div className="mdp-policy-panel__result-head">
								<strong>{result.mdpId}</strong>
							</div>
							{result.error ? (
								<div className="mdp-policy-panel__result-error">{result.error}</div>
							) : (
								<div className="mdp-policy-panel__result-body">
									<div>Expected score: {result.expectedScore ?? 'N/A'}</div>
									<div>Optimal club: {result.clubId ?? 'N/A'}</div>
									<div>
										Target: {result.targetX ?? 'N/A'}, {result.targetY ?? 'N/A'}
									</div>
								</div>
							)}
						</div>
					))}
				</div>
			) : null}
		</div>
	)
}

export default MdpPolicyPanel
