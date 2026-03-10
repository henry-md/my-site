import React from 'react';
import PropTypes from 'prop-types';

class FeaturedProject extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      mediaOutlineColor: null,
    };
    this._mounted = false;
    this._colorRequestId = 0;
  }

  componentDidMount() {
    this._mounted = true;
    this.setMediaOutlineFromPoster(this.props.poster);
  }

  componentDidUpdate(prevProps) {
    if (prevProps.poster !== this.props.poster) {
      this.setMediaOutlineFromPoster(this.props.poster);
    }
  }

  componentWillUnmount() {
    this._mounted = false;
    this._colorRequestId += 1;
  }

  setMediaOutlineFromPoster(poster) {
    const requestId = this._colorRequestId + 1;
    this._colorRequestId = requestId;

    const sourceImage = new Image();
    sourceImage.decoding = 'async';

    sourceImage.onload = () => {
      if (!this._mounted || requestId !== this._colorRequestId) {
        return;
      }

      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      const context = canvas.getContext('2d');
      if (!context) {
        this.setState({ mediaOutlineColor: null });
        return;
      }

      context.drawImage(sourceImage, 0, 0);
      const [red, green, blue, alpha] = context.getImageData(0, 0, 1, 1).data;
      if (alpha === 0) {
        this.setState({ mediaOutlineColor: null });
        return;
      }

      const normalizedAlpha = Number((alpha / 255).toFixed(3));
      this.setState({
        mediaOutlineColor: `rgba(${red}, ${green}, ${blue}, ${normalizedAlpha})`,
      });
    };

    sourceImage.onerror = () => {
      if (this._mounted && requestId === this._colorRequestId) {
        this.setState({ mediaOutlineColor: null });
      }
    };

    sourceImage.src = poster;
  }

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
    const { mediaOutlineColor } = this.state;
    const mediaStyle = mediaOutlineColor ? { '--featured-media-outline': mediaOutlineColor } : undefined;

    return (
      <div className="featured-project fade-up">
        {src ? (
          <video className="featured-video" autoPlay loop muted playsInline poster={poster} draggable={false} style={mediaStyle}>
            <source src={src}></source>
            Your browser does not support this video format.
          </video>
        ) : (
          <img className="featured-video" src={poster} alt={alt} loading="lazy" draggable={false} style={mediaStyle} />
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
