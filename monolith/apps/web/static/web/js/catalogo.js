(async () => {
  const { t, api, money, h } = RT;
  const lista = document.getElementById("lista"), estado = document.getElementById("estado-lista");
  const buscar = document.getElementById("buscar"), categoria = document.getElementById("categoria");
  let herramientas = [];

  estado.textContent = t("cargando");
  const [cats, herr, stats] = await Promise.all([api("/categorias/"), api("/herramientas/"), api("/publico/estadisticas/")]);

  if (!herr.ok) { lista.setAttribute("aria-busy", "false"); estado.textContent = RT.errorText(herr); return; }
  herramientas = herr.data;
  if (cats.ok) cats.data.forEach((c) => categoria.append(h("option", { value: c.id }, c.nombre)));
  if (stats.ok) {
    const r = stats.data.resumen;
    document.getElementById("stats").textContent = t("stats", { h: r.herramientas_activas, r: r.reservas_total });
  }

  function tarjeta(x) {
    const foto = x.foto_url
      ? h("img", { src: x.foto_url, alt: "", loading: "lazy", referrerpolicy: "no-referrer", onerror: (e) => e.target.replaceWith(document.createTextNode(t("sin_foto"))) })
      : document.createTextNode(t("sin_foto"));
    return h("li", {}, h("article", { class: "card" },
      h("div", { class: "card__img" }, foto),
      h("div", { class: "card__body" },
        h("span", { class: "badge" }, x.categoria_nombre),
        h("h2", { class: "card__title" }, h("a", { href: `/herramientas/${x.id}/` }, x.nombre)),
        h("p", { class: "card__price" }, money(x.precio_por_dia), " ", h("span", {}, "/ " + t("dia"))))));
  }

  function pintar() {
    const q = buscar.value.trim().toLowerCase(), c = categoria.value;
    const visibles = herramientas.filter((x) => (!c || String(x.categoria_id) === c) && (!q || (x.nombre + " " + x.descripcion).toLowerCase().includes(q)));
    lista.replaceChildren(...visibles.map(tarjeta));
    lista.setAttribute("aria-busy", "false");
    estado.textContent = visibles.length ? "" : t("sin_resultados");
  }
  buscar.addEventListener("input", pintar);
  categoria.addEventListener("change", pintar);
  pintar();
})();
