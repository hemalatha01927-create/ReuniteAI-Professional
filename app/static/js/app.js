(() => {
  const menu = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  if (menu && sidebar) {
    menu.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (event) => {
      if (window.innerWidth <= 900 && sidebar.classList.contains('open') && !sidebar.contains(event.target) && !menu.contains(event.target)) {
        sidebar.classList.remove('open');
      }
    });
  }
  document.querySelectorAll('.flash-close').forEach((button) => {
    button.addEventListener('click', () => button.closest('.flash')?.remove());
  });
  document.querySelectorAll('.upload-zone input[type=file]').forEach((input) => {
    input.addEventListener('change', () => {
      const label = input.closest('.upload-zone');
      const name = input.files?.[0]?.name;
      const title = label?.querySelector('b');
      if (name && title) title.textContent = name;
    });
  });
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const button = form.querySelector('button[type="submit"],button:not([type])');
      if (button && !button.dataset.noBusy) {
        button.dataset.originalText = button.textContent;
        button.disabled = true;
        button.textContent = 'Please wait…';
        window.setTimeout(() => {
          button.disabled = false;
          if (button.dataset.originalText) button.textContent = button.dataset.originalText;
        }, 5000);
      }
    });
  });
})();
