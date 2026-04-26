// Color normalization, picker/hex sync, and palette checks.
(function () {
  const app = window.QRApp || (window.QRApp = {});
  const hexColorPattern = /^#[0-9a-fA-F]{6}$/;

  function createColorUtils({ elements }) {
    const colorControls = new Set([
      elements.foregroundColorField,
      elements.foregroundHexField,
      elements.foregroundColor2Field,
      elements.foregroundHex2Field,
      elements.backgroundColorField,
      elements.backgroundHexField,
    ]);

    function normalizeHexColor(value) {
      const trimmedValue = (value || "").trim();
      const prefixedValue = trimmedValue.startsWith("#") ? trimmedValue : `#${trimmedValue}`;

      return hexColorPattern.test(prefixedValue) ? prefixedValue.toUpperCase() : null;
    }

    function usesGradientColor() {
      return elements.colorModeField.value !== "solid";
    }

    function currentColorValues() {
      const colors = [
        normalizeHexColor(elements.foregroundHexField.value || elements.foregroundColorField.value),
      ];

      if (usesGradientColor()) {
        colors.push(normalizeHexColor(elements.foregroundHex2Field.value || elements.foregroundColor2Field.value));
      }

      if (!elements.transparentBackgroundField.checked) {
        colors.push(normalizeHexColor(elements.backgroundHexField.value || elements.backgroundColorField.value));
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

    function foregroundMatchesBackground() {
      if (elements.transparentBackgroundField.checked) {
        return false;
      }

      const foregroundColor = normalizeHexColor(
        elements.foregroundHexField.value || elements.foregroundColorField.value,
      );
      const backgroundColor = normalizeHexColor(
        elements.backgroundHexField.value || elements.backgroundColorField.value,
      );

      return Boolean(foregroundColor) && Boolean(backgroundColor) && foregroundColor === backgroundColor;
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

    return {
      foregroundMatchesBackground,
      hasFrenchPalette,
      isColorControl,
      normalizeHexColor,
      syncHexFromPicker,
      syncPickerFromHex,
      usesGradientColor,
    };
  }

  app.createColorUtils = createColorUtils;
}());
