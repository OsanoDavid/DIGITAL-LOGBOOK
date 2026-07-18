/**
 * ICTA Portal - Accessibility Suite (v3)
 * Implements: Sidebar Push Layout & Multi-Color Visibility Themes
 */

(function () {
    let currentFontSize = localStorage.getItem('acc-font-size') ? parseInt(localStorage.getItem('acc-font-size')) : 100;
    let isDyslexic = localStorage.getItem('acc-dyslexic') === 'true';
    let currentTheme = localStorage.getItem('acc-theme') || 'default';
    let activeModes = localStorage.getItem('acc-modes') ? JSON.parse(localStorage.getItem('acc-modes')) : {};
    let currentFontFamily = localStorage.getItem('acc-font-family') || '';

    const filterMap = {
        dark: 'invert(1) hue-rotate(180deg)',
        contrast: 'contrast(2.2) brightness(1.05)',
        grayscale: 'grayscale(1)',
        sepia: 'sepia(0.85) brightness(1.05)'
    };
    const btnMap = {
        dark: 'btn-dark', contrast: 'btn-contrast',
        grayscale: 'btn-gray', sepia: 'btn-sepia'
    };

    window.toggleAccPanel = function () {
        const panel = document.getElementById('accessibility-panel');
        if(!panel) return;
        const isOpening = !panel.classList.contains('active');
        if (isOpening) {
            panel.classList.add('active');
            document.body.classList.add('acc-sidebar-open');
        } else {
            panel.classList.remove('active');
            document.body.classList.remove('acc-sidebar-open');
        }
    };

    window.toggleAccSetting = function (setting) {
        const body = document.body;
        if (setting === 'dyslexic') {
            isDyslexic = !isDyslexic;
            if(isDyslexic) body.classList.add('acc-dyslexic');
            else body.classList.remove('acc-dyslexic');
            localStorage.setItem('acc-dyslexic', isDyslexic);
        }
    };

    window.setTheme = function (theme) {
        const body = document.body;
        const themeClass = `theme-${theme}`;

        if (theme !== 'default' && body.classList.contains(themeClass)) {
            body.classList.remove(themeClass);
            if(currentTheme !== 'default') speak("Default theme restored");
            currentTheme = 'default';
        } else {
            body.classList.remove('theme-red', 'theme-yellow', 'theme-blue');
            if (theme !== 'default') {
                body.classList.add(themeClass);
                speak(`${theme} high visibility theme activated`);
                currentTheme = theme;
            } else {
                if(currentTheme !== 'default') speak("Default theme restored");
                currentTheme = 'default';
            }
        }
        localStorage.setItem('acc-theme', currentTheme);
    };

    window.changeFontSize = function (delta) {
        currentFontSize += delta;
        if (currentFontSize < 80) currentFontSize = 80;
        if (currentFontSize > 220) currentFontSize = 220;
        applyFontSize();
        if (delta !== 0) speak('Font ' + currentFontSize + ' percent');
    };

    function applyFontSize() {
        document.documentElement.style.fontSize = currentFontSize + '%';
        const display = document.getElementById('acc-font-display');
        if (display) display.textContent = currentFontSize + '%';
        localStorage.setItem('acc-font-size', currentFontSize);
    }

    window.toggleDisplayMode = function (mode) {
        if (activeModes[mode]) {
            // Already active — turn OFF this mode
            delete activeModes[mode];
            speak(mode + ' off');
        } else {
            // Turn ON this mode
            activeModes[mode] = filterMap[mode];
            speak(mode + ' on');
        }
        localStorage.setItem('acc-modes', JSON.stringify(activeModes));
        reapplyFilters();
    };

    function buildCombinedFilter() {
        return Object.values(activeModes).join(' ');
    }

    function reapplyFilters() {
        const old = document.getElementById('acc-style-combined');
        if (old) old.remove();

        for(let mode in btnMap) {
            const btn = document.getElementById(btnMap[mode]);
            if (btn) {
                if(activeModes[mode]) btn.classList.add('mode-active');
                else btn.classList.remove('mode-active');
            }
        }

        const combined = buildCombinedFilter();
        if (!combined) return;

        const style = document.createElement('style');
        style.id = 'acc-style-combined';
        style.textContent =
            'body > *:not(#accessibility-panel):not(#accessibility-widget):not(#voice-overlay) {' +
            '  filter: ' + combined + ' !important;' +
            '}';
        document.head.appendChild(style);
    }

    // Font Family Switcher
    window.changeFont = function (family, silent) {
        const old = document.getElementById('acc-font-style');
        if (old) old.remove();
        
        currentFontFamily = family;
        localStorage.setItem('acc-font-family', currentFontFamily || '');
        
        if (!family) {
            if(!silent) speak('Default font restored');
            return;
        }
        const style = document.createElement('style');
        style.id = 'acc-font-style';
        style.textContent = 'body, body * { font-family: ' + family + ' !important; }';
        document.head.appendChild(style);
        if(!silent) speak('Font changed');
    };

    // Voice Assistant Core
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = SpeechRecognition ? new SpeechRecognition() : null;
    const synth = window.speechSynthesis;

    window.speak = function (text) {
        if (!synth) return;
        synth.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        utter.rate = 1.1;
        synth.speak(utter);
    };

    window.startVoiceAssistant = function () {
        if (!recognition) return;
        const overlay = document.getElementById('voice-overlay');
        if(overlay) overlay.style.display = 'flex';
        speak("Voice engine engaged. Command me.");
        recognition.start();

        recognition.onresult = function (event) {
            const command = event.results[0][0].transcript.toLowerCase();
            setTimeout(() => {
                processCommand(command);
                if(overlay) overlay.style.display = 'none';
            }, 800);
        };
        recognition.onerror = () => { if(overlay) overlay.style.display = 'none'; };
    };

    function processCommand(cmd) {
        if (cmd.includes('home')) window.location.href = "/";
        else if (cmd.includes('dashboard')) window.location.href = "/dashboard/";
        else if (cmd.includes('supervisor')) window.location.href = "/supervisor/";
        else if (cmd.includes('roster')) window.location.href = "/roster/bulk-assign/";
        else if (cmd.includes('red theme')) setTheme('red');
        else if (cmd.includes('yellow theme')) setTheme('yellow');
        else if (cmd.includes('blue theme')) setTheme('blue');
        else if (cmd.includes('default theme')) setTheme('default');
        else if (cmd.includes('bigger')) changeFontSize(20);
        else if (cmd.includes('smaller')) changeFontSize(-20);
        else speak("I recognize your voice but that path is not mapped yet.");
    }

    // ===== GEAR BUTTON SPIN ON CLICK =====
    const _origToggle = window.toggleAccPanel;
    window.toggleAccPanel = function () {
        const btn = document.getElementById('accessibility-btn');
        if (btn) {
            btn.classList.add('spinning');
            setTimeout(() => btn.classList.remove('spinning'), 520);
        }
        _origToggle();
    };

    function initPersistedSettings() {
        if (isDyslexic) document.body.classList.add('acc-dyslexic');
        if (currentTheme !== 'default') {
            const themeClass = `theme-${currentTheme}`;
            document.body.classList.add(themeClass);
        }
        applyFontSize();
        reapplyFilters();
        if (currentFontFamily) changeFont(currentFontFamily, true);
    }

    // ===== PAGE LOAD, SPROUT & NAVIGATION INTERCEPTOR =====
    document.addEventListener("DOMContentLoaded", function () {
        const loader = document.getElementById('system-page-loader');

        initPersistedSettings();

        // Collect all sproutable elements — any direct children of main sections
        function getSproutTargets() {
            const selectors = [
                'nav', 'header',
                'main > *', '.container > *', '.container-fluid > *',
                'section', 'article', '.card', '.row',
                'form', 'table', 'footer'
            ];
            const seen = new Set();
            const targets = [];
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    if (!el.closest('#system-page-loader') &&
                        !el.closest('#accessibility-panel') &&
                        !el.closest('#accessibility-widget') &&
                        !seen.has(el)) {
                        seen.add(el);
                        targets.push(el);
                    }
                });
            });
            return targets;
        }

        const sproutTargets = getSproutTargets();
        sproutTargets.forEach(el => {
            el.classList.add('sprout-auto');
        });

        const LOADER_DURATION = 350; 
        const SPROUT_DELAY = 160;  

        setTimeout(() => {
            if (loader) loader.classList.add('loaded');

            setTimeout(() => {
                sproutTargets.forEach((el, i) => {
                    setTimeout(() => {
                        el.classList.add('sprouted');
                    }, i * SPROUT_DELAY);
                });
            }, 100);
        }, LOADER_DURATION);

        // ===== NAVIGATION LINK INTERCEPTOR =====
        document.addEventListener('click', function (e) {
            const anchor = e.target.closest('a');
            if (anchor) {
                const href = anchor.getAttribute('href');
                const target = anchor.getAttribute('target');
                if (href &&
                    !href.startsWith('#') &&
                    !href.startsWith('javascript:') &&
                    !e.defaultPrevented &&
                    (!target || target === '_self') &&
                    !anchor.classList.contains('no-transition') &&
                    !anchor.hasAttribute('data-bs-toggle') &&
                    !anchor.hasAttribute('data-toggle')) {

                    e.preventDefault();
                    if (loader) loader.classList.remove('loaded');
                    document.querySelectorAll('.sprouted').forEach(el => el.classList.remove('sprouted'));
                    setTimeout(() => { window.location.href = href; }, 500);
                }
            }
        });

        // ===== FORM SUBMIT INTERCEPTOR =====
        document.addEventListener('submit', function (e) {
            const form = e.target;
            if (form && !form.classList.contains('no-transition')) {
                e.preventDefault();
                if (loader) loader.classList.remove('loaded');
                document.querySelectorAll('.sprouted').forEach(el => el.classList.remove('sprouted'));
                setTimeout(() => { form.submit(); }, 500);
            }
        });
    });
})();
