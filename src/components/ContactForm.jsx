import React from 'react';
import { useForm, ValidationError } from '@formspree/react';

// Make sure to run npm install @formspree/react
// For more help visit https://formspr.ee/react-help

function ContactForm() {
  const [state, handleSubmit] = useForm("mleqdbev");
  // if (state.succeeded) {
  //     return <p>Thanks for joining!</p>;
  // }

  const handleSubmitWithCallback = async (event) => {
    event.preventDefault();
    try {
      const result = await handleSubmit(event);
      window.location.href = "https://formspree.io/thanks?language=en";
    } catch (error) {
      console.error('Error submitting form:', error);
      // Handle the error here
    }
  };
  return (
    <form onSubmit={handleSubmitWithCallback}>
      <div className="form-container">
        <h2>Get In Touch!</h2>
        <div className='name-email'>
          <input
            id="email"
            type="email" 
            name="email"
            placeholder="Email"
            required
          />
          <ValidationError 
            prefix="Email" 
            field="email"
            errors={state.errors}
          />

          <input
            id="name"
            type="name" 
            name="name"
            placeholder="Name"
            required
          />
          <ValidationError 
            prefix="Name" 
            field="name"
            errors={state.errors}
          />
        </div>

        <textarea
          id="message"
          name="message"
          placeholder="Message"
          style={{ resize: "none" }}
          required
        />
        <ValidationError 
          prefix="Message" 
          field="message"
          errors={state.errors}
        />

        <button type="submit" className="dark-button submit" disabled={state.submitting}>
          Send
        </button>
      </div>
      
    </form>
  );
}

export default ContactForm;