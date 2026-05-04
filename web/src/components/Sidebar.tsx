import './Sidebar.css';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onSearchClick: () => void;
}

export default function Sidebar({
  collapsed,
  onToggle,
  onSearchClick,
}: SidebarProps) {
  return (
    <nav className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"
              fill="#2AA364"
              stroke="#2AA364"
              strokeWidth="1"
            />
          </svg>
          {!collapsed && (
            <span className="sidebar__title">Electricity Maps</span>
          )}
        </div>
        <button
          className="sidebar__toggle"
          onClick={onToggle}
          aria-label="Toggle Sidebar"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            {collapsed ? (
              <path d="M6 3l5 5-5 5V3z" />
            ) : (
              <path d="M10 3L5 8l5 5V3z" />
            )}
          </svg>
        </button>
      </div>

      <ul className="sidebar__nav">
        <li>
          <a href="#" className="sidebar__link">
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M3 10.5L10 4l7 6.5V17a1 1 0 01-1 1H4a1 1 0 01-1-1V10.5z" />
            </svg>
            {!collapsed && <span>Home</span>}
          </a>
        </li>
        <li>
          <a href="#" className="sidebar__link sidebar__link--active">
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <rect x="2" y="3" width="16" height="14" rx="2" />
              <path d="M2 8h16M8 8v9" />
            </svg>
            {!collapsed && <span>Map</span>}
          </a>
        </li>
        <li>
          <a href="#" className="sidebar__link">
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M5 3l2 6H3l2 6M11 3l2 6h-4l2 6" />
            </svg>
            {!collapsed && <span>Developer Hub</span>}
          </a>
        </li>
        <li>
          <a href="#" className="sidebar__link">
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <rect x="2" y="2" width="6" height="6" rx="1" />
              <rect x="12" y="2" width="6" height="6" rx="1" />
              <rect x="2" y="12" width="6" height="6" rx="1" />
              <rect x="12" y="12" width="6" height="6" rx="1" />
            </svg>
            {!collapsed && <span>Coverage</span>}
          </a>
        </li>
      </ul>

      <div className="sidebar__footer">
        <button className="sidebar__link" onClick={onSearchClick}>
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="9" cy="9" r="6" />
            <path d="M14 14l4 4" />
          </svg>
          {!collapsed && <span>Search areas</span>}
        </button>
      </div>
    </nav>
  );
}
