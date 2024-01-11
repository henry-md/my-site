import { useState } from 'react'
import TestimonialSwiper from './components/TestimonialSwiper.jsx'
import FeaturedProject from './components/FeaturedProject.jsx'
import { toggle, smoothScroll } from './utils/general.js';

import './App.css'
import 'swiper/css';

function App() {
  return (
    <>
    {/* start navigation bar */}
    <div className="topnav" id="myTopnav">
      <a href="#home" className="name">Henry Magnus Deutsch</a>
      <div className="horizontal-tabs">
        <a href="#experience">Experience</a>
        <a href="#skills">Skills</a>
        <a href="#testimonials" onClick={smoothScroll}>Testimonials</a>
        <a href="#featured">Featured Projects</a>
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
            <p className="subhead-small">Software Developer</p>
            <p className="subhead-big">
              Full stack developer studying at <span class="jhu-span">Johns Hopkins University</span>
            </p>
            <div>
              <p className="subhead-rainbow">Hi, I'm Henry</p>
            </div>
            <a className="subhead-contact" href="#contact">Download Resume</a>
            <img
              className="mobile-avatar avatar"
              src="https://www.w3schools.com/howto/img_avatar.png"
              alt="Avatar"
            />
          </div>
          <div className="header-image">
            <img
              src="https://www.w3schools.com/howto/img_avatar.png"
              alt="Avatar"
              className="avatar"
            />
          </div>
        </div>
      </div>

      {/* start testimonials section */}
      <div className="testimonials section" id="testimonials">
        <h2>Testiminials</h2>
        <TestimonialSwiper />
      </div>

      {/* start featured projects section */}
      <div className="projects section">
        <h2>Featured Projects</h2>
        <FeaturedProject
          src="./src/assets/vincent-dunn-demo.mov"
          alt="project 1"
          title="Vincent Dunn"
          description="PetCode is a Pet-Tech Startup that helps pet owners keep their furry friends safer, happier, and healthier with our Smart QR Tag and companion mobile app"
          callToAction="View Project"
          callToActionLink="https://henry-md.github.io/ChessHelper/"
          secondCallToAction="View Github"
          secondCallToActionLink="https://github.com/henry-md/ChessHelper"
        />

        <FeaturedProject
          src="./src/assets/chess-helper-demo.mov"
          alt="project 1"
          title="ChessHelper: An Interactive Way to Practice Chess Theory"
          description="Understanding and memorizing chess theory is absolutely essential in becoming a better chess player. Create a PGN (Portable Game Notation) file with an app like Stockfish and practice that move-tree interactively with ChessHelper! I couldn't find any site/app that did this, so I made this for myself."
          callToAction="View Project"
          callToActionLink="https://henry-md.github.io/ChessHelper/"
          secondCallToAction="View Github"
          secondCallToActionLink="https://github.com/henry-md/ChessHelper"
        />
      </div>
    </div>
    </>
  )
}

export default App
