// Form state, validation, and advanced-option visibility.
(function () {
  const app = window.QRApp || (window.QRApp = {});

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
  const contentRequirements = {
    text: {
      selector: "#text",
      message: "validation.text",
    },
    wifi: {
      selector: "#wifi-ssid",
      message: "validation.wifi",
    },
    email: {
      selector: "#email-to",
      message: "validation.email",
    },
    phone: {
      selector: "#phone-number",
      message: "validation.phone",
    },
    sms: {
      selector: "#sms-number",
      message: "validation.sms",
    },
    contact: {
      selector: "#contact-first-name",
      secondarySelector: "#contact-last-name",
      message: "validation.contact",
    },
    location: {
      selector: "#location-latitude",
      secondarySelector: "#location-longitude",
      message: "validation.location",
    },
  };

  function createFormOptions({ elements, colorUtils, setStatus, clearCurrentPreview }) {
    function normalizeText(value) {
      return (value || "").trim().replace(/\s+/g, " ").toLowerCase();
    }

    function normalizeFilename(value) {
      const normalizedValue = normalizeText(value);
      return normalizedValue.replace(/\.(png|svg)$/i, "");
    }

    function activeContentValue() {
      return elements.qrTypeField.value === "text" ? elements.textField.value.trim() : "";
    }

    function updateLogoSizeOutput() {
      elements.logoSizeOutput.value = `${elements.logoSizeField.value}%`;
      elements.logoSizeOutput.textContent = `${elements.logoSizeField.value}%`;
    }

    function setOptionGroupVisibility(group, isVisible) {
      group.hidden = !isVisible;
      group.querySelectorAll("input, select, textarea").forEach((control) => {
        control.disabled = !isVisible;
      });
    }

    function updateQrTypeFields() {
      elements.qrTypeFieldGroups.forEach((group) => {
        setOptionGroupVisibility(group, group.dataset.qrTypeFields === elements.qrTypeField.value);
      });
      setOptionGroupVisibility(
        elements.wifiPasswordGroup,
        elements.qrTypeField.value === "wifi" && elements.wifiSecurityField.value !== "nopass",
      );
    }

    function updateConditionalOptions() {
      setOptionGroupVisibility(elements.secondaryColorGroup, colorUtils.usesGradientColor());
      setOptionGroupVisibility(elements.backgroundColorGroup, !elements.transparentBackgroundField.checked);
      const hasLogo = elements.logoField.files.length > 0;
      setOptionGroupVisibility(elements.logoSizeGroup, hasLogo);
      if (hasLogo) {
        elements.errorCorrectionField.value = "high";
      }
    }

    function validateQrContent() {
      const requirement = contentRequirements[elements.qrTypeField.value] || contentRequirements.text;
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

    function validateBeforeSubmit() {
      const logoFile = elements.logoField.files[0];

      updateQrTypeFields();
      updateConditionalOptions();

      if (!validateQrContent()) {
        return false;
      }

      if (logoFile && logoFile.size > maxLogoBytes) {
        setStatus("validation.logoSize", "error");
        elements.logoField.focus();
        return false;
      }

      if (!colorUtils.syncPickerFromHex(elements.foregroundColorField, elements.foregroundHexField)) {
        setStatus("validation.foregroundHex", "error");
        elements.foregroundHexField.focus();
        return false;
      }

      if (
        colorUtils.usesGradientColor() &&
        !colorUtils.syncPickerFromHex(elements.foregroundColor2Field, elements.foregroundHex2Field)
      ) {
        setStatus("validation.secondaryHex", "error");
        elements.foregroundHex2Field.focus();
        return false;
      }

      if (
        !elements.transparentBackgroundField.checked &&
        !colorUtils.syncPickerFromHex(elements.backgroundColorField, elements.backgroundHexField)
      ) {
        setStatus("validation.backgroundHex", "error");
        elements.backgroundHexField.focus();
        return false;
      }

      return true;
    }

    function resetAdvancedOptions() {
      elements.outputFormatField.value = defaultOptions.outputFormat;
      elements.errorCorrectionField.value = defaultOptions.errorCorrection;
      elements.borderSizeField.value = defaultOptions.borderSize;
      elements.colorModeField.value = defaultOptions.colorMode;
      elements.foregroundColorField.value = defaultOptions.foregroundColor;
      elements.foregroundHexField.value = defaultOptions.foregroundColor.toUpperCase();
      elements.foregroundColor2Field.value = defaultOptions.foregroundColor2;
      elements.foregroundHex2Field.value = defaultOptions.foregroundColor2.toUpperCase();
      elements.backgroundColorField.value = defaultOptions.backgroundColor;
      elements.backgroundHexField.value = defaultOptions.backgroundColor.toUpperCase();
      elements.transparentBackgroundField.checked = defaultOptions.transparentBackground;
      elements.moduleStyleField.value = defaultOptions.moduleStyle;
      elements.eyeStyleField.value = defaultOptions.eyeStyle;
      elements.qualityField.value = defaultOptions.quality;
      elements.logoSizeField.value = defaultOptions.logoSize;
      elements.logoField.value = "";
      updateLogoSizeOutput();
      updateConditionalOptions();
      clearCurrentPreview();
      setStatus("status.optionsReset", "info");
    }

    return {
      activeContentValue,
      normalizeFilename,
      normalizeText,
      resetAdvancedOptions,
      updateConditionalOptions,
      updateLogoSizeOutput,
      updateQrTypeFields,
      validateBeforeSubmit,
    };
  }

  app.createFormOptions = createFormOptions;
}());
