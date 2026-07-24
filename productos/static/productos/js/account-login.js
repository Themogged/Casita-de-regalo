(() => {
    "use strict";

    const form = document.querySelector("[data-login-form]");
    if (!form) return;

    const passwordInput = form.querySelector('input[name="password"]');
    const passwordToggle = form.querySelector("[data-password-toggle]");
    const submitButton = form.querySelector("[data-login-submit]");
    const submitLabel = form.querySelector("[data-login-submit-label]");
    const liveRegion = form.querySelector("[data-login-live]");

    const setPasswordVisibility = (visible) => {
        if (!passwordInput || !passwordToggle) return;
        passwordInput.type = visible ? "text" : "password";
        passwordToggle.classList.toggle("is-visible", visible);
        passwordToggle.setAttribute("aria-pressed", String(visible));
        passwordToggle.setAttribute(
            "aria-label",
            visible ? "Ocultar contrase\u00f1a" : "Mostrar contrase\u00f1a",
        );
        passwordToggle.title = visible ? "Ocultar contrase\u00f1a" : "Mostrar contrase\u00f1a";
    };

    passwordToggle?.addEventListener("click", () => {
        setPasswordVisibility(passwordInput?.type === "password");
        passwordInput?.focus({ preventScroll: true });
    });

    form.querySelectorAll(".login-field.has-error input").forEach((input) => {
        input.setAttribute("aria-invalid", "true");
    });

    form.addEventListener(
        "invalid",
        (event) => {
            const input = event.target;
            if (!(input instanceof HTMLInputElement)) return;
            input.setAttribute("aria-invalid", "true");
            input.closest(".login-field")?.classList.add("has-client-error");
        },
        true,
    );

    form.addEventListener("input", (event) => {
        const input = event.target;
        if (!(input instanceof HTMLInputElement) || !input.validity.valid) return;
        input.removeAttribute("aria-invalid");
        input.closest(".login-field")?.classList.remove("has-client-error");
    });

    const resetSubmittingState = () => {
        if (!submitButton) return;
        submitButton.disabled = false;
        submitButton.classList.remove("is-submitting");
        submitButton.removeAttribute("aria-busy");
        if (submitLabel) submitLabel.textContent = "Ingresar";
        if (liveRegion) liveRegion.textContent = "";
    };

    form.addEventListener("submit", () => {
        if (!submitButton || !form.checkValidity()) return;
        submitButton.disabled = true;
        submitButton.classList.add("is-submitting");
        submitButton.setAttribute("aria-busy", "true");
        if (submitLabel) submitLabel.textContent = "Validando";
        if (liveRegion) liveRegion.textContent = "Validando tus datos de acceso.";
    });

    window.addEventListener("pageshow", resetSubmittingState);
})();
