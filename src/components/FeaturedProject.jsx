import React from 'react';
import PropTypes from 'prop-types';

class FeaturedProject extends React.Component {
  render() {
    const {
      poster,
      src,
      alt,
      title,
      description,
      callToAction,
      callToActionLink,
      secondCallToAction,
      secondCallToActionLink,
    } = this.props;

    return (
      <div className="featured-project fade-up">
        {src ? (
          <video className="featured-video" autoPlay loop muted playsInline poster={poster} draggable={false}>
            <source src={src}></source>
            Your browser does not support this video format.
          </video>
        ) : (
          <img className="featured-video" src={poster} alt={alt} loading="lazy" draggable={false} />
        )}

        <div className="featured-text">
          <p className="featured-title sub-head">{title}</p>
          <p className="featured-description">{description}</p>
          <div className="featured-call-container">
            <a href={callToActionLink} className="dark-button featured-call" target="_blank" rel="noreferrer">{callToAction}</a>
            {secondCallToAction && (
              <a href={secondCallToActionLink} className="light-button featured-call" target="_blank" rel="noreferrer">{secondCallToAction}</a>
            )}
          </div>
        </div>
      </div>
    );
  }
}

FeaturedProject.propTypes = {
  poster: PropTypes.string.isRequired,
  src: PropTypes.string,
  alt: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  callToActionLink: PropTypes.string.isRequired,
  callToAction: PropTypes.string.isRequired,
  secondCallToAction: PropTypes.string,
  secondCallToActionLink: PropTypes.string,
};

export default FeaturedProject;
