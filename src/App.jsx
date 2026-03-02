import React from 'react';
import PropTypes from 'prop-types';
import TestimonialSwiper from './components/TestimonialSwiper.jsx';
import FeaturedProject from './components/FeaturedProject.jsx';
import ContactForm from './components/ContactForm.jsx';
import { toggle, smoothScroll } from './utils/general.js';

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
import './App.css';

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
  return (
    <>
      <div className="topnav" id="myTopnav">
        <a href="#home" className="name" onClick={smoothScroll}>Henry Magnus Deutsch</a>

        <div className="horizontal-tabs">
          <a href="#testimonials" onClick={smoothScroll}>Testimonials</a>
          <a href="#featured" onClick={smoothScroll}>Featured Projects</a>
          <a href="#contact" onClick={smoothScroll}>Contact</a>
        </div>

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
              <p className="subhead-big">
                I build polished, high-performance software while studying at <span className="jhu-span">Johns Hopkins University.</span>
              </p>
              <p className="hero-meta">Open to impactful engineering internships and selective freelance engagements.</p>

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
    </>
  );
}

export default App;
