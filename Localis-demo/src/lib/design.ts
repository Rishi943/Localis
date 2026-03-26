export const colors = {
  bg: '#000000',
  panel: 'rgba(15,15,15,0.45)',       // was 0.85, match real --bg-panel
  sidebar: 'rgba(10,10,10,0.55)',      // was 0.90, match real --bg-sidebar
  glass: 'rgba(20,20,20,0.70)',
  border: 'rgba(255,255,255,0.15)',    // was 0.08, match real --border-subtle
  borderHighlight: 'rgba(255,255,255,0.20)', // was 0.15, match real --border-highlight
  borderInner: 'rgba(255,255,255,0.06)',
  text: '#ffffff',
  textMuted: 'rgba(255,255,255,0.55)',
  textDim: 'rgba(255,255,255,0.28)',   // was 0.30, match real --text-muted
  accent: '#1275e2',                   // was #3b82f6, match real --accent-primary
  accentSoft: 'rgba(18,117,226,0.12)', // for active toolbar buttons
  accentBorder: 'rgba(18,117,226,0.28)',
  green: '#22c55e',
  amber: '#f59e0b',
  sand: '#c8b89a',
  red: '#ef4444',
  glassBg: 'rgba(20,20,20,0.70)',
} as const;

export const fonts = {
  ui: "'Inter', system-ui, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const glass = {
  background: colors.glass,
  backdropFilter: 'blur(24px) saturate(180%)',
  WebkitBackdropFilter: 'blur(24px) saturate(180%)',
  border: `1px solid ${colors.border}`,
} as const;

export const glassShadow = '0 32px 80px rgba(0,0,0,.75), inset 0 1px 0 rgba(255,255,255,0.20), inset 1px 0 0 rgba(255,255,255,0.05)';
