"use strict";
(() => {
  var __async = (__this, __arguments, generator) => {
    return new Promise((resolve, reject) => {
      var fulfilled = (value) => {
        try {
          step(generator.next(value));
        } catch (e) {
          reject(e);
        }
      };
      var rejected = (value) => {
        try {
          step(generator.throw(value));
        } catch (e) {
          reject(e);
        }
      };
      var step = (x) => x.done ? resolve(x.value) : Promise.resolve(x.value).then(fulfilled, rejected);
      step((generator = generator.apply(__this, __arguments)).next());
    });
  };

  // src/code.ts
  function parseColor(value) {
    if (!value)
      return null;
    value = value.trim();
    if (value.startsWith("#")) {
      var hex = value.replace("#", "");
      if (hex.length === 3)
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
      return { r: parseInt(hex.substring(0, 2), 16) / 255, g: parseInt(hex.substring(2, 4), 16) / 255, b: parseInt(hex.substring(4, 6), 16) / 255, a: 1 };
    }
    var m = value.match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+))?\s*\)/);
    if (m)
      return { r: parseFloat(m[1]) / 255, g: parseFloat(m[2]) / 255, b: parseFloat(m[3]) / 255, a: m[4] ? parseFloat(m[4]) : 1 };
    return null;
  }
  function px(v) {
    if (!v)
      return 0;
    var m = v.match(/([\d.]+)/);
    return m ? parseFloat(m[1]) : 0;
  }
  function parseGradient(value) {
    var m = value.match(/linear-gradient\(\s*([\d.]+)deg\s*,\s*(.+)\s*\)/);
    if (!m)
      return null;
    var angle = parseFloat(m[1]), stops = [];
    var hexR = /(#[0-9a-fA-F]{3,8})\s+([\d.]+)%/g, hm;
    while ((hm = hexR.exec(m[2])) !== null) {
      var c = parseColor(hm[1]);
      if (c)
        stops.push({ color: c, position: parseFloat(hm[2]) / 100 });
    }
    if (stops.length < 2) {
      stops = [];
      var rgbR = /(rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*(?:,\s*[\d.]+)?\s*\))\s+([\d.]+)%/g, rm;
      while ((rm = rgbR.exec(m[2])) !== null) {
        var c = parseColor(rm[1]);
        if (c)
          stops.push({ color: c, position: parseFloat(rm[2]) / 100 });
      }
    }
    return stops.length >= 2 ? { angle, stops } : null;
  }
  function applyFill(node, s) {
    var bgImg = s["backgroundImage"] || s["background"] || "";
    if (bgImg.indexOf("linear-gradient") >= 0) {
      var g = parseGradient(bgImg);
      if (g) {
        var a = g.angle * Math.PI / 180;
        node.fills = [{
          type: "GRADIENT_LINEAR",
          gradientTransform: [[Math.cos(a), Math.sin(a), 0], [-Math.sin(a), Math.cos(a), 0]],
          gradientStops: g.stops.map(function(st) {
            return { position: st.position, color: { r: st.color.r, g: st.color.g, b: st.color.b, a: st.color.a } };
          })
        }];
        return;
      }
    }
    var bgColor = s["backgroundColor"] || "";
    if (!bgColor && s["background"]) {
      var bc = parseColor(s["background"]);
      if (bc)
        bgColor = s["background"];
    }
    if (bgColor) {
      var c = parseColor(bgColor);
      if (c) {
        node.fills = [{ type: "SOLID", color: { r: c.r, g: c.g, b: c.b }, opacity: c.a }];
        return;
      }
    }
    node.fills = [];
  }
  function applyBorders(node, s) {
    var sides = ["Top", "Right", "Bottom", "Left"], maxW = 0, sc = null;
    for (var i = 0; i < 4; i++) {
      var w = px(s["border" + sides[i] + "Width"]);
      if (w > maxW) {
        maxW = w;
        sc = parseColor(s["border" + sides[i] + "Color"] || "");
      }
    }
    if (sc && maxW > 0) {
      node.strokes = [{ type: "SOLID", color: { r: sc.r, g: sc.g, b: sc.b }, opacity: sc.a }];
      node.strokeTopWeight = px(s["borderTopWidth"]);
      node.strokeRightWeight = px(s["borderRightWidth"]);
      node.strokeBottomWeight = px(s["borderBottomWidth"]);
      node.strokeLeftWeight = px(s["borderLeftWidth"]);
    }
  }
  function applyShadow(node, v) {
    if (!v || v === "none")
      return;
    var m = v.match(/([\d.]+)px\s+([\d.]+)px\s+([\d.]+)px\s+(?:([\d.]+)px\s+)?rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)/);
    if (m)
      node.effects = [{ type: "DROP_SHADOW", visible: true, blendMode: "NORMAL", offset: { x: parseFloat(m[1]), y: parseFloat(m[2]) }, radius: parseFloat(m[3]), spread: m[4] ? parseFloat(m[4]) : 0, color: { r: parseFloat(m[5]) / 255, g: parseFloat(m[6]) / 255, b: parseFloat(m[7]) / 255, a: parseFloat(m[8]) } }];
  }
  function pxOrPctRadius(val, size) {
    if (!val)
      return 0;
    if (val.indexOf("%") >= 0)
      return parseFloat(val) / 100 * size;
    return px(val);
  }
  function applyRadius(node, s) {
    var size = Math.min(node.width || 100, node.height || 100);
    var tl = pxOrPctRadius(s["borderTopLeftRadius"], size);
    var tr = pxOrPctRadius(s["borderTopRightRadius"], size);
    var bl = pxOrPctRadius(s["borderBottomLeftRadius"], size);
    var br = pxOrPctRadius(s["borderBottomRightRadius"], size);
    if (tl === tr && tr === bl && bl === br) {
      if (tl > 0)
        node.cornerRadius = tl;
    } else {
      node.topLeftRadius = tl;
      node.topRightRadius = tr;
      node.bottomLeftRadius = bl;
      node.bottomRightRadius = br;
    }
  }
  var fontFamily = "Inter";
  function loadFonts() {
    return __async(this, null, function* () {
      var fams = ["Pretendard", "Inter", "Roboto"], stys = ["Regular", "Medium", "SemiBold", "Bold", "ExtraBold"];
      for (var f = 0; f < fams.length; f++) {
        try {
          yield figma.loadFontAsync({ family: fams[f], style: "Regular" });
          fontFamily = fams[f];
          for (var s = 0; s < stys.length; s++) {
            try {
              yield figma.loadFontAsync({ family: fams[f], style: stys[s] });
            } catch (e) {
            }
          }
          break;
        } catch (e) {
        }
      }
    });
  }
  function fontStyle(w) {
    var n = parseInt(w || "400");
    if (n >= 800)
      return "ExtraBold";
    if (n >= 700)
      return "Bold";
    if (n >= 600)
      return "SemiBold";
    if (n >= 500)
      return "Medium";
    return "Regular";
  }
  function applyTextStyles(tn, s, textColor) {
    return __async(this, null, function* () {
      var fs = fontStyle(s["fontWeight"]);
      try {
        yield figma.loadFontAsync({ family: fontFamily, style: fs });
      } catch (e) {
        yield figma.loadFontAsync({ family: fontFamily, style: "Regular" });
      }
      tn.fontName = { family: fontFamily, style: fs };
      var fontSize = px(s["fontSize"]);
      if (fontSize > 0)
        tn.fontSize = fontSize;
      var tc = parseColor(textColor);
      if (!tc)
        tc = { r: 0.1, g: 0.1, b: 0.18, a: 1 };
      tn.fills = [{ type: "SOLID", color: { r: tc.r, g: tc.g, b: tc.b }, opacity: tc.a }];
      var ls = px(s["letterSpacing"]);
      if (ls !== 0)
        tn.letterSpacing = { value: ls, unit: "PIXELS" };
      var lh = s["lineHeight"];
      if (lh && lh !== "normal") {
        if (lh.indexOf("px") >= 0)
          tn.lineHeight = { value: px(lh), unit: "PIXELS" };
        else if (parseFloat(lh) < 10)
          tn.lineHeight = { value: parseFloat(lh) * 100, unit: "PERCENT" };
      }
      var ta = s["textAlign"];
      if (ta === "center")
        tn.textAlignHorizontal = "CENTER";
      else if (ta === "right")
        tn.textAlignHorizontal = "RIGHT";
      tn.textAutoResize = "WIDTH_AND_HEIGHT";
    });
  }
  function createNode(parent, parsed, parentColor) {
    return __async(this, null, function* () {
      var s = parsed.styles;
      var r = parsed.rect;
      if (r.width < 1 && r.height < 1)
        return;
      var currentColor = s["color"] || parentColor || "#1A1A2E";
      var bgColor = s["backgroundColor"] || "";
      var bgIsTransparent = bgColor === "rgba(0, 0, 0, 0)" || bgColor === "transparent";
      var isLeafText = parsed.children.length === 0 && parsed.text;
      var hasBg = !bgIsTransparent && bgColor && parseColor(bgColor);
      var hasGrad = s["backgroundImage"] && s["backgroundImage"].indexOf("gradient") >= 0 || s["background"] && s["background"].indexOf("gradient") >= 0;
      var hasPadding = px(s["paddingTop"]) > 0 || px(s["paddingLeft"]) > 0 || px(s["paddingRight"]) > 0 || px(s["paddingBottom"]) > 0;
      var hasBorder = px(s["borderTopWidth"]) > 0 || px(s["borderBottomWidth"]) > 0 || px(s["borderLeftWidth"]) > 0;
      var hasRadius = px(s["borderTopLeftRadius"]) > 0;
      var hasShadow = s["boxShadow"] && s["boxShadow"] !== "none";
      var needsFrame = hasBg || hasGrad || hasPadding || hasBorder || hasRadius || hasShadow;
      if (isLeafText && !needsFrame) {
        var tn = figma.createText();
        parent.appendChild(tn);
        tn.x = r.x;
        tn.y = r.y;
        var fs1 = fontStyle(s["fontWeight"]);
        try {
          yield figma.loadFontAsync({ family: fontFamily, style: fs1 });
        } catch (e) {
          yield figma.loadFontAsync({ family: fontFamily, style: "Regular" });
        }
        tn.fontName = { family: fontFamily, style: fs1 };
        tn.characters = parsed.text;
        yield applyTextStyles(tn, s, currentColor);
        tn.name = parsed.id || parsed.classes[0] || parsed.tag;
        return;
      }
      var frame = figma.createFrame();
      parent.appendChild(frame);
      frame.name = parsed.id || parsed.classes[0] || parsed.tag;
      frame.resize(Math.max(r.width, 1), Math.max(r.height, 1));
      frame.x = r.x;
      frame.y = r.y;
      if (hasGrad) {
        applyFill(frame, s);
      } else if (hasBg) {
        applyFill(frame, s);
      } else {
        frame.fills = [];
      }
      applyRadius(frame, s);
      applyBorders(frame, s);
      applyShadow(frame, s["boxShadow"]);
      if (s["opacity"] && parseFloat(s["opacity"]) < 1)
        frame.opacity = parseFloat(s["opacity"]);
      if (s["overflow"] === "hidden")
        frame.clipsContent = true;
      if (isLeafText && parsed.text) {
        var textNode = figma.createText();
        frame.appendChild(textNode);
        var fs2 = fontStyle(s["fontWeight"]);
        try {
          yield figma.loadFontAsync({ family: fontFamily, style: fs2 });
        } catch (e) {
          yield figma.loadFontAsync({ family: fontFamily, style: "Regular" });
        }
        textNode.fontName = { family: fontFamily, style: fs2 };
        textNode.characters = parsed.text;
        yield applyTextStyles(textNode, s, currentColor);
        var padL = px(s["paddingLeft"]), padT = px(s["paddingTop"]);
        var padR = px(s["paddingRight"]), padB = px(s["paddingBottom"]);
        var innerW = r.width - padL - padR;
        var innerH = r.height - padT - padB;
        var textW = textNode.width;
        var textH = textNode.height;
        var jc2 = s["justifyContent"] || "";
        var ai2 = s["alignItems"] || "";
        var ta2 = s["textAlign"] || "";
        if (ta2 === "center" || jc2 === "center" || ai2 === "center") {
          textNode.x = padL + (innerW - textW) / 2;
        } else if (ta2 === "right" || jc2 === "flex-end") {
          textNode.x = padL + innerW - textW;
        } else {
          textNode.x = padL;
        }
        if (jc2 === "center" || ai2 === "center") {
          textNode.y = padT + (innerH - textH) / 2;
        } else if (jc2 === "flex-end") {
          textNode.y = padT + innerH - textH;
        } else {
          textNode.y = padT;
        }
        textNode.name = "text";
        return;
      }
      for (var i = 0; i < parsed.children.length; i++) {
        yield createNode(frame, parsed.children[i], currentColor);
      }
    });
  }
  function createSlide(container, slide) {
    return __async(this, null, function* () {
      var frame = figma.createFrame();
      container.appendChild(frame);
      frame.name = slide.id;
      frame.resize(1920, 1080);
      frame.clipsContent = true;
      applyFill(frame, slide.slideStyles);
      var slideColor = slide.slideStyles["color"] || "#1A1A2E";
      for (var i = 0; i < slide.nodes.length; i++) {
        yield createNode(frame, slide.nodes[i], slideColor);
      }
      return frame;
    });
  }
  figma.showUI(__html__, { width: 320, height: 300 });
  figma.ui.onmessage = function(msg) {
    return __async(this, null, function* () {
      if (msg.type !== "CREATE_SLIDES")
        return;
      try {
        var slides = msg.slides;
        var total = slides.length;
        figma.ui.postMessage({ type: "PROGRESS", percent: 35, message: "\uD3F0\uD2B8 \uB85C\uB529 \uC911..." });
        yield loadFonts();
        var COLS = 5;
        var GAP = 100;
        var container = figma.createFrame();
        container.name = "Proposal Slides";
        container.layoutMode = "VERTICAL";
        container.primaryAxisSizingMode = "AUTO";
        container.counterAxisSizingMode = "AUTO";
        container.itemSpacing = GAP;
        container.fills = [];
        figma.currentPage.appendChild(container);
        var currentRow = null;
        for (var i = 0; i < slides.length; i++) {
          if (i % COLS === 0) {
            currentRow = figma.createFrame();
            currentRow.name = "Row " + (Math.floor(i / COLS) + 1);
            currentRow.layoutMode = "HORIZONTAL";
            currentRow.primaryAxisSizingMode = "AUTO";
            currentRow.counterAxisSizingMode = "AUTO";
            currentRow.itemSpacing = GAP;
            currentRow.fills = [];
            container.appendChild(currentRow);
          }
          figma.ui.postMessage({ type: "PROGRESS", percent: 40 + Math.round(i / total * 55), message: "\uC2AC\uB77C\uC774\uB4DC " + (i + 1) + "/" + total });
          yield createSlide(currentRow, slides[i]);
        }
        figma.viewport.scrollAndZoomIntoView([container]);
        figma.ui.postMessage({ type: "COMPLETE", slideCount: total });
      } catch (err) {
        figma.ui.postMessage({ type: "ERROR", message: err.message || String(err) });
      }
    });
  };
})();
