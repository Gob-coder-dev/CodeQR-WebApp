const form = document.querySelector("#qr-form");
const submitButton = document.querySelector("#submit-button");
const statusBox = document.querySelector("#status");
const textField = document.querySelector("#text");
const filenameField = document.querySelector("#filename");

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

async function handleSubmit(event) {
  event.preventDefault();

  const text = textField.value.trim();
  const filename = filenameField.value.trim();

  if (!text) {
    setStatus("Enter text or a link first.", "error");
    textField.focus();
    return;
  }

  submitButton.disabled = true;
  setStatus("Generating the QR code...", "loading");

  try {
    const response = await fetch("/api/qr-code", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text, filename }),
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => null);
      const errorMessage = errorPayload?.error || "The QR code generation failed.";
      throw new Error(errorMessage);
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("Content-Disposition");
    const downloadName = extractFilename(contentDisposition) || fallbackName(filename);

    triggerDownload(blob, downloadName);
    setStatus(`Download started for ${downloadName}.`, "success");
  } catch (error) {
    setStatus(error.message || "An unexpected error occurred.", "error");
  } finally {
    submitButton.disabled = false;
  }
}

form.addEventListener("submit", handleSubmit);

textField.addEventListener("input", () => {
  if (statusBox.dataset.state === "error") {
    setStatus("Ready to generate a new QR code.", "info");
  }
});
