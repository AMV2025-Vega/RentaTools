(async () => {
  const { t, api, money, day, h, note, busy } = RT;
  const tabla = document.getElementById("tabla"), filas = document.getElementById("filas"), vacio = document.getElementById("vacio"), msg = document.getElementById("msg");
  const nombres = {};

  async function cargar() {
    const r = await api("/reservas/");
    if (!r.ok) { note(msg, "error", RT.errorText(r)); return; }
    const ids = [...new Set(r.data.map((x) => x.herramienta_id))].filter((i) => !(i in nombres));
    await Promise.all(ids.map(async (i) => { const g = await api(`/herramientas/${i}/`); nombres[i] = g.ok ? g.data.nombre : `#${i}`; }));
    filas.replaceChildren(...r.data.map((x) => h("tr", {},
      h("td", {}, x.id),
      h("td", {}, h("a", { href: `/herramientas/${x.herramienta_id}/` }, nombres[x.herramienta_id])),
      h("td", {}, `${day(x.fecha_inicio)} → ${day(x.fecha_fin)}`),
      h("td", {}, x.dias),
      h("td", {}, money(x.costo_total, x.moneda)),
      h("td", {}, h("span", { class: `badge badge--estado badge--${x.estado}` }, t("estado_" + x.estado))),
      h("td", {}, ["PENDIENTE_PAGO", "CONFIRMADA"].includes(x.estado)
        ? h("button", { class: "btn btn--danger btn--sm", type: "button", onclick: (e) => cancelar(x.id, e.currentTarget) }, t("cancelar")) : ""))));
    tabla.hidden = r.data.length === 0;
    vacio.hidden = r.data.length !== 0; vacio.textContent = t("sin_reservas");
  }

  async function cancelar(id, btn) {
    if (!confirm(t("confirmar_cancelar"))) return;
    busy(btn, true);
    const r = await api(`/reservas/${id}/cancelar/`, { method: "POST" });
    note(msg, r.ok ? "ok" : "error", r.ok ? t("cancelada_ok") : RT.errorText(r));
    await cargar();
  }

  // Reporte CSV: se encola (202) y se consulta hasta que el worker de Celery lo deje LISTO.
  document.getElementById("btn-reporte").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    busy(btn, true, t("reporte_generando")); note(msg, "ok", t("reporte_generando"));
    const ini = await api("/reportes/reservas/", { method: "POST" });
    if (!ini.ok) { busy(btn, false); note(msg, "error", RT.errorText(ini)); return; }
    for (let i = 0; i < 30; i++) {
      await new Promise((ok) => setTimeout(ok, 1000));
      const s = await api(`/reportes/${ini.data.tarea_id}/`);
      if (!s.ok) { busy(btn, false); note(msg, "error", RT.errorText(s)); return; }
      if (s.data.estado === "FALLIDO") { busy(btn, false); note(msg, "error", t("reporte_fallo")); return; }
      if (s.data.estado === "LISTO") {
        const blob = new Blob([s.data.resultado.contenido], { type: "text/csv;charset=utf-8" });
        const a = h("a", { href: URL.createObjectURL(blob), download: s.data.resultado.nombre_archivo });
        document.body.append(a); a.click(); a.remove();
        busy(btn, false); note(msg, "ok", t("reporte_listo")); return;
      }
    }
    busy(btn, false); note(msg, "warn", t("reporte_tardo"));
  });

  await cargar();
})();
