const elements = {
  form: document.querySelector("#qr-form"),
  submitButton: document.querySelector("#submit-button"),
  statusBox: document.querySelector("#status"),
  languageButton: document.querySelector("#language-button"),
  languageButtonFlag: document.querySelector("#language-button-flag"),
  languageButtonCode: document.querySelector("#language-button-code"),
  languageMenu: document.querySelector("#language-menu"),
  languageMenuButtons: document.querySelectorAll("[data-language]"),
  qrTypeField: document.querySelector("#qr-type"),
  uiLanguageField: document.querySelector("#ui-language"),
  qrTypeFieldGroups: document.querySelectorAll("[data-qr-type-fields]"),
  textField: document.querySelector("#text"),
  wifiSecurityField: document.querySelector("#wifi-security"),
  wifiPasswordGroup: document.querySelector("#wifi-password-field"),
  filenameField: document.querySelector("#filename"),
  outputFormatField: document.querySelector("#output-format"),
  errorCorrectionField: document.querySelector("#error-correction"),
  borderSizeField: document.querySelector("#border-size"),
  colorModeField: document.querySelector("#color-mode"),
  foregroundColorField: document.querySelector("#foreground-color"),
  foregroundHexField: document.querySelector("#foreground-color-hex"),
  foregroundColor2Field: document.querySelector("#foreground-color-2"),
  foregroundHex2Field: document.querySelector("#foreground-color-2-hex"),
  backgroundColorField: document.querySelector("#background-color"),
  backgroundHexField: document.querySelector("#background-color-hex"),
  secondaryColorGroup: document.querySelector("#secondary-color-field"),
  backgroundColorGroup: document.querySelector("#background-color-field"),
  transparentBackgroundField: document.querySelector("#transparent-background"),
  moduleStyleField: document.querySelector("#module-style"),
  eyeStyleField: document.querySelector("#eye-style"),
  qualityField: document.querySelector("#quality"),
  logoField: document.querySelector("#logo"),
  logoSizeGroup: document.querySelector("#logo-size-field"),
  logoSizeField: document.querySelector("#logo-size"),
  logoSizeOutput: document.querySelector("#logo-size-output"),
  resetOptionsButton: document.querySelector("#reset-options"),
  preview: document.querySelector("#preview"),
  previewImage: document.querySelector("#preview-image"),
  downloadButton: document.querySelector("#download-button"),
  copyButton: document.querySelector("#copy-button"),
  delightTargets: {
    content: document.querySelector("#content-delight"),
    filename: document.querySelector("#filename-delight"),
    color: document.querySelector("#color-delight"),
  },
  resetDelight: document.querySelector("#reset-delight"),
};

const i18n = QRApp.createI18n({
  languageConfig: window.qrLanguageConfig,
  elements,
});
const colorUtils = QRApp.createColorUtils({ elements });
const previewController = QRApp.createPreview({
  elements,
  setStatus: i18n.setStatus,
});
const qrApi = QRApp.createQrApi({ elements });
const formOptions = QRApp.createFormOptions({
  elements,
  colorUtils,
  setStatus: i18n.setStatus,
  clearCurrentPreview: previewController.clearCurrentPreview,
});
const delights = QRApp.createDelights({
  elements,
  colorUtils,
  formOptions,
  i18n,
});

i18n.addApplyListener(() => {
  formOptions.updateLogoSizeOutput();
  delights.evaluate();
});

async function handleSubmit(event) {
  event.preventDefault();

  const text = elements.textField.value.trim();
  const filename = elements.filenameField.value.trim();
  const logoFile = elements.logoField.files[0];

  if (!formOptions.validateBeforeSubmit()) {
    return;
  }

  elements.submitButton.disabled = true;
  i18n.setStatus("status.loading", "loading");

  try {
    const { blob, downloadName } = await qrApi.generateQrCode({
      text,
      filename,
      logoFile,
    });

    previewController.setCurrentPreview(blob, downloadName);
    i18n.setStatus("status.previewReady", "success", { filename: downloadName });
  } catch (error) {
    i18n.setStatus(error.message || "errors.unexpected", "error");
  } finally {
    elements.submitButton.disabled = false;
  }
}

function clearErrorStatus() {
  if (elements.statusBox.dataset.state === "error") {
    i18n.setStatus("status.ready", "info");
  }
}

function handleFormActivity(event) {
  clearErrorStatus();
  if (colorUtils.isColorControl(event.target)) {
    return;
  }

  delights.evaluate();
}

elements.form.addEventListener("submit", handleSubmit);
elements.form.addEventListener("input", handleFormActivity);
elements.form.addEventListener("change", handleFormActivity);
elements.qrTypeField.addEventListener("change", () => {
  formOptions.updateQrTypeFields();
  previewController.clearCurrentPreview();
  delights.evaluate();
});
elements.wifiSecurityField.addEventListener("change", formOptions.updateQrTypeFields);
elements.foregroundColorField.addEventListener("input", () => {
  colorUtils.syncHexFromPicker(elements.foregroundColorField, elements.foregroundHexField);
});
elements.foregroundColor2Field.addEventListener("input", () => {
  colorUtils.syncHexFromPicker(elements.foregroundColor2Field, elements.foregroundHex2Field);
});
elements.backgroundColorField.addEventListener("input", () => {
  colorUtils.syncHexFromPicker(elements.backgroundColorField, elements.backgroundHexField);
});
elements.filenameField.addEventListener("input", delights.evaluate);
elements.foregroundHexField.addEventListener("blur", () => {
  colorUtils.syncPickerFromHex(elements.foregroundColorField, elements.foregroundHexField);
  delights.evaluate();
});
elements.foregroundHex2Field.addEventListener("blur", () => {
  colorUtils.syncPickerFromHex(elements.foregroundColor2Field, elements.foregroundHex2Field);
  delights.evaluate();
});
elements.backgroundHexField.addEventListener("blur", () => {
  colorUtils.syncPickerFromHex(elements.backgroundColorField, elements.backgroundHexField);
  delights.evaluate();
});
elements.foregroundColorField.addEventListener("change", delights.evaluate);
elements.foregroundColor2Field.addEventListener("change", delights.evaluate);
elements.backgroundColorField.addEventListener("change", delights.evaluate);
elements.foregroundHexField.addEventListener("change", delights.evaluate);
elements.foregroundHex2Field.addEventListener("change", delights.evaluate);
elements.backgroundHexField.addEventListener("change", delights.evaluate);
elements.foregroundColorField.addEventListener("blur", delights.evaluate);
elements.foregroundColor2Field.addEventListener("blur", delights.evaluate);
elements.backgroundColorField.addEventListener("blur", delights.evaluate);
elements.logoSizeField.addEventListener("input", formOptions.updateLogoSizeOutput);
elements.colorModeField.addEventListener("change", formOptions.updateConditionalOptions);
elements.transparentBackgroundField.addEventListener("change", formOptions.updateConditionalOptions);
elements.logoField.addEventListener("change", formOptions.updateConditionalOptions);
elements.downloadButton.addEventListener("click", previewController.downloadCurrentPreview);
elements.copyButton.addEventListener("click", previewController.copyCurrentPreview);
elements.resetOptionsButton.addEventListener("click", () => {
  formOptions.resetAdvancedOptions();
  delights.registerResetClick();
  delights.evaluate();
});

i18n.bindEvents();
formOptions.updateQrTypeFields();
formOptions.updateLogoSizeOutput();
formOptions.updateConditionalOptions();
i18n.init();
delights.evaluate();
