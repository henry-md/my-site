import React from 'react';
import TestimonialSwiper from './components/TestimonialSwiper.jsx'
import FeaturedProject from './components/FeaturedProject.jsx'
import ContactForm from './components/ContactForm.jsx'
import { toggle, smoothScroll } from './utils/general.js';
import PropTypes from 'prop-types';

import VincentDemo from './assets/vincent-dunn-demo.mov'
import CheckItOutDemo from './assets/checkitout-demo.mov'
import ChessHelperDemo from './assets/chess-helper-demo.mov'
import TypingHelperDemo from './assets/typing-helper-demo.mov'

import VincentPoster from './assets/vincent-dunn-poster.png'
import CheckItOutPoster from './assets/checkitout-poster.png'
import ChessHelperPoster from './assets/chess-helper-poster.png'
import TypingHelperPoster from './assets/typing-helper-poster.png'
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
        <h2>Featured Projects</h2>
        {/* <p>A lot of the projects I make, including the ChessHelper and TypingHelper projects, I make because I want a website to exist that doesn't. </p> */}
        
        <FadeInSection key={'1'}>
          <FeaturedProject
            src={VincentDemo}
            poster={VincentPoster}
            alt="Vincent Dunn website demo"
            title="Vincent Dunn: Turned a Book Into Interactive Learning Site"
            description="Worked for Vincent Dunn to turn his book, “A Firefighter's Battlespace,” into a website. Wrote JS to parse the pdf and create features dynamically. Created interactive UI for quizzing material. The site was up for ~12 months and got 2.7k pageviews per month."
            callToAction="View Project"
            callToActionLink="https://henry-md.github.io/Vincent-Dunn-Book/"
            secondCallToAction="View Github"
            secondCallToActionLink="https://github.com/henry-md/Vincent-Dunn-Book"
          />
        </FadeInSection>
        
        <FadeInSection key={'2'}>
          <FeaturedProject
            src={CheckItOutDemo}
            poster={CheckItOutPoster}
            alt="Check It Out project demo"
            title="CheckItOut: Computer Vision Powered Solution to Checkout"
            description="Made a physical checkout counter with an integrated scale, overhead camera, and processing unit performing automatic detection and classification of grocery items. Lightweight classifier and detector using MobileNetV2, with robust accuracy."
            callToAction="View Website"
            callToActionLink="https://henry-md.github.io/CheckItOut/"
            secondCallToAction="View Devpost"
            secondCallToActionLink="https://devpost.com/software/check-it-out"
          />
        </FadeInSection>
        
        <FadeInSection key={'3'}>
          <FeaturedProject
            src={ChessHelperDemo}
            poster={ChessHelperPoster}
            alt="Chess Helper project demo"
            title="ChessHelper: An Interactive Way to Practice Chess Theory"
            description="Understanding and memorizing chess theory is absolutely essential to becoming a better chess player. Create a PGN (Portable Game Notation) file with an app like Stockfish and practice that move-tree interactively with ChessHelper!"
            callToAction="View Project"
            callToActionLink="https://henry-md.github.io/ChessHelper/"
            secondCallToAction="View Github"
            secondCallToActionLink="https://github.com/henry-md/ChessHelper"
          />
        </FadeInSection>
        
        <FadeInSection key={'4'}>
          <FeaturedProject
            src={TypingHelperDemo}
            poster={TypingHelperPoster}
            alt="Typing helper project demo"
            title="TypingHelper: Improve Special Character Typing Speed"
            description="Generates typing test heavy in special characters to help with typing speed when coding. You can programatically control variables like the method used to generate the typing test, length of the test, and concentration of special characters."
            callToAction="View Project"
            callToActionLink="https://henry-md.github.io/Typing-Helper/"
            secondCallToAction="View Github"
            secondCallToActionLink="https://github.com/henry-md/Typing-Helper"
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
