/**
 * Login form validation and error handling enhancement
 * This script improves the user experience by providing better visual feedback
 * for authentication errors.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Get form elements
  const loginForm = document.getElementById('login-form');
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const togglePassword = document.getElementById('toggle-password');
  
  if (!loginForm || !usernameInput || !passwordInput) return;
  
  // Toggle password visibility
  if (togglePassword) {
    togglePassword.addEventListener('click', function () {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      
      // Toggle eye icon
      const eyeIcon = this.querySelector('i');
      if (eyeIcon) {
        eyeIcon.classList.toggle('fa-eye');
        eyeIcon.classList.toggle('fa-eye-slash');
      }
    });
  }

  // Enhanced error handling
  function handleFormErrors() {
    // Check for backend form errors
    const hasUsernameErrors = usernameInput.closest('div').querySelectorAll('.text-xs.text-red-600').length > 0;
    const hasPasswordErrors = passwordInput.closest('div').querySelectorAll('.text-xs.text-red-600').length > 0;
    
    // Check for general error messages that might contain specific error text
    const allErrorMessages = document.querySelectorAll('p.text-red-600, p.text-xs.text-red-600, p.text-center.text-sm.text-red-600');
    
    allErrorMessages.forEach(errorMsg => {
      const errorText = errorMsg.textContent.toLowerCase();
      
      // Username/email related errors
      if (errorText.includes('no encontrado') || 
          errorText.includes('usuario no encontrado') || 
          errorText.includes('correo electrónico no encontrado') ||
          errorText.includes('usuario o correo')) {
        usernameInput.classList.add('border-red-500');
        usernameInput.classList.remove('border-gray-200');
        
        // If this error is not already under the username field, add it
        if (!errorMsg.closest('div').contains(usernameInput)) {
          const errorContainer = usernameInput.closest('div');
          const existingErrors = errorContainer.querySelectorAll('.text-xs.text-red-600');
          
          // Only add if there's no existing error with the same text
          let errorExists = false;
          existingErrors.forEach(existing => {
            if (existing.textContent === errorMsg.textContent) {
              errorExists = true;
            }
          });
          
          if (!errorExists && !hasUsernameErrors) {
            const newError = document.createElement('p');
            newError.className = 'mt-1 text-xs text-red-600';
            newError.textContent = errorMsg.textContent;
            errorContainer.appendChild(newError);
          }
        }
      }
      
      // Password related errors
      if (errorText.includes('contraseña incorrecta') || 
          errorText.includes('olvidaste tu contraseña') ||
          errorText.includes('campo obligatorio') && errorMsg.closest('div')?.contains(passwordInput)) {
        passwordInput.classList.add('border-red-500');
        passwordInput.classList.remove('border-gray-200');
        
        // If this error is not already under the password field, add it
        if (!errorMsg.closest('div').contains(passwordInput)) {
          const errorContainer = passwordInput.closest('div');
          const existingErrors = errorContainer.querySelectorAll('.text-xs.text-red-600');
          
          // Only add if there's no existing error with the same text
          let errorExists = false;
          existingErrors.forEach(existing => {
            if (existing.textContent === errorMsg.textContent) {
              errorExists = true;
            }
          });
          
          if (!errorExists && !hasPasswordErrors) {
            const newError = document.createElement('p');
            newError.className = 'mt-1 text-xs text-red-600';
            newError.textContent = errorMsg.textContent;
            errorContainer.appendChild(newError);
          }
        }
      }
    });
    
    // Focus on the first field with error
    if (usernameInput.classList.contains('border-red-500')) {
      usernameInput.focus();
    } else if (passwordInput.classList.contains('border-red-500')) {
      passwordInput.focus();
    }
  }

  // Run error handling on page load
  handleFormErrors();

  // Add form submission handler to provide immediate feedback
  loginForm.addEventListener('submit', function(event) {
    let hasError = false;

    // Clear previous error states
    usernameInput.classList.remove('border-red-500');
    passwordInput.classList.remove('border-red-500');

    // Remove any dynamically added error messages
    const errorMessages = loginForm.querySelectorAll('.text-xs.text-red-600');
    errorMessages.forEach(msg => {
      if (!msg.hasAttribute('data-original')) {
        msg.remove();
      }
    });
    
    // Basic validation
    if (!usernameInput.value.trim()) {
      usernameInput.classList.add('border-red-500');
      const errorContainer = usernameInput.closest('div');
      const newError = document.createElement('p');
      newError.className = 'mt-1 text-xs text-red-600';
      newError.textContent = 'Este campo es obligatorio';
      errorContainer.appendChild(newError);
      hasError = true;
    }
    
    if (!passwordInput.value.trim()) {
      passwordInput.classList.add('border-red-500');
      const errorContainer = passwordInput.closest('div');
      const newError = document.createElement('p');
      newError.className = 'mt-1 text-xs text-red-600';
      newError.textContent = 'Este campo es obligatorio';
      errorContainer.appendChild(newError);
      hasError = true;
    }
    
    if (hasError) {
      event.preventDefault();
      // Focus on the first field with error
      if (usernameInput.classList.contains('border-red-500')) {
        usernameInput.focus();
      } else if (passwordInput.classList.contains('border-red-500')) {
        passwordInput.focus();
      }
    }
  });
});