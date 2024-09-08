import React from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import vincent from '../assets/vincent-dunn.jpeg';
import logan from '../assets/logan-ye.png';
import quote from '../assets/quote.jpeg';
import 'swiper/css';


class TestimonialSwiper extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      slidesPerView: this.getSlidesPerView(),
    };
  }

  componentDidMount() {
    window.addEventListener('resize', this.updateSlidesPerView);
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.updateSlidesPerView);
  }

  getSlidesPerView() {
    if (window.innerWidth > 1000) return 2;
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
            <p>
              I&apos;ve had the pleasure of working with Henry to develop my
              website, and have been consistently impressed by his ability
              to ask the right questions, and deliver on software that fits
              the particular needs of the situation. In all of the projects
              we&apos;ve worked on together he&apos;s kept great communication, and
              made my role stress-free. After completely re-doing my site
              and enhancing SEO my online book sales increased by 50%.
            </p>
            <p>
              Henry has a rare combination of technical proficiency and
              creative insight. In our work together he&apos;s encouraged me to
              rethink aspects of the UI (User Interface) both in terms of function and
              aesthetics, and in the end it created a better user
              experience. I give Henry my whole-hearted recommendation.
            </p>
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
            <p>
              Henry was a standout member of our team this summer where he worked on the development of KnoWhiz, an application that had both front and backend challenges.
            </p>
            <p>
              Henry demonstrated an exceptional ability to handle complex tasks and deliver high-quality results. His contributions in leading the development of the explore page, helping implement course generation from wikipedia and youtube links, etc. were critical to the timely launch of the 1.1v of our app.
            </p>
            <p>
              Beyond his technical skills, he was a pleasure to have on the team, and regularly took the initiative to mentor other interns, sharing his knowledge and helping to resolve issues as they arose. 
            </p>
            <p>
              I have no doubt that Henry will continue to excel in his future endeavors, and I highly recommend him for any role that he chooses to pursue. He would be an invaluable asset to any team.
            </p>
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