// API call and response handling for QR generation.
(function () {
  const app = window.QRApp || (window.QRApp = {});

  const backendErrorKeys = {
    "QR color and background color need more contrast.": "backend.lowContrast",
    "Selected QR code quality is not supported.": "backend.invalidQuality",
    "Selected QR code type is not supported.": "backend.invalidType",
    "Selected error correction level is not supported.": "backend.invalidErrorCorrection",
    "Please enter a text or a link before generating a QR code.": "backend.emptyText",
  };

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

  function createQrApi({ elements }) {
    async function generateQrCode({ text, filename, logoFile }) {
      const formData = new FormData(elements.form);
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
        const errorMessage = errorPayload?.error || "errors.generationFailed";
        throw new Error(backendErrorKeys[errorMessage] || errorMessage);
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get("Content-Disposition");
      const extension = elements.outputFormatField.value === "svg" ? "svg" : "png";
      const downloadName = extractFilename(contentDisposition) || fallbackName(filename, extension);

      return { blob, downloadName };
    }

    return {
      generateQrCode,
    };
  }

  app.createQrApi = createQrApi;
}());
