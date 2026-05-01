import { useEffect, useMemo, useState } from 'react'
import apiClient from '../../services/api'
import GreenButton from './GreenButton'
import SectionHeader from './SectionHeader'

type MdpSolvePanelProps = {
	gmmIds: string[]
	onSolveComplete?: () => void
}

type SolveResponse = {
	mdp_id: string
	gmm_ids: string[]
}

const DEFAULT_GRID_STEP = '10'

const MdpSolvePanel = ({ gmmIds, onSolveComplete }: MdpSolvePanelProps) => {
	const [mdpId, setMdpId] = useState('')
	const [gridStep, setGridStep] = useState(DEFAULT_GRID_STEP)
	const [loading, setLoading] = useState(false)
	const [progress, setProgress] = useState(0)
	const [error, setError] = useState<string | null>(null)
	const [result, setResult] = useState<SolveResponse | null>(null)

	const selectedCount = gmmIds?.length ?? 0

	const parsedGridStep = useMemo(() => {
		const value = Number(gridStep)
		if (!Number.isFinite(value)) return null
		const integerValue = Math.floor(value)
		if (integerValue < 1 || integerValue > 50) return null
		return integerValue
	}, [gridStep])

	useEffect(() => {
		if (!loading) return undefined

		setProgress(10)
		const timer = window.setInterval(() => {
			setProgress((current) => {
				if (current >= 92) return current
				return Math.min(92, current + 4)
			})
		}, 180)

		return () => window.clearInterval(timer)
	}, [loading])

	const handleSolve = async () => {
		if (!gmmIds || gmmIds.length === 0) {
			setError('Select one or more gmm_ids from the sidebar.')
			return
		}

		const trimmedMdpId = mdpId.trim()
		if (!trimmedMdpId) {
			setError('Enter an mdp_id to save the solved MDP.')
			return
		}

		if (parsedGridStep === null) {
			setError('Grid step must be an integer between 1 and 50.')
			return
		}

		setLoading(true)
		setError(null)
		setResult(null)
		setProgress(10)

		try {
			const response = (await apiClient.post('/mdp/solve', {
				mdp_id: trimmedMdpId,
				gmm_ids: gmmIds,
				grid_step: parsedGridStep,
			})) as SolveResponse

			setProgress(100)
			setResult({
				mdp_id: response.mdp_id ?? trimmedMdpId,
				gmm_ids: response.gmm_ids ?? gmmIds,
			})
			if (onSolveComplete) onSolveComplete()
		} catch (solveError: any) {
			console.error('Failed to solve MDP:', solveError)
			setError(solveError?.message ?? 'Failed to solve MDP.')
			setProgress(0)
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="mdp-solve-panel">
			<SectionHeader
				mainText="Solve MDP"
				subText="Select a group of gmm_ids, provide an mdp_id and grid step, then execute to build and save the MDP."
			/>

			<div className="mdp-solve-panel__controls">
				<label className="field">
					<span className="field__label">MDP ID</span>
					<input
						className="field__input"
						type="text"
						value={mdpId}
						onChange={(e) => setMdpId(e.target.value)}
						placeholder="Enter mdp id"
					/>
				</label>

				<label className="field">
					<span className="field__label">Grid Step</span>
					<input
						className="field__input"
						type="number"
						min={1}
						max={50}
						step={1}
						value={gridStep}
						onChange={(e) => setGridStep(e.target.value)}
						placeholder="Enter grid step"
					/>
				</label>
			</div>

			<div className="mdp-solve-panel__selection">
				<div className="mdp-solve-panel__selection-label">Selected gmm_ids</div>
				<div className="mdp-solve-panel__chips">
					{gmmIds.length > 0 ? (
						gmmIds.map((id) => (
							<span key={id} className="gmm-fit-panel__chip">
								{id}
							</span>
						))
					) : (
						<span className="mdp-solve-panel__empty-selection">No gmm_ids selected.</span>
					)}
				</div>
			</div>

			<div className="mdp-solve-panel__actions">
				<GreenButton onClick={handleSolve} disabled={loading || selectedCount === 0}>
					{loading ? 'Executing...' : 'Execute'}
				</GreenButton>
				<div className="mdp-solve-panel__selected-count">{selectedCount} gmm_ids selected</div>
			</div>

			<div className="mdp-solve-panel__progress-wrap" aria-hidden={!loading && progress === 0 && !result}>
				<div className="mdp-solve-panel__progress-track">
					<div
						className={`mdp-solve-panel__progress-bar ${loading ? 'is-loading' : ''} ${progress === 100 ? 'is-complete' : ''}`}
						style={{ width: `${progress}%` }}
					/>
				</div>
				<div className="mdp-solve-panel__progress-text">
					{loading ? `Solving... ${progress}%` : progress === 100 ? 'Solve complete' : 'Idle'}
				</div>
			</div>

			{error ? <div className="mdp-solve-panel__error">{error}</div> : null}

			{result ? (
				<div className="mdp-solve-panel__result">
					<div className="mdp-solve-panel__result-title">MDP saved successfully</div>
					<div className="mdp-solve-panel__result-row">MDP ID: {result.mdp_id}</div>
					<div className="mdp-solve-panel__result-row">
						GMM IDs: {result.gmm_ids.join(', ')}
					</div>
				</div>
			) : null}
		</div>
	)
}

export default MdpSolvePanel