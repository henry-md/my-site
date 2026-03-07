import React from 'react';
import PropTypes from 'prop-types';
import { BIRD_THEME_COLOR_GRADIENT, BIRD_THEME_COLOR_MODE } from '../constants.ts';

const THREE_SCRIPT_SRC = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js';
const VANTA_BIRDS_SCRIPT_SRC = 'https://cdn.jsdelivr.net/npm/vanta@0.5.24/dist/vanta.birds.min.js';

const scriptPromises = new Map();

function hexToVantaColor(hex) {
  const raw = String(hex).trim().replace(/^#/, '');
  const normalized = raw.length === 3
    ? raw.split('').map((ch) => ch + ch).join('')
    : raw;

  if (!/^[\da-fA-F]{6}$/.test(normalized)) {
    return 0x5478bb;
  }

  return Number.parseInt(normalized, 16);
}

function loadScript(src, isReady) {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Script loading is only available in the browser.'));
  }

  if (isReady()) {
    return Promise.resolve();
  }

  if (scriptPromises.has(src)) {
    return scriptPromises.get(src);
  }

  const promise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error(`Failed to load script: ${src}`)), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });

  scriptPromises.set(src, promise);
  return promise;
}

function BirdsBackground({ opacity = 1 }) {
  const rootRef = React.useRef(null);
  const startColor = BIRD_THEME_COLOR_GRADIENT.start;
  const endColor = BIRD_THEME_COLOR_GRADIENT.end;
  const colorMode = BIRD_THEME_COLOR_MODE;

  React.useEffect(() => {
    let cancelled = false;
    let vantaEffect = null;

    const init = async () => {
      try {
        await loadScript(THREE_SCRIPT_SRC, () => Boolean(window.THREE));
        await loadScript(
          VANTA_BIRDS_SCRIPT_SRC,
          () => Boolean(window.VANTA && typeof window.VANTA.BIRDS === 'function')
        );

        if (cancelled || !rootRef.current || !window.VANTA) {
          return;
        }

        vantaEffect = window.VANTA.BIRDS({
          el: rootRef.current,
          mouseControls: true,
          touchControls: true,
          gyroControls: false,
          minHeight: 200,
          minWidth: 200,
          scale: 1,
          scaleMobile: 1,
          backgroundAlpha: 0,
          backgroundColor: 0xf8fbff,
          colorMode,
          color1: hexToVantaColor(startColor),
          color2: hexToVantaColor(endColor),
          quantity: 3,
          birdSize: 1.05,
          wingSpan: 21,
          speedLimit: 4,
          separation: 36,
          alignment: 24,
          cohesion: 19,
        });
      } catch (error) {
        console.error('Unable to initialize bird background.', error);
      }
    };

    init();

    return () => {
      cancelled = true;
      if (vantaEffect && typeof vantaEffect.destroy === 'function') {
        vantaEffect.destroy();
      }
    };
  }, [startColor, endColor, colorMode]);

  return (
    <div
      className="background-canvas"
      ref={rootRef}
      style={{ opacity }}
      aria-hidden="true"
    />
  );
}

BirdsBackground.propTypes = {
  opacity: PropTypes.number,
};

export default BirdsBackground;
