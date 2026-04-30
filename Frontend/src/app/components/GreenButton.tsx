import React from 'react'

interface GreenButtonProps {
  onClick: () => void
  children: React.ReactNode
  disabled?: boolean
}

const GreenButton: React.FC<GreenButtonProps> = ({ onClick, children, disabled = false }) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        backgroundColor: disabled ? '#a8c97f' : '#2d5016',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: '6px',
        fontSize: '16px',
        fontWeight: '600',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'background-color 0.2s ease',
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          (e.target as HTMLButtonElement).style.backgroundColor = '#1f3a0f'
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          (e.target as HTMLButtonElement).style.backgroundColor = '#2d5016'
        }
      }}
    >
      {children}
    </button>
  )
}

export default GreenButton
