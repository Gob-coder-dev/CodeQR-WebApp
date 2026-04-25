const form = document.querySelector("#qr-form");
const submitButton = document.querySelector("#submit-button");
const statusBox = document.querySelector("#status");
const textField = document.querySelector("#text");
const filenameField = document.querySelector("#filename");
const outputFormatField = document.querySelector("#output-format");
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

const defaultOptions = {
  foregroundColor: "#000000",
  foregroundColor2: "#0f766e",
  backgroundColor: "#ffffff",
  outputFormat: "png",
  colorMode: "solid",
  moduleStyle: "square",
  eyeStyle: "square",
  quality: "medium",
  logoSize: "22",
  transparentBackground: false,
};
const maxLogoBytes = 2 * 1024 * 1024;
const hexColorPattern = /^#[0-9a-fA-F]{6}$/;
let currentPreview = null;

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

function updateConditionalOptions() {
  setOptionGroupVisibility(secondaryColorGroup, usesGradientColor());
  setOptionGroupVisibility(backgroundColorGroup, !transparentBackgroundField.checked);
  setOptionGroupVisibility(logoSizeGroup, logoField.files.length > 0);
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

  if (!text) {
    setStatus("Ajoutez un lien ou un texte d'abord.", "error");
    textField.focus();
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

  updateConditionalOptions();

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

form.addEventListener("input", clearErrorStatus);
form.addEventListener("change", clearErrorStatus);
foregroundColorField.addEventListener("input", () => {
  syncHexFromPicker(foregroundColorField, foregroundHexField);
});
foregroundColor2Field.addEventListener("input", () => {
  syncHexFromPicker(foregroundColor2Field, foregroundHex2Field);
});
backgroundColorField.addEventListener("input", () => {
  syncHexFromPicker(backgroundColorField, backgroundHexField);
});
foregroundHexField.addEventListener("blur", () => {
  syncPickerFromHex(foregroundColorField, foregroundHexField);
});
foregroundHex2Field.addEventListener("blur", () => {
  syncPickerFromHex(foregroundColor2Field, foregroundHex2Field);
});
backgroundHexField.addEventListener("blur", () => {
  syncPickerFromHex(backgroundColorField, backgroundHexField);
});
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
resetOptionsButton.addEventListener("click", resetAdvancedOptions);
updateLogoSizeOutput();
updateConditionalOptions();
