(function () {
    "use strict";

    const select = (selector, root) => (root || document).querySelector(selector);
    const selectAll = (selector, root) => Array.from((root || document).querySelectorAll(selector));
    const csrfToken = select('meta[name="csrf-token"]')?.content || "";

    function createElement(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (typeof text === "string") node.textContent = text;
        return node;
    }

    function updateCartCounters(units) {
        const value = Number.isFinite(Number(units)) ? Number(units) : 0;
        selectAll(".cart-count").forEach((counter) => {
            counter.textContent = String(value);
        });
    }

    function initConfirmationDialog() {
        const dialog = select("[data-confirm-dialog]");
        if (!dialog) return;
        const copy = select("[data-confirm-dialog-copy]", dialog);
        const bypassedForms = new WeakSet();

        const ask = (message) => new Promise((resolve) => {
            if (typeof dialog.showModal !== "function") {
                resolve(window.confirm(message));
                return;
            }
            if (copy) copy.textContent = message;
            const handleClose = () => {
                dialog.removeEventListener("close", handleClose);
                resolve(dialog.returnValue === "confirm");
            };
            dialog.addEventListener("close", handleClose);
            dialog.showModal();
        });

        document.addEventListener("submit", async (event) => {
            const form = event.target.closest("form[data-confirm-submit]");
            if (!form || bypassedForms.has(form)) return;
            event.preventDefault();
            event.stopImmediatePropagation();
            const confirmed = await ask(form.dataset.confirmSubmit || "Confirmar esta accion");
            if (!confirmed) return;
            bypassedForms.add(form);
            form.requestSubmit();
            window.setTimeout(() => bypassedForms.delete(form), 0);
        }, true);

        document.confirmStorefrontAction = ask;
    }

    function initCartDrawer() {
        const layer = select("[data-cart-drawer-layer]");
        const drawer = select("[data-cart-drawer]", layer);
        const itemsContainer = select("[data-cart-drawer-items]", layer);
        const totalNode = select("[data-cart-drawer-total]", layer);
        const checkoutLink = select("[data-cart-drawer-checkout]", layer);
        const toggles = selectAll("[data-cart-drawer-toggle]");
        if (!layer || !drawer || !itemsContainer) return;

        let previousFocus = null;
        let cartData = null;
        let requestPending = false;
        let closeTimer = null;
        let dragState = null;

        function setLoading() {
            itemsContainer.replaceChildren();
            const loading = createElement("div", "cart-drawer-loading");
            loading.setAttribute("role", "status");
            loading.append(createElement("span"), createElement("span"), createElement("span"));
            loading.append(createElement("p", "", "Preparando tu lista..."));
            itemsContainer.append(loading);
        }

        function setError(message) {
            itemsContainer.replaceChildren();
            const error = createElement("div", "cart-drawer-error");
            error.append(
                createElement("strong", "", "No pudimos cargar la lista"),
                createElement("p", "", message || "Intenta de nuevo en un momento.")
            );
            const retry = createElement("button", "btn-secondary", "Reintentar");
            retry.type = "button";
            retry.addEventListener("click", () => loadCart(true));
            error.append(retry);
            itemsContainer.append(error);
        }

        function createProductImage(item) {
            const media = createElement("a", "drawer-item-media");
            media.href = item.detail_url;
            const customerImage = item.personalization_data?.customer_image_url || "";
            const previewUrl = customerImage || item.image_url;
            if (previewUrl) {
                const image = createElement("img");
                image.src = previewUrl;
                image.alt = customerImage
                    ? "Vista previa enviada para " + item.name
                    : item.name;
                image.loading = "lazy";
                image.decoding = "async";
                media.append(image);
                if (customerImage) {
                    media.append(createElement("span", "drawer-item-media-label", "Tu imagen"));
                }
            } else {
                media.append(createElement("span", "sr-only", "Imagen no disponible"));
            }
            return media;
        }

        function createActionButton(label, action, url, disabled) {
            const button = createElement("button", "", label);
            button.type = "button";
            button.dataset.drawerAction = action;
            button.dataset.url = url;
            button.setAttribute("aria-label", action === "increase" ? "Aumentar cantidad" : "Disminuir cantidad");
            button.disabled = Boolean(disabled);
            return button;
        }

        function createDrawerItem(item) {
            const article = createElement("article", "drawer-item");
            article.dataset.itemId = String(item.id);
            article.append(createProductImage(item));

            const copy = createElement("div", "drawer-item-copy");
            const title = createElement("a", "", item.name);
            title.href = item.detail_url;
            copy.append(
                createElement("span", "drawer-item-category", item.category),
                title,
                createElement("span", "drawer-item-unit", item.price_label + " cada uno")
            );

            if (Array.isArray(item.personalization) && item.personalization.length) {
                const personalization = createElement("div", "drawer-item-personalization");
                item.personalization.slice(0, 4).forEach((value) => {
                    personalization.append(createElement("span", "", String(value)));
                });
                copy.append(personalization);
            }

            const controls = createElement("div", "drawer-item-controls");
            controls.append(
                createActionButton("-", "decrease", item.decrease_url, false),
                createElement("strong", "", String(item.quantity)),
                createActionButton("+", "increase", item.increase_url, item.can_increase === false)
            );
            copy.append(controls);
            article.append(copy);

            const side = createElement("div", "drawer-item-side");
            side.append(createElement("strong", "", item.subtotal_label));
            const remove = createElement("button", "drawer-remove", "x");
            remove.type = "button";
            remove.dataset.drawerAction = "remove";
            remove.dataset.url = item.remove_url;
            remove.dataset.productName = item.name;
            remove.setAttribute("aria-label", "Quitar " + item.name);
            side.append(remove);
            article.append(side);
            return article;
        }

        function renderCart(cart) {
            cartData = cart || { items: [], units: 0, total_label: "$0", is_empty: true };
            updateCartCounters(cartData.units);
            if (totalNode) totalNode.textContent = cartData.total_label || "$0";
            if (checkoutLink) {
                checkoutLink.href = cartData.checkout_url || checkoutLink.href;
                checkoutLink.toggleAttribute("aria-disabled", Boolean(cartData.is_empty));
                checkoutLink.classList.toggle("is-disabled", Boolean(cartData.is_empty));
            }

            itemsContainer.replaceChildren();
            if (cartData.is_empty || !Array.isArray(cartData.items) || !cartData.items.length) {
                const empty = createElement("div", "cart-drawer-empty");
                empty.append(
                    createElement("span", "cart-drawer-empty-mark", "+"),
                    createElement("strong", "", "Tu lista esta lista para empezar"),
                    createElement("p", "", "Guarda una referencia y ajustamos los detalles contigo.")
                );
                const explore = createElement("a", "btn-secondary", "Explorar catalogo");
                explore.href = cartData.catalog_url || "/catalogo/#catalogo";
                empty.append(explore);
                itemsContainer.append(empty);
                return;
            }
            const fragment = document.createDocumentFragment();
            cartData.items.forEach((item) => fragment.append(createDrawerItem(item)));
            itemsContainer.append(fragment);
        }

        async function loadCart(force) {
            if (requestPending || (cartData && !force)) return;
            requestPending = true;
            setLoading();
            try {
                const response = await fetch(drawer.dataset.cartSummaryEndpoint, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                    credentials: "same-origin",
                });
                const data = await response.json();
                if (!response.ok || !data.ok) throw new Error(data.message || "Respuesta invalida");
                renderCart(data.cart);
            } catch (error) {
                setError("Revisa tu conexion e intenta nuevamente.");
            } finally {
                requestPending = false;
            }
        }

        function openDrawer(options) {
            window.clearTimeout(closeTimer);
            previousFocus = document.activeElement;
            layer.hidden = false;
            document.body.classList.add("is-cart-drawer-open");
            toggles.forEach((toggle) => toggle.setAttribute("aria-expanded", "true"));
            window.requestAnimationFrame(() => {
                layer.classList.add("is-open");
                select("[data-cart-drawer-close]", drawer)?.focus({ preventScroll: true });
            });
            loadCart(Boolean(options && options.refresh));
        }

        function closeDrawer() {
            drawer.classList.remove("is-dragging");
            drawer.style.removeProperty("transform");
            layer.classList.remove("is-open");
            document.body.classList.remove("is-cart-drawer-open");
            toggles.forEach((toggle) => toggle.setAttribute("aria-expanded", "false"));
            closeTimer = window.setTimeout(() => {
                layer.hidden = true;
                previousFocus?.focus?.({ preventScroll: true });
            }, 330);
        }

        async function updateItem(url, button, action) {
            if (!url || requestPending) return;
            if (action === "remove") {
                const name = button.dataset.productName || "este producto";
                const confirmed = await (document.confirmStorefrontAction?.("Retirar " + name + " de tu lista") || Promise.resolve(window.confirm("Retirar " + name)));
                if (!confirmed) return;
            }
            requestPending = true;
            button.classList.add("is-request-pending");
            button.disabled = true;
            try {
                const response = await fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    credentials: "same-origin",
                });
                const data = await response.json();
                if (!response.ok || data.ok === false) throw new Error(data.message || "No se pudo actualizar");
                if (data.cart) renderCart(data.cart);
                document.dispatchEvent(new CustomEvent("cart:updated", { detail: data }));
            } catch (error) {
                setError(error.message || "No se pudo actualizar la lista.");
                cartData = null;
            } finally {
                requestPending = false;
                button.classList.remove("is-request-pending");
                button.disabled = false;
            }
        }

        toggles.forEach((toggle) => toggle.addEventListener("click", () => openDrawer()));
        selectAll("[data-cart-drawer-close]", layer).forEach((button) => button.addEventListener("click", closeDrawer));
        const dragHandle = select(".cart-drawer-header", drawer);
        dragHandle?.addEventListener("pointerdown", (event) => {
            if (event.pointerType === "mouse" || event.button !== 0) return;
            if (event.target.closest("button, a, input, select, textarea")) return;
            dragState = {
                pointerId: event.pointerId,
                startY: event.clientY,
                currentY: event.clientY,
                startedAt: performance.now(),
            };
            drawer.classList.add("is-dragging");
            dragHandle.setPointerCapture?.(event.pointerId);
        });
        dragHandle?.addEventListener("pointermove", (event) => {
            if (!dragState || event.pointerId !== dragState.pointerId) return;
            dragState.currentY = event.clientY;
            const distance = Math.max(0, event.clientY - dragState.startY);
            drawer.style.transform = `translateY(${Math.min(distance, drawer.offsetHeight)}px)`;
        });
        const finishDrag = (event) => {
            if (!dragState || event.pointerId !== dragState.pointerId) return;
            const distance = Math.max(0, dragState.currentY - dragState.startY);
            const elapsed = Math.max(1, performance.now() - dragState.startedAt);
            const velocity = distance / elapsed;
            dragState = null;
            drawer.classList.remove("is-dragging");
            drawer.style.removeProperty("transform");
            if (distance >= 82 || velocity >= 0.55) closeDrawer();
        };
        dragHandle?.addEventListener("pointerup", finishDrag);
        dragHandle?.addEventListener("pointercancel", finishDrag);
        layer.addEventListener("keydown", (event) => {
            if (event.key === "Escape") closeDrawer();
            if (event.key !== "Tab") return;
            const focusable = selectAll('a[href], button:not([disabled]), input, textarea, select, [tabindex]:not([tabindex="-1"])', drawer)
                .filter((node) => !node.hidden && node.offsetParent !== null);
            if (!focusable.length) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        });
        itemsContainer.addEventListener("click", (event) => {
            const button = event.target.closest("[data-drawer-action]");
            if (!button) return;
            updateItem(button.dataset.url, button, button.dataset.drawerAction);
        });
        checkoutLink?.addEventListener("click", (event) => {
            if (checkoutLink.getAttribute("aria-disabled") === "true") event.preventDefault();
        });

        document.addEventListener("cart:updated", (event) => {
            const detail = event.detail || {};
            if (detail.cart) renderCart(detail.cart);
            else if (typeof detail.cart_total !== "undefined") updateCartCounters(detail.cart_total);
        });
        document.addEventListener("cart:open", (event) => {
            openDrawer({ refresh: Boolean(event.detail?.refresh) });
        });
    }

    function initAssistantSound() {
        const controls = selectAll("[data-assistant-sound]");
        if (!controls.length) return;
        const panel = select("[data-assistant-voice-panel]");
        const voiceSelect = select("[data-assistant-voice]");
        const pauseButton = select("[data-assistant-voice-pause]");
        const status = select("[data-assistant-voice-status]");
        const synthesis = window.speechSynthesis;
        const supported = Boolean(synthesis && window.SpeechSynthesisUtterance);
        let enabled = window.localStorage.getItem("coraVoiceEnabled") === "true";
        let paused = false;
        let voices = [];

        function setStatus(message) {
            if (status) status.textContent = message;
        }

        function normalizeSpeechText(value) {
            return String(value || "")
                .replace(/https?:\/\/\S+/gi, "")
                .replace(/\$\s*([\d.]+)/g, (_, amount) => {
                    const number = Number(String(amount).replace(/\./g, ""));
                    return Number.isFinite(number) ? `${number.toLocaleString("es-CO")} pesos` : amount;
                })
                .replace(/[*_#`>|~]/g, " ")
                .replace(/\s+/g, " ")
                .trim()
                .slice(0, 520);
        }

        function preferredVoices() {
            return synthesis.getVoices()
                .filter((voice) => /^es([-_]|$)/i.test(voice.lang))
                .sort((left, right) => {
                    const rank = (voice) => (/^es[-_]CO/i.test(voice.lang) ? 0 : /^es[-_](MX|US)/i.test(voice.lang) ? 1 : 2);
                    return rank(left) - rank(right) || left.name.localeCompare(right.name);
                });
        }

        function loadVoices() {
            if (!supported || !voiceSelect) return;
            voices = preferredVoices();
            const storedName = window.localStorage.getItem("coraVoiceName") || "";
            voiceSelect.replaceChildren();
            if (!voices.length) {
                const option = new Option("Voz predeterminada", "");
                voiceSelect.add(option);
                voiceSelect.disabled = true;
                return;
            }
            voices.forEach((voice) => voiceSelect.add(new Option(`${voice.name} (${voice.lang})`, voice.name)));
            const selected = voices.find((voice) => voice.name === storedName) || voices[0];
            voiceSelect.value = selected.name;
            voiceSelect.disabled = !enabled;
        }

        function render() {
            if (!supported) {
                enabled = false;
                panel?.classList.add("is-unavailable");
                setStatus("La voz no está disponible en este navegador.");
            }
            controls.forEach((control) => {
                control.setAttribute("aria-pressed", String(enabled));
                control.setAttribute("aria-label", enabled ? "Silenciar voz de Cora" : "Activar voz de Cora");
                control.title = enabled ? "Voz activada" : "Voz desactivada";
            });
            if (voiceSelect) voiceSelect.disabled = !supported || !enabled || !voices.length;
            if (pauseButton) {
                pauseButton.disabled = !supported || !enabled || !synthesis.speaking;
                pauseButton.textContent = paused ? "Continuar" : "Pausar";
            }
            if (supported && !synthesis.speaking) setStatus(enabled ? "Voz activada" : "Voz desactivada");
        }

        function stopSpeech() {
            if (!supported) return;
            synthesis.cancel();
            paused = false;
            render();
        }

        function speak(event) {
            if (!enabled || !supported) return;
            const text = normalizeSpeechText(event.detail?.reply || event.detail?.text || "");
            if (!text) return;
            synthesis.cancel();
            try {
                const utterance = new SpeechSynthesisUtterance(text);
                const selectedVoice = voices.find((voice) => voice.name === voiceSelect?.value) || voices[0];
                if (selectedVoice) utterance.voice = selectedVoice;
                utterance.lang = selectedVoice?.lang || "es-CO";
                utterance.rate = 0.98;
                utterance.pitch = 1.04;
                utterance.volume = 0.94;
                utterance.onstart = () => {
                    paused = false;
                    setStatus("Cora está hablando");
                    render();
                };
                utterance.onend = () => {
                    paused = false;
                    render();
                };
                utterance.onerror = (speechError) => {
                    if (speechError.error !== "interrupted" && speechError.error !== "canceled") {
                        setStatus("No pudimos reproducir la voz.");
                    }
                    paused = false;
                    render();
                };
                synthesis.speak(utterance);
            } catch (error) {
                setStatus("No pudimos reproducir la voz.");
            }
        }

        controls.forEach((control) => control.addEventListener("click", () => {
            if (!supported) return;
            enabled = !enabled;
            window.localStorage.setItem("coraVoiceEnabled", String(enabled));
            if (!enabled) stopSpeech();
            render();
        }));
        voiceSelect?.addEventListener("change", () => {
            window.localStorage.setItem("coraVoiceName", voiceSelect.value);
        });
        pauseButton?.addEventListener("click", () => {
            if (!supported || !synthesis.speaking) return;
            if (synthesis.paused) {
                synthesis.resume();
                paused = false;
                setStatus("Cora está hablando");
            } else {
                synthesis.pause();
                paused = true;
                setStatus("Voz en pausa");
            }
            render();
        });
        if (supported) {
            loadVoices();
            synthesis.addEventListener?.("voiceschanged", loadVoices);
        }
        document.addEventListener("assistant:reply", speak);
        document.addEventListener("assistant:closed", stopSpeech);
        window.addEventListener("pagehide", stopSpeech);
        render();
    }

    function initAssistantDrag() {
        const shell = select("[data-assistant]");
        const panel = select("[data-assistant-panel]", shell);
        const handle = select(".assistant-header", panel);
        if (!shell || !panel || !handle) return;
        const media = window.matchMedia("(min-width: 861px) and (pointer: fine)");
        let drag = null;

        function restore() {
            if (!media.matches) {
                shell.style.removeProperty("left");
                shell.style.removeProperty("top");
                shell.style.removeProperty("right");
                shell.style.removeProperty("bottom");
                return;
            }
            try {
                const position = JSON.parse(window.localStorage.getItem("coraDesktopPosition") || "null");
                if (!position) return;
                shell.style.left = Math.max(8, Math.min(position.left, window.innerWidth - 90)) + "px";
                shell.style.top = Math.max(8, Math.min(position.top, window.innerHeight - 90)) + "px";
                shell.style.right = "auto";
                shell.style.bottom = "auto";
            } catch (error) {
                window.localStorage.removeItem("coraDesktopPosition");
            }
        }

        handle.addEventListener("pointerdown", (event) => {
            if (!media.matches || event.button !== 0 || event.target.closest("button, a, input")) return;
            const rect = shell.getBoundingClientRect();
            drag = { pointerId: event.pointerId, offsetX: event.clientX - rect.left, offsetY: event.clientY - rect.top };
            shell.style.left = rect.left + "px";
            shell.style.top = rect.top + "px";
            shell.style.right = "auto";
            shell.style.bottom = "auto";
            shell.classList.add("is-dragging");
            handle.setPointerCapture(event.pointerId);
            event.preventDefault();
        });

        handle.addEventListener("pointermove", (event) => {
            if (!drag || drag.pointerId !== event.pointerId) return;
            const rect = shell.getBoundingClientRect();
            const left = Math.max(8, Math.min(event.clientX - drag.offsetX, window.innerWidth - rect.width - 8));
            const top = Math.max(8, Math.min(event.clientY - drag.offsetY, window.innerHeight - rect.height - 8));
            shell.style.left = left + "px";
            shell.style.top = top + "px";
        });

        function finishDrag(event) {
            if (!drag || drag.pointerId !== event.pointerId) return;
            drag = null;
            shell.classList.remove("is-dragging");
            handle.releasePointerCapture?.(event.pointerId);
            const rect = shell.getBoundingClientRect();
            window.localStorage.setItem("coraDesktopPosition", JSON.stringify({ left: rect.left, top: rect.top }));
        }

        handle.addEventListener("pointerup", finishDrag);
        handle.addEventListener("pointercancel", finishDrag);
        media.addEventListener?.("change", restore);
        window.addEventListener("resize", restore, { passive: true });
        restore();
    }

    function initVideoExperience() {
        const videos = selectAll("video[data-autoplay-video]");
        videos.forEach((video) => {
            video.controls = false;
            video.removeAttribute("controls");
            video.muted = true;
            video.playsInline = true;
            if ("disablePictureInPicture" in video) video.disablePictureInPicture = true;
        });

        const processSurfaces = [
            select(".hero-process-panel"),
            document.getElementById("proceso-real"),
        ].filter(Boolean);
        if (processSurfaces.length && "IntersectionObserver" in window) {
            const visibleSurfaces = new Set();
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting && entry.intersectionRatio > 0.2) {
                        visibleSurfaces.add(entry.target);
                    } else {
                        visibleSurfaces.delete(entry.target);
                    }
                });
                document.body.classList.toggle(
                    "is-process-video-visible",
                    visibleSurfaces.size > 0,
                );
            }, { threshold: [0, 0.24, 0.5] });
            processSurfaces.forEach((surface) => observer.observe(surface));
        }
    }

    function initCustomerImagePreview() {
        const today = new Date();
        const localToday = new Date(today.getTime() - today.getTimezoneOffset() * 60000)
            .toISOString()
            .slice(0, 10);
        selectAll("input[type='date'][data-min-today]").forEach((input) => {
            input.min = localToday;
        });
        selectAll("[data-customer-image-input]").forEach((input) => {
            const preview = select("[data-customer-image-preview]", input.closest("form"));
            const image = select("img", preview);
            const label = select("span", preview);
            if (!preview || !image || !label) return;
            let objectUrl = "";
            input.addEventListener("change", () => {
                if (objectUrl) URL.revokeObjectURL(objectUrl);
                const file = input.files?.[0];
                if (!file) {
                    preview.classList.remove("is-visible");
                    image.removeAttribute("src");
                    return;
                }
                if (!file.type.startsWith("image/")) {
                    input.value = "";
                    preview.classList.remove("is-visible");
                    return;
                }
                objectUrl = URL.createObjectURL(file);
                image.src = objectUrl;
                image.alt = "Vista previa de la imagen seleccionada";
                label.textContent = file.name;
                preview.classList.add("is-visible");
            });
        });
    }

    function initPrivacyFriendlyTelemetry() {
        const endpoint = "/eventos/";
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
        const nativeFetch = window.fetch.bind(window);

        function track(event, details = {}) {
            if (!event || navigator.doNotTrack === "1") return;
            const payload = {
                event,
                path: window.location.pathname,
                product_id: details.product_id || null,
                context: details.context || {},
            };
            nativeFetch(endpoint, {
                method: "POST",
                credentials: "same-origin",
                keepalive: true,
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: JSON.stringify(payload),
            }).catch(() => {});
        }

        window.fetch = async (...args) => {
            const target = typeof args[0] === "string" ? args[0] : args[0]?.url || "";
            let isTelemetryRequest = false;
            try {
                isTelemetryRequest = new URL(target, window.location.origin).pathname === endpoint;
            } catch (error) {
                isTelemetryRequest = false;
            }
            try {
                const response = await nativeFetch(...args);
                if (!isTelemetryRequest && !response.ok) {
                    track("server_error", {
                        context: { component: "fetch", status: String(response.status), code: "http_error" },
                    });
                }
                return response;
            } catch (error) {
                if (!isTelemetryRequest) {
                    track("server_error", {
                        context: { component: "fetch", status: "network", code: "request_failed" },
                    });
                }
                throw error;
            }
        };

        const pageKey = `telemetry:page:${window.location.pathname}`;
        if (!window.sessionStorage.getItem(pageKey)) {
            window.sessionStorage.setItem(pageKey, "1");
            track("page_view", { context: { source: document.referrer ? "referral" : "direct" } });
        }
        const productId = document.querySelector('meta[name="assistant-product-id"]')?.content;
        if (productId) track("product_view", { product_id: productId });
        if (window.location.pathname.startsWith("/cuenta/")) track("auth_view");

        document.addEventListener("cart:updated", (event) => {
            const detail = event.detail || {};
            if (detail.ok && detail.product_id && detail.product_name) {
                track("cart_add", {
                    product_id: detail.product_id,
                    context: { status: detail.quantity_updated ? "quantity_updated" : "added" },
                });
            }
        });
        document.addEventListener("cart:open", () => track("cart_open"));
        document.addEventListener("assistant:reply", (event) => {
            track("assistant_interaction", { context: { mode: event.detail?.mode || "fallback" } });
        });
        document.addEventListener("quote:complete", () => track("quote_complete"));
        document.addEventListener("submit", (event) => {
            const form = event.target.closest("form");
            if (!form) return;
            let component = "form";
            if (form.matches(".js-add-to-cart-form")) component = "product";
            if (form.matches(".cart-item-editor__form")) component = "cart_personalization";
            if (form.matches(".js-whatsapp-checkout-form")) component = "quote";
            if (form.matches(".account-form")) component = "account";

            track("form_submitted", { context: { component } });
            if (component === "quote") track("quote_start");
            if (component === "account") {
                const mode = window.location.pathname.includes("crear")
                    ? "register"
                    : window.location.pathname.includes("cambiar-clave")
                        ? "password_change"
                        : "login";
                track("auth_submit", { context: { mode } });
            }

            if (form.matches(".js-add-to-cart-form")) {
                const hasPersonalization = [...form.elements].some((field) => {
                    if (!field.name || field.name === "csrfmiddlewaretoken" || field.disabled) return false;
                    if (field.type === "file") return Boolean(field.files?.[0]?.size);
                    if (["submit", "button", "hidden"].includes(field.type)) return false;
                    return String(field.value || "").trim().length > 0;
                });
                if (hasPersonalization) {
                    track("product_personalized", { product_id: productId || null });
                }
            }
        }, true);
        if (document.querySelector(".errorlist, .form-error, [aria-invalid='true']")) {
            track("form_error", {
                context: { component: document.querySelector(".account-form") ? "account" : "form", code: "validation_failed" },
            });
        }
        document.addEventListener("error", (event) => {
            const media = event.target?.closest?.("img, video");
            if (media) {
                track("media_error", {
                    context: { component: media.tagName.toLowerCase(), code: media.currentSrc ? "load_failed" : "missing_source" },
                });
            }
        }, true);
        window.addEventListener("error", (event) => {
            const filename = String(event.filename || "inline").split("/").pop();
            track("client_error", {
                context: { component: filename || "inline", code: `line_${event.lineno || 0}` },
            });
        });
        window.addEventListener("unhandledrejection", () => {
            track("client_error", { context: { component: "promise", code: "unhandled_rejection" } });
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        initConfirmationDialog();
        initCartDrawer();
        initAssistantSound();
        initAssistantDrag();
        initVideoExperience();
        initCustomerImagePreview();
        initPrivacyFriendlyTelemetry();
    });
})();
