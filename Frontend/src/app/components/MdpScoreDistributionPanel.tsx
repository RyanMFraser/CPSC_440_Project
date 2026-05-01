import { useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import apiClient from '../../services/api'
import GreenButton from './GreenButton'
import SectionHeader from './SectionHeader'

type MdpScoreDistributionPanelProps = {
	mdpIds: string[]
}

type DistributionResponse = {
	mdp_id: string
	state: { x: number; y: number }
	n_simulations: number
	distribution: number[]
}

const DEFAULT_X = '0'
const DEFAULT_Y = '25'

const MdpScoreDistributionPanel = ({ mdpIds }: MdpScoreDistributionPanelProps) => {
	const [xValue, setXValue] = useState(DEFAULT_X)
	const [yValue, setYValue] = useState(DEFAULT_Y)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [selectedMdpId, setSelectedMdpId] = useState<string | null>(null)
	const [distribution, setDistribution] = useState<number[]>([])
	const [simulationCount, setSimulationCount] = useState<number>(0)

	const hasSelection = (mdpIds?.length ?? 0) > 0
	const activeMdpId = selectedMdpId ?? mdpIds?.[0] ?? null

	const parsedState = useMemo(() => {
		const x = Number(xValue)
		const y = Number(yValue)
		if (!Number.isFinite(x) || !Number.isFinite(y)) return null
		return { x, y }
	}, [xValue, yValue])

	const shotLabels = useMemo(() => distribution.map((_, index) => String(index)), [distribution])

	const requestDistribution = async () => {
		if (!hasSelection || !activeMdpId) {
			setError('Select at least one mdp_id from the sidebar.')
			return
		}

		if (!parsedState) {
			setError('Enter a valid X and Y starting state.')
			return
		}

		setLoading(true)
		setError(null)
		setDistribution([])
		setSimulationCount(0)
		setSelectedMdpId(activeMdpId)

		try {
			const response = (await apiClient.post('/mdp/score_distribution', {
				mdp_id: activeMdpId,
				state: parsedState,
			})) as DistributionResponse

			setSelectedMdpId(response.mdp_id ?? activeMdpId)
			setDistribution(response.distribution ?? [])
			setSimulationCount(response.n_simulations ?? 0)
		} catch (requestError: any) {
			console.error('Failed fetching score distribution:', requestError)
			setError(requestError?.message ?? 'Failed to fetch score distribution.')
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="mdp-score-distribution-panel">
			<SectionHeader
				mainText="MDP Score Distribution"
				subText="Select an mdp_id, enter a starting position, then click Execute to sample 1000 rollouts and plot the shot-count distribution."
			/>

			<div className="mdp-score-distribution-panel__controls">
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

			<div className="mdp-score-distribution-panel__actions">
				<GreenButton onClick={requestDistribution} disabled={loading || !hasSelection}>
					{loading ? 'Executing...' : 'Execute'}
				</GreenButton>
				<div className="mdp-score-distribution-panel__selected">
					{activeMdpId ? `Active mdp_id: ${activeMdpId}` : 'No mdp_id selected'}
				</div>
			</div>

			{error ? <div className="mdp-score-distribution-panel__error">{error}</div> : null}

			{distribution.length > 0 ? (
				<div className="mdp-score-distribution-panel__chart-card">
					<div className="mdp-score-distribution-panel__chart-meta">
						<div className="mdp-score-distribution-panel__chart-title">
							Score distribution for {selectedMdpId}
						</div>
						<div className="mdp-score-distribution-panel__chart-subtitle">
							{simulationCount} simulations from start state ({parsedState?.x ?? xValue}, {parsedState?.y ?? yValue})
						</div>
					</div>
					<Plot
						data={[
							{
								type: 'bar',
								x: shotLabels,
								y: distribution,
								marker: {
									color: 'rgba(34, 139, 34, 0.85)',
								},
								hovertemplate: 'Shots=%{x}<br>Probability=%{y:.3f}<extra></extra>',
							},
						]}
						layout={{
							margin: { l: 55, r: 20, t: 20, b: 55 },
							paper_bgcolor: 'rgba(0,0,0,0)',
							plot_bgcolor: 'rgba(255,255,255,0)',
							height: 360,
							xaxis: {
								title: { text: 'Shots taken' },
								type: 'category',
								tickangle: 0,
								gridcolor: 'rgba(148,163,184,0.18)',
							},
							yaxis: {
								title: { text: 'Probability' },
								range: [0, Math.max(...distribution, 0.05)],
								gridcolor: 'rgba(148,163,184,0.18)',
							},
							font: { family: 'inherit', color: '#334155' },
						}}
						config={{ responsive: true, displayModeBar: false }}
						useResizeHandler
						style={{ width: '100%', height: '360px' }}
					/>
				</div>
			) : (
				<div className="mdp-score-distribution-panel__empty">
					No distribution plotted yet. Click Execute to generate the chart.
				</div>
			)}
		</div>
	)
}

export default MdpScoreDistributionPanel