import { useNavigate } from "react-router-dom";

interface PageHeaderProps {
  title: string;
  showBack?: boolean;
  subtitle?: string;
}

export function PageHeader({ title, showBack = false, subtitle }: PageHeaderProps) {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 bg-[var(--f1-bg)] border-b border-[var(--f1-border)] backdrop-blur-lg bg-opacity-95">
      <div className="flex items-center gap-3 px-4 py-3">
        {showBack && (
          <button
            onClick={() => navigate(-1)}
            className="p-1 -ml-1 text-[var(--f1-text-secondary)] hover:text-[var(--f1-text-primary)] transition-colors"
            aria-label="Go back"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
        )}
        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-bold truncate">{title}</h1>
          {subtitle && (
            <p className="text-xs text-[var(--f1-text-secondary)] truncate">
              {subtitle}
            </p>
          )}
        </div>
      </div>
    </header>
  );
}
