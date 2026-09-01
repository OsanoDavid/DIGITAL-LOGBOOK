(function () {
    document.documentElement.classList.add('ui-transition-pending');
    const duration = 420;
    const getOverlay = () => document.getElementById('system-transition-overlay');
    let transitionTimer = null;

    const hideLoading = () => {
        if (transitionTimer) {
            window.clearTimeout(transitionTimer);
            transitionTimer = null;
        }
        document.body.classList.remove('page-leaving');
        getOverlay()?.classList.remove('is-visible');
    };

    const showLoading = () => { document.body.classList.add('page-leaving'); getOverlay()?.classList.add('is-visible'); };
    window.beginSmoothNavigation = (destination, delay = duration) => {
        showLoading();
        if (transitionTimer) window.clearTimeout(transitionTimer);
        transitionTimer = window.setTimeout(() => {
            window.location.href = destination;
        }, delay);
    };
    window.cancelSmoothNavigation = () => {
        hideLoading();
    };
    window.showSmoothToast = (toast, timeout = 4200) => {
        if (!toast) return;
        window.clearTimeout(toast._hideTimer);
        window.clearTimeout(toast._removeTimer);
        toast.classList.remove('is-hiding');
        toast.style.display = '';
        requestAnimationFrame(() => toast.classList.add('is-visible'));
        toast._hideTimer = window.setTimeout(() => {
            toast.classList.add('is-hiding');
            toast.classList.remove('is-visible');
            toast._removeTimer = window.setTimeout(() => {
                toast.remove();
            }, 400);
        }, timeout);
    };
    document.addEventListener('DOMContentLoaded', () => {
        document.body.classList.add('page-ready');
        document.documentElement.classList.remove('ui-transition-pending');
        const overlay = document.createElement('div');
        overlay.id = 'system-transition-overlay'; overlay.className = 'system-transition-overlay'; overlay.setAttribute('aria-hidden', 'true');
        overlay.innerHTML = '<div class="system-transition-card"><div class="system-transition-spinner"></div><div class="system-transition-title">KISII LOGBOOK</div><p class="system-transition-message">Preparing your workspace…</p><button type="button" class="system-transition-cancel" aria-label="Cancel loading">Cancel</button></div>';
        const cancelButton = overlay.querySelector('.system-transition-cancel');
        if (cancelButton) {
            cancelButton.addEventListener('click', () => window.cancelSmoothNavigation());
        }
        document.body.appendChild(overlay);
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape' && overlay.classList.contains('is-visible')) {
                window.cancelSmoothNavigation();
            }
        });
        document.addEventListener('click', event => {
            const link = event.target.closest('a');
            if (!link || event.defaultPrevented || link.classList.contains('no-transition')) return;
            const href = link.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('javascript:') || link.target === '_blank' || link.hasAttribute('download')) return;
            event.preventDefault(); window.beginSmoothNavigation(href);
        });
        document.addEventListener('submit', event => {
            const form = event.target;
            if (event.defaultPrevented || form.classList.contains('no-transition') || form.dataset.transitioning === 'true' || form.method.toLowerCase() === 'dialog') return;
            form.dataset.transitioning = 'true';
            const submitter = event.submitter || form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitter) { submitter.classList.add('is-submitting'); submitter.disabled = true; }
            event.preventDefault(); showLoading(); window.setTimeout(() => form.submit(), duration);
        });
    });
})();
