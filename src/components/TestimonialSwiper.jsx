import React from 'react';
import ReactDOM from 'react-dom/client';
import { Swiper, SwiperSlide } from 'swiper/react';
import vincent from '../assets/vincent-dunn.jpeg';
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
              I've had the pleasure of working with Henry to develop my
              website, and have been consistently impressed by his ability
              to ask the right questions, and deliver on software that fits
              the particular needs of the situation. In all of the projects
              we've worked on together he's kept great communication, and
              made my role stress-free. After completely re-doing my site
              and enhancing SEO my online book sales increased by 50%.
            </p>
            <p>
              Henry has a rare combination of technical proficiency and
              creative insight. In our work together he's encouraged me to
              rethink aspects of the UI both in terms of function and
              aesthetics, and in the end it created a better user
              experience. I give Henry my whole-hearted recommendation.
            </p>
          </div>
          <div className="tab-footer">
            <img
              src={vincent}
              alt="Avatar"
              className="avatar"
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
              Coming Soon
            </p>
          </div>
          <div className="tab-footer">
            <img
              src={"https://www.w3schools.com/howto/img_avatar.png"}
              alt="Avatar"
              className="avatar"
            />
            <div className="name-title">
              <p>First Last</p>
              <p>Title</p>
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