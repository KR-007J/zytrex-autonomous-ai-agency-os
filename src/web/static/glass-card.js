// LeadForge — Real-Time Liquid Glass Refraction Engine
// The card is a live optical window onto a refracted duplicate of the background video.

(function initGlassCard() {
  function setup() {
    const video = document.getElementById("bg-video");
    const card = document.querySelector("[data-glass-card]");
    const container = document.getElementById("dup-video-container");
    const canvas = document.getElementById("dup-image");

    if (!video || !card || !container || !canvas) {
      setTimeout(setup, 100);
      return;
    }

    const ctx = canvas.getContext("2d", { alpha: true });
    let currentWidth = 0;
    let currentHeight = 0;

    const DUP_PIXEL_RATIO = Math.min(window.devicePixelRatio || 1, 2);
    const BLEED = 80;

    function renderFrame() {
      requestAnimationFrame(renderFrame);

      if (document.hidden) return;
      if (!video.videoWidth || !video.videoHeight) return;

      const rect = card.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return;

      const vw = document.documentElement.clientWidth;
      const vh = document.documentElement.clientHeight;

      container.style.left = `${-rect.left - BLEED}px`;
      container.style.top = `${-rect.top - BLEED}px`;
      container.style.width = `${vw + BLEED * 2}px`;
      container.style.height = `${vh + BLEED * 2}px`;

      const targetW = Math.round((vw + BLEED * 2) * DUP_PIXEL_RATIO);
      const targetH = Math.round((vh + BLEED * 2) * DUP_PIXEL_RATIO);

      if (currentWidth !== targetW || currentHeight !== targetH) {
        canvas.width = targetW;
        canvas.height = targetH;
        currentWidth = targetW;
        currentHeight = targetH;
      }

      try {
        const cover = Math.max(vw / video.videoWidth, vh / video.videoHeight);
        const sw_vp = vw / cover;
        const sh_vp = vh / cover;
        const sx_vp = (video.videoWidth - sw_vp) / 2;
        const sy_vp = (video.videoHeight - sh_vp) / 2;

        const sx = sx_vp - BLEED / cover;
        const sy = sy_vp - BLEED / cover;
        const sw = (vw + BLEED * 2) / cover;
        const sh = (vh + BLEED * 2) / cover;

        ctx.drawImage(video, sx, sy, sw, sh, 0, 0, targetW, targetH);
      } catch (e) {
        // Frame not decodable yet
      }
    }

    requestAnimationFrame(renderFrame);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
