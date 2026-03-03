import React from 'react';
import PropTypes from 'prop-types';

function Hexagon3dBackground({ opacity = 1 }) {
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
      ctx.strokeStyle = 'hsla(0,0%,100%,0.2)';
      ctx.fillStyle = 'hsla(0,0%,100%,0.2)';

      const radius = canvas.hyp / 8;
      const slices = PI / 240;
      const width = radius;
      const height = radius;
      const xcenter = canvas.width / 2;
      const ycenter = canvas.height / 2;

      for (let arc = 0; arc <= PI * 2; arc += slices) {
        ctx.save();
        ctx.translate(sin(arc + t / 22) * radius + xcenter, cos(arc - t / 23) * radius + ycenter);
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
  }, []);

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
};

export default Hexagon3dBackground;
