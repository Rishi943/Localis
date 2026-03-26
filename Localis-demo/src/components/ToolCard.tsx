import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { colors, fonts, glass } from '../lib/design';

export interface ToolRow {
  key: string;
  value: string;
  valueColor?: string;
}

interface ToolCardProps {
  /** Scene-relative frame when card slides in */
  startFrame: number;
  /** e.g. "assist.action" or "web_search" */
  toolName: string;
  /** e.g. "Light controlled" or "3 results" */
  subtitle: string;
  rows?: ToolRow[];
  /** Dot colour: defaults to green */
  dotColor?: string;
}

export const ToolCard: React.FC<ToolCardProps> = ({
  startFrame,
  toolName,
  subtitle,
  rows = [],
  dotColor = colors.green,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - startFrame);

  const progress = spring({
    frame: localFrame,
    fps,
    config: { damping: 20, stiffness: 140 },
  });

  const opacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });
  const translateY = interpolate(progress, [0, 1], [24, 0]);

  return (
    <div style={{
      opacity,
      transform: `translateY(${translateY}px)`,
      ...glass,
      background: 'rgba(12,16,12,0.80)',
      border: `1px solid rgba(34,197,94,0.2)`,
      borderRadius: 12,
      padding: '10px 14px',
      fontFamily: fonts.mono,
      fontSize: 12,
      maxWidth: 480,
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: rows.length ? 10 : 0 }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: dotColor,
          boxShadow: `0 0 6px ${dotColor}`,
        }} />
        <span style={{ color: colors.green, fontWeight: 600 }}>{toolName}</span>
        <span style={{ color: colors.border }}>·</span>
        <span style={{ color: colors.textMuted }}>{subtitle}</span>
      </div>

      {/* Rows */}
      {rows.map((row, i) => (
        <div key={i} style={{
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'center',
          padding: '4px 0',
          borderTop: `1px solid ${colors.border}`,
          gap: 16,
        }}>
          <span style={{ color: colors.textMuted }}>{row.key}</span>
          <span style={{
            color: row.valueColor ?? colors.textMuted,
            fontFamily: fonts.mono,
            background: row.valueColor ? `${row.valueColor}18` : 'transparent',
            padding: row.valueColor ? '2px 8px' : '0',
            borderRadius: 4,
            fontSize: 11,
          }}>{row.value}</span>
        </div>
      ))}
    </div>
  );
};
