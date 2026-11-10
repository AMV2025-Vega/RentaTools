(async () => {
  const { t, api, money, h, note, busy } = RT;
  const form = document.getElementById("form-publicar"), msg = document.getElementById("msg"), btn = document.getElementById("btn-publicar");
  const sel = document.getElementById("categoria"), mias = document.getElementById("mias");

  const c = await api("/categorias/");
  if (c.ok) c.data.forEach((x) => sel.append(h("option", { value: x.id }, x.nombre)));

  async function cargarMias() {
    const r = await api("/herramientas/?mias=1");
    if (!r.ok) { note(msg, "error", RT.errorText(r)); return; }
    if (!r.data.length) { mias.replaceChildren(h("li", {}, t("sin_herramientas"))); return; }
    mias.replaceChildren(...r.data.map((x) => h("li", {},
      h("span", {}, h("a", { href: `/herramientas/${x.id}/` }, x.nombre), " · ", money(x.precio_por_dia), " ",
        h("span", { class: `badge badge--${x.estado}` }, t("estado_" + x.estado))),
      h("button", { class: "btn btn--ghost btn--sm", type: "button", onclick: async (e) => {
        busy(e.currentTarget, true);
        const nuevo = x.estado === "ACTIVA" ? "MANTENIMIENTO" : "ACTIVA";
        const res = await api(`/herramientas/${x.id}/estado/`, { method: "PATCH", body: { estado: nuevo } });
        if (!res.ok) note(msg, "error", RT.errorText(res));
        await cargarMias();
      } }, x.estado === "ACTIVA" ? t("poner_mantenimiento") : t("activar")))));
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    note(msg, "ok", ""); RT.fieldErrors(form, null);
    busy(btn, true, t("publicando"));
    const body = {
      categoria_id: Number(sel.value), nombre: form.nombre.value.trim(), precio_por_dia: form.precio.value,
      descripcion: form.descripcion.value.trim(), foto_url: form.foto.value.trim(),
    };
    const r = await api("/herramientas/", { method: "POST", body });
    busy(btn, false);
    if (r.ok) { form.reset(); note(msg, "ok", t("publicada_ok")); await cargarMias(); return; }
    if (!RT.fieldErrors(form, r.data)) note(msg, "error", RT.errorText(r));
  });
  await cargarMias();
})();
