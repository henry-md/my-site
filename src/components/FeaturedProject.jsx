import React from 'react';
import ReactDOM from 'react-dom/client';

class FeaturedProject extends React.Component {

  render() {
    return (
      <div className="featured-project">
        <video className="featured-video" autoPlay loop poster={this.props.poster}>
          <source src={this.props.src} type="video/quicktime"></source>
        </video>
        <div className="featured-text">
          <p className="featured-title sub-head">{this.props.title}</p>
          <p className="featured-description">{this.props.description}</p>
          <div className="featured-call-container">
            <a href={this.props.callToActionLink} className="dark-button featured-call" target="_blank">{this.props.callToAction}</a>
            {this.props.secondCallToAction && <a href={this.props.secondCallToActionLink} className="light-button featured-call" target="_blank">{this.props.secondCallToAction}</a>}
          </div>
        </div>
      </div>
    );
  }
}

export default FeaturedProject;