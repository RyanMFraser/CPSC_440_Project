import React from 'react'

type SectionHeaderProps = {
	mainText: string
	subText?: string
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ mainText, subText }) => {
	return (
		<div className="section-header">
			<div className="section-header__main">{mainText}</div>
			{subText && <div className="section-header__sub">{subText}</div>}
		</div>
	)
}

export default SectionHeader
