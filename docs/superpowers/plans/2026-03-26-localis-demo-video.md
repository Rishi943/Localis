# Localis Demo Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished 83.4-second Remotion product demo video for Localis — 6 scenes, beat-synced to 100 BPM jazz, Midnight Glass aesthetic, 1920×1080.

**Architecture:** All animation driven by `useCurrentFrame()` — no CSS transitions. Shared design tokens in `lib/`. Reusable components in `components/`. Six scene files wired together via `TransitionSeries` with 18-frame (1-beat) fade transitions. Audio baked in via `<Audio>`.

**Tech Stack:** Remotion 4.0.441, React 19, TypeScript, @remotion/transitions, TailwindCSS v4

**Beat grid constants:** BPM=100, FPS=30, BEAT=18f, BAR=72f

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/lib/design.ts` | Create | Colour tokens + font stacks |
| `src/lib/beats.ts` | Create | Beat/bar frame constants |
| `src/components/Shell.tsx` | Create | Full Localis UI chrome (header, sidebars, wallpaper) |
| `src/components/ChatBubble.tsx` | Create | User (right) + Assistant (left with logo avatar) bubbles |
| `src/components/TypeWriter.tsx` | Create | Character-by-character text reveal |
| `src/components/ZoomWrapper.tsx` | Create | Spring scale punch-in wrapper |
| `src/components/ToolCard.tsx` | Create | web_search / assist.action cards |
| `src/components/ThinkingBlock.tsx` | Create | Animated reasoning panel |
| `src/components/VoiceBar.tsx` | Create | Gray→amber→green pill with pulse |
| `src/components/IngestProgress.tsx` | Create | Staggered RAG checklist |
| `src/components/RsbPanel.tsx` | Create | Quick Controls sidebar (bulb, swatches, slider) |
| `src/components/NotesPanel.tsx` | Create | Notes overlay card grid |
| `src/scenes/00-Intro.tsx` | Create | Logo + tagline, 216f |
| `src/scenes/01-Rag.tsx` | Create | Ingest + summarise, 576f |
| `src/scenes/02-WebSearch.tsx` | Create | F1 web search, 432f |
| `src/scenes/03-HomeAssistant.tsx` | Create | RSB animated controls, 576f |
| `src/scenes/04-Notes.tsx` | Create | Voice note creation, 360f |
| `src/scenes/05-Climax.tsx` | Create | Light banda kar climax, 432f |
| `src/Composition.tsx` | Rewrite | TransitionSeries + Audio fade |
| `src/Root.tsx` | Rewrite | Register 1920×1080, 2502f composition |

---

## Task 1: Foundation — design tokens, beat constants, CSS

**Files:**
- Create: `src/lib/design.ts`
- Create: `src/lib/beats.ts`
- Modify: `src/index.css`

- [ ] **Step 1: Create `src/lib/design.ts`**

```typescript
export const colors = {
  bg: '#000000',
  panel: 'rgba(15,15,15,0.85)',
  sidebar: 'rgba(10,10,10,0.90)',
  glass: 'rgba(20,20,20,0.70)',
  border: 'rgba(255,255,255,0.08)',
  borderHighlight: 'rgba(255,255,255,0.15)',
  text: '#ffffff',
  textMuted: 'rgba(255,255,255,0.55)',
  textDim: 'rgba(255,255,255,0.30)',
  accent: '#3b82f6',
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
```

- [ ] **Step 2: Create `src/lib/beats.ts`**

```typescript
export const BPM = 100;
export const FPS = 30;
/** Frames per beat: FPS * 60 / BPM = 18 */
export const BEAT = 18;
/** Frames per bar (4 beats) */
export const BAR = 72;

export const beat = (n: number): number => Math.round(n * BEAT);
export const bar = (n: number): number => Math.round(n * BAR);
```

- [ ] **Step 3: Replace `src/index.css` content**

```css
@import "tailwindcss";

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
```

- [ ] **Step 4: Verify — open `http://localhost:3000`. Studio should load without errors.**

- [ ] **Step 5: Commit**

```bash
git add src/lib/design.ts src/lib/beats.ts src/index.css
git commit -m "feat(demo): design tokens, beat constants, font import"
```

---

## Task 2: Shell — full Localis UI chrome

**Files:**
- Create: `src/components/Shell.tsx`

- [ ] **Step 1: Create `src/components/Shell.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate, Img, staticFile } from 'remotion';
import { colors, fonts, glass } from '../lib/design';

interface ShellProps {
  /** Total frame count for this scene (drives bg push calc) */
  sceneDuration: number;
  /** Chat content for centre column */
  children?: React.ReactNode;
  /** Right sidebar content — if provided, RSB renders */
  rsbContent?: React.ReactNode;
  /** 0–1 opacity multiplier for chat area (for dimming in later scenes) */
  chatOpacity?: number;
  /** Extra dark overlay on bg (0–1) for climax scene */
  bgDimExtra?: number;
}

export const Shell: React.FC<ShellProps> = ({
  sceneDuration,
  children,
  rsbContent,
  chatOpacity = 1,
  bgDimExtra = 0,
}) => {
  const frame = useCurrentFrame();

  const bgScale = interpolate(frame, [0, sceneDuration], [1.0, 1.06], {
    extrapolateRight: 'clamp',
    extrapolateLeft: 'clamp',
  });

  return (
    <div style={{ width: 1920, height: 1080, overflow: 'hidden', position: 'relative', fontFamily: fonts.ui }}>
      {/* Wallpaper — slow cinematic push */}
      <div style={{
        position: 'absolute', inset: -80,
        transform: `scale(${bgScale})`,
        transformOrigin: 'center center',
        background: [
          'radial-gradient(ellipse at 25% 85%, rgba(12,18,10,0.7) 0%, transparent 35%)',
          'radial-gradient(ellipse at 75% 80%, rgba(10,14,18,0.5) 0%, transparent 30%)',
          'radial-gradient(ellipse at 50% 55%, rgba(18,22,28,0.4) 0%, transparent 50%)',
          'linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(6,8,12,1) 25%, rgba(10,12,16,1) 55%, rgba(4,5,8,1) 80%, rgba(0,0,0,1) 100%)',
        ].join(', '),
        zIndex: 0,
      }} />

      {/* Extra dim overlay for climax */}
      {bgDimExtra > 0 && (
        <div style={{
          position: 'absolute', inset: 0,
          background: `rgba(0,0,0,${bgDimExtra})`,
          zIndex: 1,
          pointerEvents: 'none',
        }} />
      )}

      {/* LEFT SIDEBAR — 48px */}
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: 48,
        background: colors.sidebar,
        borderRight: `1px solid ${colors.border}`,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        paddingTop: 12, paddingBottom: 12, gap: 8,
        zIndex: 10,
      }}>
        {/* Logo button */}
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: '#161616',
          border: `1px solid ${colors.borderHighlight}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          overflow: 'hidden',
        }}>
          <Img src={staticFile('logo.svg')} style={{ width: 28, height: 28 }} />
        </div>
        <div style={{ flex: 1 }} />
        {/* Settings icon */}
        <div style={{ color: colors.textDim, fontSize: 16 }}>⚙</div>
      </div>

      {/* HEADER — full width */}
      <div style={{
        position: 'absolute', left: 48, right: 0, top: 0, height: 52,
        ...glass,
        background: 'rgba(8,8,12,0.80)',
        borderBottom: `1px solid ${colors.border}`,
        display: 'flex', alignItems: 'center',
        paddingLeft: 20, paddingRight: 20,
        zIndex: 10,
      }}>
        <div>
          <div style={{ color: colors.text, fontSize: 15, fontWeight: 600, letterSpacing: '0.02em' }}>Localis</div>
          <div style={{ color: colors.textDim, fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase' }}>No Model Loaded</div>
        </div>
        <div style={{ flex: 1 }} />
        {/* Neural Engine Active */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'rgba(34,197,94,0.12)',
          border: `1px solid rgba(34,197,94,0.3)`,
          borderRadius: 20, padding: '4px 12px',
          color: colors.green, fontSize: 12, fontWeight: 500,
        }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: colors.green }} />
          Neural Engine Active
        </div>
        <div style={{
          marginLeft: 12, width: 32, height: 32, borderRadius: '50%',
          background: colors.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: 13, fontWeight: 700,
        }}>U</div>
      </div>

      {/* CHAT AREA */}
      <div style={{
        position: 'absolute',
        left: 48,
        right: rsbContent ? 280 : 48,
        top: 52,
        bottom: 80,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        padding: '24px 0',
        overflow: 'hidden',
        opacity: chatOpacity,
        zIndex: 5,
      }}>
        <div style={{ width: '100%', maxWidth: 760, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {children}
        </div>
      </div>

      {/* RIGHT SIDEBAR */}
      {rsbContent && (
        <div style={{
          position: 'absolute', right: 0, top: 52, bottom: 0, width: 280,
          background: colors.sidebar,
          borderLeft: `1px solid ${colors.border}`,
          zIndex: 10,
          overflowY: 'hidden',
        }}>
          {rsbContent}
        </div>
      )}

      {/* BOTTOM INPUT BAR */}
      <div style={{
        position: 'absolute', left: 48, right: rsbContent ? 280 : 48, bottom: 0, height: 80,
        ...glass,
        background: 'rgba(8,8,12,0.80)',
        borderTop: `1px solid ${colors.border}`,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: 8, zIndex: 10,
      }}>
        {/* Mode pills */}
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {['🌐 Web', '🏠 Home', '💭 Think', '📌 Remember'].map((label, i) => (
            <div key={i} style={{
              padding: '3px 10px', borderRadius: 20, fontSize: 11,
              background: i === 1 ? 'rgba(59,130,246,0.2)' : 'transparent',
              border: i === 1 ? `1px solid rgba(59,130,246,0.4)` : `1px solid ${colors.border}`,
              color: i === 1 ? colors.accent : colors.textMuted,
            }}>{label}</div>
          ))}
          <div style={{
            width: 28, height: 16, borderRadius: 8,
            background: 'rgba(255,255,255,0.15)',
            position: 'relative',
          }}>
            <div style={{
              width: 12, height: 12, borderRadius: '50%', background: '#fff',
              position: 'absolute', top: 2, right: 2,
            }} />
          </div>
        </div>
        {/* Input pill */}
        <div style={{
          width: '90%', maxWidth: 700, height: 44, borderRadius: 22,
          background: 'rgba(255,255,255,0.06)',
          border: `1px solid ${colors.borderHighlight}`,
          display: 'flex', alignItems: 'center',
          padding: '0 16px',
        }}>
          <span style={{ color: colors.textDim, fontSize: 14, flex: 1 }}>Message Localis…</span>
          <span style={{ color: colors.textDim, fontSize: 18 }}>🎤</span>
          <div style={{
            marginLeft: 10, width: 32, height: 32, borderRadius: '50%',
            background: colors.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 16,
          }}>↑</div>
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Add a quick preview registration in `src/Root.tsx`** (temporary, to verify)

```tsx
import './index.css';
import { Composition } from 'remotion';
import { Shell } from './components/Shell';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ShellPreview"
      component={() => <Shell sceneDuration={90}><div style={{color:'white',padding:20}}>Test</div></Shell>}
      durationInFrames={90}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

- [ ] **Step 3: Preview at `http://localhost:3000` — verify:**
  - Dark gradient wallpaper fills screen
  - Left sidebar (48px) with logo and settings icon
  - Header: "Localis" + "NO MODEL LOADED" left, green "Neural Engine Active" pill right
  - Bottom input bar with mode pills and input pill
  - Background should slowly push from 1.0→1.06 across the 90-frame preview

- [ ] **Step 4: Commit**

```bash
git add src/components/Shell.tsx
git commit -m "feat(demo): Shell component — Midnight Glass chrome"
```

---

## Task 3: TypeWriter + ZoomWrapper

**Files:**
- Create: `src/components/TypeWriter.tsx`
- Create: `src/components/ZoomWrapper.tsx`

- [ ] **Step 1: Create `src/components/TypeWriter.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame } from 'remotion';

interface TypeWriterProps {
  text: string;
  /** Frame within the scene at which typing begins */
  startFrame: number;
  /** Characters revealed per second */
  charsPerSecond?: number;
  style?: React.CSSProperties;
}

export const TypeWriter: React.FC<TypeWriterProps> = ({
  text,
  startFrame,
  charsPerSecond = 40,
  style,
}) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);
  const charsToShow = Math.min(
    text.length,
    Math.floor((localFrame / 30) * charsPerSecond),
  );
  return <span style={style}>{text.slice(0, charsToShow)}</span>;
};
```

- [ ] **Step 2: Create `src/components/ZoomWrapper.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

interface ZoomWrapperProps {
  /** Scene-relative frame at which the punch-in starts */
  startFrame: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export const ZoomWrapper: React.FC<ZoomWrapperProps> = ({ startFrame, children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - startFrame);

  const progress = spring({
    frame: localFrame,
    fps,
    config: { damping: 18, stiffness: 120, mass: 1 },
  });

  const scale = interpolate(progress, [0, 1], [0.92, 1.0]);

  return (
    <div style={{ transform: `scale(${scale})`, transformOrigin: 'center center', ...style }}>
      {children}
    </div>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add src/components/TypeWriter.tsx src/components/ZoomWrapper.tsx
git commit -m "feat(demo): TypeWriter + ZoomWrapper animation primitives"
```

---

## Task 4: ChatBubble

**Files:**
- Create: `src/components/ChatBubble.tsx`

- [ ] **Step 1: Create `src/components/ChatBubble.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Img, staticFile } from 'remotion';
import { colors, fonts, glass } from '../lib/design';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  /** Scene-relative frame when this bubble slides in */
  startFrame: number;
  children: React.ReactNode;
  /** Small label above the bubble e.g. "You" or "Localis" */
  label?: string;
  /** Timestamp string e.g. "12:32 · 5 tokens" */
  meta?: string;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  role,
  startFrame,
  children,
  label,
  meta,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - startFrame);

  const slideProgress = spring({
    frame: localFrame,
    fps,
    config: { damping: 20, stiffness: 140, mass: 1 },
  });

  const opacity = interpolate(localFrame, [0, 12], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const translateX = interpolate(slideProgress, [0, 1], [role === 'user' ? 40 : -40, 0]);

  const isUser = role === 'user';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      opacity,
      transform: `translateX(${translateX}px)`,
      gap: 6,
      fontFamily: fonts.ui,
    }}>
      {/* Label row */}
      {label && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          flexDirection: isUser ? 'row-reverse' : 'row',
        }}>
          {/* Avatar */}
          {isUser ? (
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: colors.accent,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: 12, fontWeight: 700,
            }}>U</div>
          ) : (
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: '#161616',
              border: `1px solid ${colors.borderHighlight}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              overflow: 'hidden',
            }}>
              <Img src={staticFile('logo.svg')} style={{ width: 24, height: 24 }} />
            </div>
          )}
          <span style={{ color: colors.textMuted, fontSize: 12 }}>{label}</span>
        </div>
      )}

      {/* Bubble */}
      <div style={{
        maxWidth: 600,
        padding: '12px 18px',
        borderRadius: isUser ? '18px 6px 18px 18px' : '6px 18px 18px 18px',
        ...glass,
        background: isUser ? 'rgba(59,130,246,0.15)' : 'rgba(20,20,20,0.75)',
        border: `1px solid ${isUser ? 'rgba(59,130,246,0.3)' : colors.border}`,
        color: colors.text,
        fontSize: 15,
        lineHeight: 1.6,
      }}>
        {children}
      </div>

      {/* Meta */}
      {meta && (
        <div style={{ color: colors.textDim, fontSize: 11, paddingLeft: isUser ? 0 : 8, paddingRight: isUser ? 8 : 0 }}>
          {meta}
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ChatBubble.tsx
git commit -m "feat(demo): ChatBubble — user + assistant with logo avatar"
```

---

## Task 5: ToolCard + ThinkingBlock

**Files:**
- Create: `src/components/ToolCard.tsx`
- Create: `src/components/ThinkingBlock.tsx`

- [ ] **Step 1: Create `src/components/ToolCard.tsx`**

```tsx
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
```

- [ ] **Step 2: Create `src/components/ThinkingBlock.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { colors, fonts, glass } from '../lib/design';

interface ThinkingBlockProps {
  /** Scene-relative frame when block appears */
  startFrame: number;
  /** Scene-relative frame when thinking ends (block stays but dims) */
  endFrame?: number;
}

export const ThinkingBlock: React.FC<ThinkingBlockProps> = ({ startFrame, endFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - startFrame);

  const progress = spring({
    frame: localFrame,
    fps,
    config: { damping: 22, stiffness: 120 },
  });

  const opacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });
  const height = interpolate(progress, [0, 1], [0, 64]);

  // Dots animation — 3 dots cycling
  const dotPhase = (frame * 0.12) % (Math.PI * 2);
  const dot1 = 0.4 + 0.6 * Math.abs(Math.sin(dotPhase));
  const dot2 = 0.4 + 0.6 * Math.abs(Math.sin(dotPhase + 1.0));
  const dot3 = 0.4 + 0.6 * Math.abs(Math.sin(dotPhase + 2.0));

  const PREVIEW_TEXT = 'Okay, the user wants me to summarise the file. Let me read through the content. The file is about Localis, an AI assistant that runs on the user\'s own computer using their GPU…';
  const charsVisible = Math.min(
    PREVIEW_TEXT.length,
    Math.floor((localFrame / 30) * 60),
  );

  return (
    <div style={{
      opacity,
      height,
      overflow: 'hidden',
      ...glass,
      background: 'rgba(10,12,16,0.75)',
      border: `1px solid rgba(255,255,255,0.06)`,
      borderRadius: 10,
      padding: height > 20 ? '10px 14px' : 0,
      fontFamily: fonts.mono,
      fontSize: 11,
      color: colors.textDim,
      maxWidth: 600,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ color: colors.textMuted, fontSize: 11, fontFamily: fonts.ui }}>⚙ Reasoning</span>
        <div style={{ display: 'flex', gap: 3 }}>
          {[dot1, dot2, dot3].map((o, i) => (
            <div key={i} style={{ width: 4, height: 4, borderRadius: '50%', background: colors.textDim, opacity: o }} />
          ))}
        </div>
      </div>
      <div style={{ lineHeight: 1.5, fontSize: 11 }}>
        {PREVIEW_TEXT.slice(0, charsVisible)}
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add src/components/ToolCard.tsx src/components/ThinkingBlock.tsx
git commit -m "feat(demo): ToolCard + ThinkingBlock components"
```

---

## Task 6: VoiceBar + IngestProgress

**Files:**
- Create: `src/components/VoiceBar.tsx`
- Create: `src/components/IngestProgress.tsx`

- [ ] **Step 1: Create `src/components/VoiceBar.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { colors, fonts } from '../lib/design';

type VoiceState = 'idle' | 'listening' | 'done';

interface VoiceBarProps {
  /** Scene-relative frame when bar appears */
  startFrame: number;
  /** Array of state transitions: [{ frame, state }] — frame is scene-relative */
  states: Array<{ frame: number; state: VoiceState }>;
}

export const VoiceBar: React.FC<VoiceBarProps> = ({ startFrame, states }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - startFrame);

  // Determine current state
  let currentState: VoiceState = 'idle';
  for (const s of states) {
    if (localFrame >= s.frame) currentState = s.state;
  }

  const stateColors: Record<VoiceState, string> = {
    idle: 'rgba(120,120,120,0.6)',
    listening: `rgba(245,158,11,0.8)`,
    done: `rgba(34,197,94,0.8)`,
  };

  const stateLabels: Record<VoiceState, string> = {
    idle: 'Voice Ready',
    listening: 'Hey Chotu…',
    done: 'Hey Chotu',
  };

  const dotColor = stateColors[currentState];

  // Pulse for listening state
  const pulse = currentState === 'listening'
    ? 1.0 + 0.015 * Math.sin(frame * 0.25)
    : 1.0;

  const opacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });

  const slideProgress = spring({ frame: localFrame, fps, config: { damping: 20, stiffness: 140 } });
  const translateY = interpolate(slideProgress, [0, 1], [-20, 0]);

  return (
    <div style={{
      opacity,
      transform: `translateY(${translateY}px) scale(${pulse})`,
      display: 'inline-flex', alignItems: 'center', gap: 6,
      background: 'rgba(15,15,20,0.85)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      border: `1px solid ${dotColor}`,
      borderRadius: 20,
      padding: '6px 14px',
      fontFamily: fonts.ui,
      fontSize: 12,
      color: colors.text,
    }}>
      <div style={{
        width: 7, height: 7, borderRadius: '50%',
        background: dotColor,
        boxShadow: `0 0 8px ${dotColor}`,
      }} />
      {stateLabels[currentState]}
    </div>
  );
};
```

- [ ] **Step 2: Create `src/components/IngestProgress.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { colors, fonts } from '../lib/design';
import { BEAT } from '../lib/beats';

const ITEMS = [
  { label: 'From File: Ingest complete ♥', isHeader: true },
  { label: 'Upload', isHeader: false },
  { label: 'Extract', isHeader: false },
  { label: 'Chunk', isHeader: false },
  { label: 'Index', isHeader: false },
];

interface IngestProgressProps {
  /** Scene-relative frame when first item appears */
  startFrame: number;
}

export const IngestProgress: React.FC<IngestProgressProps> = ({ startFrame }) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);

  return (
    <div style={{
      position: 'absolute',
      top: 20, left: 20,
      fontFamily: fonts.mono,
      fontSize: 12,
      lineHeight: 1.8,
    }}>
      {ITEMS.map((item, i) => {
        const itemFrame = i * BEAT; // each item appears 1 beat apart
        const opacity = interpolate(localFrame, [itemFrame, itemFrame + 10], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        return (
          <div key={i} style={{ opacity, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ color: colors.green }}>✓</span>
            <span style={{ color: item.isHeader ? colors.green : colors.textMuted }}>
              {item.label}
            </span>
          </div>
        );
      })}
      {/* Files: 1/1 */}
      <div style={{
        opacity: interpolate(localFrame, [ITEMS.length * BEAT, ITEMS.length * BEAT + 10], [0, 1], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
        }),
        color: colors.textDim, fontSize: 11, marginTop: 2,
      }}>
        Files: 1/1
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add src/components/VoiceBar.tsx src/components/IngestProgress.tsx
git commit -m "feat(demo): VoiceBar (gray/amber/green) + IngestProgress"
```

---

## Task 7: RsbPanel + NotesPanel

**Files:**
- Create: `src/components/RsbPanel.tsx`
- Create: `src/components/NotesPanel.tsx`

- [ ] **Step 1: Create `src/components/RsbPanel.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, interpolateColors } from 'remotion';
import { colors, fonts, glass } from '../lib/design';
import { BAR, BEAT } from '../lib/beats';

interface RsbPanelProps {
  /** Scene-relative frame at which panel slides in */
  startFrame: number;
}

const SWATCH_SEQUENCE = [
  '#f97316', // orange
  '#f59e0b', // amber
  '#14b8a6', // teal
  '#06b6d4', // cyan
  '#3b82f6', // blue
  '#ffffff',  // white
];

export const RsbPanel: React.FC<RsbPanelProps> = ({ startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - startFrame);

  // Slide in from right
  const slideProgress = spring({ frame: localFrame, fps, config: { damping: 22, stiffness: 130 } });
  const translateX = interpolate(slideProgress, [0, 1], [280, 0]);

  // Colour cycling starts at BAR * 2 local frames (bar 3 of scene)
  const CYCLE_START = BAR * 2;
  const cycleFrame = Math.max(0, localFrame - CYCLE_START);
  const swatchInterval = BEAT * 2; // each swatch shown for 2 beats
  const activeSwatchIndex = Math.floor(cycleFrame / swatchInterval) % SWATCH_SEQUENCE.length;
  const activeColor = SWATCH_SEQUENCE[activeSwatchIndex];

  // Bulb glow colour matches active swatch
  const bulbGlow = activeColor;

  // Brightness animation: stays at 27% until bar 7 local (frame 432), then animates
  const BRIGHTNESS_ANIM_START = BAR * 6; // f432
  const rawBrightness = localFrame < BRIGHTNESS_ANIM_START
    ? 27
    : interpolate(localFrame, [BRIGHTNESS_ANIM_START, BRIGHTNESS_ANIM_START + BAR], [27, 80], {
        extrapolateRight: 'clamp',
      });
  // Returns to 27 after
  const brightness = localFrame > BRIGHTNESS_ANIM_START + BAR
    ? interpolate(localFrame, [BRIGHTNESS_ANIM_START + BAR, BRIGHTNESS_ANIM_START + BAR + BAR / 2], [80, 27], {
        extrapolateRight: 'clamp',
      })
    : rawBrightness;

  // Bulb pulse
  const bulbPulse = 1.0 + 0.04 * Math.sin(localFrame * 0.15);

  return (
    <div style={{
      transform: `translateX(${translateX}px)`,
      width: 280, height: '100%',
      background: colors.sidebar,
      borderLeft: `1px solid ${colors.border}`,
      fontFamily: fonts.ui,
      padding: '16px 14px',
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      {/* Header */}
      <div style={{ color: colors.textDim, fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 600 }}>
        Quick Controls
      </div>

      {/* Light toggle */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '8px 10px',
        ...glass,
        background: 'rgba(25,25,30,0.6)',
        borderRadius: 10,
      }}>
        <span style={{ color: colors.text, fontSize: 13, fontWeight: 500 }}>Rishi Room Light</span>
        <div style={{
          width: 36, height: 20, borderRadius: 10,
          background: colors.green,
          display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
          padding: '0 3px',
        }}>
          <div style={{ width: 14, height: 14, borderRadius: '50%', background: '#fff' }} />
        </div>
      </div>

      {/* Bulb icon */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
        <div style={{
          fontSize: 52,
          transform: `scale(${bulbPulse})`,
          filter: `drop-shadow(0 0 16px ${bulbGlow}) drop-shadow(0 0 32px ${bulbGlow}44)`,
          lineHeight: 1,
        }}>💡</div>
        <div style={{ color: colors.text, fontSize: 22, fontWeight: 700 }}>
          {Math.round(brightness)}%
        </div>
      </div>

      {/* Colour swatches */}
      <div style={{ display: 'flex', gap: 6, justifyContent: 'center', flexWrap: 'wrap' }}>
        {SWATCH_SEQUENCE.map((c, i) => (
          <div key={i} style={{
            width: 24, height: 24, borderRadius: '50%',
            background: c,
            border: i === activeSwatchIndex
              ? `2px solid #fff`
              : `2px solid transparent`,
            boxShadow: i === activeSwatchIndex
              ? `0 0 8px ${c}`
              : 'none',
            transition: 'none',
          }} />
        ))}
      </div>

      {/* Scene buttons */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {['Load', 'Unload', 'Default', 'Preview', 'Planning', 'Custom'].map((label) => (
          <div key={label} style={{
            padding: '6px 0',
            borderRadius: 6,
            border: `1px solid ${colors.border}`,
            background: label === 'Load' ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.04)',
            color: label === 'Load' ? colors.red : colors.textMuted,
            fontSize: 11, textAlign: 'center', fontWeight: 500,
          }}>{label}</div>
        ))}
      </div>

      {/* Brightness slider */}
      <div style={{ padding: '0 4px' }}>
        <div style={{ color: colors.textDim, fontSize: 10, marginBottom: 4 }}>Brightness</div>
        <div style={{
          height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.1)',
          position: 'relative',
        }}>
          <div style={{
            position: 'absolute', left: 0, top: 0, bottom: 0,
            width: `${brightness}%`,
            background: bulbGlow,
            borderRadius: 2,
          }} />
          <div style={{
            position: 'absolute', top: '50%',
            left: `${brightness}%`,
            transform: 'translate(-50%, -50%)',
            width: 12, height: 12, borderRadius: '50%',
            background: '#fff',
            boxShadow: `0 0 4px rgba(0,0,0,0.5)`,
          }} />
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Create `src/components/NotesPanel.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { colors, fonts, glass } from '../lib/design';

export interface NoteCard {
  title: string;
  body?: string;
  deadline?: string;
  isNew?: boolean;
  /** Scene-relative frame when this card appears */
  appearFrame: number;
}

interface NotesPanelProps {
  /** Scene-relative frame when panel slides up */
  startFrame: number;
  notes: NoteCard[];
}

export const NotesPanel: React.FC<NotesPanelProps> = ({ startFrame, notes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - startFrame);

  const slideProgress = spring({ frame: localFrame, fps, config: { damping: 22, stiffness: 130 } });
  const translateY = interpolate(slideProgress, [0, 1], [80, 0]);
  const panelOpacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 20,
    }}>
      {/* Backdrop */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'rgba(0,0,0,0.6)',
        opacity: panelOpacity,
      }} />

      {/* Panel */}
      <div style={{
        position: 'relative',
        transform: `translateY(${translateY}px)`,
        opacity: panelOpacity,
        width: 820, minHeight: 280,
        ...glass,
        background: 'rgba(10,10,14,0.92)',
        border: `1px solid ${colors.borderHighlight}`,
        borderRadius: 16,
        padding: 24,
        fontFamily: fonts.ui,
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: 20,
        }}>
          <h2 style={{ color: colors.text, fontSize: 18, fontWeight: 600, margin: 0 }}>Notes</h2>
          <div style={{ color: colors.textDim, fontSize: 18, cursor: 'default' }}>×</div>
        </div>

        {/* Card grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {/* Add a note placeholder */}
          <div style={{
            border: `1px dashed ${colors.border}`,
            borderRadius: 10, padding: 12, minHeight: 80,
            display: 'flex', alignItems: 'flex-start',
          }}>
            <span style={{ color: colors.textDim, fontSize: 12 }}>Add a note…</span>
          </div>

          {notes.map((note, i) => {
            const noteLocalFrame = Math.max(0, localFrame - note.appearFrame);
            const noteProgress = spring({
              frame: noteLocalFrame,
              fps,
              config: { damping: 18, stiffness: 160 },
            });
            const noteScale = interpolate(noteProgress, [0, 1], [0.85, 1.0]);
            const noteOpacity = interpolate(noteLocalFrame, [0, 8], [0, 1], { extrapolateRight: 'clamp' });

            return (
              <div key={i} style={{
                transform: `scale(${noteScale})`,
                opacity: noteOpacity,
                background: note.isNew ? 'rgba(59,130,246,0.12)' : 'rgba(30,30,36,0.8)',
                border: `1px solid ${note.isNew ? 'rgba(59,130,246,0.3)' : colors.border}`,
                borderRadius: 10, padding: '10px 12px', minHeight: 80,
              }}>
                <div style={{ color: colors.text, fontSize: 12, lineHeight: 1.6 }}>
                  {note.title}
                </div>
                {note.body && (
                  <div style={{ color: colors.textMuted, fontSize: 11, marginTop: 4, lineHeight: 1.5 }}>
                    {note.body}
                  </div>
                )}
                {note.deadline && (
                  <div style={{
                    marginTop: 8, display: 'inline-flex', alignItems: 'center', gap: 4,
                    background: 'rgba(245,158,11,0.15)',
                    border: '1px solid rgba(245,158,11,0.3)',
                    borderRadius: 4, padding: '2px 6px',
                    color: colors.amber, fontSize: 10,
                  }}>
                    🕐 {note.deadline}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add src/components/RsbPanel.tsx src/components/NotesPanel.tsx
git commit -m "feat(demo): RsbPanel (animated swatches/slider) + NotesPanel"
```

---

## Task 8: Scene 00 — Intro

**Files:**
- Create: `src/scenes/00-Intro.tsx`

- [ ] **Step 1: Create `src/scenes/00-Intro.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Img, staticFile } from 'remotion';
import { colors, fonts } from '../lib/design';
import { BEAT, BAR } from '../lib/beats';

export const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo: spring in at f0, peak by f36
  const logoProgress = spring({ frame, fps, config: { damping: 16, stiffness: 100, mass: 1.2 } });
  const logoScale = interpolate(logoProgress, [0, 1], [0.4, 1.0]);
  const logoOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // "Introducing Localis" — fades in at beat 2 (f18)
  const titleOpacity = interpolate(frame, [BEAT * 1, BEAT * 3], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const titleY = interpolate(frame, [BEAT * 1, BEAT * 3], [12, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Tagline — fades in at beat 4 / bar end (f54)
  const tagOpacity = interpolate(frame, [BEAT * 4, BEAT * 6], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const tagY = interpolate(frame, [BEAT * 4, BEAT * 6], [10, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Subtle logo glow pulse after bar 2
  const glow = frame > BAR * 2 ? 0.5 + 0.5 * Math.abs(Math.sin(frame * 0.05)) : 0;

  return (
    <div style={{
      width: 1920, height: 1080,
      background: '#000',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      gap: 28,
      fontFamily: fonts.ui,
    }}>
      {/* Logo */}
      <div style={{
        transform: `scale(${logoScale})`,
        opacity: logoOpacity,
        filter: glow > 0 ? `drop-shadow(0 0 ${20 * glow}px rgba(200,184,154,${0.3 * glow}))` : 'none',
      }}>
        <Img src={staticFile('logo.svg')} style={{ width: 100, height: 100 }} />
      </div>

      {/* "Introducing Localis" */}
      <div style={{
        opacity: titleOpacity,
        transform: `translateY(${titleY}px)`,
        color: colors.text,
        fontSize: 52, fontWeight: 700, letterSpacing: '-0.02em',
      }}>
        Introducing Localis
      </div>

      {/* Tagline */}
      <div style={{
        opacity: tagOpacity,
        transform: `translateY(${tagY}px)`,
        color: colors.textMuted,
        fontSize: 22, fontWeight: 300, letterSpacing: '0.04em',
      }}>
        Your AI. Your machine. Your rules.
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Update `src/Root.tsx` to preview this scene**

```tsx
import './index.css';
import { Composition } from 'remotion';
import { IntroScene } from './scenes/00-Intro';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Intro"
      component={IntroScene}
      durationInFrames={216}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

- [ ] **Step 3: Preview at `http://localhost:3000` — verify:**
  - Black background
  - Logo springs in with scale bounce (0.4→1.0) in first 36 frames
  - "Introducing Localis" fades+slides up after beat 1 (frame 18)
  - Tagline fades in after beat 4 (frame 54)
  - Gentle sand glow on logo after frame 144

- [ ] **Step 4: Commit**

```bash
git add src/scenes/00-Intro.tsx src/Root.tsx
git commit -m "feat(demo): Scene 00 — Intro (logo spring + tagline)"
```

---

## Task 9: Scene 01 — RAG

**Files:**
- Create: `src/scenes/01-Rag.tsx`

- [ ] **Step 1: Create `src/scenes/01-Rag.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { Shell } from '../components/Shell';
import { ChatBubble } from '../components/ChatBubble';
import { ThinkingBlock } from '../components/ThinkingBlock';
import { IngestProgress } from '../components/IngestProgress';
import { ZoomWrapper } from '../components/ZoomWrapper';
import { colors, fonts } from '../lib/design';
import { BEAT, BAR } from '../lib/beats';

const DURATION = 576; // 8 bars

const RESPONSE_LINES = [
  { bold: true, text: 'The file outlines Localis' },
  { bold: false, text: ', a private AI assistant that runs entirely on your own computer using your GPU. Here\'s a summary:' },
];

const BULLETS = [
  { key: 'Technology:', value: 'Runs on your local GPU, no cloud or subscriptions.' },
  { key: 'Features:', value: 'Fully local · Two-tier memory · RAG · Web search · Multi-provider support' },
  { key: 'Purpose:', value: 'Fully-stack, self-updating, shippable (no scripts or notebooks).' },
];

export const RagScene: React.FC = () => {
  const frame = useCurrentFrame();

  // Ingest appears at beat 1
  const INGEST_START = BEAT;
  // User bubble at beat 7 (f126 → f108)
  const USER_BUBBLE_START = BEAT * 6;
  // Thinking block at bar 3 (f144)
  const THINKING_START = BAR * 2;
  // Assistant bubble at bar 4 start (f252 → bar3.5 beat)
  const ASSISTANT_START = BAR * 3 + BEAT * 2;
  // Zoom on thinking block at bar 4 (f216 -> bar 3 start)
  const THINKING_ZOOM_START = BAR * 3;
  // Zoom on assistant bubble at bar 8 start minus 1 bar
  const ASSISTANT_ZOOM_START = BAR * 7;

  // Text reveal for response
  const FULL_TEXT = 'The file outlines Localis, a private AI assistant that runs entirely on your own computer using your GPU. Here\'s a summary:';
  const localResponseFrame = Math.max(0, frame - ASSISTANT_START);
  const charsVisible = Math.min(FULL_TEXT.length, Math.floor((localResponseFrame / 30) * 35));

  // Bullet lines appear after the header text finishes
  const bulletsStart = ASSISTANT_START + Math.ceil(FULL_TEXT.length / 35 * 30);

  return (
    <Shell sceneDuration={DURATION}>
      {/* Ingest progress top-left */}
      <IngestProgress startFrame={INGEST_START} />

      {/* User bubble */}
      <div style={{ alignSelf: 'flex-end', marginTop: 80 }}>
        <ChatBubble role="user" startFrame={USER_BUBBLE_START} label="You">
          Summarise this file for me.
        </ChatBubble>
      </div>

      {/* Thinking block */}
      <ZoomWrapper startFrame={THINKING_ZOOM_START} style={{ alignSelf: 'flex-start' }}>
        <ThinkingBlock startFrame={THINKING_START} endFrame={ASSISTANT_START} />
      </ZoomWrapper>

      {/* Assistant bubble */}
      <ZoomWrapper startFrame={ASSISTANT_ZOOM_START} style={{ alignSelf: 'flex-start' }}>
        <ChatBubble role="assistant" startFrame={ASSISTANT_START} label="Localis">
          <div style={{ fontFamily: fonts.ui, lineHeight: 1.7 }}>
            <span>{FULL_TEXT.slice(0, charsVisible)}</span>
            {/* Bullet points fade in after header */}
            {BULLETS.map((b, i) => {
              const bStart = bulletsStart + i * BAR;
              const bOpacity = interpolate(frame, [bStart, bStart + 20], [0, 1], {
                extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
              });
              return (
                <div key={i} style={{ opacity: bOpacity, marginTop: 8, display: 'flex', gap: 8 }}>
                  <span style={{ color: colors.textDim }}>•</span>
                  <span>
                    <strong>{b.key}</strong>{' '}{b.value}
                  </span>
                </div>
              );
            })}
            {/* "Let me know" line */}
            {(() => {
              const lmStart = bulletsStart + BULLETS.length * BAR;
              const lmOp = interpolate(frame, [lmStart, lmStart + 20], [0, 1], {
                extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
              });
              return (
                <div style={{ opacity: lmOp, marginTop: 8, color: colors.textMuted, fontSize: 13 }}>
                  Let me know if you'd like further details!
                </div>
              );
            })()}
          </div>
        </ChatBubble>
      </ZoomWrapper>
    </Shell>
  );
};
```

- [ ] **Step 2: Update `src/Root.tsx`**

```tsx
import './index.css';
import { Composition } from 'remotion';
import { RagScene } from './scenes/01-Rag';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Rag"
      component={RagScene}
      durationInFrames={576}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

- [ ] **Step 3: Preview at `http://localhost:3000` — verify:**
  - Midnight Glass shell with wallpaper slow push
  - Ingest progress ticks in at top-left from frame 18
  - User bubble slides in from right at frame 108
  - Thinking block expands with dot animation at frame 144
  - ZoomWrapper punch-in on thinking block at frame 216
  - Assistant bubble appears at frame ~270 with text revealing
  - Bullet points fade in sequentially

- [ ] **Step 4: Commit**

```bash
git add src/scenes/01-Rag.tsx src/Root.tsx
git commit -m "feat(demo): Scene 01 — RAG (ingest progress + summary response)"
```

---

## Task 10: Scene 02 — Web Search

**Files:**
- Create: `src/scenes/02-WebSearch.tsx`

- [ ] **Step 1: Create `src/scenes/02-WebSearch.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { Shell } from '../components/Shell';
import { ChatBubble } from '../components/ChatBubble';
import { ToolCard } from '../components/ToolCard';
import { ZoomWrapper } from '../components/ZoomWrapper';
import { colors, fonts } from '../lib/design';
import { BEAT, BAR } from '../lib/beats';

const DURATION = 432; // 6 bars

// Prior conversation snippet (dimmed)
const PriorChat: React.FC = () => (
  <div style={{ opacity: 0.35, pointerEvents: 'none', display: 'flex', flexDirection: 'column', gap: 12 }}>
    <div style={{ alignSelf: 'flex-end' }}>
      <ChatBubble role="user" startFrame={0} label="You">Summarise this file for me.</ChatBubble>
    </div>
    <div style={{ alignSelf: 'flex-start' }}>
      <ChatBubble role="assistant" startFrame={0} label="Localis">
        <span style={{ fontFamily: fonts.ui, fontSize: 13, color: colors.textMuted }}>
          <strong>The file outlines Localis</strong>, a private AI assistant that runs entirely on your own computer…
        </span>
      </ChatBubble>
    </div>
  </div>
);

export const WebSearchScene: React.FC = () => {
  const frame = useCurrentFrame();

  const USER_START = BEAT;            // f18
  const TOOL_START = BAR;             // f72
  const TOOL_ZOOM_START = BEAT * 6;   // f108
  const ASSISTANT_START = BAR * 2;    // f144

  const F1_TEXT = 'The next F1 race is the Japanese Grand Prix:';
  const localAssistFrame = Math.max(0, frame - ASSISTANT_START);
  const charsVisible = Math.min(F1_TEXT.length, Math.floor((localAssistFrame / 30) * 40));

  const detail1Opacity = interpolate(frame, [ASSISTANT_START + BAR, ASSISTANT_START + BAR + 20], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const detail2Opacity = interpolate(frame, [ASSISTANT_START + BAR + BEAT, ASSISTANT_START + BAR + BEAT + 20], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <Shell sceneDuration={DURATION}>
      <PriorChat />

      {/* User bubble */}
      <div style={{ alignSelf: 'flex-end' }}>
        <ChatBubble role="user" startFrame={USER_START} label="You">
          When is the next F1 race?
        </ChatBubble>
      </div>

      {/* Tool card */}
      <ZoomWrapper startFrame={TOOL_ZOOM_START} style={{ alignSelf: 'flex-start' }}>
        <ToolCard
          startFrame={TOOL_START}
          toolName="web_search"
          subtitle="3 results"
          dotColor={colors.green}
        />
      </ZoomWrapper>

      {/* Assistant response */}
      <ChatBubble role="assistant" startFrame={ASSISTANT_START} label="Localis">
        <div style={{ fontFamily: fonts.ui, lineHeight: 1.7 }}>
          <div>{F1_TEXT.slice(0, charsVisible)}</div>
          <div style={{ opacity: detail1Opacity, marginTop: 8, display: 'flex', gap: 8 }}>
            <span>📅</span>
            <span><strong>Date:</strong> Sun, Mar 29 — 1:00 a.m.</span>
          </div>
          <div style={{ opacity: detail2Opacity, marginTop: 4, display: 'flex', gap: 8 }}>
            <span>🏎️</span>
            <span><strong>Track:</strong> Suzuka Circuit</span>
          </div>
        </div>
      </ChatBubble>
    </Shell>
  );
};
```

- [ ] **Step 2: Update `src/Root.tsx`**

```tsx
import './index.css';
import { Composition } from 'remotion';
import { WebSearchScene } from './scenes/02-WebSearch';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="WebSearch"
      component={WebSearchScene}
      durationInFrames={432}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

- [ ] **Step 3: Preview — verify prior chat dimmed, user bubble, tool card slides up with green dot, F1 details fade in**

- [ ] **Step 4: Commit**

```bash
git add src/scenes/02-WebSearch.tsx src/Root.tsx
git commit -m "feat(demo): Scene 02 — Web search (F1 Suzuka answer)"
```

---

## Task 11: Scene 03 — Home Assistant

**Files:**
- Create: `src/scenes/03-HomeAssistant.tsx`

- [ ] **Step 1: Create `src/scenes/03-HomeAssistant.tsx`**

```tsx
import React from 'react';
import { Shell } from '../components/Shell';
import { RsbPanel } from '../components/RsbPanel';
import { ZoomWrapper } from '../components/ZoomWrapper';
import { BAR } from '../lib/beats';
import { colors, fonts } from '../lib/design';

const DURATION = 576; // 8 bars

// Brief chat history (static, dimmed background)
const ChatHistory: React.FC = () => (
  <div style={{ opacity: 0.25, fontFamily: fonts.ui, color: colors.textMuted, fontSize: 14 }}>
    <div style={{ textAlign: 'right', marginBottom: 12 }}>When is the next F1 race?</div>
    <div>📅 Date: Sun, Mar 29 — 1:00 a.m. · 🏎️ Track: Suzuka Circuit</div>
  </div>
);

export const HomeAssistantScene: React.FC = () => {
  return (
    <Shell
      sceneDuration={DURATION}
      chatOpacity={0.4}
      rsbContent={<RsbPanel startFrame={0} />}
    >
      <ChatHistory />
    </Shell>
  );
};
```

- [ ] **Step 2: Update `src/Root.tsx`**

```tsx
import './index.css';
import { Composition } from 'remotion';
import { HomeAssistantScene } from './scenes/03-HomeAssistant';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="HomeAssistant"
      component={HomeAssistantScene}
      durationInFrames={576}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

- [ ] **Step 3: Preview — verify:**
  - RSB panel springs in from right
  - Light bulb glow pulses
  - Colour swatches cycle from bar 2 (~frame 144), bulb colour follows
  - Brightness bar animates up then back to 27% from frame 432
  - Chat area visible but dimmed

- [ ] **Step 4: Commit**

```bash
git add src/scenes/03-HomeAssistant.tsx src/Root.tsx
git commit -m "feat(demo): Scene 03 — Home Assistant RSB (animated bulb + swatches)"
```

---

## Task 12: Scene 04 — Notes

**Files:**
- Create: `src/scenes/04-Notes.tsx`

- [ ] **Step 1: Create `src/scenes/04-Notes.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { Shell } from '../components/Shell';
import { NotesPanel } from '../components/NotesPanel';
import { VoiceBar } from '../components/VoiceBar';
import { BEAT, BAR } from '../lib/beats';
import { colors, fonts } from '../lib/design';

const DURATION = 360; // 5 bars

const NOTES_START = 0;
const VOICE_START = BEAT * 6;  // f108

const NOTES_DATA = [
  {
    title: 'Push Day',
    body: 'Bench Press x5 · Arnold Press x3 · Pac Dec x1 · Tricep Pushdown x4 · Tricep Lockdown x4 · Abs - crunches 20 × 6',
    appearFrame: BEAT,          // f18
  },
  {
    title: 'Record Localis DEMO',
    body: 'Post (LinkedIn + Reddit)',
    appearFrame: BEAT * 3,      // f54
  },
  {
    title: 'Order Eggs, Milk, Dinner Rolls, Chicken thighs from Instacart',
    deadline: '22 May, 11:00',
    isNew: true,
    appearFrame: BAR * 2 + BEAT * 2, // f180 — after voice goes green
  },
];

export const NotesScene: React.FC = () => {
  const frame = useCurrentFrame();

  // VoiceBar row position — absolute overlay above notes panel
  const voiceBarOpacity = interpolate(frame, [VOICE_START, VOICE_START + 10], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <Shell sceneDuration={DURATION} chatOpacity={0.3}>
      {/* Notes panel fills the viewport overlay */}
      <NotesPanel startFrame={NOTES_START} notes={NOTES_DATA} />

      {/* Voice bar — centered at top of notes panel */}
      <div style={{
        position: 'absolute',
        top: 140, left: '50%', transform: 'translateX(-50%)',
        opacity: voiceBarOpacity,
        zIndex: 30,
      }}>
        <VoiceBar
          startFrame={VOICE_START}
          states={[
            { frame: 0, state: 'idle' },
            { frame: 0, state: 'listening' },          // immediately listening when it appears
            { frame: BAR + BEAT * 2 - VOICE_START, state: 'done' },  // f72 relative to VoiceBar
          ]}
        />
      </div>
    </Shell>
  );
};
```

- [ ] **Step 2: Update `src/Root.tsx`**

```tsx
import './index.css';
import { Composition } from 'remotion';
import { NotesScene } from './scenes/04-Notes';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Notes"
      component={NotesScene}
      durationInFrames={360}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

- [ ] **Step 3: Preview — verify:**
  - Notes panel slides up from bottom
  - First two note cards appear staggered (f18, f54)
  - Voice bar appears in amber at f108 with "Hey Chotu…" pulse
  - Third card (Instacart, blue tint, deadline badge) springs in at ~f180

- [ ] **Step 4: Commit**

```bash
git add src/scenes/04-Notes.tsx src/Root.tsx
git commit -m "feat(demo): Scene 04 — Notes (voice creates Instacart card)"
```

---

## Task 13: Scene 05 — Climax

**Files:**
- Create: `src/scenes/05-Climax.tsx`

- [ ] **Step 1: Create `src/scenes/05-Climax.tsx`**

```tsx
import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Img, staticFile } from 'remotion';
import { Shell } from '../components/Shell';
import { ChatBubble } from '../components/ChatBubble';
import { ToolCard } from '../components/ToolCard';
import { VoiceBar } from '../components/VoiceBar';
import { ZoomWrapper } from '../components/ZoomWrapper';
import { colors, fonts } from '../lib/design';
import { BEAT, BAR } from '../lib/beats';

const DURATION = 432; // 6 bars

export const ClimaxScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Timeline
  const VOICE_START = 0;
  const SUBTITLE_START = BEAT;        // f18
  const USER_BUBBLE_START = BEAT * 5; // f90
  const ASSIST_CARD_START = BEAT * 7; // f126
  const ASSIST_ZOOM_START = BAR * 2;  // f144
  const ASSISTANT_START = BEAT * 11;  // f198
  const ASSIST_BUBBLE_ZOOM = BAR * 3; // f216
  const FADE_TO_BLACK_START = BAR * 4;// f288
  const LOGO_START = BAR * 5;         // f360

  // Subtitle fade
  const subtitleOpacity = interpolate(frame, [SUBTITLE_START, SUBTITLE_START + 14], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const subtitleFadeOut = interpolate(frame, [FADE_TO_BLACK_START, FADE_TO_BLACK_START + BAR], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Fade to black
  const fadeBlack = interpolate(frame, [FADE_TO_BLACK_START, FADE_TO_BLACK_START + BAR * 1.5], [0, 0.92], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Outro logo
  const logoOpacity = interpolate(frame, [LOGO_START, LOGO_START + 24], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const logoProgress = spring({ frame: Math.max(0, frame - LOGO_START), fps, config: { damping: 20, stiffness: 100 } });
  const logoScale = interpolate(logoProgress, [0, 1], [0.7, 1.0]);

  return (
    <Shell sceneDuration={DURATION} bgDimExtra={0.25}>
      {/* Voice bar — top right area */}
      <div style={{ position: 'absolute', top: 70, right: rsbContent ? 300 : 60, zIndex: 20 }}>
        <VoiceBar
          startFrame={VOICE_START}
          states={[
            { frame: 0, state: 'idle' },
            { frame: BEAT, state: 'listening' },
            { frame: BAR + BEAT * 2, state: 'done' },
          ]}
        />
      </div>

      {/* Subtitle — lower third */}
      <div style={{
        position: 'absolute',
        bottom: 120, left: 0, right: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
        opacity: subtitleOpacity * subtitleFadeOut,
        zIndex: 20,
      }}>
        <div style={{ color: colors.text, fontSize: 36, fontWeight: 700, letterSpacing: '0.02em', fontFamily: fonts.ui }}>
          light banda kar
        </div>
        <div style={{ color: colors.textMuted, fontSize: 18, fontFamily: fonts.ui }}>
          (Marathi)
        </div>
      </div>

      {/* Chat messages */}
      <div style={{ marginTop: 80, display: 'flex', flexDirection: 'column', gap: 14, width: '100%' }}>
        {/* User bubble */}
        <div style={{ alignSelf: 'flex-end' }}>
          <ChatBubble role="user" startFrame={USER_BUBBLE_START} label="You" meta="12:32 · 5 tokens">
            light banda kar
          </ChatBubble>
        </div>

        {/* Assist tool card */}
        <ZoomWrapper startFrame={ASSIST_ZOOM_START} style={{ alignSelf: 'flex-start' }}>
          <ToolCard
            startFrame={ASSIST_CARD_START}
            toolName="assist.action"
            subtitle="Light controlled"
            rows={[
              { key: 'Entity', value: 'light.rishi_room_light', valueColor: colors.textMuted },
              { key: 'Change', value: '→ OFF', valueColor: colors.red },
            ]}
          />
        </ZoomWrapper>

        {/* Assistant response */}
        <ZoomWrapper startFrame={ASSIST_BUBBLE_ZOOM} style={{ alignSelf: 'flex-start' }}>
          <ChatBubble role="assistant" startFrame={ASSISTANT_START} label="Localis">
            Rishi Room Light turned OFF.
          </ChatBubble>
        </ZoomWrapper>
      </div>

      {/* Fade to black overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `rgba(0,0,0,${fadeBlack})`,
        zIndex: 25, pointerEvents: 'none',
      }} />

      {/* Outro logo */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        opacity: logoOpacity,
        transform: `scale(${logoScale})`,
        zIndex: 30,
      }}>
        <Img src={staticFile('logo.svg')} style={{ width: 64, height: 64 }} />
      </div>
    </Shell>
  );
};
```

> **Note:** Remove `rsbContent` from VoiceBar position line — it's not defined in scope. Change `right: rsbContent ? 300 : 60` to `right: 60`.

- [ ] **Step 2: Fix the `rsbContent` reference in Step 1 — change the VoiceBar positioning to:**

```tsx
<div style={{ position: 'absolute', top: 70, right: 60, zIndex: 20 }}>
```

- [ ] **Step 3: Update `src/Root.tsx`**

```tsx
import './index.css';
import { Composition } from 'remotion';
import { ClimaxScene } from './scenes/05-Climax';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Climax"
      component={ClimaxScene}
      durationInFrames={432}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

- [ ] **Step 4: Preview — verify:**
  - Voice bar: idle → amber (f18) → green (f90)
  - "light banda kar" + "(Marathi)" subtitle fades in at f18
  - User bubble at f90
  - Assist card slides up at f126, punch-in at f144
  - Assistant bubble at f198, punch-in at f216
  - Subtitle fades out at f288
  - Fade to near-black from f288
  - Localis logo appears centred at f360

- [ ] **Step 5: Commit**

```bash
git add src/scenes/05-Climax.tsx src/Root.tsx
git commit -m "feat(demo): Scene 05 — Climax (light banda kar, fade to black)"
```

---

## Task 14: Composition — wire all scenes + audio

**Files:**
- Rewrite: `src/Composition.tsx`
- Rewrite: `src/Root.tsx`

- [ ] **Step 1: Rewrite `src/Composition.tsx`**

```tsx
import React from 'react';
import { Audio, staticFile, useVideoConfig, interpolate, useCurrentFrame } from 'remotion';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { IntroScene } from './scenes/00-Intro';
import { RagScene } from './scenes/01-Rag';
import { WebSearchScene } from './scenes/02-WebSearch';
import { HomeAssistantScene } from './scenes/03-HomeAssistant';
import { NotesScene } from './scenes/04-Notes';
import { ClimaxScene } from './scenes/05-Climax';
import { BEAT } from './lib/beats';

/** 1-beat fade transition between every scene */
const TRANSITION_FRAMES = BEAT; // 18f

export const LocalisDemoComposition: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Audio fade-out over last 60 frames (2s)
  const audioVolume = interpolate(
    frame,
    [durationInFrames - 60, durationInFrames],
    [0.5, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  return (
    <>
      {/* ADD AUDIO HERE — drop music.mp3 in public/ */}
      <Audio src={staticFile('music.mp3')} volume={audioVolume} />

      <TransitionSeries>
        {/* Scene 00 — Intro: 216f / 3 bars */}
        <TransitionSeries.Sequence durationInFrames={216}>
          <IntroScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />

        {/* Scene 01 — RAG: 576f / 8 bars */}
        <TransitionSeries.Sequence durationInFrames={576}>
          <RagScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />

        {/* Scene 02 — Web Search: 432f / 6 bars */}
        <TransitionSeries.Sequence durationInFrames={432}>
          <WebSearchScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />

        {/* Scene 03 — Home Assistant: 576f / 8 bars */}
        <TransitionSeries.Sequence durationInFrames={576}>
          <HomeAssistantScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />

        {/* Scene 04 — Notes: 360f / 5 bars */}
        <TransitionSeries.Sequence durationInFrames={360}>
          <NotesScene />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
        />

        {/* Scene 05 — Climax: 432f / 6 bars */}
        <TransitionSeries.Sequence durationInFrames={432}>
          <ClimaxScene />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </>
  );
};
```

- [ ] **Step 2: Rewrite `src/Root.tsx`**

```tsx
import './index.css';
import { Composition } from 'remotion';
import { LocalisDemoComposition } from './Composition';

/**
 * Net frame count:
 * Scenes: 216 + 576 + 432 + 576 + 360 + 432 = 2592
 * Transitions: 5 × 18 = 90
 * Total: 2592 - 90 = 2502
 */
const TOTAL_FRAMES = 2502;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="LocalisDemo"
      component={LocalisDemoComposition}
      durationInFrames={TOTAL_FRAMES}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

- [ ] **Step 3: Preview the full composition at `http://localhost:3000`**
  - Select "LocalisDemo" in the dropdown
  - Scrub through to verify all 6 scenes play in order
  - Verify fade transitions between scenes (18f each)
  - Verify audio plays (jazz track) and fades out in final 2s
  - Verify total duration reads ~83.4s in the timeline

- [ ] **Step 4: Final commit**

```bash
git add src/Composition.tsx src/Root.tsx
git commit -m "feat(demo): wire all scenes in TransitionSeries + beat-synced audio"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Scene 00: Intro — logo spring + "Introducing Localis" + tagline ✓
- [x] Scene 01: RAG — ingest ticks, user bubble, thinking block, summary typewriter ✓
- [x] Scene 02: Web Search — F1 question, web_search tool card, Suzuka answer ✓
- [x] Scene 03: HA — RSB slides in, bulb glow, swatch cycling, brightness animation ✓
- [x] Scene 04: Notes — 2 pre-existing cards, voice bar amber, Instacart card springs in ✓
- [x] Scene 05: Climax — voice gray→amber→green, subtitle "light banda kar (Marathi)", assist.action card, response, fade to black ✓
- [x] Assistant bubbles use Localis logo SVG avatar ✓
- [x] All "Hey Chotu" (no "Jarvis") ✓
- [x] No video overlay placeholders ✓
- [x] Background slow push on every scene ✓
- [x] ZoomWrapper punch-ins at key beats ✓
- [x] Audio baked in, fades over last 60f ✓
- [x] 1920×1080, 30fps, 2502 total frames ✓

**Type consistency check:**
- `ChatBubble` props: `role`, `startFrame`, `label`, `meta`, `children` — used consistently ✓
- `ToolCard` props: `startFrame`, `toolName`, `subtitle`, `rows`, `dotColor` — consistent ✓
- `VoiceBar` props: `startFrame`, `states` — consistent ✓
- `Shell` props: `sceneDuration`, `children`, `rsbContent`, `chatOpacity`, `bgDimExtra` — consistent ✓
- `BEAT`/`BAR` imported from `../lib/beats` in all scene files ✓
