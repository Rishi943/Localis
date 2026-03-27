import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { Shell } from '../components/Shell';
import { ChatBubble } from '../components/ChatBubble';
import { ToolCard } from '../components/ToolCard';
import { ZoomWrapper } from '../components/ZoomWrapper';
import { TypeWriter } from '../components/TypeWriter';
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
  const { fps } = useVideoConfig();

  // ── Timeline ──
  const PILL_BOUNCE_FRAME = 0;         // bounce immediately
  const USER_START = BEAT;             // f18 — user bubble + typewriter start
  const PULL_BACK_START = BEAT * 3;    // f54 — camera pulls back to full view
  const TOOL_START = BAR;              // f72
  const TOOL_ZOOM_START = BEAT * 6;    // f108
  const ASSISTANT_START = BAR * 2;     // f144

  // ── Camera: start zoomed bottom (1.35) → pull back to full (1.0) ──
  const pullBackProgress = spring({
    frame: Math.max(0, frame - PULL_BACK_START),
    fps,
    config: { damping: 22, stiffness: 130 },
  });
  const cameraScale = frame < PULL_BACK_START
    ? 1.35
    : interpolate(pullBackProgress, [0, 1], [1.35, 1.0]);

  const F1_TEXT = 'The next F1 race is the Japanese Grand Prix:';

  const detail1Opacity = interpolate(frame, [ASSISTANT_START + BAR, ASSISTANT_START + BAR + 20], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const detail2Opacity = interpolate(frame, [ASSISTANT_START + BAR + BEAT, ASSISTANT_START + BAR + BEAT + 20], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <div style={{ width: 1920, height: 1080, overflow: 'hidden' }}>
      <div style={{
        transform: `scale(${cameraScale})`,
        transformOrigin: 'bottom center',
        width: 1920, height: 1080,
      }}>
        <Shell
          sceneDuration={DURATION}
          activePill={0}
          pillBounceStartFrame={PILL_BOUNCE_FRAME}
        >
          <PriorChat />

          {/* User bubble with typewriter */}
          <div style={{ alignSelf: 'flex-end' }}>
            <ChatBubble role="user" startFrame={USER_START} label="You">
              <TypeWriter
                text="When is the next F1 race?"
                startFrame={USER_START}
                charsPerSecond={45}
              />
            </ChatBubble>
          </div>

          {/* Tool card */}
          <ZoomWrapper
            startFrame={TOOL_ZOOM_START}
            style={{ alignSelf: 'flex-start', transformOrigin: 'top left' }}
          >
            <ToolCard
              startFrame={TOOL_START}
              toolName="web_search"
              subtitle="3 results"
              dotColor={colors.green}
            />
          </ZoomWrapper>

          {/* Assistant response with typewriter */}
          <ChatBubble role="assistant" startFrame={ASSISTANT_START} label="Localis">
            <div style={{ fontFamily: fonts.ui, lineHeight: 1.7 }}>
              <TypeWriter text={F1_TEXT} startFrame={ASSISTANT_START} charsPerSecond={45} />
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
      </div>
    </div>
  );
};
