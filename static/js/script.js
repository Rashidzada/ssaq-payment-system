// Privacy Show/Hide Amounts Management
function applyPrivacyState(hide) {
  if (hide) {
    document.body.classList.add('hide-amounts');
  } else {
    document.body.classList.remove('hide-amounts');
  }

  // Update all toggle buttons on page
  document.querySelectorAll('.privacy-btn').forEach(function (btn) {
    if (hide) {
      btn.innerHTML = '<span class="privacy-icon">👁️</span> <span class="privacy-btn-text">Show Amounts</span>';
      btn.setAttribute('title', 'Click to show financial amounts');
    } else {
      btn.innerHTML = '<span class="privacy-icon">🙈</span> <span class="privacy-btn-text">Hide Amounts</span>';
      btn.setAttribute('title', 'Click to hide financial amounts');
    }
  });

  // Mask / unmask all money-val elements
  document.querySelectorAll('.money-val').forEach(function (el) {
    if (!el.getAttribute('data-original')) {
      el.setAttribute('data-original', el.textContent.trim());
    }
    if (hide) {
      el.textContent = 'Rs. •••••';
    } else {
      el.textContent = el.getAttribute('data-original');
    }
  });
}

function togglePrivacyMode() {
  const isCurrentlyHidden = document.body.classList.contains('hide-amounts');
  const nextHideState = !isCurrentlyHidden;
  localStorage.setItem('hideAmounts', nextHideState ? 'true' : 'false');
  applyPrivacyState(nextHideState);
}

document.addEventListener('DOMContentLoaded', function () {
  // 1. Initialize Privacy Mode (Default: OFF / Hidden = true)
  const savedPref = localStorage.getItem('hideAmounts');
  const shouldHide = savedPref === null ? true : savedPref === 'true';
  applyPrivacyState(shouldHide);

  // 2. Auto-dismiss flash messages after 4 seconds
  document.querySelectorAll('.flash').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity .4s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 4000);
  });
});

