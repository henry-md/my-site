import { useState } from 'react'
import TestimonialSwiper from './components/TestimonialSwiper.jsx'
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
      <div className="header">
        <div className="header-text">
          <p className="subhead-small">Software Developer</p>
          <p className="subhead-big">
            Full stack developer studying at Johns Hopkins University
          </p>
          <div>
            <p className="subhead-rainbow">Hi, I'm Henry</p>
          </div>
          <a className="subhead-contact" href="#contact">Schedule a meeting</a>
          <img
            className="background-image avatar"
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

      {/* start testimonials section */}
      <div className="testimonials" id="testimonials">
        <h2>Testiminials</h2>

        <TestimonialSwiper />
      </div>

      {/* start featured projects section */}
      <div>
        <h2>Featured Projects</h2>
      </div>
    </div>
    </>
  )
}

export default App
