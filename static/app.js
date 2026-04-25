const form = document.querySelector("#qr-form");
const submitButton = document.querySelector("#submit-button");
const statusBox = document.querySelector("#status");
const textField = document.querySelector("#text");
const filenameField = document.querySelector("#filename");
const foregroundColorField = document.querySelector("#foreground-color");
const foregroundHexField = document.querySelector("#foreground-color-hex");
const backgroundColorField = document.querySelector("#background-color");
const backgroundHexField = document.querySelector("#background-color-hex");
const moduleStyleField = document.querySelector("#module-style");
const qualityField = document.querySelector("#quality");
const logoField = document.querySelector("#logo");
const resetOptionsButton = document.querySelector("#reset-options");

const defaultOptions = {
  foregroundColor: "#000000",
  backgroundColor: "#ffffff",
  moduleStyle: "square",
  quality: "medium",
};
const maxLogoBytes = 2 * 1024 * 1024;
const hexColorPattern = /^#[0-9a-fA-F]{6}$/;

function setStatus(message, type = "info") {
  statusBox.textContent = message;
  statusBox.dataset.state = type;
}

function fallbackName(rawName) {
  const value = (rawName || "").trim();
  if (!value) {
    return "qr-code.png";
  }

  return value.toLowerCase().endsWith(".png") ? value : `${value}.png`;
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

  if (!syncPickerFromHex(backgroundColorField, backgroundHexField)) {
    setStatus("La couleur du fond doit etre au format hexadecimal, par exemple #FFFFFF.", "error");
    backgroundHexField.focus();
    return;
  }

  submitButton.disabled = true;
  setStatus("Generation du QR code...", "loading");

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
    const downloadName = extractFilename(contentDisposition) || fallbackName(filename);

    triggerDownload(blob, downloadName);
    setStatus(`Telechargement lance pour ${downloadName}.`, "success");
  } catch (error) {
    setStatus(error.message || "Une erreur inattendue est survenue.", "error");
  } finally {
    submitButton.disabled = false;
  }
}

function resetAdvancedOptions() {
  foregroundColorField.value = defaultOptions.foregroundColor;
  foregroundHexField.value = defaultOptions.foregroundColor.toUpperCase();
  backgroundColorField.value = defaultOptions.backgroundColor;
  backgroundHexField.value = defaultOptions.backgroundColor.toUpperCase();
  moduleStyleField.value = defaultOptions.moduleStyle;
  qualityField.value = defaultOptions.quality;
  logoField.value = "";
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
backgroundColorField.addEventListener("input", () => {
  syncHexFromPicker(backgroundColorField, backgroundHexField);
});
foregroundHexField.addEventListener("blur", () => {
  syncPickerFromHex(foregroundColorField, foregroundHexField);
});
backgroundHexField.addEventListener("blur", () => {
  syncPickerFromHex(backgroundColorField, backgroundHexField);
});
resetOptionsButton.addEventListener("click", resetAdvancedOptions);
