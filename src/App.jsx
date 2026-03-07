import React from 'react';
import PropTypes from 'prop-types';
import TestimonialSwiper from './components/TestimonialSwiper.jsx';
import FeaturedProject from './components/FeaturedProject.jsx';
import ContactForm from './components/ContactForm.jsx';
import CreepyEyeBackground from './components/CreepyEyeBackground.jsx';
import Hexagon3dBackground from './components/Hexagon3dBackground.jsx';
import { toggle, smoothScroll } from './utils/general.js';
import { ABOVE_FOLD_TEXT_SHIMMERS, DEBUG_UI } from './constants.ts';
import { BACKGROUND_CONFIGS, DEFAULT_BACKGROUND_ID } from './background-configs.ts';

import VincentDemo from './assets/vincent-dunn-demo.mov';
import CheckItOutDemo from './assets/checkitout-demo.mov';
import ChessHelperDemo from './assets/chess-helper-demo.mov';
import IntentionSetterDemo from './assets/intention-setter-demo.mov';

import VincentPoster from './assets/vincent-dunn-poster.png';
import CheckItOutPoster from './assets/checkitout-poster.png';
import ChessHelperPoster from './assets/chess-helper-poster.png';
import IntentionSetterPoster from './assets/intention-setter-poster.png';
import RayTracerPoster from './assets/ray-tracer-poster.png';

import Resume from './assets/HenryDeutschResume.pdf';
import FancyHeadshot from './assets/headshot_fancy_small.png';

import 'swiper/css';

const THEME_STORAGE_KEY = 'site-theme-id';
const UI_MODE_STORAGE_KEY = 'ui-mode-pref-v2';
const UI_LIGHT = 'light';
const UI_DARK = 'dark';

function normalizeUiMode(value) {
  if (value === UI_LIGHT || value === UI_DARK) {
    return value;
  }
  return null;
}

function getBackgroundById(id) {
  const match = BACKGROUND_CONFIGS.find((background) => background.id === id);
  return match || BACKGROUND_CONFIGS[0];
}

function FadeInSection(props) {
  const [isVisible, setVisible] = React.useState(false);
  const domRef = React.useRef(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => setVisible(entry.isIntersecting));
    });

    if (domRef.current) {
      observer.observe(domRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div
      className={`fade-in-section ${isVisible ? 'is-visible' : ''}`}
      ref={domRef}
    >
      {props.children}
    </div>
  );
}

FadeInSection.propTypes = {
  children: PropTypes.node.isRequired,
};

function App() {
  const [themeId, setThemeId] = React.useState(() => {
    if (typeof window === 'undefined') {
      return DEFAULT_BACKGROUND_ID;
    }

    const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    return getBackgroundById(storedTheme || DEFAULT_BACKGROUND_ID).id;
  });
  const [uiModePreference, setUiModePreference] = React.useState(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    return normalizeUiMode(window.localStorage.getItem(UI_MODE_STORAGE_KEY));
  });
  const [isThemeModalOpen, setIsThemeModalOpen] = React.useState(false);

  const selectedTheme = DEBUG_UI
    ? getBackgroundById(themeId)
    : getBackgroundById(DEFAULT_BACKGROUND_ID);
  const activeUiMode = DEBUG_UI ? (uiModePreference || selectedTheme.uiMode) : UI_LIGHT;
  const hexagon3dBackgroundEnabled = selectedTheme.canvasType === 'hexagon-3d';
  const creepyEyeBackgroundEnabled = selectedTheme.canvasType === 'creepy-eye';

  React.useEffect(() => {
    const themeClassNames = BACKGROUND_CONFIGS.map((theme) => `theme-${theme.id}`);
    const bodyThemeClass = `theme-${selectedTheme.id}`;
    const bodyUiClass = `ui-${activeUiMode}`;

    document.body.classList.remove(...themeClassNames, 'ui-light', 'ui-dark');
    document.body.classList.add(bodyThemeClass, bodyUiClass);
    if (DEBUG_UI) {
      window.localStorage.setItem(THEME_STORAGE_KEY, selectedTheme.id);
      if (uiModePreference) {
        window.localStorage.setItem(UI_MODE_STORAGE_KEY, uiModePreference);
      } else {
        window.localStorage.removeItem(UI_MODE_STORAGE_KEY);
      }
    } else {
      window.localStorage.removeItem(THEME_STORAGE_KEY);
      window.localStorage.removeItem(UI_MODE_STORAGE_KEY);
    }

    return () => {
      document.body.classList.remove(bodyThemeClass, bodyUiClass);
    };
  }, [activeUiMode, selectedTheme.id, uiModePreference]);

  React.useEffect(() => {
    if (!isThemeModalOpen) {
      return undefined;
    }

    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsThemeModalOpen(false);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [isThemeModalOpen]);

  return (
    <div className={`app-shell theme-${selectedTheme.id} ui-${activeUiMode}`}>
      {creepyEyeBackgroundEnabled ? <CreepyEyeBackground opacity={selectedTheme.canvasOpacity} /> : null}
      {hexagon3dBackgroundEnabled ? <Hexagon3dBackground opacity={selectedTheme.canvasOpacity} uiMode={activeUiMode} /> : null}

      <div className="topnav" id="myTopnav">
        <a href="#home" className="name" onClick={smoothScroll}>Henry Magnus Deutsch</a>

        <div className="horizontal-tabs">
          <a href="#testimonials" onClick={smoothScroll}>Testimonials</a>
          <a href="#featured" onClick={smoothScroll}>Featured Projects</a>
          <a href="#contact" onClick={smoothScroll}>Contact</a>
        </div>

        {DEBUG_UI ? (
          <>
            <button
              type="button"
              className="theme-toggle"
              onClick={() => setIsThemeModalOpen(true)}
              aria-label="Open theme selector"
              title={`Theme: ${selectedTheme.label}`}
            >
              <svg
                className="theme-toggle-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="3.9" />
                <path d="M12 2.6v2.2M12 19.2v2.2M4.8 4.8l1.6 1.6M17.6 17.6l1.6 1.6M2.6 12h2.2M19.2 12h2.2M4.8 19.2l1.6-1.6M17.6 6.4l1.6-1.6" />
              </svg>
              <span className="toggle-label">Theme: {selectedTheme.label}</span>
            </button>

            <button
              type="button"
              className="theme-toggle ui-mode-toggle"
              onClick={() => setUiModePreference(activeUiMode === UI_DARK ? UI_LIGHT : UI_DARK)}
              aria-label="Toggle UI mode between light and dark"
              title="Toggle light or dark UI mode"
            >
              <svg
                className="theme-toggle-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M21 12.4A8.4 8.4 0 1111.6 3a6.7 6.7 0 009.4 9.4z" />
              </svg>
              <span className="toggle-label">UI: {activeUiMode}</span>
            </button>
          </>
        ) : null}

        <button type="button" className="icon" onClick={toggle} aria-label="Toggle menu">
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>

      <div className="content">
        <div className="header-container" id="home">
          <div className="header">
            <div className="header-text fade-up">
              <p className="subhead-small">Full Stack Developer</p>
              <p className="subhead-rainbow">Hi, I&apos;m Henry</p>
              <p className={`subhead-big ${ABOVE_FOLD_TEXT_SHIMMERS ? 'above-fold-text-shimmer' : ''}`}>
                Software Engineer with experience shipping large-scale, revenue-driving systems. {/* jhu-span */}
              </p>
              <p className={`hero-meta ${ABOVE_FOLD_TEXT_SHIMMERS ? 'above-fold-text-shimmer' : ''}`}>Open to full time software engineering roles.</p>

              <div className="resume-contact">
                <a className="subhead-resume" href={Resume} target="_blank" rel="noreferrer">View Resume</a>
                <a className="subhead-contact" href="#contact" onClick={smoothScroll}>Get In Touch</a>
              </div>

              <img
                className="mobile-avatar avatar"
                src={FancyHeadshot}
                alt="Portrait of Henry Deutsch"
                draggable={false}
              />
            </div>

            <div className="header-image fade-left">
              <img
                src={FancyHeadshot}
                alt="Portrait of Henry Deutsch"
                className="avatar"
                draggable={false}
              />
            </div>
          </div>
        </div>

        <div className="testimonials section" id="testimonials">
          <h2>Testimonials</h2>
          <TestimonialSwiper />
        </div>

        <div className="projects section" id="featured">
          <h2>Featured Work</h2>

          <FadeInSection key="0">
            <FeaturedProject
              src={ChessHelperDemo}
              poster={ChessHelperPoster}
              alt="Chess Helper project demo"
              title="ChessHelper: An Interactive Way to Practice Chess Theory"
              description="Full stack web app for practicing chess opening theory. Users can sign in, save projects, and go through an interactive tutorial. Features move validation, progress tracking, and configurable practice settings like playing as either color. Built node/tree based PGN parsing logic."
              callToAction="View Project"
              callToActionLink="https://chess-helper-frontend-production.up.railway.app/"
              secondCallToAction="View GitHub"
              secondCallToActionLink="https://github.com/henry-md/chess-helper"
            />
          </FadeInSection>

          <FadeInSection key="1">
            <FeaturedProject
              src={IntentionSetterDemo}
              poster={IntentionSetterPoster}
              alt="Intention Setter project"
              title="Intention Setter: Set Limits On Chrome Websites"
              description="Chrome extension to help set and track limits across websites to avoid doomscrolling. Manifest V3 architecture with a service worker tracking active timers, content scripts monitoring page visibility, and real-time Firebase sync to persist usage data and rules across devices. Users can view analytics on a Next.js dashboard to visualize browsing patterns."
              callToAction="View My Usage"
              callToActionLink="https://intention-setting-production.up.railway.app/henrymdeutsch"
              secondCallToAction="View GitHub"
              secondCallToActionLink="https://github.com/henry-md/intention-setting"
            />
          </FadeInSection>

          <FadeInSection key="4">
            <FeaturedProject
              poster={RayTracerPoster}
              alt="Ray Tracer project"
              title="Ray Tracer in C++"
              description="Built ray tracing engine with C++, OpenGL, and multithreading, achieving a 2.5x speedup over the single-thread approach. Engineered a 3D rendering pipeline with GLSL shaders and computational geometry intersection algorithms. Developed Phong illumination with quaternion camera controls, bilinear texture mapping, and ray shadow systems."
              callToAction="View GitHub"
              callToActionLink="https://github.com/henry-md/ray-tracer"
            />
          </FadeInSection>

          <FadeInSection key="2">
            <FeaturedProject
              src={VincentDemo}
              poster={VincentPoster}
              alt="Vincent Dunn website demo"
              title="Vincent Dunn's Website"
              description="Improved SEO, increasing traffic from under 100 to over 3.6K visits per month and book royalties from $8K to roughly $24K YoY. Used a custom Java-based PDF parser to extract structured content from 200+ pages and generate HTML and CSS layouts."
              callToAction="View Site"
              callToActionLink="https://www.vincentdunn.com"
            />
          </FadeInSection>

          <FadeInSection key="3">
            <FeaturedProject
              src={CheckItOutDemo}
              poster={CheckItOutPoster}
              alt="Check It Out project demo"
              title="CheckItOut: Computer Vision Powered Solution to Checkout"
              description="Built a physical checkout counter with an integrated scale, overhead camera, and processing unit for automatic detection and classification of grocery items. Developed a lightweight classifier and detector using MobileNetV2 with robust real-world accuracy."
              callToAction="View Devpost"
              callToActionLink="https://devpost.com/software/check-it-out"
            />
          </FadeInSection>
        </div>

        <div className="contact section" id="contact">
          <ContactForm />
        </div>

        <div className="copyright">
          © {new Date().getFullYear()} Henry Magnus Deutsch
        </div>
      </div>

      {DEBUG_UI && isThemeModalOpen ? (
        <div
          className="theme-modal-overlay"
          role="presentation"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setIsThemeModalOpen(false);
            }
          }}
        >
          <div className="theme-modal" role="dialog" aria-modal="true" aria-label="Theme selector">
            <div className="theme-modal-title">Select Theme</div>
            <div className="theme-modal-list">
              {BACKGROUND_CONFIGS.map((background) => (
                <button
                  type="button"
                  key={background.id}
                  className={`theme-option ${background.id === selectedTheme.id ? 'active' : ''}`}
                  onClick={() => {
                    setThemeId(background.id);
                    setUiModePreference(null);
                    setIsThemeModalOpen(false);
                  }}
                >
                  <span>{background.label}</span>
                  <span className="theme-option-mode">{background.uiMode}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;
