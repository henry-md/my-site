import { useEffect, useRef } from 'react';
import { useForm, ValidationError } from '@formspree/react';

// Make sure to run npm install @formspree/react
// For more help visit https://formspr.ee/react-help

function ContactForm() {
  const [state, handleSubmit] = useForm("mleqdbev");
  const emailInputRef = useRef(null);

  useEffect(() => {
    const contactSection = emailInputRef.current?.closest('.contact.section');
    if (!contactSection || typeof IntersectionObserver !== 'function') {
      return undefined;
    }

    let focusTimeoutId;
    let hasFocused = false;
    const observer = new IntersectionObserver(([entry]) => {
      if (hasFocused) {
        return;
      }

      if (entry.intersectionRatio >= 0.7) {
        if (focusTimeoutId !== undefined) {
          return;
        }

        focusTimeoutId = window.setTimeout(() => {
          focusTimeoutId = undefined;
          emailInputRef.current?.focus({ preventScroll: true });
          hasFocused = true;
          observer.disconnect();
        }, 1000);
        return;
      }

      window.clearTimeout(focusTimeoutId);
      focusTimeoutId = undefined;
    }, { threshold: 0.7 });

    observer.observe(contactSection);

    return () => {
      window.clearTimeout(focusTimeoutId);
      observer.disconnect();
    };
  }, []);

  // if (state.succeeded) {
  //     return <p>Thanks for joining!</p>;
  // }

  const handleSubmitWithCallback = async (event) => {
    event.preventDefault();
    try {
      await handleSubmit(event);
      window.location.href = "https://formspree.io/thanks?language=en";
    } catch (error) {
      console.error('Error submitting form:', error);
      // Handle the error here
    }
  };
  return (
    <form className="contact-form" onSubmit={handleSubmitWithCallback}>
      <h2>Get In Touch!</h2>
      <p className="contact-intro">Let me know what you&apos;re building &nbsp; 😮</p>

      <div className="name-email">
        <div className="field-wrap">
          <input
            id="email"
            type="email"
            name="email"
            placeholder="Email address"
            required
            ref={emailInputRef}
          />
          <ValidationError
            prefix="Email"
            field="email"
            errors={state.errors}
          />
        </div>

        <div className="field-wrap">
          <input
            id="name"
            type="text"
            name="name"
            placeholder="Full name"
            required
          />
          <ValidationError
            prefix="Name"
            field="name"
            errors={state.errors}
          />
        </div>
      </div>

      <div className="field-wrap">
        <textarea
          id="message"
          name="message"
          placeholder="What&apos;s up?"
          style={{ resize: "none" }}
          required
        />
        <ValidationError
          prefix="Message"
          field="message"
          errors={state.errors}
        />
      </div>

      <div className="contact-footer">
        <p className="contact-note"></p>
        <button type="submit" className="dark-button submit" disabled={state.submitting}>
          {state.submitting ? 'Sending...' : 'Send Message'}
        </button>
      </div>
    </form>
  );
}

export default ContactForm;
