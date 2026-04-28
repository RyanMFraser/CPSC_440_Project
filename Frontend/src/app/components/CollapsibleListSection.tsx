import { useState } from 'react'

type CollapsibleListSectionProps = {
  title: string
  items: string[]
  count?: number
  defaultOpen?: boolean
  loading?: boolean
  error?: string | null
}

function CollapsibleListSection({
  title,
  items,
  count,
  defaultOpen = false,
  loading = false,
  error = null,
}: CollapsibleListSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <section className="sidebar-section">
      <button
        type="button"
        className="sidebar-section__header"
        onClick={() => setIsOpen((value) => !value)}
        aria-expanded={isOpen}
      >
        <span className="sidebar-section__title">{title}</span>
        <span className="sidebar-section__meta">
          {typeof count === 'number' ? count : items.length}
          <span className={`sidebar-section__chevron ${isOpen ? 'is-open' : ''}`}>▾</span>
        </span>
      </button>

      {isOpen && (
        <div className="sidebar-section__body">
          {loading && <p className="sidebar-section__hint">Loading...</p>}
          {error && !loading && <p className="sidebar-section__error">{error}</p>}
          {!loading && !error && items.length === 0 && (
            <p className="sidebar-section__hint">No items available.</p>
          )}
          {!loading && !error && items.length > 0 && (
            <ul className="sidebar-section__list">
              {items.map((item) => (
                <li key={item} className="sidebar-section__item">
                  {item}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}

export default CollapsibleListSection
