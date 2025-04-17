/**
 * Login form validation and error handling enhancement
 * This script improves the user experience by providing better visual feedback
 * for authentication errors.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Get form elements
  const loginForm = document.querySelector('form[action*="login"]');
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
    // Mejorar los selectores para capturar todos los posibles mensajes de error
    const usernameErrorsNodeList = document.querySelectorAll('p.text-red-600, p.text-xs.text-red-600');
    const usernameErrors = Array.from(usernameErrorsNodeList).filter(el => {
      return el.textContent.includes('no encontrado') || el.textContent.includes('Usuario no encontrado') || 
             el.textContent.includes('Correo electrónico no encontrado');
    });
    
    const passwordErrorsNodeList = document.querySelectorAll('p.text-red-600, p.text-xs.text-red-600');
    const passwordErrors = Array.from(passwordErrorsNodeList).filter(el => {
      return el.textContent.includes('Contraseña incorrecta') || el.textContent.includes('Este campo es obligatorio');
    });

    // Apply visual feedback for username errors
    if (usernameErrors.length > 0) {
      usernameInput.classList.add('border-red-500');
      usernameInput.classList.remove('border-gray-200');
      usernameInput.focus();
      
      // Make sure error message is visible
      usernameErrors.forEach(error => {
        error.style.display = 'block';
      });
    }

    // Apply visual feedback for password errors
    if (passwordErrors.length > 0) {
      passwordInput.classList.add('border-red-500');
      passwordInput.classList.remove('border-gray-200');
      
      // Make sure error message is visible
      passwordErrors.forEach(error => {
        error.style.display = 'block';
      });
      
      if (!usernameErrors.length) {
        passwordInput.focus();
      }
    }
  }

  // Run error handling on page load
  handleFormErrors();

  // Add form submission handler to provide immediate feedback
  loginForm.addEventListener('submit', function(event) {
    // Clear previous error states
    usernameInput.classList.remove('border-red-500');
    passwordInput.classList.remove('border-red-500');
    
    // Basic validation
    let hasError = false;
    
    if (!usernameInput.value.trim()) {
      usernameInput.classList.add('border-red-500');
      hasError = true;
    }
    
    if (!passwordInput.value.trim()) {
      passwordInput.classList.add('border-red-500');
      hasError = true;
    }
    
    if (hasError) {
      event.preventDefault();
    }
  });
});