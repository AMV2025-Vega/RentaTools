/* Utilidades compartidas del frontend: llamadas a la API, formato regional y DOM seguro. */
const RT = (() => {
  const lang = document.documentElement.lang || "es";
  const locale = lang === "en" ? "en-US" : "es-CO";
  const csrf = () => document.querySelector('meta[name="csrf-token"]').content;

  /** Textos traducidos (window.I18N viene del servidor, vía gettext). {x} se reemplaza con vars. */
  const t = (clave, vars = {}) =>
    String((window.I18N && window.I18N[clave]) ?? clave).replace(/\{(\w+)\}/g, (_, k) => (k in vars ? vars[k] : `{${k}}`));

  /** Llama a /api/... con sesión y CSRF. Nunca lanza: devuelve {ok, status, data}. */
  async function api(path, { method = "GET", body } = {}) {
    const headers = { Accept: "application/json" };
    if (method !== "GET") headers["X-CSRFToken"] = csrf();
    if (body !== undefined) headers["Content-Type"] = "application/json";
    try {
      const res = await fetch("/api" + path, { method, headers, credentials: "same-origin", body: body !== undefined ? JSON.stringify(body) : undefined });
      let data = null;
      try { data = await res.json(); } catch (_) { /* respuesta vacía (204) */ }
      return { ok: res.ok, status: res.status, data };
    } catch (_) {
      return { ok: false, status: 0, data: { error: t("error_red") } };
    }
  }

  /** Extrae un texto legible de una respuesta de error (dominio {error} o validación {campo:[...]}). */
  function errorText(r) {
    if (r.status === 0) return t("error_red");
    const d = r.data || {};
    if (d.error) return d.error;
    if (d.detail) return d.detail;
    const first = Object.values(d).flat()[0];
    return typeof first === "string" ? first : t("error_generico");
  }
  /** Errores por campo {campo: [mensajes]} → <p id="err-campo">. Devuelve true si pintó alguno. */
  function fieldErrors(form, data) {
    let any = false;
    form.querySelectorAll(".err").forEach((p) => { p.hidden = true; p.textContent = ""; });
    form.querySelectorAll("[aria-invalid]").forEach((i) => i.removeAttribute("aria-invalid"));
    if (!data || typeof data !== "object") return false;
    for (const [campo, msgs] of Object.entries(data)) {
      const p = form.querySelector("#err-" + campo);
      if (p && Array.isArray(msgs)) {
        p.textContent = msgs.join(" "); p.hidden = false; any = true;
        const input = p.previousElementSibling && p.previousElementSibling.matches("input,select,textarea") ? p.previousElementSibling : p.parentElement.querySelector("input,select,textarea");
        if (input) input.setAttribute("aria-invalid", "true");
      }
    }
    return any;
  }
  const money = (v, cur = "COP") => new Intl.NumberFormat(locale, { style: "currency", currency: cur, maximumFractionDigits: cur === "COP" ? 0 : 2 }).format(Number(v));
  const day = (iso) => new Date(iso + "T00:00:00").toLocaleDateString(locale, { day: "2-digit", month: "short", year: "numeric" });
  const today = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };

  /** Crea elementos sin innerHTML (los textos de usuarios nunca se interpretan como HTML). */
  function h(tag, attrs = {}, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === false || v == null) continue;
      if (k === "class") el.className = v; else if (k.startsWith("on")) el.addEventListener(k.slice(2), v); else el.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid != null) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return el;
  }
  function note(el, kind, text) {
    el.className = "msg msg--" + kind; el.textContent = text; el.hidden = !text;
  }
  /** Bloquea/desbloquea un botón; al desbloquear restaura su texto original. */
  const busy = (btn, on, label) => {
    if (on) { btn.dataset.label = btn.dataset.label || btn.textContent; if (label) btn.textContent = label; }
    else if (btn.dataset.label) btn.textContent = btn.dataset.label;
    btn.disabled = on;
  };
  return { lang, t, api, errorText, fieldErrors, money, day, today, h, note, busy };
})();

document.getElementById("btn-salir")?.addEventListener("click", async () => {
  await RT.api("/auth/logout/", { method: "POST" });
  location.href = "/";
});
