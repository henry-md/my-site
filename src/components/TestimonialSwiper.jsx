import React from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Pagination } from 'swiper/modules';
import vincent from '../assets/vincent-dunn.jpeg';
import logan from '../assets/logan-ye.png';
import james from '../assets/james-butler.jpeg';
import quote from '../assets/quote.jpeg';
import 'swiper/css';
import 'swiper/css/pagination';

class TestimonialSwiper extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      slidesPerView: this.getSlidesPerView(),
    };
  }

  // to show and hide the testiminial overflow text
  toggleText = (container, button, content) => {
    if (container.classList.contains('expanded')) {
      container.classList.remove('expanded');
      button.textContent = 'See More';
      content.style.maxHeight = '480px'; // [Ref 1] Should match what's in App.css
    } else {
      container.classList.add('expanded');
      button.textContent = 'See Less';
      content.style.maxHeight = 'none';
    }
  };

  componentDidMount() {
    window.addEventListener('resize', this.updateSlidesPerView);
    window.addEventListener('load', this.setupTestimonials);

    // deal with testimonials overflow
    this.setupTestimonials();
  }

  setupTestimonials = () => {
    const containers = document.querySelectorAll('.expandable-container');
    
    containers.forEach(container => {
      const content = container.querySelector('.expandable-content');
      const button = container.querySelector('.toggle-see-more-btn');
      
      // Remove existing event listener if any
      button.removeEventListener('click', button.toggleTextHandler);
      
      // Check if content overflows
      if (content.scrollHeight > 480) { // [Ref 1] - should match what's in App.css
        console.log('overflow');
        button.classList.add('visible');
        // Create a new handler and store it on the button element
        button.toggleTextHandler = () => this.toggleText(container, button, content);
        button.addEventListener('click', button.toggleTextHandler);
        content.classList.add('gradient-hide');
      } else {
        console.log('no overflow');
        // Remove gradient if content doesn't overflow
        content.classList.remove('gradient-hide');
        button.classList.remove('visible');
      }
    });
  };

  componentDidUpdate() {
    // Re-setup testimonials after component updates
    this.setupTestimonials();
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.updateSlidesPerView);
    
    // Remove all event listeners
    const buttons = document.querySelectorAll('.toggle-see-more-btn');
    buttons.forEach(button => {
      if (button.toggleTextHandler) {
        button.removeEventListener('click', button.toggleTextHandler);
      }
    });
  }

  getSlidesPerView() {
    if (window.innerWidth > 800) return 2;
    return 1;
  }

  updateSlidesPerView = () => {
    this.setState({ slidesPerView: this.getSlidesPerView() });
  };

  render() {
    return ( 
      <Swiper
        spaceBetween={50}
        slidesPerView={this.state.slidesPerView}
        onSlideChange={() => console.log('slide change')}
        onSwiper={(swiper) => console.log(swiper)}
        loop={true}
        pagination={{ clickable: true }}
        modules={[Pagination]}
      >
        <SwiperSlide>
          <div className="quote-content">
            <img
              className="open-quote"
              src={quote}
              alt="Open Quote"
            />
            <img
              className="close-quote"
              src={quote}
              alt="Close Quote"
            />
            <div className="expandable-container">
              <div className="expandable-content">
                <p>&quot;A Force Multiplier&quot; perfectly captures Henry Deutsch&apos;s contributions during his time at Helpful Engineering.</p>
                <p>I had the pleasure of working with Henry for a summer internship on a Program-Home, an internal development effort focused on platform work, and his impact consistently exceeded expectations.</p>
                <p>Henry exemplified the ideal team player. He wasn&apos;t just content with fulfilling his assigned tasks; he actively sought opportunities to contribute. This &quot;force multiplier&quot; mentality shone brightly in his work on developing an internal tool for onboarding future volunteers. He didn&apos;t simply churn out code — he actively participated in design discussions, provided valuable input on workflow and functionality, and even researched AI tooling to identify potential future workflow enhancements.</p>
                <p>I was truly impressed by Henry&apos;s technical ability, well beyond his years in terms of skill and maturity as an intern. He led the development of our internal platform that other developers and engineers use to join one of our work tracks, using mainly Typescript, CSS, and AWS Amplify. He produced professional-quality code that was not only functional but also elegantly structured and well-documented.</p>
                <p>Henry&apos;s self-starting nature is another hallmark of his work style. He readily took ownership of tasks, needing minimal direction to get things done effectively. This characteristic was particularly evident during the resolution of the Program-Home issues, where he independently identified areas for improvement and proactively implemented solutions.</p>
                <p>Henry&apos;s combination of technical expertise, collaborative spirit, and self-starting drive makes him a truly unique talent. I have no doubt he will continue to excel in any environment he encounters. I wholeheartedly recommend him for a software engineering role.</p>
              </div>
              <button className="toggle-see-more-btn">See More</button>
            </div>
          </div>
          <div className="tab-footer">
            <img
              src={james}
              alt="Avatar"
              className="avatar logan"
            />
            <div className="name-title">
              <p>James Butler</p>
              <p>CEO of Helpful Engineering</p>
            </div>
          </div>
        </SwiperSlide>
        <SwiperSlide>
          <div className="quote-content">
            <img
              className="open-quote"
              src={quote}
              alt="Open Quote"
            />
            <img
              className="close-quote"
              src={quote}
              alt="Close Quote"
            />
            <div className="expandable-container">
              <div className="expandable-content">
                <p>Henry was a standout member of our team this summer where he worked on the development of KnoWhiz, an application that had both front and backend challenges.</p>
                <p>Henry demonstrated an exceptional ability to handle complex tasks and deliver high-quality results. His contributions in leading the development of the explore page, helping implement course generation from wikipedia and youtube links, etc. were critical to the timely launch of the 1.1v of our app.</p>
                <p>Beyond his technical skills, he was a pleasure to have on the team, and regularly took the initiative to mentor other interns, sharing his knowledge and helping to resolve issues as they arose.</p>
                <p>I have no doubt that Henry will continue to excel in his future endeavors, and I highly recommend him for any role that he chooses to pursue. He would be an invaluable asset to any team.</p>
              </div>
              <button className="toggle-see-more-btn">See More</button>
            </div>
          </div>
          <div className="tab-footer">
            <img
              src={logan}
              alt="Avatar"
              className="avatar logan"
            />
            <div className="name-title">
              <p>Logan Ye</p>
              <p>CEO of KnoWhiz</p>
            </div>
          </div>
        </SwiperSlide>
        <SwiperSlide>
          <div className="quote-content">
            <img
              className="open-quote"
              src={quote}
              alt="Open Quote"
            />
            <img
              className="close-quote"
              src={quote}
              alt="Close Quote"
            />
            <div className="expandable-container">
              <div className="expandable-content">
                <p>I&apos;ve had the pleasure of working with Henry to develop my website, and have been consistently impressed by his ability to ask the right questions, and deliver on software that fits the particular needs of the situation. In all of the projects we&apos;ve worked on together he&apos;s kept great communication, and made my role stress-free. After completely re-doing my site and enhancing SEO my online book sales increased by 50%.</p>
                <p>Henry has a rare combination of technical proficiency and creative insight. In our work together he&apos;s encouraged me to rethink aspects of the UI (User Interface) both in terms of function and aesthetics, and in the end it created a better user experience. I give Henry my whole-hearted recommendation.</p>
              </div>
              <button className="toggle-see-more-btn">See More</button>
            </div>
          </div>
          <div className="tab-footer">
            <img
              src={vincent}
              alt="Avatar"
              className="avatar vincent"
            />
            <div className="name-title">
              <p>Vincent Dunn</p>
              <p>Ret. Chief of NYC Fire Dept.</p>
            </div>
          </div>
        </SwiperSlide>
      </Swiper>

      
    )
  }
}

// function updateSlidesPerView() {
//   swiper.params.slidesPerView = getSlidesPerView();
//   swiper.update();
// }

// function goToView(viewIndex) {
//   swiper.slideTo(viewIndex);
// }

// window.addEventListener("resize", updateSlidesPerView);

export default TestimonialSwiper