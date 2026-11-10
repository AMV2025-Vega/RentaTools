(async () => {
  const { t, api, money, day, today, h, note, busy } = RT;
  const root = document.getElementById("detalle");
  const id = root.dataset.id, autenticado = root.dataset.auth === "1";
  const $ = (s) => document.getElementById(s);

  const r = await api(`/herramientas/${id}/`);
  if (!r.ok) { $("detalle-estado").textContent = RT.errorText(r); return; }
  const x = r.data;
  document.title = x.nombre + " · RentaTools";
  $("detalle-estado").hidden = true; $("detalle-cuerpo").hidden = false;
  $("nombre").textContent = x.nombre; $("descripcion").textContent = x.descripcion; $("categoria").textContent = x.categoria_nombre;
  $("precio").textContent = money(x.precio_por_dia);
  if (x.foto_url) { const f = $("foto"); f.src = x.foto_url; f.alt = x.nombre; f.hidden = false; f.onerror = () => (f.hidden = true); }

  const ul = $("ocupadas");
  const inicio = $("inicio"), fin = $("fin"), cot = $("cotizacion"), msg = $("msg"), btn = $("btn-reservar");
  inicio.min = fin.min = today();
  let ultima = 0;

  const fila = (k, v, cls) => [h("dt", {}, k), h("dd", { class: cls || "" }, v)];

  async function cotizar() {
    note(msg, "error", "");
    if (!inicio.value || !fin.value) { cot.replaceChildren(); return; }
    cot.replaceChildren(h("p", { class: "muted" }, t("cotizando")));
    const turno = ++ultima;
    const q = await api(`/cotizaciones/?herramienta_id=${id}&fecha_inicio=${inicio.value}&fecha_fin=${fin.value}`);
    if (turno !== ultima) return; // llegó una respuesta más nueva
    if (!q.ok) { cot.replaceChildren(); note(msg, "error", RT.errorText(q)); return; }
    const c = q.data, partes = [];
    partes.push(...fila(`${t("alquiler")} (${c.dias} ${c.dias === 1 ? t("dia") : t("dias")})`, money(c.costo_alquiler)));
    if (c.seguro) {
      partes.push(...fila(`${t("seguro")} · ${c.seguro.aseguradora}`, money(c.seguro.prima)));
      partes.push(h("p", { class: "small" }, `${t("cobertura")}: ${money(c.seguro.cobertura_maxima)}`));
    }
    partes.push(...fila(t("total"), money(c.total), "total"));
    if (c.total_usd != null) {
      partes.push(...fila(t("equivale"), money(c.total_usd, "USD")));
      partes.push(h("p", { class: "small" }, t("tasa", { cop: Number(c.cop_por_usd).toLocaleString(RT.lang === "en" ? "en-US" : "es-CO"), fecha: c.tasa_actualizada_en || "" }), " · ",
        h("a", { href: c.atribucion.url, rel: "noopener", target: "_blank" }, c.atribucion.texto)));
    }
    cot.replaceChildren(h("dl", {}, partes));
    // El aviso de seguro sin servicio (aliado) se informa; lo demás se deduce de lo que falta.
    c.avisos.forEach((a) => cot.append(h("p", { class: "msg msg--warn" }, t("aviso_" + a))));
  }
  inicio.addEventListener("change", () => { if (fin.value && fin.value < inicio.value) fin.value = inicio.value; fin.min = inicio.value || today(); cotizar(); });
  fin.addEventListener("change", cotizar);

  $("form-reserva").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!autenticado) { location.href = "/ingresar/?next=" + encodeURIComponent(location.pathname); return; }
    if (!inicio.value || !fin.value) { note(msg, "error", t("fechas_requeridas")); return; }
    busy(btn, true, t("reservando"));
    const res = await api("/reservas/", { method: "POST", body: { herramienta_id: Number(id), fecha_inicio: inicio.value, fecha_fin: fin.value } });
    if (res.ok) { note(msg, "ok", t("reserva_ok")); setTimeout(() => (location.href = "/mis-reservas/"), 900); return; }
    busy(btn, false);
    note(msg, "error", RT.errorText(res));
    if (res.status === 409) { const o = await api(`/herramientas/${id}/ocupacion/`); if (o.ok) ul.replaceChildren(...o.data.map((z) => h("li", {}, `${day(z.fecha_inicio)} → ${day(z.fecha_fin)}`))); }
  });

  // La ocupación se carga al final para no retrasar el registro de los listeners del formulario.
  const oc = await api(`/herramientas/${id}/ocupacion/`);
  if (oc.ok && oc.data.length) oc.data.forEach((o) => ul.append(h("li", {}, `${day(o.fecha_inicio)} → ${day(o.fecha_fin)}`)));
  else ul.append(h("li", {}, t("sin_ocupacion")));

})();
