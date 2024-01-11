import React from 'react';
import ReactDOM from 'react-dom/client';

class FeaturedProject extends React.Component {

  render() {
    return (
      <div className="featured-project">
        <video className="featured-video" autoPlay loop>
          <source src={this.props.src} type="video/quicktime"></source>
        </video>
        <div className="featured-text">
          <p className="featured-title">{this.props.title}</p>
          <p className="featured-description">{this.props.description}</p>
          <div className="call-to-action-container">
            <a href={this.props.callToActionLink} className="featured-call" target="_blank">{this.props.callToAction}</a>
            {this.props.secondCallToAction && <a href={this.props.secondCallToActionLink} className="featured-call" target="_blank">{this.props.secondCallToAction}</a>}
          </div>
        </div>
      </div>
    );
  }
}

export default FeaturedProject;