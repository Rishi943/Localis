import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { colors, fonts } from '../lib/design';
import { BAR, BEAT } from '../lib/beats';

interface RsbPanelProps {
  startFrame: number;
}

const SWATCH_COLORS = [
  '#f97316', '#fb923c', '#e5e5e5', '#ffffff', '#818cf8', '#c084fc', '#f43f5e',
];

/** SVG bulb graphic matching real app's #rsb-bulb-graphic (110×110) */
const BulbGraphic: React.FC<{ color: string; brightness: number }> = ({ color, brightness }) => {
  const glowOpacity = brightness / 100;
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width={110} height={110}>
      {/* Body — fills with active swatch color */}
      <path
        d="M12 2C8.686 2 6 4.686 6 8c0 2.21 1.136 4.15 2.857 5.285L9 15h6l.143-1.715C16.864 12.15 18 10.21 18 8c0-3.314-2.686-6-6-6z"
        fill={color}
        fillOpacity={0.6}
      />
      {/* Glow layer — blur, matches swatch color */}
      <path
        d="M12 2C8.686 2 6 4.686 6 8c0 2.21 1.136 4.15 2.857 5.285L9 15h6l.143-1.715C16.864 12.15 18 10.21 18 8c0-3.314-2.686-6-6-6z"
        fill={color}
        fillOpacity={glowOpacity * 0.5}
        style={{ filter: 'blur(3px)' }}
      />
      {/* Base rings */}
      <rect x={9} y={15} width={6} height={1.8} rx={0.9} fill="rgba(255,255,255,0.28)" />
      <rect x={9.5} y={16.8} width={5} height={1.4} rx={0.7} fill="rgba(255,255,255,0.18)" />
      <rect x={10} y={18.2} width={4} height={1.4} rx={0.7} fill="rgba(255,255,255,0.12)" />
    </svg>
  );
};

/** Stat bar row */
const StatRow: React.FC<{ label: string; value: string; pct: number; barColor: string }> = ({ label, value, pct, barColor }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 9 }}>
    <span style={{ fontSize: 10, fontWeight: 600, color: 'rgba(255,255,255,0.35)', width: 34, flexShrink: 0 }}>{label}</span>
    <div style={{ flex: 1, height: 3, background: 'rgba(255,255,255,0.1)', borderRadius: 100, overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: 100 }} />
    </div>
    <span style={{ fontSize: 10, fontFamily: fonts.mono, color: 'rgba(255,255,255,0.4)', width: 44, textAlign: 'right' as const, flexShrink: 0 }}>{value}</span>
  </div>
);

export const RsbPanel: React.FC<RsbPanelProps> = ({ startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - startFrame);

  // Slide in
  const slideProgress = spring({ frame: localFrame, fps, config: { damping: 22, stiffness: 130 } });
  const translateX = interpolate(slideProgress, [0, 1], [284, 0]);

  // Swatch cycling starts at BAR * 2 local
  const CYCLE_START = BAR * 2;
  const cycleFrame = Math.max(0, localFrame - CYCLE_START);
  const swatchInterval = BEAT * 2;
  const activeSwatchIndex = Math.floor(cycleFrame / swatchInterval) % SWATCH_COLORS.length;
  const activeColor = localFrame < CYCLE_START ? '#555' : SWATCH_COLORS[activeSwatchIndex];

  // Brightness animation
  const BRIGHTNESS_ANIM_START = BAR * 6;
  const rawBrightness = localFrame < BRIGHTNESS_ANIM_START
    ? 27
    : interpolate(localFrame, [BRIGHTNESS_ANIM_START, BRIGHTNESS_ANIM_START + BAR], [27, 80], { extrapolateRight: 'clamp' });
  const brightness = localFrame > BRIGHTNESS_ANIM_START + BAR
    ? interpolate(localFrame, [BRIGHTNESS_ANIM_START + BAR, BRIGHTNESS_ANIM_START + BAR + BAR / 2], [80, 27], { extrapolateRight: 'clamp' })
    : rawBrightness;

  const sectionBorder = '1px solid rgba(255,255,255,0.06)';

  return (
    <div style={{
      transform: `translateX(${translateX}px)`,
      width: RSB_PANEL_WIDTH,
      height: '100%',
      fontFamily: fonts.ui,
      display: 'flex', flexDirection: 'column',
      overflowY: 'hidden',
    }}>
      {/* Panel header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '13px 14px 11px',
        borderBottom: sectionBorder, flexShrink: 0,
      }}>
        <span style={{ fontSize: 15, color: 'rgba(255,255,255,0.35)' }}>⚙</span>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.5)', flex: 1 }}>
          Quick Controls
        </span>
        <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 15 }}>▶</span>
      </div>

      {/* Scrollable body */}
      <div style={{ flex: 1, overflowY: 'hidden' }}>
        {/* ── HA Section ── */}
        <div style={{ padding: 14, borderBottom: sectionBorder }}>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.25)', marginBottom: 11 }}>
            Lights
          </div>
          {/* Light name + toggle */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#fff' }}>Rishi Room Light</span>
            <div style={{
              width: 38, height: 21, borderRadius: 100,
              background: colors.green, position: 'relative',
            }}>
              <div style={{
                position: 'absolute', left: 20, top: 3,
                width: 15, height: 15, borderRadius: '50%', background: '#fff',
              }} />
            </div>
          </div>
          {/* Brightness % */}
          <div style={{ textAlign: 'center' as const, fontSize: 38, fontWeight: 700, color: '#fff', lineHeight: 1 }}>
            {Math.round(brightness)}%
          </div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.28)', textAlign: 'center' as const, marginTop: 3, marginBottom: 14 }}>
            Updated just now
          </div>
          {/* SVG bulb graphic */}
          <div style={{
            display: 'flex', justifyContent: 'center', marginBottom: 14,
            filter: activeColor !== '#555' ? `drop-shadow(0 0 20px ${activeColor}44)` : 'none',
          }}>
            <BulbGraphic color={activeColor} brightness={brightness} />
          </div>
          {/* Control buttons: power, brightness, color, kelvin */}
          <div style={{ display: 'flex', gap: 7, justifyContent: 'center', marginBottom: 12 }}>
            {['⏻', '☀', '🎨', '🌡'].map((icon, i) => (
              <div key={i} style={{
                width: 38, height: 38, borderRadius: '50%',
                background: i === 2 ? 'rgba(251,146,60,0.18)' : 'rgba(255,255,255,0.06)',
                border: i === 2 ? '1px solid rgba(251,146,60,0.4)' : '1px solid rgba(255,255,255,0.09)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: i === 2 ? '#fb923c' : 'rgba(255,255,255,0.45)', fontSize: 14,
              }}>{icon}</div>
            ))}
          </div>
          {/* Color swatches */}
          <div style={{ display: 'flex', gap: 7, justifyContent: 'center', flexWrap: 'wrap' as const }}>
            {SWATCH_COLORS.map((c, i) => (
              <div key={i} style={{
                width: 22, height: 22, borderRadius: '50%',
                background: c,
                border: i === activeSwatchIndex && localFrame >= CYCLE_START
                  ? `2px solid rgba(255,255,255,0.85)`
                  : '2px solid transparent',
                boxShadow: i === activeSwatchIndex && localFrame >= CYCLE_START
                  ? `0 0 8px ${c}88`
                  : 'none',
              }} />
            ))}
          </div>
        </div>

        {/* ── Model Section ── */}
        <div style={{ padding: 14, borderBottom: sectionBorder }}>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.25)', marginBottom: 11 }}>
            Model
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '9px 12px', borderRadius: 8,
            border: '1px solid rgba(255,255,255,0.08)',
            background: 'rgba(255,255,255,0.03)',
            marginBottom: 9,
          }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'rgba(255,255,255,0.7)' }}>Qwen2.5-7B-Instruct</span>
            <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 15 }}>▼</span>
          </div>
          <div style={{ display: 'flex', gap: 7 }}>
            <div style={{
              flex: 1, padding: 8, borderRadius: 8, textAlign: 'center' as const,
              fontSize: 12, fontWeight: 600,
              background: 'rgba(18,117,226,0.2)', border: '1px solid rgba(18,117,226,0.35)',
              color: 'rgba(255,255,255,0.7)',
            }}>Load</div>
            <div style={{
              flex: 1, padding: 8, borderRadius: 8, textAlign: 'center' as const,
              fontSize: 12, fontWeight: 600,
              background: 'rgba(185,28,28,0.18)', border: '1px solid rgba(185,28,28,0.35)',
              color: '#f87171',
            }}>Unload</div>
          </div>
        </div>

        {/* ── Prompt Section ── */}
        <div style={{ padding: 14, borderBottom: sectionBorder }}>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.25)', marginBottom: 11 }}>
            Prompt
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 9 }}>
            {['Default', 'Creative', 'Planning', 'Custom'].map((label, i) => (
              <div key={label} style={{
                padding: '8px 10px', borderRadius: 8, textAlign: 'center' as const,
                fontSize: 12, fontWeight: i === 0 ? 600 : 500,
                border: i === 0 ? '1px solid rgba(18,117,226,0.35)' : '1px solid rgba(255,255,255,0.09)',
                background: i === 0 ? 'rgba(18,117,226,0.16)' : 'rgba(255,255,255,0.04)',
                color: i === 0 ? '#60a5fa' : 'rgba(255,255,255,0.5)',
              }}>{label}</div>
            ))}
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '9px 12px', borderRadius: 8,
            border: '1px solid rgba(255,255,255,0.08)',
            background: 'rgba(255,255,255,0.03)',
            color: 'rgba(255,255,255,0.4)', fontSize: 12,
          }}>
            Edit System Prompt
            <span style={{ fontSize: 14 }}>→</span>
          </div>
        </div>

        {/* ── Stats Section ── */}
        <div style={{ padding: 14 }}>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.25)', marginBottom: 11 }}>
            Stats
          </div>
          <StatRow label="CPU" value="12%" pct={12} barColor={colors.green} />
          <StatRow label="RAM" value="4.2G" pct={53} barColor="#3b82f6" />
          <StatRow label="VRAM" value="6.1G" pct={76} barColor={colors.amber} />
        </div>
      </div>
    </div>
  );
};

const RSB_PANEL_WIDTH = 284;
