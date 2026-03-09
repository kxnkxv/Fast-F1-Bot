interface DriverSelectorProps {
  availableDrivers: string[];
  selectedDrivers: string[];
  onToggle: (driver: string) => void;
  maxSelection?: number;
}

export function DriverSelector({
  availableDrivers,
  selectedDrivers,
  onToggle,
  maxSelection = 2,
}: DriverSelectorProps) {
  return (
    <div className="px-4">
      <p className="text-xs text-[var(--f1-text-secondary)] mb-2">
        Select up to {maxSelection} drivers to compare
      </p>
      <div className="flex flex-wrap gap-2">
        {availableDrivers.map((driver) => {
          const isSelected = selectedDrivers.includes(driver);
          const isDisabled =
            !isSelected && selectedDrivers.length >= maxSelection;

          return (
            <button
              key={driver}
              onClick={() => onToggle(driver)}
              disabled={isDisabled}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                isSelected
                  ? "bg-[var(--f1-accent)] text-white"
                  : isDisabled
                    ? "bg-[var(--f1-border)] text-[var(--f1-text-secondary)] opacity-40"
                    : "bg-[var(--f1-card-bg)] text-[var(--f1-text-secondary)] active:bg-[var(--f1-border)]"
              }`}
            >
              {driver}
            </button>
          );
        })}
      </div>
    </div>
  );
}
