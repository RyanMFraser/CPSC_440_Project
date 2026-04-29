import { useMemo } from 'react'
import Plot from 'react-plotly.js'

type DispersionHeatMapProps = {
	gmmId: string
	weights: number[]
	means: number[][]
	covariances: number[][][]
	height?: number
}

const X_MIN = -50
const X_MAX = 50
const Y_MIN = 0
const Y_MAX = 250

function multivariateNormalPdf(point: number[], mean: number[], covariance: number[][]) {
	const determinant = covariance[0][0] * covariance[1][1] - covariance[0][1] * covariance[1][0]
	if (determinant <= 0) return 0

	const inverse00 = covariance[1][1] / determinant
	const inverse01 = -covariance[0][1] / determinant
	const inverse10 = -covariance[1][0] / determinant
	const inverse11 = covariance[0][0] / determinant

	const deltaX = point[0] - mean[0]
	const deltaY = point[1] - mean[1]
	const mahalanobis =
		deltaX * (inverse00 * deltaX + inverse01 * deltaY) +
		deltaY * (inverse10 * deltaX + inverse11 * deltaY)

	const normalization = 1 / (2 * Math.PI * Math.sqrt(determinant))
	return normalization * Math.exp(-0.5 * mahalanobis)
}

function buildDensityGrid(weights: number[], means: number[][], covariances: number[][][], gridSize = 90) {
	const xValues: number[] = []
	const yValues: number[] = []

	for (let i = 0; i < gridSize; i += 1) {
		xValues.push(X_MIN + (i / (gridSize - 1)) * (X_MAX - X_MIN))
		yValues.push(Y_MIN + (i / (gridSize - 1)) * (Y_MAX - Y_MIN))
	}

	const zValues: number[][] = []
	let minPositive = Number.POSITIVE_INFINITY
	let maxValue = 0

	for (let row = 0; row < yValues.length; row += 1) {
		const currentRow: number[] = []
		for (let column = 0; column < xValues.length; column += 1) {
			const point = [xValues[column], yValues[row]]
			let density = 0

			for (let component = 0; component < weights.length; component += 1) {
				density += weights[component] * multivariateNormalPdf(point, means[component], covariances[component])
			}

			const safeDensity = Math.max(density, 1e-12)
			currentRow.push(safeDensity)
			if (safeDensity < minPositive) minPositive = safeDensity
			if (safeDensity > maxValue) maxValue = safeDensity
		}
		zValues.push(currentRow)
	}

	const logZ = zValues.map((row) => row.map((value) => Math.log10(value)))
	const minLog = Math.log10(minPositive)
	const maxLog = Math.log10(Math.max(maxValue, minPositive * 10))

	return { xValues, yValues, zValues, logZ, minLog, maxLog }
}

const DispersionHeatMap = ({ gmmId, weights, means, covariances, height = 520 }: DispersionHeatMapProps) => {
	const { xValues, yValues, logZ, minLog, maxLog } = useMemo(
		() => buildDensityGrid(weights, means, covariances),
		[weights, means, covariances],
	)

	const contourStep = Math.max((maxLog - minLog) / 10, 0.1)

	return (
		<div className="dispersion-heatmap">
			<Plot
				data={[
					{
						type: 'heatmap',
						x: xValues,
						y: yValues,
						z: logZ,
						colorscale: 'Viridis',
						colorbar: {
							title: 'log10 density',
							tickformat: '.2f',
						},
						hovertemplate: 'X=%{x:.1f}<br>Y=%{y:.1f}<br>log10 density=%{z:.2f}<extra></extra>',
						zsmooth: 'best',
					},
					{
						type: 'contour',
						x: xValues,
						y: yValues,
						z: logZ,
						contours: {
							coloring: 'none',
							showlabels: true,
							start: minLog,
							end: maxLog,
							size: contourStep,
						},
						line: {
							color: 'rgba(255,255,255,0.95)',
							width: 1.25,
						},
						hoverinfo: 'skip',
						showscale: false,
					},
				]}
				layout={{
					title: {
						text: `${gmmId} Density Heatmap`,
						font: { size: 18, color: '#0f172a' },
					},
					xaxis: {
						title: { text: 'X' },
						range: [X_MIN, X_MAX],
						gridcolor: 'rgba(148,163,184,0.22)',
						zeroline: false,
					},
					yaxis: {
						title: { text: 'Y' },
						range: [Y_MIN, Y_MAX],
						gridcolor: 'rgba(148,163,184,0.22)',
						zeroline: false,
						scaleanchor: 'x',
						scaleratio: 1,
					},
					margin: { l: 60, r: 20, t: 60, b: 55 },
					paper_bgcolor: 'rgba(0,0,0,0)',
					plot_bgcolor: 'rgba(255,255,255,0)',
					height,
					autosize: true,
					font: { family: 'inherit', color: '#334155' },
				}}
				config={{
					responsive: true,
					displayModeBar: false,
				}}
				useResizeHandler
				style={{ width: '100%', height: `${height}px` }}
			/>
		</div>
	)
}

export default DispersionHeatMap
