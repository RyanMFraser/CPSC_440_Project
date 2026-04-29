import React from 'react'

type SectionHeaderProps = {
	mainText: string
	subText?: string
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ mainText, subText }) => {
	return (
		<div
			className="section-header"
			style={{
				backgroundColor: '#228B22',
				color: '#ffffff',
				borderRadius: 12,
				padding: '1rem 1.1rem',
				boxShadow: '0 6px 18px rgba(15, 23, 42, 0.08)',
				width: '100%',
			}}
		>
			<div className="section-header__main" style={{ color: '#ffffff' }}>
				{mainText}
			</div>
			{subText && (
				<div className="section-header__sub" style={{ color: 'rgba(255,255,255,0.9)' }}>
					{subText}
				</div>
			)}
		</div>
	)
}

export default SectionHeader
