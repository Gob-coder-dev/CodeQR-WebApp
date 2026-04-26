// Language selection and text application. Text dictionaries live in language.js.
(function () {
  const app = window.QRApp || (window.QRApp = {});
  const languageStorageKey = "qr_language";

  function createI18n({ languageConfig, elements }) {
    if (!languageConfig) {
      throw new Error("Missing language configuration. Load language.js before i18n.js.");
    }

    const { supportedLanguages, translations } = languageConfig;
    const applyCallbacks = [];
    let currentLanguage = "en";
    let lastStatus = null;

    function hasTranslation(key) {
      return Boolean(translations[currentLanguage]?.[key] || translations.en[key]);
    }

    function translate(key, params = {}) {
      const template = translations[currentLanguage]?.[key] || translations.en[key] || key;
      return template.replace(/\{(\w+)\}/g, (_match, name) => params[name] ?? "");
    }

    function resolveMessage(messageOrKey, params = {}) {
      return hasTranslation(messageOrKey) ? translate(messageOrKey, params) : messageOrKey;
    }

    function getStoredLanguage() {
      try {
        return window.localStorage.getItem(languageStorageKey);
      } catch (_error) {
        return null;
      }
    }

    function storeLanguage(language) {
      try {
        window.localStorage.setItem(languageStorageKey, language);
      } catch (_error) {
        // Language selection still works for the current page when storage is unavailable.
      }
    }

    function chooseInitialLanguage() {
      const storedLanguage = getStoredLanguage();
      if (supportedLanguages[storedLanguage]) {
        return storedLanguage;
      }

      const browserLanguages = navigator.languages?.length ? navigator.languages : [navigator.language];
      for (const browserLanguage of browserLanguages) {
        const language = String(browserLanguage || "").toLowerCase().split("-")[0];
        if (supportedLanguages[language]) {
          return language;
        }
      }

      return "en";
    }

    function updateLanguageControls() {
      const language = supportedLanguages[currentLanguage];
      elements.languageButtonFlag.textContent = language.flag;
      elements.languageButtonCode.textContent = language.code;

      elements.languageMenuButtons.forEach((button) => {
        button.setAttribute("aria-current", String(button.dataset.language === currentLanguage));
      });
    }

    function applyTranslations() {
      document.documentElement.lang = currentLanguage;
      document.title = translate("meta.title");
      document
        .querySelector('meta[name="description"]')
        ?.setAttribute("content", translate("meta.description"));

      document.querySelectorAll("[data-i18n]").forEach((element) => {
        element.textContent = translate(element.dataset.i18n);
      });
      document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
        element.setAttribute("placeholder", translate(element.dataset.i18nPlaceholder));
      });
      document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
        element.setAttribute("aria-label", translate(element.dataset.i18nAriaLabel));
      });
      document.querySelectorAll("[data-i18n-alt]").forEach((element) => {
        element.setAttribute("alt", translate(element.dataset.i18nAlt));
      });

      updateLanguageControls();
      if (lastStatus) {
        elements.statusBox.textContent = resolveMessage(lastStatus.message, lastStatus.params);
      }
      if (!elements.resetDelight.hidden) {
        elements.resetDelight.textContent = translate("delight.reset");
      }
      applyCallbacks.forEach((callback) => callback());
    }

    function setLanguage(language) {
      if (!supportedLanguages[language]) {
        return;
      }

      currentLanguage = language;
      storeLanguage(language);
      applyTranslations();
    }

    function setLanguageMenuOpen(isOpen) {
      elements.languageMenu.hidden = !isOpen;
      elements.languageButton.setAttribute("aria-expanded", String(isOpen));
    }

    function setStatus(message, type = "info", params = {}) {
      lastStatus = { message, params };
      elements.statusBox.textContent = resolveMessage(message, lastStatus.params);
      elements.statusBox.dataset.state = type;
    }

    function bindEvents() {
      elements.languageButton.addEventListener("click", () => {
        setLanguageMenuOpen(elements.languageMenu.hidden);
      });
      elements.languageMenuButtons.forEach((button) => {
        button.addEventListener("click", () => {
          setLanguage(button.dataset.language);
          setLanguageMenuOpen(false);
        });
      });
      document.addEventListener("click", (event) => {
        if (elements.languageButton.contains(event.target) || elements.languageMenu.contains(event.target)) {
          return;
        }

        setLanguageMenuOpen(false);
      });
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          setLanguageMenuOpen(false);
        }
      });
    }

    function addApplyListener(callback) {
      applyCallbacks.push(callback);
    }

    function init() {
      currentLanguage = chooseInitialLanguage();
      applyTranslations();
    }

    return {
      addApplyListener,
      applyTranslations,
      bindEvents,
      init,
      resolveMessage,
      setLanguage,
      setLanguageMenuOpen,
      setStatus,
      translate,
    };
  }

  app.createI18n = createI18n;
}());
