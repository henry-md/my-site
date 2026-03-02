import React from 'react';
import TestimonialSwiper from './components/TestimonialSwiper.jsx'
import FeaturedProject from './components/FeaturedProject.jsx'
import ContactForm from './components/ContactForm.jsx'
import { toggle, smoothScroll } from './utils/general.js';
import PropTypes from 'prop-types';

import VincentDemo from './assets/vincent-dunn-demo.mov'
import CheckItOutDemo from './assets/checkitout-demo.mov'
import ChessHelperDemo from './assets/chess-helper-demo.mov'
import IntentionSetterDemo from './assets/intention-setter-demo.mov'

import VincentPoster from './assets/vincent-dunn-poster.png'
import CheckItOutPoster from './assets/checkitout-poster.png'
import ChessHelperPoster from './assets/chess-helper-poster.png'
import IntentionSetterPoster from './assets/intention-setter-poster.png'
import RayTracerPoster from './assets/ray-tracer-poster.png'

import Resume from './assets/HenryDeutschResume.pdf'
import FancyHeadshot from './assets/headshot_fancy_small.png'


import 'swiper/css';
import './App.css'

function FadeInSection(props) {
  const [isVisible, setVisible] = React.useState(false);
  const domRef = React.useRef();
  React.useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => setVisible(entry.isIntersecting));
    });
    observer.observe(domRef.current);
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
    {/* start navigation bar */}
    <div className="topnav" id="myTopnav">
      <a href="#home" className="name">Henry Magnus Deutsch</a>
      <div className="horizontal-tabs">
        <a href="#testimonials" onClick={smoothScroll}>Testimonials</a>
        <a href="#featured" onClick={smoothScroll}>Featured Projects</a>
        <a href="#contact" onClick={smoothScroll}>Contact</a>
      </div>

      <a href="javascript:void(0);" className="icon" onClick={toggle}>
        <i className="fa fa-bars"></i>
      </a>
    </div>

    {/* start content */}
    <div className="content">
      {/* start above the fold section */}
      <div className="header-container">
        <div className="header">
          <div className="header-text">
            <p className="subhead-small">Full Stack Developer</p>
            <p className="subhead-big">
              Software developer studying at <span className="jhu-span">Johns Hopkins University</span>
            </p>
            <div>
              <p className="subhead-rainbow">Hi, I&apos;m Henry</p>
            </div>
            <div className="resume-contact">
              <a className="subhead-resume" href={Resume} target="_blank" rel="noreferrer">View&nbsp;Resume</a>
              <a className="subhead-contact" href="#contact" onClick={smoothScroll}>Get&nbsp;in&nbsp;Touch</a>
            </div>
            <img
              className="mobile-avatar avatar"
              src={FancyHeadshot}
              alt="Avatar"
            />
          </div>
          <div className="header-image">
            <img
              src={FancyHeadshot}
              alt="Avatar"
              className="avatar fade-left"
            />
          </div>
        </div>
      </div>

      {/* start experience section */}
      {/* <div className="experience section" id="testimonials">
        <h2>What I do</h2>
        <div className="exieriences">
          <Experience />
        </div>
      </div> */}

      {/* start testimonials section */}
      <div className="testimonials section" id="testimonials">
        <h2>Testimonials</h2>
        <TestimonialSwiper />
      </div>

      {/* start featured projects section */}
      <div className="projects section" id="featured">
        <h2>Things I&apos;ve made</h2>
        {/* <p>A lot of the projects I make, including the ChessHelper and TypingHelper projects, I make because I want a website to exist that doesn't. </p> */}
        
        {/* Chess Helper */}
        <FadeInSection key={'0'}>
          <FeaturedProject
            src={ChessHelperDemo}
            poster={ChessHelperPoster}
            alt="Chess Helper project demo"
            title="ChessHelper: An Interactive Way to Practice Chess Theory"
            description="Full stack web app for practicing chess opening theory. Users can sign in, save projects, and go through an interactive tutorial. Features move validation, progress tracking, and configurable practice settings like playing as either color. Built node/tree based PGN parsing logic."
            callToAction="View Project"
            callToActionLink="https://chess-helper-frontend-production.up.railway.app/"
            secondCallToAction="View Github"
            secondCallToActionLink="https://github.com/henry-md/chess-helper"
          />
        </FadeInSection>

        {/* Intention Setter */}
        <FadeInSection key={'1'}>
          <FeaturedProject
            src={IntentionSetterDemo}
            poster={IntentionSetterPoster}
            alt="Intention Setter project"
            title="Intention Setter: Set Limtis On Chrome Websites"
            description="Chrome extension to help set and track limits across websites to avoid doomscrolling. Manifest V3 architecture with a service worker tracking active timers, content scripts monitoring page visibility, and real-time Firebase sync to persist usage data and rules across devices. Users can view analytics on a Next.js dashboard to visualizes browsing patterns."
            callToAction="View My Usage"
            callToActionLink="https://intention-setting-production.up.railway.app/henrymdeutsch"
            secondCallToAction="View Github"
            secondCallToActionLink="https://github.com/henry-md/intention-setting"
          />
        </FadeInSection>

        {/* Ray Tracer */}
        <FadeInSection key={'4'}>
          <FeaturedProject
            poster={RayTracerPoster}
            alt="Ray Tracer project picture"
            title="Ray Tracer in C++"
            description="Built ray tracing engine with C++, OpenGL, and multithreading — achieved 2.5x speedup over single-thread approach. Engineered 3D rendering pipeline with GLSL shaders and computational geometry intersection algorithms. Developed Phong illumination with quaternion camera controls, bilinear texture mapping, and ray shadow systems"
            callToAction="View Github"
            callToActionLink="https://github.com/henry-md/ray-tracer"
          />
        </FadeInSection>

        {/* Vincent Dunn */}
        <FadeInSection key={'2'}>
          <FeaturedProject
            src={VincentDemo}
            poster={VincentPoster}
            alt="Vincent Dunn website demo"
            title="Vincent Dunn's Website"
            description="Improved SEO, increasing traffic from <100 to >3.6k visits per mo. and book royalties from 8K to ~24K YoY (2.99x). Used custom Java-based PDF parser to extract structured content from 200+ pages and generate HTML and CSS layouts."
            callToAction="View Site"
            callToActionLink="https://www.vincentdunn.com"
          />
        </FadeInSection>
        
        {/* Check It Out */}
        <FadeInSection key={'3'}>
          <FeaturedProject
            src={CheckItOutDemo}
            poster={CheckItOutPoster}
            alt="Check It Out project demo"
            title="CheckItOut: Computer Vision Powered Solution to Checkout"
            description="Made a physical checkout counter with an integrated scale, overhead camera, and processing unit performing automatic detection and classification of grocery items. Lightweight classifier and detector using MobileNetV2, with robust accuracy."
            callToAction="View Devpost"
            callToActionLink="https://devpost.com/software/check-it-out"
          />
        </FadeInSection>

      </div>

      {/* start contact section */}
      <div className="contact section" id="contact">
        <ContactForm />
      </div>
      <div className='copyright'>
        © {new Date().getFullYear()} Henry Magnus Deutsch
      </div>
    </div>
    </>
  )
}

/*

*/

export default App
