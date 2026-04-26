// Contextual easter eggs. Search "delight" to adjust these frontend-only rules.
(function () {
  const app = window.QRApp || (window.QRApp = {});
  const ownSiteHost = "qr-code-converter.onrender.com";
  const resetBurstWindowMs = 10000;

  function createDelights({ elements, colorUtils, formOptions, i18n }) {
    let resetClickCount = 0;
    let resetClickTimer = null;
    const transientDelights = {};

    function parsePossibleUrl(value) {
      const trimmedValue = (value || "").trim();
      if (!trimmedValue) {
        return null;
      }

      const candidates = [trimmedValue];
      if (trimmedValue.startsWith("/")) {
        candidates.push(`https://${ownSiteHost}${trimmedValue}`);
      }
      if (/^(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i.test(trimmedValue)) {
        candidates.push(`http://${trimmedValue}`);
      }

      for (const candidate of candidates) {
        try {
          return new URL(candidate);
        } catch (_error) {
          // Keep trying lightweight URL normalizations.
        }
      }

      return null;
    }

    function isRickrollUrl(content) {
      const normalizedContent = formOptions.normalizeText(content);
      return normalizedContent.includes("dqw4w9wgxcq");
    }

    function isOwnSiteUrl(content) {
      const url = parsePossibleUrl(content);
      if (!url) {
        return false;
      }

      const pathname = url.pathname.replace(/\/+$/, "") || "/";
      return url.hostname === ownSiteHost && pathname === "/";
    }

    function isOwnHealthUrl(content) {
      const normalizedContent = formOptions.normalizeText(content);
      const url = parsePossibleUrl(content);
      const pathname = url?.pathname.replace(/\/+$/, "") || "";
      return normalizedContent === "/health" || (url?.hostname === ownSiteHost && pathname === "/health");
    }

    function isLocalhostUrl(content) {
      const url = parsePossibleUrl(content);
      return ["localhost", "127.0.0.1", "::1"].includes(url?.hostname);
    }

    function isQrGoogleSearch(content) {
      const url = parsePossibleUrl(content);
      if (!url || !url.hostname.includes("google.") || url.pathname !== "/search") {
        return false;
      }

      const query = formOptions.normalizeText(url.searchParams.get("q") || "");
      return query.includes("qr code") || query.includes("qrcode");
    }

    function normalizeSearchText(value) {
      return formOptions
        .normalizeText(value)
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
    }

    function normalizePhrase(value) {
      return normalizeSearchText(value)
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
    }

    function isTeamPepsUrl(content) {
      const url = parsePossibleUrl(content);
      if (!url || url.protocol !== "https:") {
        return false;
      }

      const pathname = url.pathname.replace(/\/+$/, "") || "/";
      if (url.hostname === "teampeps.fr" && pathname === "/") {
        return true;
      }

      return url.hostname === "liquipedia.net" && pathname.toLowerCase() === "/overwatch/team_peps";
    }

    function isClairObscurContact({ qrType, contactFirstName, contactOrganization }) {
      if (qrType !== "contact" || normalizeSearchText(contactFirstName) !== "francois") {
        return false;
      }

      return [
        "clair obscur expedition 33",
        "clair obscur",
        "expedition 33",
      ].includes(normalizePhrase(contactOrganization));
    }

    function isHelldiversWifi({ qrType, wifiSsid, wifiPassword }) {
      if (qrType !== "wifi") {
        return false;
      }

      const normalizedSsid = normalizeSearchText(wifiSsid);
      const normalizedPassword = normalizeSearchText(wifiPassword);
      return (
        ["liber-tea", "a cup of liber-tea"].includes(normalizedSsid) &&
        (wifiPassword.trim() === "\u2191\u2192\u2193\u2193\u2193" ||
          normalizedPassword === "up right down down down")
      );
    }

    const delightRules = [
      {
        id: "rickroll-content",
        priority: 100,
        target: "content",
        tone: "orange",
        messageKey: "delight.rickGive",
        when: ({ content }) => isRickrollUrl(content),
      },
      {
        id: "rickroll-filename",
        priority: 100,
        target: "filename",
        tone: "orange",
        messageKey: "delight.rickGive",
        when: ({ filename }) => filename === "rickroll",
      },
      {
        id: "rickroll-filename-followup",
        priority: 101,
        target: "filename",
        tone: "orange",
        messageKey: "delight.rickDown",
        when: ({ content, filename }) => filename === "rickroll" && isRickrollUrl(content),
      },
      {
        id: "health",
        priority: 95,
        target: "content",
        tone: "badge",
        messageKey: "delight.health",
        when: ({ content }) => isOwnHealthUrl(content),
      },
      {
        id: "qrception",
        priority: 90,
        target: "content",
        tone: "badge",
        messageKey: "delight.qrception",
        when: ({ content }) => isOwnSiteUrl(content),
      },
      {
        id: "google-qr-search",
        priority: 85,
        target: "content",
        tone: "subtle",
        messageKey: "delight.google",
        when: ({ content }) => isQrGoogleSearch(content),
      },
      {
        id: "team-peps",
        priority: 84,
        target: "content",
        tone: "gold",
        messageKey: "delight.teamPeps",
        when: ({ qrType, content }) => qrType === "text" && isTeamPepsUrl(content),
      },
      {
        id: "localhost",
        priority: 80,
        target: "content",
        tone: "red",
        messageKey: "delight.localhost",
        when: ({ content }) => isLocalhostUrl(content),
      },
      {
        id: "france-palette",
        priority: 75,
        target: "color",
        tone: "france",
        messageKey: "delight.france",
        when: () => colorUtils.hasFrenchPalette(),
      },
      {
        id: "hidden-qr",
        priority: 70,
        target: "color",
        tone: "orange",
        messageKey: "delight.hiddenQr",
        when: () => colorUtils.foregroundMatchesBackground(),
      },
      {
        id: "clair-obscur",
        priority: 70,
        target: "contact",
        tone: "orange",
        messageKey: "delight.clairObscur",
        when: (context) => isClairObscurContact(context),
      },
      {
        id: "helldivers",
        priority: 70,
        target: "wifi",
        tone: "dark",
        messageKey: "delight.helldivers",
        when: (context) => isHelldiversWifi(context),
      },
      {
        id: "answer-42",
        priority: 65,
        target: "content",
        tone: "badge",
        messageKey: "delight.answer42",
        when: ({ normalizedContent }) => normalizedContent === "42",
      },
      {
        id: "hello",
        priority: 60,
        target: "content",
        tone: "subtle",
        messageKey: "delight.hello",
        when: ({ normalizedContent }) => normalizedContent === "bonjour",
      },
      {
        id: "secret-file",
        priority: 55,
        target: "filename",
        tone: "subtle",
        messageKey: "delight.secret",
        when: ({ filename }) => filename === "secret",
      },
      {
        id: "test-file",
        priority: 50,
        target: "filename",
        tone: "red",
        messageKey: "delight.test",
        when: ({ filename }) => filename === "test",
      },
      {
        id: "default-file",
        priority: 45,
        target: "filename",
        tone: "subtle",
        messageKey: "delight.defaultFile",
        when: ({ filename }) => filename === "qr-code",
      },
    ];

    function buildDelightContext() {
      const content = formOptions.activeContentValue();

      return {
        qrType: elements.qrTypeField.value,
        content,
        normalizedContent: formOptions.normalizeText(content),
        filename: formOptions.normalizeFilename(elements.filenameField.value),
        contactFirstName: elements.contactFirstNameField?.value || "",
        contactOrganization: elements.contactOrgField?.value || "",
        wifiSsid: elements.wifiSsidField?.value || "",
        wifiPassword: elements.wifiPasswordField?.value || "",
        foregroundColor: colorUtils.normalizeHexColor(
          elements.foregroundHexField.value || elements.foregroundColorField.value,
        ),
        backgroundColor: colorUtils.normalizeHexColor(
          elements.backgroundHexField.value || elements.backgroundColorField.value,
        ),
      };
    }

    function renderDelight(targetName, delight) {
      const target = elements.delightTargets[targetName];
      if (!target) {
        return;
      }

      if (!delight) {
        target.hidden = true;
        target.textContent = "";
        target.removeAttribute("data-tone");
        return;
      }

      target.textContent = i18n.resolveMessage(delight.messageKey || delight.message);
      target.dataset.tone = delight.tone || "subtle";
      target.hidden = false;
    }

    function clearDelightTargets() {
      Object.keys(elements.delightTargets).forEach((targetName) => {
        renderDelight(targetName, null);
      });
    }

    function showTransientDelight(delight, duration = 4200) {
      const targetName = delight.target || "content";
      transientDelights[targetName] = {
        ...delight,
        target: targetName,
        expiresAt: Date.now() + duration,
      };
      evaluate();
    }

    function evaluate() {
      const context = buildDelightContext();
      const delightsByTarget = {};

      delightRules.forEach((rule) => {
        if (!rule.when(context)) {
          return;
        }

        const targetName = rule.target || "content";
        const currentDelight = delightsByTarget[targetName];
        if (!currentDelight || rule.priority > currentDelight.priority) {
          delightsByTarget[targetName] = rule;
        }
      });

      Object.entries(transientDelights).forEach(([targetName, delight]) => {
        if (delight.expiresAt <= Date.now()) {
          delete transientDelights[targetName];
          return;
        }

        delightsByTarget[targetName] = delight;
      });

      clearDelightTargets();
      Object.entries(delightsByTarget).forEach(([targetName, delight]) => {
        renderDelight(targetName, delight);
      });
    }

    function registerResetClick() {
      resetClickCount += 1;
      window.clearTimeout(resetClickTimer);
      resetClickTimer = window.setTimeout(() => {
        resetClickCount = 0;
        elements.resetDelight.hidden = true;
        elements.resetDelight.textContent = "";
      }, resetBurstWindowMs);

      if (resetClickCount >= 10) {
        elements.resetDelight.textContent = i18n.translate("delight.reset");
        elements.resetDelight.hidden = false;
      }
    }

    return {
      evaluate,
      registerResetClick,
      showTransientDelight,
    };
  }

  app.createDelights = createDelights;
}());
