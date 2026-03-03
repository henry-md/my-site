import React from 'react';
import PropTypes from 'prop-types';

const EYES_TEXTURE_URL = '/assets/backgrounds/eyesblueorange.jpg';

function CreepyEyeBackground({ opacity = 1 }) {
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

    const imgCanvas = document.createElement('canvas');
    const imgContext = imgCanvas.getContext('2d');
    const brushCanvas = document.createElement('canvas');
    const brushCtx = brushCanvas.getContext('2d');

    if (!imgContext || !brushCtx) {
      return undefined;
    }

    const cleanups = [];
    const addListener = (target, eventName, handler, options = false) => {
      target.addEventListener(eventName, handler, options);
      cleanups.push(() => target.removeEventListener(eventName, handler, options));
    };

    const hypotenuse = (a, b) => Math.sqrt(a * a + b * b);

    const hsla = (h = 0, s = 100, l = 50, a = 1) => {
      const hue = h % 360;
      const sat = Math.min(Math.max(s, 0), 100);
      const lig = Math.min(Math.max(l, 0), 100);
      const alp = Math.min(Math.max(a, 0), 1);
      return `hsla(${hue}, ${sat}%, ${lig}%, ${alp})`;
    };

    const imageSmoothing = (context, enabled = false) => {
      context.webkitImageSmoothingEnabled = enabled;
      context.mozImageSmoothingEnabled = enabled;
      context.imageSmoothingEnabled = enabled;
    };

    const sizeCanvas = (targetCanvas, width, height) => {
      targetCanvas.w_FLOAT = width;
      targetCanvas.h_FLOAT = height;
      targetCanvas.width = width;
      targetCanvas.height = height;
      targetCanvas.top = -height / 2;
      targetCanvas.right = width / 2;
      targetCanvas.bottom = height / 2;
      targetCanvas.left = -width / 2;
    };

    const centerContextOrigin = (context) => {
      context.restore();
      context.translate(context.canvas.w_FLOAT / 2, context.canvas.h_FLOAT / 2);
      context.save();
    };

    const resetContextOrigin = (context) => {
      context.restore();
      context.translate(context.canvas.left, context.canvas.top);
      context.save();
    };

    const decay = (context, hor = 0, ver = 0, hspread = 0, vspread = 0, rotate = 0) => {
      const dx = context.canvas.left - hspread / 2;
      const dy = context.canvas.top - vspread / 2;
      const dw = context.canvas.width + hspread;
      const dh = context.canvas.height + vspread;

      context.save();
      context.translate(hor, ver);
      if (rotate !== 0) {
        context.rotate(rotate);
      }
      context.globalAlpha = 0.5;
      context.drawImage(context.canvas, dx, dy, dw, dh);
      context.restore();
    };

    const config = { smoothing: false };
    const bloops = [];

    let fps = 0;
    let fpsNow = null;
    let lastUpdate = Date.now() * 1 - 1;
    const fpsFilter = 50;
    let frameId = 0;
    let running = true;

    const img = new Image();

    const sizeCanvasesToWindow = (event, zoom = 1) => {
      resetContextOrigin(ctx);

      const w = window;
      const d = document;
      const e = d.documentElement;
      const g = d.getElementsByTagName('body')[0];
      const width = w.innerWidth || e.clientWidth || g.clientWidth;
      const height = w.innerHeight || e.clientHeight || g.clientHeight;

      const oldWidth = canvas.width;
      const oldHeight = canvas.height;
      const canvasCopy = document.createElement('canvas');
      const contextCopy = canvasCopy.getContext('2d');

      if (contextCopy) {
        canvasCopy.width = oldWidth;
        canvasCopy.height = oldHeight;
        contextCopy.drawImage(canvas, 0, 0);
      }

      sizeCanvas(canvas, width / zoom, height / zoom);
      if (contextCopy) {
        ctx.drawImage(canvasCopy, 0, 0, width / zoom, height / zoom);
      }

      canvas.style.zoom = zoom;
      canvas.style.MozTransformOrigin = '0 0';
      canvas.style.MozTransform = `scale(${zoom}, ${zoom})`;

      centerContextOrigin(ctx);
      imageSmoothing(ctx, !config.smoothing);
    };

    const initWallpaper = () => {
      if (!img.width || !img.height || !canvas.width || !canvas.height) {
        return;
      }

      sizeCanvas(
        imgCanvas,
        img.width * Math.ceil(canvas.width / img.width + 1),
        img.height * Math.ceil(canvas.height / img.height + 1),
      );

      for (let y = 0; y <= imgCanvas.height; y += img.height) {
        for (let x = 0; x <= imgCanvas.width; x += img.width) {
          imgContext.drawImage(img, x, y);
        }
      }
    };

    const initBrush = () => {
      const size = hypotenuse(canvas.width, canvas.height);
      sizeCanvas(brushCanvas, size, size);
      const x0 = size / 2;
      const y0 = size / 2;
      const r0 = 0;
      const x1 = size / 2;
      const y1 = size / 2;
      const r1 = size / 2;
      const gradient = brushCtx.createRadialGradient(x0, y0, r0, x1, y1, r1);
      gradient.addColorStop(0, hsla(120, 100, 50, 1));
      gradient.addColorStop(1, hsla(120, 100, 50, 0));
      brushCtx.fillStyle = gradient;
    };

    const Mouse = {
      x: 0,
      y: 0,
      xs: 0,
      ys: 0,
      xa: -1,
      xb: -1,
      ya: -1,
      yb: -1,
      xUp: 0,
      yUp: 0,
      up: true,
      down: false,
      clicks: 0,
      points: [],
      downTime: 0,
      events: {
        up: () => {
          Mouse.up = true;
          Mouse.down = false;
          Mouse.downTime = 0;
          Mouse.xUp = Mouse.x;
          Mouse.yUp = Mouse.y;
          canvas.style.cursor = 'pointer';
        },
        down: (event) => {
          event.preventDefault();
          Mouse.clicks += 1;
          Mouse.down = true;
          Mouse.up = false;
          canvas.style.cursor = 'none';
        },
        move: (event) => {
          let evt = event;
          if ('touches' in evt && evt.touches.length > 0) {
            evt.preventDefault();
            [evt] = evt.touches;
          }

          if (evt.pageX === Mouse.x || evt.pageY === Mouse.y) {
            return;
          }

          Mouse.x = ~~(evt.pageX - window.innerWidth / 2);
          Mouse.y = ~~(evt.pageY - window.innerHeight / 2);
          Mouse.points.unshift({
            x: Mouse.x,
            y: Mouse.y,
          });
          if (Mouse.points.length > 30) {
            Mouse.points.pop();
          }

          Mouse.xs = (Mouse.x + Mouse.xb) * 0.5;
          Mouse.ys = (Mouse.y + Mouse.yb) * 0.5;
          Mouse.xb = Mouse.x;
          Mouse.yb = Mouse.y;
        },
      },
    };

    class Bloop {
      constructor(x, y, age, death) {
        this.x = x;
        this.y = y;
        this.age = age;
        this.death = death;
      }

      draw(context) {
        if (this.age > context.canvas.width + context.canvas.height) {
          return;
        }

        context.lineWidth =
          (Math.sin((this.age / this.death) * 25) * 0.4 + 0.5) * (1 - this.age / this.death);
        context.beginPath();
        context.arc(
          this.x,
          this.y,
          this.age + Math.sin((this.age / this.death) * Math.PI * 4) * 10,
          0,
          Math.PI * 2,
          false,
        );
        context.closePath();
        context.strokeStyle = 'black';
        context.stroke();
        this.age += 1;
      }
    }

    const paintimg = (x, y) => {
      const size = hypotenuse(canvas.width, canvas.height);
      brushCtx.clearRect(0, 0, size, size);
      brushCtx.globalCompositeOperation = 'source-over';

      let randomSeed = 0;
      let newX = Mouse.x + brushCanvas.width / 2;
      let newY = Mouse.y + brushCanvas.height / 2;

      if (Mouse.down) {
        bloops.push(new Bloop(newX, newY, 0, size / 2));
      }

      if (Date.now() % (90 + randomSeed) === 0) {
        newX = (Math.random() - 0.5) * canvas.width + brushCanvas.width / 2;
        newY = (Math.random() - 0.5) * canvas.height + brushCanvas.height / 2;
        bloops.push(new Bloop(newX, newY, 0, size / 2));
        randomSeed = ((Math.random() * 0.5) * 20) | 0;
      }

      if (bloops.length > 0) {
        for (let i = 0; i < bloops.length; i += 1) {
          bloops[i].draw(brushCtx);
        }

        const fpsGate = (((60 / fps) * 10) | 0) / 10;
        const maxBloops = 180 / (fpsGate || 1);
        if (bloops[0].age > bloops[0].death || bloops.length > maxBloops) {
          bloops.shift();
        }
      }

      const sx = (x + canvas.right + size) % img.width;
      const sy = ~~(y + canvas.bottom + size) % img.height;
      const sw = size;
      const sh = size;
      const dx = 0;
      const dy = 0;
      const dw = sw;
      const dh = sh;

      brushCtx.globalCompositeOperation = 'source-in';
      brushCtx.drawImage(imgCanvas, sx, sy, sw, sh, dx, dy, dw, dh);
      ctx.drawImage(brushCanvas, x - size / 2, y - size / 2);
    };

    const animloop = () => {
      if (!running) {
        return;
      }

      frameId = window.requestAnimationFrame(animloop);

      const thisFrameFPS = 1000 / ((fpsNow = Date.now()) - lastUpdate);
      fps += (thisFrameFPS - fps) / fpsFilter;
      lastUpdate = fpsNow;

      imageSmoothing(ctx, true);
      if (Mouse.down) {
        Mouse.downTime += 1;
      }

      const spread = 0;
      const mAdjust = -1;
      const x = (Mouse.xs / canvas.width) * mAdjust;
      const y = (Mouse.ys / canvas.height) * mAdjust;

      decay(ctx, x, y, spread, spread, 0);

      const offset = 10;
      paintimg((Mouse.xs / canvas.width) * offset, (Mouse.ys / canvas.height) * offset);
    };

    const startAnimation = () => {
      ctx.fillStyle = 'black';
      ctx.fillRect(canvas.left, canvas.top, canvas.width, canvas.height);
      animloop();
    };

    const handleResize = () => {
      sizeCanvasesToWindow();
      initWallpaper();
      initBrush();
    };

    const initCanvas = () => {
      ctx.save();
      sizeCanvasesToWindow();
      addListener(window, 'resize', sizeCanvasesToWindow, false);
    };

    const initImage = () => {
      img.src = EYES_TEXTURE_URL;
      addListener(img, 'load', initWallpaper, false);
      addListener(img, 'load', startAnimation, false);
      addListener(window, 'resize', initWallpaper, false);
      addListener(window, 'orientationchange', initWallpaper, false);
    };

    const initMouse = () => {
      Mouse.y = canvas.bottom / 2;
      Mouse.ys = canvas.bottom / 2;
      Mouse.yUp = canvas.bottom / 2;

      addListener(window, 'mousedown', Mouse.events.down, false);
      addListener(window, 'mouseup', Mouse.events.up, false);
      addListener(window, 'mousemove', Mouse.events.move, false);
      addListener(window, 'touchstart', Mouse.events.down, false);
      addListener(window, 'touchend', Mouse.events.up, false);
      addListener(window, 'touchmove', Mouse.events.move, false);
    };

    initCanvas();
    initImage();
    ctx.fillStyle = 'hsla(0,0%,90%,0.8)';
    ctx.fillText('Loading...', 0, 0);
    initBrush();
    initMouse();
    addListener(window, 'resize', handleResize, false);
    addListener(window, 'orientationchange', handleResize, false);

    return () => {
      running = false;
      window.cancelAnimationFrame(frameId);
      cleanups.forEach((cleanup) => cleanup());
    };
  }, []);

  return (
    <canvas
      className="creepy-eye-canvas"
      id="canvas"
      ref={canvasRef}
      style={{ opacity }}
      aria-hidden="true"
    >
      this requires javascript
    </canvas>
  );
}

CreepyEyeBackground.propTypes = {
  opacity: PropTypes.number,
};

export default CreepyEyeBackground;
