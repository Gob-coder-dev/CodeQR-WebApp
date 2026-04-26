// QR preview state, download, and clipboard copy.
(function () {
  const app = window.QRApp || (window.QRApp = {});

  function createPreview({ elements, setStatus }) {
    let currentPreview = null;

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

    function clearCurrentPreview() {
      if (currentPreview?.url) {
        window.URL.revokeObjectURL(currentPreview.url);
      }

      currentPreview = null;
      elements.preview.hidden = true;
      elements.previewImage.removeAttribute("src");
      elements.downloadButton.disabled = true;
      elements.copyButton.disabled = true;
    }

    function setCurrentPreview(blob, filename) {
      clearCurrentPreview();
      const url = window.URL.createObjectURL(blob);
      currentPreview = { blob, filename, url };
      elements.previewImage.src = url;
      elements.preview.hidden = false;
      elements.downloadButton.disabled = false;
      elements.copyButton.disabled = false;
    }

    function loadImage(url) {
      return new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error("errors.imagePrepare"));
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
              reject(new Error("errors.svgCopyFailed"));
            }
          }, "image/png");
        });
      } finally {
        window.URL.revokeObjectURL(url);
      }
    }

    function downloadCurrentPreview() {
      if (currentPreview) {
        triggerDownload(currentPreview.blob, currentPreview.filename);
      }
    }

    async function copyCurrentPreview() {
      if (!currentPreview) {
        return;
      }

      if (!navigator.clipboard?.write || !window.ClipboardItem) {
        setStatus("errors.copyUnavailable", "error");
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
        setStatus("status.copied", "success");
      } catch (error) {
        setStatus(error.message || "errors.copyFailed", "error");
      }
    }

    return {
      clearCurrentPreview,
      copyCurrentPreview,
      downloadCurrentPreview,
      setCurrentPreview,
    };
  }

  app.createPreview = createPreview;
}());
