const form = document.querySelector("#qr-form");
const submitButton = document.querySelector("#submit-button");
const statusBox = document.querySelector("#status");
const qrTypeField = document.querySelector("#qr-type");
const qrTypeFieldGroups = document.querySelectorAll("[data-qr-type-fields]");
const textField = document.querySelector("#text");
const wifiSecurityField = document.querySelector("#wifi-security");
const wifiPasswordGroup = document.querySelector("#wifi-password-field");
const filenameField = document.querySelector("#filename");
const outputFormatField = document.querySelector("#output-format");
const errorCorrectionField = document.querySelector("#error-correction");
const borderSizeField = document.querySelector("#border-size");
const colorModeField = document.querySelector("#color-mode");
const foregroundColorField = document.querySelector("#foreground-color");
const foregroundHexField = document.querySelector("#foreground-color-hex");
const foregroundColor2Field = document.querySelector("#foreground-color-2");
const foregroundHex2Field = document.querySelector("#foreground-color-2-hex");
const backgroundColorField = document.querySelector("#background-color");
const backgroundHexField = document.querySelector("#background-color-hex");
const secondaryColorGroup = document.querySelector("#secondary-color-field");
const backgroundColorGroup = document.querySelector("#background-color-field");
const transparentBackgroundField = document.querySelector("#transparent-background");
const moduleStyleField = document.querySelector("#module-style");
const eyeStyleField = document.querySelector("#eye-style");
const qualityField = document.querySelector("#quality");
const logoField = document.querySelector("#logo");
const logoSizeGroup = document.querySelector("#logo-size-field");
const logoSizeField = document.querySelector("#logo-size");
const logoSizeOutput = document.querySelector("#logo-size-output");
const resetOptionsButton = document.querySelector("#reset-options");
const preview = document.querySelector("#preview");
const previewImage = document.querySelector("#preview-image");
const downloadButton = document.querySelector("#download-button");
const copyButton = document.querySelector("#copy-button");
const delightTargets = {
  content: document.querySelector("#content-delight"),
  filename: document.querySelector("#filename-delight"),
  color: document.querySelector("#color-delight"),
};
const resetDelight = document.querySelector("#reset-delight");

const defaultOptions = {
  foregroundColor: "#000000",
  foregroundColor2: "#0f766e",
  backgroundColor: "#ffffff",
  outputFormat: "png",
  errorCorrection: "medium",
  borderSize: "standard",
  colorMode: "solid",
  moduleStyle: "square",
  eyeStyle: "square",
  quality: "medium",
  logoSize: "22",
  transparentBackground: false,
};
const maxLogoBytes = 2 * 1024 * 1024;
const hexColorPattern = /^#[0-9a-fA-F]{6}$/;
const ownSiteHost = "qr-code-converter.onrender.com";
const resetBurstWindowMs = 10000;
const contentRequirements = {
  text: {
    selector: "#text",
    message: "Ajoutez un lien ou un texte d'abord.",
  },
  wifi: {
    selector: "#wifi-ssid",
    message: "Ajoutez le nom du reseau Wi-Fi.",
  },
  email: {
    selector: "#email-to",
    message: "Ajoutez le destinataire de l'email.",
  },
  phone: {
    selector: "#phone-number",
    message: "Ajoutez un numero de telephone.",
  },
  sms: {
    selector: "#sms-number",
    message: "Ajoutez le numero de telephone du SMS.",
  },
  contact: {
    selector: "#contact-name",
    message: "Ajoutez le nom du contact.",
  },
  location: {
    selector: "#location-latitude",
    secondarySelector: "#location-longitude",
    message: "Ajoutez une latitude et une longitude.",
  },
};
let currentPreview = null;
let resetClickCount = 0;
let resetClickTimer = null;
const transientDelights = {};

const colorControls = new Set([
  foregroundColorField,
  foregroundHexField,
  foregroundColor2Field,
  foregroundHex2Field,
  backgroundColorField,
  backgroundHexField,
]);

function setStatus(message, type = "info") {
  statusBox.textContent = message;
  statusBox.dataset.state = type;
}

function fallbackName(rawName, extension = "png") {
  const value = (rawName || "").trim();
  if (!value) {
    return `qr-code.${extension}`;
  }

  return value.toLowerCase().endsWith(`.${extension}`) ? value : `${value}.${extension}`;
}

function extractFilename(contentDisposition) {
  if (!contentDisposition) {
    return null;
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match) {
    return decodeURIComponent(utf8Match[1]);
  }

  const simpleMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  return simpleMatch ? simpleMatch[1] : null;
}

function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(() => window.URL.revokeObjectURL(url), 0);
}

function normalizeHexColor(value) {
  const trimmedValue = value.trim();
  const prefixedValue = trimmedValue.startsWith("#") ? trimmedValue : `#${trimmedValue}`;

  return hexColorPattern.test(prefixedValue) ? prefixedValue.toUpperCase() : null;
}

function normalizeText(value) {
  return (value || "").trim().replace(/\s+/g, " ").toLowerCase();
}

function normalizeFilename(value) {
  const normalizedValue = normalizeText(value);
  return normalizedValue.replace(/\.(png|svg)$/i, "");
}

function activeContentValue() {
  return qrTypeField.value === "text" ? textField.value.trim() : "";
}

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
  const normalizedContent = normalizeText(content);
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
  const normalizedContent = normalizeText(content);
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

  const query = normalizeText(url.searchParams.get("q") || "");
  return query.includes("qr code") || query.includes("qrcode");
}

function currentColorValues() {
  const colors = [
    normalizeHexColor(foregroundHexField.value || foregroundColorField.value),
  ];

  if (usesGradientColor()) {
    colors.push(normalizeHexColor(foregroundHex2Field.value || foregroundColor2Field.value));
  }

  if (!transparentBackgroundField.checked) {
    colors.push(normalizeHexColor(backgroundHexField.value || backgroundColorField.value));
  }

  return colors.filter(Boolean);
}

function hasFrenchPalette() {
  const colors = currentColorValues();
  const hasWhite = colors.includes("#FFFFFF");
  const hasRed = colors.some((color) => ["#FF0000", "#EF4135"].includes(color));
  const hasBlue = colors.some((color) => ["#0000FF", "#0055A4"].includes(color));

  return hasWhite && hasRed && hasBlue;
}

function isColorControl(control) {
  return colorControls.has(control);
}

function syncHexFromPicker(colorField, hexField) {
  hexField.value = colorField.value.toUpperCase();
}

function syncPickerFromHex(colorField, hexField) {
  const normalizedValue = normalizeHexColor(hexField.value);
  if (!normalizedValue) {
    return false;
  }

  colorField.value = normalizedValue.toLowerCase();
  hexField.value = normalizedValue;
  return true;
}

function clearCurrentPreview() {
  if (currentPreview?.url) {
    window.URL.revokeObjectURL(currentPreview.url);
  }

  currentPreview = null;
  preview.hidden = true;
  previewImage.removeAttribute("src");
  downloadButton.disabled = true;
  copyButton.disabled = true;
}

function setCurrentPreview(blob, filename) {
  clearCurrentPreview();
  const url = window.URL.createObjectURL(blob);
  currentPreview = { blob, filename, url };
  previewImage.src = url;
  preview.hidden = false;
  downloadButton.disabled = false;
  copyButton.disabled = false;
}

function updateLogoSizeOutput() {
  logoSizeOutput.value = `${logoSizeField.value}%`;
  logoSizeOutput.textContent = `${logoSizeField.value}%`;
}

function setOptionGroupVisibility(group, isVisible) {
  group.hidden = !isVisible;
  group.querySelectorAll("input, select, textarea").forEach((control) => {
    control.disabled = !isVisible;
  });
}

function usesGradientColor() {
  return colorModeField.value !== "solid";
}

function updateQrTypeFields() {
  qrTypeFieldGroups.forEach((group) => {
    setOptionGroupVisibility(group, group.dataset.qrTypeFields === qrTypeField.value);
  });
  setOptionGroupVisibility(
    wifiPasswordGroup,
    qrTypeField.value === "wifi" && wifiSecurityField.value !== "nopass",
  );
}

function updateConditionalOptions() {
  setOptionGroupVisibility(secondaryColorGroup, usesGradientColor());
  setOptionGroupVisibility(backgroundColorGroup, !transparentBackgroundField.checked);
  const hasLogo = logoField.files.length > 0;
  setOptionGroupVisibility(logoSizeGroup, hasLogo);
  if (hasLogo) {
    errorCorrectionField.value = "high";
  }
}

function validateQrContent() {
  const requirement = contentRequirements[qrTypeField.value] || contentRequirements.text;
  const field = document.querySelector(requirement.selector);
  const secondaryField = requirement.secondarySelector
    ? document.querySelector(requirement.secondarySelector)
    : null;

  if (!field.value.trim() || (secondaryField && !secondaryField.value.trim())) {
    setStatus(requirement.message, "error");
    field.focus();
    return false;
  }

  return true;
}

// Contextual delights. Search "delight" to adjust these lightweight frontend-only rules.
const delightRules = [
  {
    id: "rickroll-content",
    priority: 100,
    target: "content",
    tone: "orange",
    message: "Never gonna give you up...",
    when: ({ content }) => isRickrollUrl(content),
  },
  {
    id: "rickroll-filename",
    priority: 100,
    target: "filename",
    tone: "orange",
    message: "Never gonna give you up...",
    when: ({ filename }) => filename === "rickroll",
  },
  {
    id: "rickroll-filename-followup",
    priority: 101,
    target: "filename",
    tone: "orange",
    message: "Never gonna let you down...",
    when: ({ content, filename }) => filename === "rickroll" && isRickrollUrl(content),
  },
  {
    id: "health",
    priority: 95,
    target: "content",
    tone: "badge",
    message: "Le site respire encore. \u2665",
    when: ({ content }) => isOwnHealthUrl(content),
  },
  {
    id: "qrception",
    priority: 90,
    target: "content",
    tone: "badge",
    message: "QRception \u2665",
    when: ({ content }) => isOwnSiteUrl(content),
  },
  {
    id: "google-qr-search",
    priority: 85,
    target: "content",
    tone: "subtle",
    message: "Un QR code qui cherche un QR code ?",
    when: ({ content }) => isQrGoogleSearch(content),
  },
  {
    id: "localhost",
    priority: 80,
    target: "content",
    tone: "red",
    message: "Mode d\u00e9veloppeur d\u00e9tect\u00e9.",
    when: ({ content }) => isLocalhostUrl(content),
  },
  {
    id: "france-palette",
    priority: 75,
    target: "color",
    tone: "france",
    message: "\u00c7a c'est ma France ! Baguette ! Fromage !",
    when: () => hasFrenchPalette(),
  },
  {
    id: "hidden-qr",
    priority: 70,
    target: "color",
    tone: "orange",
    message: "Le QR code joue \u00e0 cache-cache ?",
    when: ({ foregroundColor, backgroundColor }) =>
      !transparentBackgroundField.checked &&
      Boolean(foregroundColor) &&
      Boolean(backgroundColor) &&
      foregroundColor === backgroundColor,
  },
  {
    id: "answer-42",
    priority: 65,
    target: "content",
    tone: "badge",
    message: "Mais oui ! C'est une super r\u00e9ponse !",
    when: ({ normalizedContent }) => normalizedContent === "42",
  },
  {
    id: "hello",
    priority: 60,
    target: "content",
    tone: "subtle",
    message: "Bonjour \u00e0 toi aussi.",
    when: ({ normalizedContent }) => normalizedContent === "bonjour",
  },
  {
    id: "secret-file",
    priority: 55,
    target: "filename",
    tone: "subtle",
    message: "un QRcode confidenciel ?",
    when: ({ filename }) => filename === "secret",
  },
  {
    id: "test-file",
    priority: 50,
    target: "filename",
    tone: "red",
    message: "Encore un test, comme toujours...",
    when: ({ filename }) => filename === "test",
  },
  {
    id: "default-file",
    priority: 45,
    target: "filename",
    tone: "subtle",
    message: "Original. Tr\u00e8s original.",
    when: ({ filename }) => filename === "qr-code",
  },
];

function buildDelightContext() {
  const content = activeContentValue();

  return {
    content,
    normalizedContent: normalizeText(content),
    filename: normalizeFilename(filenameField.value),
    foregroundColor: normalizeHexColor(foregroundHexField.value || foregroundColorField.value),
    backgroundColor: normalizeHexColor(backgroundHexField.value || backgroundColorField.value),
  };
}

function renderDelight(targetName, delight) {
  const target = delightTargets[targetName];
  if (!target) {
    return;
  }

  if (!delight) {
    target.hidden = true;
    target.textContent = "";
    target.removeAttribute("data-tone");
    return;
  }

  target.textContent = delight.message;
  target.dataset.tone = delight.tone || "subtle";
  target.hidden = false;
}

function clearDelightTargets() {
  Object.keys(delightTargets).forEach((targetName) => {
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
  evaluateDelights();
}

function evaluateDelights() {
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
    resetDelight.hidden = true;
    resetDelight.textContent = "";
  }, resetBurstWindowMs);

  if (resetClickCount >= 10) {
    resetDelight.textContent = "Encore ? Le bouton commence \u00e0 te conna\u00eetre \u00e0 force.";
    resetDelight.hidden = false;
  }
}

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("L'image n'a pas pu etre preparee."));
    image.src = url;
  });
}

async function convertSvgBlobToPng(svgBlob) {
  const url = window.URL.createObjectURL(svgBlob);
  try {
    const image = await loadImage(url);
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d");
    context.drawImage(image, 0, 0);

    return await new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error("La copie du SVG a echoue."));
        }
      }, "image/png");
    });
  } finally {
    window.URL.revokeObjectURL(url);
  }
}

async function copyCurrentPreview() {
  if (!currentPreview) {
    return;
  }

  if (!navigator.clipboard?.write || !window.ClipboardItem) {
    setStatus("La copie d'image n'est pas disponible dans ce navigateur.", "error");
    return;
  }

  try {
    const blob =
      currentPreview.blob.type === "image/svg+xml"
        ? await convertSvgBlobToPng(currentPreview.blob)
        : currentPreview.blob;

    await navigator.clipboard.write([
      new ClipboardItem({
        "image/png": blob,
      }),
    ]);
    setStatus("Image copiee dans le presse-papiers.", "success");
  } catch (error) {
    setStatus(error.message || "La copie a echoue.", "error");
  }
}

async function handleSubmit(event) {
  event.preventDefault();

  const text = textField.value.trim();
  const filename = filenameField.value.trim();
  const logoFile = logoField.files[0];

  updateQrTypeFields();
  updateConditionalOptions();

  if (!validateQrContent()) {
    return;
  }

  if (logoFile && logoFile.size > maxLogoBytes) {
    setStatus("Le logo doit faire 2 Mo maximum.", "error");
    logoField.focus();
    return;
  }

  if (!syncPickerFromHex(foregroundColorField, foregroundHexField)) {
    setStatus("La couleur du QR code doit etre au format hexadecimal, par exemple #000000.", "error");
    foregroundHexField.focus();
    return;
  }

  if (usesGradientColor() && !syncPickerFromHex(foregroundColor2Field, foregroundHex2Field)) {
    setStatus("La couleur secondaire doit etre au format hexadecimal, par exemple #0F766E.", "error");
    foregroundHex2Field.focus();
    return;
  }

  if (!transparentBackgroundField.checked && !syncPickerFromHex(backgroundColorField, backgroundHexField)) {
    setStatus("La couleur du fond doit etre au format hexadecimal, par exemple #FFFFFF.", "error");
    backgroundHexField.focus();
    return;
  }

  submitButton.disabled = true;
  setStatus("Generation de l'apercu...", "loading");

  try {
    const formData = new FormData(form);
    formData.set("text", text);
    formData.set("filename", filename);

    if (!logoFile) {
      formData.delete("logo");
    }

    const response = await fetch("/api/qr-code", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => null);
      const errorMessage = errorPayload?.error || "Le QR code n'a pas pu etre genere.";
      throw new Error(errorMessage);
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("Content-Disposition");
    const extension = outputFormatField.value === "svg" ? "svg" : "png";
    const downloadName = extractFilename(contentDisposition) || fallbackName(filename, extension);

    setCurrentPreview(blob, downloadName);
    setStatus(`Apercu pret pour ${downloadName}.`, "success");
  } catch (error) {
    setStatus(error.message || "Une erreur inattendue est survenue.", "error");
  } finally {
    submitButton.disabled = false;
  }
}

function resetAdvancedOptions() {
  outputFormatField.value = defaultOptions.outputFormat;
  errorCorrectionField.value = defaultOptions.errorCorrection;
  borderSizeField.value = defaultOptions.borderSize;
  colorModeField.value = defaultOptions.colorMode;
  foregroundColorField.value = defaultOptions.foregroundColor;
  foregroundHexField.value = defaultOptions.foregroundColor.toUpperCase();
  foregroundColor2Field.value = defaultOptions.foregroundColor2;
  foregroundHex2Field.value = defaultOptions.foregroundColor2.toUpperCase();
  backgroundColorField.value = defaultOptions.backgroundColor;
  backgroundHexField.value = defaultOptions.backgroundColor.toUpperCase();
  transparentBackgroundField.checked = defaultOptions.transparentBackground;
  moduleStyleField.value = defaultOptions.moduleStyle;
  eyeStyleField.value = defaultOptions.eyeStyle;
  qualityField.value = defaultOptions.quality;
  logoSizeField.value = defaultOptions.logoSize;
  logoField.value = "";
  updateLogoSizeOutput();
  updateConditionalOptions();
  clearCurrentPreview();
  setStatus("Options avancees reinitialisees.", "info");
}

form.addEventListener("submit", handleSubmit);

function clearErrorStatus() {
  if (statusBox.dataset.state === "error") {
    setStatus("Pret a generer un nouveau QR code.", "info");
  }
}

function handleFormActivity(event) {
  clearErrorStatus();
  if (isColorControl(event.target)) {
    return;
  }

  evaluateDelights();
}

form.addEventListener("input", handleFormActivity);
form.addEventListener("change", handleFormActivity);
qrTypeField.addEventListener("change", () => {
  updateQrTypeFields();
  clearCurrentPreview();
  evaluateDelights();
});
wifiSecurityField.addEventListener("change", updateQrTypeFields);
foregroundColorField.addEventListener("input", () => {
  syncHexFromPicker(foregroundColorField, foregroundHexField);
});
foregroundColor2Field.addEventListener("input", () => {
  syncHexFromPicker(foregroundColor2Field, foregroundHex2Field);
});
backgroundColorField.addEventListener("input", () => {
  syncHexFromPicker(backgroundColorField, backgroundHexField);
});
filenameField.addEventListener("input", () => {
  evaluateDelights();
});
foregroundHexField.addEventListener("blur", () => {
  syncPickerFromHex(foregroundColorField, foregroundHexField);
  evaluateDelights();
});
foregroundHex2Field.addEventListener("blur", () => {
  syncPickerFromHex(foregroundColor2Field, foregroundHex2Field);
  evaluateDelights();
});
backgroundHexField.addEventListener("blur", () => {
  syncPickerFromHex(backgroundColorField, backgroundHexField);
  evaluateDelights();
});
foregroundColorField.addEventListener("change", evaluateDelights);
foregroundColor2Field.addEventListener("change", evaluateDelights);
backgroundColorField.addEventListener("change", evaluateDelights);
foregroundHexField.addEventListener("change", evaluateDelights);
foregroundHex2Field.addEventListener("change", evaluateDelights);
backgroundHexField.addEventListener("change", evaluateDelights);
foregroundColorField.addEventListener("blur", evaluateDelights);
foregroundColor2Field.addEventListener("blur", evaluateDelights);
backgroundColorField.addEventListener("blur", evaluateDelights);
logoSizeField.addEventListener("input", updateLogoSizeOutput);
colorModeField.addEventListener("change", updateConditionalOptions);
transparentBackgroundField.addEventListener("change", updateConditionalOptions);
logoField.addEventListener("change", updateConditionalOptions);
downloadButton.addEventListener("click", () => {
  if (currentPreview) {
    triggerDownload(currentPreview.blob, currentPreview.filename);
  }
});
copyButton.addEventListener("click", copyCurrentPreview);
resetOptionsButton.addEventListener("click", () => {
  resetAdvancedOptions();
  registerResetClick();
  evaluateDelights();
});
updateQrTypeFields();
updateLogoSizeOutput();
updateConditionalOptions();
evaluateDelights();
