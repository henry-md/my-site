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
      await handleSubmit(event);
      window.location.href = "https://formspree.io/thanks?language=en";
    } catch (error) {
      console.error('Error submitting form:', error);
      // Handle the error here
    }
  };
  return (
    <form onSubmit={handleSubmitWithCallback}>
      <div className="form-container">
        <h2>Let&apos;s Get In Touch!</h2>
        <p className="contact-intro">Messages will go right to my personal inbox.</p>
        <div className='name-email'>
          <input
            id="email"
            type="email" 
            name="email"
            placeholder="Email address"
            required
          />
          <ValidationError 
            prefix="Email" 
            field="email"
            errors={state.errors}
          />

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

        <textarea
          id="message"
          name="message"
          placeholder="Tell me what you&apos;re building"
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
