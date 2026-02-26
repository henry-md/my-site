import React from 'react';
import PropTypes from 'prop-types';

class FeaturedProject extends React.Component {

  render() {
    return (
      <div className="featured-project fade-up">
        <video className="featured-video" autoPlay loop muted playsInline poster={this.props.poster}>
          <source src={this.props.src}></source>
          Your browser does not support this video format.
        </video>
        <div className="featured-text">
          <p className="featured-title sub-head">{this.props.title}</p>
          <p className="featured-description">{this.props.description}</p>
          <div className="featured-call-container">
            <a href={this.props.callToActionLink} className="dark-button featured-call" target="_blank" rel="noreferrer">{this.props.callToAction}</a>
            {this.props.secondCallToAction && <a href={this.props.secondCallToActionLink} className="light-button featured-call" target="_blank" rel="noreferrer">{this.props.secondCallToAction}</a>}
          </div>
        </div>
      </div>
    );
  }
}

FeaturedProject.propTypes = {
  poster: PropTypes.string,
  src: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  callToActionLink: PropTypes.string.isRequired,
  callToAction: PropTypes.string.isRequired,
  secondCallToAction: PropTypes.string,
  secondCallToActionLink: PropTypes.string,
};

export default FeaturedProject;
