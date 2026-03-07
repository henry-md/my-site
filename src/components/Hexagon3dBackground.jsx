import React from 'react';
import PropTypes from 'prop-types';
import { LIGHT_THEME_COLOR_GRADIENT } from '../constants.ts';

function hexToRgb(color) {
  const normalized = color.replace('#', '').trim();
  const raw = normalized.length === 3
    ? normalized.split('').map((char) => `${char}${char}`).join('')
    : normalized;

  if (!/^[0-9a-fA-F]{6}$/.test(raw)) {
    return null;
  }

  const value = Number.parseInt(raw, 16);
  return {
    r: (value >> 16) & 255,
    g: (value >> 8) & 255,
    b: value & 255,
  };
}

function rgbToRgba(rgb, alpha) {
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

function mixRgb(start, end, ratio) {
  const t = Math.max(0, Math.min(1, ratio));
  return {
    r: Math.round(start.r + (end.r - start.r) * t),
    g: Math.round(start.g + (end.g - start.g) * t),
    b: Math.round(start.b + (end.b - start.b) * t),
  };
}

function Hexagon3dBackground({ opacity = 1, uiMode = 'light' }) {
  const canvasRef = React.useRef(null);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return undefined;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return undefined;
    }

    const PI = Math.PI;
    const startTime = Date.now();
    let frameId = 0;
    const bodyStyles = window.getComputedStyle(document.body);
    const darkStrokeColor = bodyStyles.getPropertyValue('--thread-stroke').trim() || 'hsla(0,0%,100%,0.2)';
    const darkFillColor = bodyStyles.getPropertyValue('--thread-fill').trim() || 'hsla(0,0%,100%,0.2)';
    const lightGradientStart = hexToRgb(LIGHT_THEME_COLOR_GRADIENT.start) || { r: 95, g: 130, b: 187 };
    const lightGradientEnd = hexToRgb(LIGHT_THEME_COLOR_GRADIENT.end) || { r: 142, g: 178, b: 224 };
    const lightGradientMid = mixRgb(lightGradientStart, lightGradientEnd, 0.5);

    const hypot = (a, b) => Math.sqrt(a * a + b * b);
    const sin = (a) => Math.sin(a);
    const cos = (a) => Math.cos(a);

    const resizeHandler = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      canvas.hyp = hypot(canvas.width, canvas.height);
    };

    const animloop = () => {
      frameId = window.requestAnimationFrame(animloop);

      const t = (Date.now() - startTime) / 1000;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (uiMode !== 'light') {
        ctx.strokeStyle = darkStrokeColor;
        ctx.fillStyle = darkFillColor;
      }

      const radius = canvas.hyp / 8;
      const slices = PI / 240;
      const width = radius;
      const height = radius;
      const xcenter = canvas.width / 2;
      const ycenter = canvas.height / 2;

      for (let arc = 0; arc <= PI * 2; arc += slices) {
        const threadX = sin(arc + t / 22) * radius + xcenter;
        const threadY = cos(arc - t / 23) * radius + ycenter;

        if (uiMode === 'light') {
          const xMix = threadX / canvas.width;
          const yMix = threadY / canvas.height;
          const positionMix = xMix * 0.72 + yMix * 0.28;
          const waveMix = (sin(arc * 1.8 - t / 7) + 1) / 2;
          const blendRatio = Math.max(0, Math.min(1, positionMix * 0.74 + waveMix * 0.26));
          const strokeRgb = mixRgb(lightGradientStart, lightGradientEnd, blendRatio);
          const fillRgb = mixRgb(lightGradientStart, lightGradientMid, blendRatio);
          ctx.strokeStyle = rgbToRgba(strokeRgb, 0.47);
          ctx.fillStyle = rgbToRgba(fillRgb, 0.2);
        }

        ctx.save();
        ctx.translate(threadX, threadY);
        ctx.rotate(arc);
        ctx.strokeRect(-width / 2, -height / 2, width, height);
        ctx.restore();
      }
    };

    resizeHandler();
    window.addEventListener('resize', resizeHandler, false);
    animloop();

    return () => {
      window.cancelAnimationFrame(frameId);
      window.removeEventListener('resize', resizeHandler, false);
    };
  }, [uiMode]);

  return (
    <canvas
      className="background-canvas"
      ref={canvasRef}
      style={{ opacity, backgroundColor: 'transparent' }}
      aria-hidden="true"
    />
  );
}

Hexagon3dBackground.propTypes = {
  opacity: PropTypes.number,
  uiMode: PropTypes.oneOf(['light', 'dark']),
};

export default Hexagon3dBackground;
