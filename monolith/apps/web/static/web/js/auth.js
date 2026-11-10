(() => {
  const { t, api, note, busy } = RT;
  const form = document.getElementById("form-auth"), msg = document.getElementById("msg"), btn = document.getElementById("btn-auth");
  const registro = form.dataset.modo === "registro", destino = form.dataset.siguiente || "/";

  async function entrar(username, password) {
    return api("/auth/login/", { method: "POST", body: { username, password } });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    note(msg, "ok", ""); RT.fieldErrors(form, null);
    const username = form.username.value.trim(), password = form.password.value;
    busy(btn, true, registro ? t("creando") : t("ingresando"));
    let r;
    if (registro) {
      r = await api("/auth/registro/", { method: "POST", body: { username, email: form.email.value.trim(), password, telefono: form.telefono.value.trim() } });
      if (r.ok) r = await entrar(username, password);
    } else {
      r = await entrar(username, password);
    }
    if (r.ok) { location.href = destino; return; }
    busy(btn, false);
    if (!RT.fieldErrors(form, r.data)) note(msg, "error", RT.errorText(r));
  });
})();
