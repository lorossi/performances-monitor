// the only way i found to access css variables
function getCssProperty(property) {
  let css_property = $(":root").css(property);
  return css_property.split(" ").join("");
}
