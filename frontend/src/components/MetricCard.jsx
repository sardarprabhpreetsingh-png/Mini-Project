import React from 'react';

export default function MetricCard({
  title,
  value,
  unit = '',
  badgeText,
  badgeType = 'neutral', // 'success' | 'warning' | 'danger' | 'info' | 'neutral'
  icon: Icon,
  description,
  accentColor = 'var(--accent-primary)'
}) {
  return (
    <div className="glass-card metric-card">
      <div className="metric-card-header">
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {title}
        </span>
        {Icon && (
          <div className="metric-icon-wrap" style={{ color: accentColor }}>
            <Icon size={20} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
        <span className="metric-card-value">{value}</span>
        {unit && <span className="metric-unit">{unit}</span>}
      </div>

      {badgeText && (
        <div style={{ marginTop: '10px' }}>
          <span className={`badge badge-${badgeType}`}>
            {badgeText}
          </span>
        </div>
      )}

      {description && (
        <p className="metric-card-desc">
          {description}
        </p>
      )}
    </div>
  );
}
