(() => {
  if (document.getElementById('pp-alert-banner')) return;

  const banner = document.createElement('div');
  banner.id = 'pp-alert-banner';
  banner.textContent =
    '⚠️  Suspicious page detected. Check your notifications! ⚠️';

  Object.assign(banner.style, {
    position: 'fixed',
    top: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    maxWidth: '90%',
    width: '400px',
    zIndex: '999999',
    background: '#dc3545', // Bootstrap-style crimson
    color: 'white',
    fontSize: '15px',
    fontWeight: '600',
    padding: '12px 20px',
    textAlign: 'center',
    fontFamily: 'Roboto, sans-serif',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    pointerEvents: 'none', // prevent interaction
  });

  document.body.appendChild(banner);
  return null;
})();
