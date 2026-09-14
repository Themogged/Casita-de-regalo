const storefrontLinks = document.currentScript.dataset;
const initMobileMenu = () => {
            const header = document.querySelector('.site-header');
            const toggle = document.querySelector('[data-menu-toggle]');
            const menu = document.querySelector('#main-menu');
            if (!header || !toggle || !menu) return;

            const mobileQuery = window.matchMedia('(max-width: 767px)');

            const closeMenu = () => {
                header.classList.remove('is-menu-open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.setAttribute('aria-label', 'Abrir menú');
                menu.inert = mobileQuery.matches;
            };

            const toggleMenu = () => {
                const shouldOpen = !header.classList.contains('is-menu-open');
                header.classList.toggle('is-menu-open', shouldOpen);
                toggle.setAttribute('aria-expanded', String(shouldOpen));
                toggle.setAttribute('aria-label', shouldOpen ? 'Cerrar menú' : 'Abrir menú');
                menu.inert = mobileQuery.matches && !shouldOpen;
            };

            toggle.addEventListener('click', (event) => {
                event.stopPropagation();
                toggleMenu();
            });

            menu.addEventListener('click', (event) => {
                if (event.target.closest('a')) closeMenu();
            });

            document.addEventListener('click', (event) => {
                if (!mobileQuery.matches) return;
                if (!header.classList.contains('is-menu-open')) return;
                if (header.contains(event.target)) return;
                closeMenu();
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && header.classList.contains('is-menu-open')) {
                    closeMenu();
                    toggle.focus();
                }
            });

            mobileQuery.addEventListener('change', (event) => {
                closeMenu();
            });
            closeMenu();
        };

        const getMessagesContainer = () => {
            let container = document.querySelector('.messages');
            if (!container) {
                container = document.createElement('div');
                container.className = 'messages';
                document.body.appendChild(container);
            }
            return container;
        };

        const getToastMeta = (level = 'success', options = {}) => {
            const variant = options.variant || level || 'success';
            const defaults = {
                'cart-added': {
                    title: 'Agregado a la lista',
                    icon: '\u2713',
                    detail: 'Puedes revisar tu lista cuando quieras.',
                },
                'cart-updated': {
                    title: 'Lista actualizada',
                    icon: '\u2713',
                    detail: 'Tu lista quedo al dia.',
                },
                'cart-removed': {
                    title: 'Retirado de la lista',
                    icon: '\u2212',
                    detail: 'Producto retirado correctamente.',
                },
                checkout: {
                    title: 'WhatsApp listo',
                    icon: '\u2713',
                    detail: 'Abrimos tu cotizacion organizada.',
                },
                warning: {
                    title: 'Revisa esto',
                    icon: '!',
                    detail: 'Hay un detalle por confirmar.',
                },
                error: {
                    title: 'No se pudo completar',
                    icon: '!',
                    detail: 'Intentalo nuevamente.',
                },
                success: {
                    title: 'Lista actualizada',
                    icon: '\u2713',
                    detail: 'Cambio guardado correctamente.',
                },
            };

            return {
                ...(defaults[variant] || defaults[level] || defaults.success),
                ...options,
                variant,
            };
        };

        const showToast = (message, level = 'success', options = {}) => {
            const container = getMessagesContainer();
            const item = document.createElement('div');
            const meta = getToastMeta(level, options);
            const hasAction = Boolean(meta.actionHref);
            const isProductToast = Boolean(meta.productName || meta.thumbnailUrl);
            const duration = Number(meta.duration) || 3600;
            let dismissTimer;
            let removeTimer;

            if (isProductToast) {
                container.querySelectorAll('.message--product-toast').forEach((toast) => toast.remove());
            }

            const dismiss = () => {
                if (item.classList.contains('is-leaving')) return;
                window.clearTimeout(dismissTimer);
                window.clearTimeout(removeTimer);
                item.classList.add('is-leaving');
                removeTimer = window.setTimeout(() => item.remove(), 280);
            };

            item.className = `message message--toast ${level}`;
            if (meta.variant) {
                item.classList.add(`message--${meta.variant}`);
            }
            if (hasAction) {
                item.classList.add('has-action');
            }
            if (isProductToast) {
                item.classList.add('message--product-toast');
            }
            item.setAttribute('role', level === 'error' ? 'alert' : 'status');

            let icon;
            if (isProductToast) {
                icon = document.createElement('span');
                icon.className = 'toast-thumbnail';
                icon.setAttribute('aria-hidden', 'true');
                if (meta.thumbnailUrl) {
                    const image = document.createElement('img');
                    image.src = meta.thumbnailUrl;
                    image.alt = '';
                    image.loading = 'eager';
                    image.decoding = 'async';
                    icon.append(image);
                } else {
                    icon.textContent = meta.icon;
                }
            } else {
                icon = document.createElement('span');
                icon.className = 'toast-check';
                icon.setAttribute('aria-hidden', 'true');
                icon.textContent = meta.icon;
            }

            const copy = document.createElement('span');
            copy.className = 'toast-copy';

            const title = document.createElement('strong');
            title.className = 'toast-title';
            title.textContent = meta.title;

            const detail = document.createElement('span');
            detail.className = 'toast-detail';
            detail.textContent = meta.productName || message || meta.detail;

            copy.append(title, detail);
            item.append(icon, copy);

            if (hasAction) {
                const action = meta.actionCallback
                    ? document.createElement('button')
                    : document.createElement('a');
                action.className = 'toast-action';
                if (meta.actionCallback) {
                    action.type = 'button';
                    action.addEventListener('click', () => {
                        meta.actionCallback();
                        dismiss();
                    });
                } else {
                    action.href = meta.actionHref;
                }
                action.textContent = meta.actionLabel || 'Ver lista';
                if (isProductToast) {
                    const actions = document.createElement('span');
                    actions.className = 'toast-inline-actions';
                    actions.append(action);
                    copy.append(actions);
                } else {
                    item.append(action);
                }
            }

            if (isProductToast) {
                const close = document.createElement('button');
                close.type = 'button';
                close.className = 'toast-dismiss';
                close.setAttribute('aria-label', 'Cerrar confirmación');
                close.textContent = '\u00d7';
                close.addEventListener('click', dismiss);
                item.append(close);
            }
            container.appendChild(item);

            dismissTimer = window.setTimeout(dismiss, duration);
        };

        const showAddToCartToast = (data, response) => {
            const level = data.level || (response.ok ? 'success' : 'warning');
            const isSuccessfulAdd = data.ok === true && response.ok;
            const quantityUpdated = isSuccessfulAdd && data.quantity_updated === true;
            const cartItem = Array.isArray(data.cart?.items)
                ? data.cart.items.find((item) => item.id === data.item_id)
                : null;

            showToast(
                data.message || 'Producto actualizado.',
                level,
                {
                    variant: isSuccessfulAdd
                        ? (quantityUpdated ? 'cart-quantity' : 'cart-added')
                        : 'warning',
                    title: isSuccessfulAdd
                        ? (quantityUpdated ? 'Cantidad actualizada' : 'Agregado a tu lista')
                        : 'Revisa disponibilidad',
                    productName: isSuccessfulAdd
                        ? (data.product_name || cartItem?.name || data.message)
                        : '',
                    thumbnailUrl: isSuccessfulAdd
                        ? (data.product_image_url || cartItem?.image_url || '')
                        : '',
                    actionHref: isSuccessfulAdd ? '#cart-drawer' : '',
                    actionCallback: isSuccessfulAdd
                        ? () => document.dispatchEvent(new CustomEvent('cart:open', {
                            detail: { refresh: false },
                        }))
                        : null,
                    actionLabel: 'Ver lista',
                    duration: 3800,
                },
            );
        };

        const updateCartCount = (value) => {
            document.querySelectorAll('.cart-count').forEach((node) => {
                node.textContent = value;
            });
        };

        const getCartAnimationTarget = () => {
            return Array.from(document.querySelectorAll('.cart-btn')).find((node) => {
                const rect = node.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            });
        };

        const confirmAddToCart = (button, nextCartTotal) => {
            updateCartCount(nextCartTotal);
            button.classList.add('is-confirmed');

            const target = getCartAnimationTarget();
            if (!target) return;
            target.classList.add('is-receiving');
            window.setTimeout(() => target.classList.remove('is-receiving'), 560);
        };

        const updateCartPageState = (data) => {
            if (!data || typeof data !== 'object') return;

            if (typeof data.cart_total !== 'undefined') {
                updateCartCount(data.cart_total);
            }

            if (data.total_label) {
                document.querySelectorAll('[data-cart-total-label]').forEach((node) => {
                    node.textContent = data.total_label;
                });
            }

            if (typeof data.references_count !== 'undefined') {
                const count = Number(data.references_count) || 0;
                const plural = count === 1 ? '' : 's';
                document.querySelectorAll('[data-cart-reference-count]').forEach((node) => {
                    node.textContent = count;
                });
                document.querySelectorAll('[data-cart-reference-label]').forEach((node) => {
                    node.textContent = `referencia${plural} para cotizar`;
                });
                document.querySelectorAll('[data-cart-reference-summary]').forEach((node) => {
                    node.textContent = `${count} referencia${plural} lista${plural} para cotizar.`;
                });
            }

            const row = data.item_id
                ? document.querySelector(`[data-cart-row="${data.item_id}"]`)
                : null;

            if (row && data.item_removed) {
                row.remove();
            } else if (row) {
                row.classList.remove('is-updating');
                const quantityNode = row.querySelector('[data-cart-item-qty]');
                const subtotalNode = row.querySelector('[data-cart-item-subtotal]');
                const increaseButton = row.querySelector('[data-cart-increase-button]');

                if (quantityNode && typeof data.item_quantity !== 'undefined') {
                    quantityNode.textContent = data.item_quantity;
                }
                if (subtotalNode && data.item_subtotal_label) {
                    subtotalNode.textContent = data.item_subtotal_label;
                }

                row.querySelectorAll('.qty-btn, .remove-btn').forEach((button) => {
                    button.disabled = false;
                    button.classList.remove('is-disabled');
                });

                if (increaseButton) {
                    const shouldDisable = Number(data.item_quantity) >= Number(data.item_stock);
                    increaseButton.disabled = shouldDisable;
                    increaseButton.classList.toggle('is-disabled', shouldDisable);
                }
            }

            if (data.is_empty && data.cart_url) {
                window.setTimeout(() => {
                    window.location.assign(data.cart_url);
                }, data.item_removed ? 1500 : 520);
            }
        };

        const syncCarousel = (shell) => {
            const track = shell.querySelector('.js-carousel-track');
            const prev = shell.querySelector('[data-carousel-prev]');
            const next = shell.querySelector('[data-carousel-next]');
            if (!track || !prev || !next) return;

            const maxScroll = Math.max(0, track.scrollWidth - track.clientWidth);
            const hasOverflow = maxScroll > 8;

            prev.hidden = !hasOverflow;
            next.hidden = !hasOverflow;
            prev.disabled = !hasOverflow || track.scrollLeft <= 6;
            next.disabled = !hasOverflow || track.scrollLeft >= maxScroll - 6;
        };

        const bindCarousel = (shell) => {
            if (shell.dataset.carouselReady === 'true') {
                syncCarousel(shell);
                return;
            }

            const track = shell.querySelector('.js-carousel-track');
            const prev = shell.querySelector('[data-carousel-prev]');
            const next = shell.querySelector('[data-carousel-next]');
            if (!track || !prev || !next) return;

            const step = () => Math.max(220, Math.floor(track.clientWidth * 0.78));

            prev.addEventListener('click', () => {
                track.scrollBy({ left: -step(), behavior: 'smooth' });
            });

            next.addEventListener('click', () => {
                track.scrollBy({ left: step(), behavior: 'smooth' });
            });

            track.addEventListener('scroll', () => syncCarousel(shell), { passive: true });
            shell.dataset.carouselReady = 'true';
            syncCarousel(shell);
        };

        const initCarousels = (scope = document) => {
            scope.querySelectorAll('.js-carousel').forEach((shell) => bindCarousel(shell));
        };

        const initMobileCatalogPanels = (scope = document) => {
            if (!window.matchMedia('(max-width: 760px)').matches) return;

            scope.querySelectorAll('.sidebar-panel').forEach((panel) => {
                const searchValue = panel.querySelector('input[name="q"]')?.value?.trim() || '';
                const categoryValue = panel.querySelector('select[name="categoria"]')?.value || '';
                const orderValue = panel.querySelector('select[name="orden"]')?.value || '';
                const hasActiveFilters = Boolean(
                    searchValue
                    || categoryValue
                    || (orderValue && orderValue !== 'destacados')
                );

                panel.open = hasActiveFilters;
            });
        };

        const initMobileCategoryMore = (scope = document) => {
            scope.querySelectorAll('.category-more, .catalog-chip-more').forEach((details) => {
                if (details.dataset.mobileCategoryReady === 'true') return;
                details.dataset.mobileCategoryReady = 'true';

                details.addEventListener('toggle', () => {
                    if (!details.open || !window.matchMedia('(max-width: 760px)').matches) return;

                    const row = details.closest('.category-strip-inner, .catalog-chip-row');
                    const summary = details.querySelector(':scope > summary');
                    if (!row || !summary) return;

                    window.requestAnimationFrame(() => {
                        summary.scrollIntoView({
                            block: 'nearest',
                            inline: 'start',
                            behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
                        });
                    });
                });
            });
        };

        const initAutoplayVideos = (scope = document) => {
            const videos = Array.from(scope.querySelectorAll('video[data-autoplay-video]'));
            if (!videos.length) return;

            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            const effectiveType = connection?.effectiveType || '';
            const prefersReducedData = connection?.saveData === true;
            const hasSlowConnection = ['slow-2g', '2g', '3g'].includes(effectiveType);
            const avoidsBackgroundLoading = prefersReducedData || hasSlowConnection;
            let activeVideo = null;
            let backgroundVideoHydrated = false;

            const getVideoUi = (video) => {
                const media = video?.closest('.process-video-media, .hero-process-media');
                return {
                    media,
                    toggle: media?.querySelector('[data-video-toggle]'),
                    mute: media?.querySelector('[data-video-mute]'),
                };
            };

            const syncVideoControls = (video) => {
                const { toggle, mute } = getVideoUi(video);
                if (toggle) {
                    toggle.textContent = video.paused ? 'Reproducir' : 'Pausar';
                    toggle.setAttribute('aria-label', video.paused ? 'Reproducir video' : 'Pausar video');
                }
                if (mute) {
                    mute.textContent = video.muted ? 'Audio' : 'Silenciar';
                    mute.setAttribute('aria-label', video.muted ? 'Activar audio' : 'Silenciar video');
                }
            };

            const setVideoState = (video, state) => {
                const { media } = getVideoUi(video);
                if (!media) return;

                media.dataset.videoLoadState = state;
                media.classList.toggle('is-loading', state === 'loading');
                media.classList.toggle('has-video-error', state === 'error');
            };

            const hydrateVideo = (video) => {
                if (!video || video.dataset.videoLoaded === 'true') return false;
                const sources = Array.from(video.querySelectorAll('source[data-src]'));
                sources.forEach((source) => {
                    source.src = source.dataset.src;
                    source.removeAttribute('data-src');
                });
                video.dataset.videoLoaded = 'true';
                video.preload = 'metadata';
                setVideoState(video, 'loading');
                video.load();
                return true;
            };

            const pauseVideo = (video) => {
                if (!video || video.paused) return;
                video.pause();
            };

            const playVideo = async (video, { preserveAudio = false } = {}) => {
                if (!video || video.dataset.userPaused === 'true' || (activeVideo === video && !video.paused)) return;
                const hydratedNow = hydrateVideo(video);
                const { media } = getVideoUi(video);
                if (!hydratedNow && media?.dataset.videoLoadState === 'error') {
                    setVideoState(video, 'loading');
                    video.load();
                }
                videos.forEach((item) => {
                    if (item !== video) pauseVideo(item);
                });
                activeVideo = video;
                if (!preserveAudio) video.muted = true;
                video.playsInline = true;

                try {
                    await video.play();
                } catch (error) {
                    activeVideo = null;
                    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
                        setVideoState(video, 'ready');
                    }
                }
            };

            videos.forEach((video) => {
                const { media } = getVideoUi(video);
                video.autoplay = false;
                video.removeAttribute('autoplay');
                video.muted = true;
                video.loop = true;
                video.playsInline = true;
                video.controls = false;
                video.removeAttribute('controls');
                video.addEventListener('canplay', () => {
                    media?.classList.add('is-video-ready');
                    setVideoState(video, video.paused ? 'ready' : 'playing');
                    syncVideoControls(video);
                });
                video.addEventListener('play', () => {
                    media?.classList.add('is-playing', 'is-video-ready');
                    setVideoState(video, 'playing');
                    syncVideoControls(video);
                });
                video.addEventListener('pause', () => {
                    media?.classList.remove('is-playing');
                    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
                        setVideoState(video, 'ready');
                    }
                    syncVideoControls(video);
                });
                video.addEventListener('ended', () => {
                    media?.classList.remove('is-playing');
                    setVideoState(video, 'ready');
                    if (activeVideo === video) activeVideo = null;
                });
                video.addEventListener('error', () => {
                    media?.classList.remove('is-playing', 'is-video-ready');
                    setVideoState(video, 'error');
                    if (activeVideo === video) activeVideo = null;
                });

                const { toggle, mute } = getVideoUi(video);
                toggle?.addEventListener('click', async () => {
                    if (video.paused) {
                        video.dataset.userPaused = 'false';
                        await playVideo(video, { preserveAudio: true });
                    } else {
                        video.dataset.userPaused = 'true';
                        if (activeVideo === video) activeVideo = null;
                        pauseVideo(video);
                    }
                    syncVideoControls(video);
                });
                mute?.addEventListener('click', async () => {
                    video.muted = !video.muted;
                    if (!video.muted && video.paused) {
                        video.dataset.userPaused = 'false';
                        await playVideo(video, { preserveAudio: true });
                    }
                    syncVideoControls(video);
                });
                syncVideoControls(video);
            });

            if (!('IntersectionObserver' in window) || avoidsBackgroundLoading) return;

            const preloadObserver = new IntersectionObserver((entries, observer) => {
                if (backgroundVideoHydrated) return;
                const candidate = entries
                    .filter((entry) => entry.isIntersecting && entry.intersectionRatio >= 0.35)
                    .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];
                if (!candidate) return;

                backgroundVideoHydrated = true;
                hydrateVideo(candidate.target);
                observer.disconnect();
            }, {
                rootMargin: '40px 0px',
                threshold: [0.35, 0.6],
            });

            videos.forEach((video) => preloadObserver.observe(video));
            if (prefersReducedMotion) return;

            const observer = new IntersectionObserver((entries) => {
                const candidate = entries
                    .filter((entry) => entry.isIntersecting && entry.intersectionRatio >= 0.55 && entry.target.dataset.userPaused !== 'true')
                    .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];

                entries.forEach((entry) => {
                    const video = entry.target;
                    if (!entry.isIntersecting || entry.intersectionRatio < 0.55) {
                        if (activeVideo === video) activeVideo = null;
                        pauseVideo(video);
                    }
                });

                if (candidate) playVideo(candidate.target);
            }, {
                threshold: [0, 0.35, 0.55, 0.8],
                rootMargin: '-4% 0px -8% 0px',
            });

            videos.forEach((video) => observer.observe(video));
        };

        const normalizeAssistantText = (value) => (
            (value || '')
                .toLowerCase()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .replace(/[^a-z0-9\s]/g, ' ')
                .replace(/\s+/g, ' ')
                .trim()
        );

        const buildAssistantCategoryActions = () => {
            return [...document.querySelectorAll('.category-strip .category-pill')]
                .map((link) => ({
                    label: link.textContent.trim(),
                    href: link.href,
                    keywords: normalizeAssistantText(link.textContent),
                }))
                .filter((item) => item.label && item.href);
        };

        const assistantCategories = buildAssistantCategoryActions();

        const readAssistantHistory = () => {
            try {
                const stored = JSON.parse(window.sessionStorage.getItem('coraConversation') || '[]');
                return Array.isArray(stored) ? stored.slice(-20) : [];
            } catch (error) {
                return [];
            }
        };

        const assistantState = {
            greeted: false,
            history: readAssistantHistory(),
            privateHistory: [],
            mode: 'fallback',
            pending: false,
        };

        const assistantElements = {
            shell: document.querySelector('[data-assistant]'),
            panel: document.querySelector('[data-assistant-panel]'),
            toggle: document.querySelector('[data-assistant-toggle]'),
            close: document.querySelector('[data-assistant-close]'),
            messages: document.querySelector('[data-assistant-messages]'),
            form: document.querySelector('[data-assistant-form]'),
            input: document.querySelector('[data-assistant-input]'),
            send: document.querySelector('[data-assistant-send]'),
            suggestions: document.querySelector('[data-assistant-suggestions]'),
            status: document.querySelector('[data-assistant-status]'),
            privateSession: document.querySelector('[data-assistant-private]'),
        };

        const assistantGestureTimers = {};
        const playAssistantGesture = (gesture, duration = 800) => {
            const { shell } = assistantElements;
            if (!shell) return;

            const className = `is-${gesture}`;
            window.clearTimeout(assistantGestureTimers[gesture]);
            shell.classList.remove(className);
            void shell.offsetWidth;
            shell.classList.add(className);
            assistantGestureTimers[gesture] = window.setTimeout(() => {
                shell.classList.remove(className);
            }, duration);
        };

        const appendAssistantMessage = ({ role = 'bot', text = '', actions = [] }) => {
            const { messages, shell } = assistantElements;
            if (!messages) return;

            const wrapper = document.createElement('div');
            wrapper.className = `assistant-message is-${role}`;

            if (role === 'bot' && shell?.dataset.assistantAvatar) {
                const avatar = document.createElement('span');
                avatar.className = 'assistant-message-avatar';
                avatar.setAttribute('aria-hidden', 'true');

                const avatarImage = document.createElement('img');
                avatarImage.src = shell.dataset.assistantAvatar;
                avatarImage.alt = '';
                avatarImage.width = 30;
                avatarImage.height = 30;
                avatarImage.decoding = 'async';
                avatar.appendChild(avatarImage);
                wrapper.appendChild(avatar);
            }

            const bubble = document.createElement('div');
            bubble.className = 'assistant-bubble';
            bubble.textContent = text;
            wrapper.appendChild(bubble);

            if (actions.length) {
                const actionsRow = document.createElement('div');
                actionsRow.className = 'assistant-actions';

                actions.forEach((action) => {
                    if (action.href) {
                        const link = document.createElement('a');
                        link.className = 'assistant-action';
                        link.href = action.href;
                        link.textContent = action.label;
                        if (action.external) {
                            link.target = '_blank';
                            link.rel = 'noopener noreferrer';
                        }
                        actionsRow.appendChild(link);
                        return;
                    }

                    if (action.prompt) {
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.className = 'assistant-action';
                        button.dataset.assistantPrompt = action.prompt;
                        button.textContent = action.label;
                        actionsRow.appendChild(button);
                    }
                });

                wrapper.appendChild(actionsRow);
            }

            messages.appendChild(wrapper);
            messages.scrollTop = messages.scrollHeight;
            return wrapper;
        };

        const updateAssistantStatus = (mode = 'fallback') => {
            const { status } = assistantElements;
            if (!status) return;

            assistantState.mode = mode;
            status.classList.toggle('is-fallback', mode !== 'ai');
            status.textContent = mode === 'ai' ? 'Asesoría conectada' : 'Guía del catálogo';
        };

        const pushAssistantHistory = (role, text) => {
            if (!text) return;
            const isPrivate = assistantElements.privateSession?.checked === true;
            const target = isPrivate ? 'privateHistory' : 'history';
            assistantState[target].push({ role, text });
            assistantState[target] = assistantState[target].slice(-20);
            if (isPrivate) return;
            try {
                window.sessionStorage.setItem('coraConversation', JSON.stringify(assistantState.history));
            } catch (error) {
                // La conversación sigue disponible en la sesión de Django.
            }
        };

        const showAssistantTyping = () => {
            const node = appendAssistantMessage({
                role: 'bot',
                text: 'Buscando la mejor orientación...',
                actions: [],
            });
            node?.classList.add('is-typing');
            return node;
        };

        const getAssistantWelcome = () => ({
            text: 'Hola, soy Cora. Cuéntame para quién es, la fecha y tu presupuesto; te recomiendo opciones reales y te ayudo a preparar la cotización.',
            actions: [],
        });

        const assistantEndpoint = assistantElements.shell?.dataset.assistantEndpoint || '';

        const getAssistantPageContext = () => ({
            path: window.location.pathname,
            page_title: document.title,
            product_id: document.querySelector('meta[name="assistant-product-id"]')?.content || '',
            product_name: document.querySelector('meta[name="assistant-product-name"]')?.content || '',
            category: document.querySelector('meta[name="assistant-product-category"]')?.content || '',
            selected_options: document.querySelector('[data-designer-summary]')?.textContent?.trim() || '',
        });

        const assistantFallbackKnowledge = (rawInput) => {
            const input = normalizeAssistantText(rawInput);

            const matchedCategory = assistantCategories.find((item) => {
                const words = item.keywords.split(' ').filter(Boolean);
                return words.some((word) => word.length > 3 && input.includes(word));
            });

            if (matchedCategory) {
                return {
                    text: `Te llevo a ${matchedCategory.label}. Ahí podrás ver las referencias disponibles y elegir la que mejor conecte con tu ocasión.`,
                    actions: [
                        { label: `Abrir ${matchedCategory.label}`, href: matchedCategory.href },
                        { label: 'Hablar por WhatsApp', href: storefrontLinks.whatsappCategory, external: true },
                    ],
                };
            }

            if (input.includes('catalogo') || input.includes('producto') || input.includes('ver todo')) {
                return {
                    text: 'Puedes recorrer el catálogo completo o entrar por categoría si ya tienes una idea más clara del tipo de detalle que buscas.',
                    actions: [
                        { label: 'Ir al catálogo', href: `${window.location.origin}${storefrontLinks.catalog}#catalogo` },
                        { label: 'Explorar categorías', prompt: 'Qué categorías hay' },
                    ],
                };
            }

            if (input.includes('categoria') || input.includes('categorias')) {
                const categoryButtons = assistantCategories.slice(0, 5).map((item) => ({
                    label: item.label,
                    href: item.href,
                }));
                return {
                    text: 'Estas son algunas de las categorías activas que puedes explorar ahora mismo:',
                    actions: categoryButtons,
                };
            }

            if (input.includes('lista') || input.includes('cotizar') || input.includes('cotizacion') || input.includes('carrito') || input.includes('agregar')) {
                return {
                    text: 'La lista para cotizar guarda referencias sin pagar todavía. Agregas productos, revisas cantidades y luego enviamos todo por WhatsApp para confirmar disponibilidad, personalización y valor final.',
                    actions: [
                        { label: 'Ver mi lista', href: `${window.location.origin}${storefrontLinks.cart}` },
                        { label: 'Ver catálogo', href: `${window.location.origin}${storefrontLinks.catalog}#catalogo` },
                    ],
                };
            }

            if (input.includes('medida') || input.includes('armar') || input.includes('crear') || input.includes('disena') || input.includes('diseñar')) {
                return {
                    text: 'Para un regalo a medida eliges una referencia real, ocasión, colores, presupuesto y detalles clave. Con eso Casita ajusta el acabado contigo por WhatsApp.',
                    actions: [
                        { label: 'Armar regalo', href: `${window.location.origin}${storefrontLinks.designer}` },
                        { label: 'Cotizar por WhatsApp', href: storefrontLinks.whatsappPersonalization, external: true },
                    ],
                };
            }

            if (input.includes('como comprar') || input.includes('comprar') || input.includes('proceso') || input.includes('pedido')) {
                return {
                    text: 'El proceso recomendado es: revisas el catálogo, abres el detalle si quieres ver más, agregas a la lista para cotizar y confirmas por WhatsApp disponibilidad, entrega y pago.',
                    actions: [
                        { label: 'Ver cómo comprar', href: `${window.location.origin}${storefrontLinks.howTo}` },
                        { label: 'Ver mi lista', href: `${window.location.origin}${storefrontLinks.cart}` },
                    ],
                };
            }

            if (input.includes('pago') || input.includes('nequi') || input.includes('bancolombia')) {
                return {
                    text: 'Primero se valida disponibilidad, personalización y valor final. Después se coordinan los datos de pago, normalmente por Nequi o Bancolombia.',
                    actions: [
                        { label: 'Ir a medios de pago', href: `${window.location.origin}${storefrontLinks.howTo}` },
                        { label: 'Pedir datos por WhatsApp', href: storefrontLinks.whatsappPayment, external: true },
                    ],
                };
            }

            if (input.includes('personaliz') || input.includes('mensaje') || input.includes('tematica') || input.includes('colores')) {
                return {
                    text: 'Sí. Puedes ajustar colores, mensaje, temática, nombre, estilo y presupuesto. Lo ideal es partir de una referencia del catálogo para que el acabado quede claro.',
                    actions: [
                        { label: 'Armar regalo', href: `${window.location.origin}${storefrontLinks.designer}` },
                        { label: 'Cotizar personalización', href: storefrontLinks.whatsappPersonalization, external: true },
                    ],
                };
            }

            if (input.includes('whatsapp') || input.includes('hablar') || input.includes('asesoria') || input.includes('contacto')) {
                return {
                    text: 'Perfecto. Si ya quieres una atención más directa, te llevo al WhatsApp de Casita para cotizar, confirmar o resolver una duda puntual.',
                    actions: [
                        { label: 'Abrir WhatsApp', href: storefrontLinks.whatsappAssistance, external: true },
                        { label: 'Ir a contacto', href: '#footer' },
                    ],
                };
            }

            if (input.includes('carrito') || input.includes('agregar')) {
                return {
                    text: 'Puedes guardar detalles desde el catálogo o desde la ficha del producto. Luego revisas tu lista para cotizar y confirmas por WhatsApp.',
                    actions: [
                        { label: 'Ver mi lista', href: `${window.location.origin}${storefrontLinks.cart}` },
                        { label: 'Ver catálogo', href: `${window.location.origin}${storefrontLinks.catalog}#catalogo` },
                    ],
                };
            }

            if (input.includes('donde estan') || input.includes('ubicacion') || input.includes('medellin') || input.includes('bello')) {
                return {
                    text: 'Casita de Regalos atiende desde Bello, Antioquia, con cobertura en Medellín y el área metropolitana.',
                    actions: [
                        { label: 'Ver contacto', href: '#footer' },
                        { label: 'Hablar por WhatsApp', href: storefrontLinks.whatsappCoverage, external: true },
                    ],
                };
            }

            if (input.includes('entrega') || input.includes('envio') || input.includes('domicilio') || input.includes('reserva') || input.includes('hoy')) {
                return {
                    text: 'La entrega se coordina por WhatsApp según dirección, horario y disponibilidad. Si puedes, reserva con 1 a 2 días para cuidar mejor el armado.',
                    actions: [
                        { label: 'Cómo comprar', href: `${window.location.origin}${storefrontLinks.howTo}` },
                        { label: 'Consultar entrega', href: storefrontLinks.whatsappCoverage, external: true },
                    ],
                };
            }

            return {
                text: 'Puedo ayudarte con catálogo, lista para cotizar, regalo a medida, pagos, entrega o WhatsApp. Dime para quién es, fecha y presupuesto aproximado para orientarte mejor.',
                actions: [
                    { label: 'Ver catálogo', prompt: 'Quiero ver el catálogo' },
                    { label: 'A medida', prompt: 'Quiero armar un regalo a medida' },
                    { label: 'WhatsApp', prompt: 'Hablar por whatsapp' },
                ],
            };
        };

        const requestAssistantReply = async (message, history) => {
            if (!assistantEndpoint) {
                const fallback = assistantFallbackKnowledge(message);
                return {
                    reply: fallback.text,
                    actions: fallback.actions || [],
                    mode: 'fallback',
                };
            }

            const response = await fetch(assistantEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || '',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    message,
                    history,
                    context: getAssistantPageContext(),
                    private_session: assistantElements.privateSession?.checked === true,
                }),
            });

            if (!response.ok) {
                throw new Error('assistant-request-failed');
            }

            const data = await response.json();
            if (!data.ok || !data.reply) {
                throw new Error('assistant-response-invalid');
            }

            return data;
        };

        const openAssistant = () => {
            const { panel, toggle, input, messages } = assistantElements;
            if (!panel || !toggle || !messages) return;

            panel.hidden = false;
            toggle.setAttribute('aria-expanded', 'true');
            toggle.setAttribute('aria-label', 'Cerrar asistente Cora');
            playAssistantGesture('greeting', 820);

            if (!assistantState.greeted) {
                updateAssistantStatus('fallback');
                if (assistantState.history.length) {
                    assistantState.history.slice(-8).forEach((item) => {
                        appendAssistantMessage({
                            role: item.role === 'assistant' ? 'bot' : 'user',
                            text: item.text,
                        });
                    });
                } else {
                    appendAssistantMessage({ role: 'bot', ...getAssistantWelcome() });
                }
                assistantState.greeted = true;
            }

            if (window.matchMedia('(min-width: 769px) and (pointer: fine)').matches) {
                setTimeout(() => input?.focus(), 60);
            }
        };

        const closeAssistant = () => {
            const { panel, toggle } = assistantElements;
            if (!panel || !toggle) return;
            panel.hidden = true;
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', 'Abrir asistente Cora');
            document.dispatchEvent(new CustomEvent('assistant:closed'));
            toggle.focus({ preventScroll: true });
        };

        const setAssistantPending = (isPending) => {
            const { form, input, send, shell } = assistantElements;
            form?.classList.toggle('is-pending', isPending);
            form?.setAttribute('aria-busy', String(isPending));
            if (input) input.disabled = isPending;
            if (send) send.disabled = isPending;
            shell?.classList.toggle('is-thinking', isPending);
        };

        const handleAssistantPrompt = async (text) => {
            const cleanText = (text || '').trim();
            if (!cleanText || assistantState.pending) return;

            assistantState.pending = true;
            setAssistantPending(true);
            appendAssistantMessage({ role: 'user', text: cleanText });
            const activeHistory = assistantElements.privateSession?.checked
                ? assistantState.privateHistory
                : assistantState.history;
            const historyBeforeRequest = activeHistory.slice(-8);

            const typingNode = showAssistantTyping();

            try {
                const response = await requestAssistantReply(cleanText, historyBeforeRequest);
                typingNode?.remove();
                updateAssistantStatus(response.mode || 'fallback');
                appendAssistantMessage({ role: 'bot', text: response.reply, actions: response.actions || [] });
                document.dispatchEvent(new CustomEvent('assistant:reply', { detail: response }));
                playAssistantGesture('celebrating', 760);
                pushAssistantHistory('user', cleanText);
                pushAssistantHistory('assistant', response.reply);
            } catch (error) {
                typingNode?.remove();
                const fallback = assistantFallbackKnowledge(cleanText);
                updateAssistantStatus('fallback');
                appendAssistantMessage({ role: 'bot', text: fallback.text, actions: fallback.actions || [] });
                document.dispatchEvent(new CustomEvent('assistant:reply', {
                    detail: { reply: fallback.text, actions: fallback.actions || [], mode: 'fallback' },
                }));
                playAssistantGesture('celebrating', 760);
                pushAssistantHistory('user', cleanText);
                pushAssistantHistory('assistant', fallback.text);
            } finally {
                assistantState.pending = false;
                setAssistantPending(false);
            }
        };

        const initAssistant = () => {
            const { shell, panel, toggle, close, form, input, suggestions, privateSession, messages } = assistantElements;
            if (!shell || !panel || !toggle || !close || !form || !input || !suggestions) return;

            toggle.addEventListener('click', () => {
                if (panel.hidden) {
                    openAssistant();
                    return;
                }
                closeAssistant();
            });

            close.addEventListener('click', closeAssistant);

            panel.addEventListener('click', async (event) => {
                const promptButton = event.target.closest('[data-assistant-prompt]');
                if (!promptButton) return;
                await handleAssistantPrompt(promptButton.dataset.assistantPrompt);
            });

            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                const value = input.value.trim();
                if (!value) return;
                await handleAssistantPrompt(value);
                input.value = '';
            });

            privateSession?.addEventListener('change', () => {
                messages.replaceChildren();
                const activeHistory = privateSession.checked
                    ? assistantState.privateHistory
                    : assistantState.history;
                if (activeHistory.length) {
                    activeHistory.slice(-8).forEach((item) => {
                        appendAssistantMessage({
                            role: item.role === 'assistant' ? 'bot' : 'user',
                            text: item.text,
                        });
                    });
                } else {
                    appendAssistantMessage({
                        role: 'bot',
                        text: privateSession.checked
                            ? 'Conversación privada activa. Estos mensajes no se guardarán al salir.'
                            : getAssistantWelcome().text,
                    });
                }
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && !panel.hidden) closeAssistant();
            });
        };

        const scrollToCatalogSection = () => {
            const catalog = document.querySelector('#catalogo');
            if (!catalog) return;

            catalog.scrollIntoView({ behavior: 'smooth', block: 'start' });
        };

        const fetchCatalogSection = async (url, options = {}) => {
            const currentCatalog = document.querySelector('#catalogo');
            if (!currentCatalog) return;
            if (currentCatalog.dataset.loading === 'true') return;

            currentCatalog.dataset.loading = 'true';
            currentCatalog.classList.add('is-loading');

            try {
                const response = await fetch(url, {
                    method: options.method || 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'same-origin',
                    body: options.body || null,
                });

                if (!response.ok) {
                    window.location.href = url;
                    return;
                }

                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const nextCatalog = doc.querySelector('#catalogo');

                if (!nextCatalog) {
                    window.location.href = url;
                    return;
                }

                currentCatalog.replaceWith(nextCatalog);
                initMobileCatalogPanels(nextCatalog);
                initMobileCategoryMore(nextCatalog);
                initCarousels(nextCatalog);
                if (options.pushState !== false) {
                    window.history.pushState({ catalog: true }, '', url);
                }
                scrollToCatalogSection();
            } catch (error) {
                window.location.href = url;
            } finally {
                const catalog = document.querySelector('#catalogo');
                if (catalog) {
                    catalog.dataset.loading = 'false';
                    catalog.classList.remove('is-loading');
                }
            }
        };

        const getCsrfToken = (form) => {
            return (
                form.querySelector('input[name=csrfmiddlewaretoken]')?.value
                || document.querySelector('meta[name="csrf-token"]')?.content
                || ''
            );
        };

        document.addEventListener('submit', async (event) => {
            const catalogForm = event.target.closest('.js-catalog-form');
            if (catalogForm) {
                event.preventDefault();
                const formData = new FormData(catalogForm);
                const params = new URLSearchParams();

                for (const [key, value] of formData.entries()) {
                    const cleanValue = typeof value === 'string' ? value.trim() : value;
                    if (!cleanValue) continue;
                    if (key === 'orden' && cleanValue === 'destacados') continue;
                    params.append(key, cleanValue);
                }

                const baseUrl = catalogForm.action.split('#', 1)[0];
                const queryString = params.toString();
                const targetUrl = `${baseUrl}${queryString ? `?${queryString}` : ''}#catalogo`;
                await fetchCatalogSection(targetUrl);
                return;
            }

            const cartUpdateForm = event.target.closest('.js-cart-update-form');
            if (cartUpdateForm) {
                event.preventDefault();

                const button = event.submitter || cartUpdateForm.querySelector('button');
                const row = cartUpdateForm.closest('[data-cart-row]');
                if (!button || button.dataset.loading === 'true') return;

                const originalText = button.textContent;
                button.dataset.loading = 'true';
                button.disabled = true;
                button.textContent = '...';
                row?.classList.add('is-updating');

                try {
                    const response = await fetch(cartUpdateForm.action, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': getCsrfToken(cartUpdateForm),
                        },
                        credentials: 'same-origin',
                        body: new FormData(cartUpdateForm),
                    });

                    const data = await response.json();
                    updateCartPageState(data);
                    document.dispatchEvent(new CustomEvent('cart:updated', { detail: data }));
                    const updateOk = response.ok && data.ok !== false;
                    const updateVariant = updateOk
                        ? (data.item_removed ? 'cart-removed' : 'cart-updated')
                        : 'warning';
                    const updateTitle = updateOk
                        ? (data.item_removed ? 'Retirado de la lista' : 'Lista actualizada')
                        : 'Revisa tu lista';

                    showToast(
                        data.message || 'Lista actualizada.',
                        data.level || (response.ok ? 'success' : 'warning'),
                        {
                            variant: updateVariant,
                            title: updateTitle,
                        },
                    );
                } catch (error) {
                    row?.classList.remove('is-updating');
                    button.disabled = false;
                    showToast(
                        'No pudimos actualizar la lista en este momento.',
                        'error',
                        {
                            variant: 'error',
                            title: 'No se pudo actualizar',
                        },
                    );
                } finally {
                    button.dataset.loading = 'false';
                    button.textContent = originalText;
                }

                return;
            }

            const checkoutForm = event.target.closest('.js-whatsapp-checkout-form');
            if (checkoutForm) {
                event.preventDefault();

                const button = event.submitter || checkoutForm.querySelector('.js-whatsapp-checkout-button');
                if (!button || button.dataset.loading === 'true') return;

                const originalText = button.textContent.trim();
                button.dataset.loading = 'true';
                button.style.pointerEvents = 'none';
                button.style.opacity = '0.72';
                button.textContent = 'Abriendo WhatsApp...';

                try {
                    const response = await fetch(checkoutForm.action, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': getCsrfToken(checkoutForm),
                        },
                        credentials: 'same-origin',
                        body: new FormData(checkoutForm),
                    });

                    const data = await response.json();
                    const checkoutOk = response.ok && data.ok !== false;
                    showToast(
                        data.message || 'Preparando tu pedido...',
                        data.level || (response.ok ? 'success' : 'warning'),
                        {
                            variant: checkoutOk ? 'checkout' : 'warning',
                            title: checkoutOk ? 'WhatsApp listo' : 'Revisa tu lista',
                        },
                    );

                    if (typeof data.cart_total !== 'undefined') {
                        updateCartCount(data.cart_total);
                    }

                    if (data.whatsapp_url) {
                        document.dispatchEvent(new CustomEvent('quote:complete', {
                            detail: { order_id: data.order_id || null },
                        }));
                        window.location.assign(data.whatsapp_url);
                        return;
                    }

                    if (data.redirect_url) {
                        window.location.assign(data.redirect_url);
                        return;
                    }
                } catch (error) {
                    showToast(
                        'No pudimos abrir WhatsApp en este momento.',
                        'error',
                        {
                            variant: 'error',
                            title: 'WhatsApp no abrio',
                        },
                    );
                } finally {
                    button.dataset.loading = 'false';
                    button.style.pointerEvents = '';
                    button.style.opacity = '';
                    button.textContent = originalText;
                }

                return;
            }

            const form = event.target.closest('.js-add-to-cart-form');
            if (!form) return;

            const button = event.submitter || form.querySelector('.js-add-to-cart');
            if (!button) return;

            event.preventDefault();
            if (button.dataset.loading === 'true') return;

            const originalHtml = button.innerHTML;
            let keepSuccessState = false;
            button.dataset.loading = 'true';
            button.style.pointerEvents = 'none';
            button.style.opacity = '0.72';
            button.textContent = 'Guardando...';

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(form),
                    },
                    credentials: 'same-origin',
                    body: new FormData(form),
                });

                const data = await response.json();
                showAddToCartToast(data, response);
                document.dispatchEvent(new CustomEvent('cart:updated', {
                    detail: data,
                }));

                if (typeof data.cart_total !== 'undefined') {
                    if (data.ok === true && response.ok) {
                        confirmAddToCart(button, data.cart_total);
                        button.textContent = 'Agregado';
                        keepSuccessState = true;
                    } else {
                        updateCartCount(data.cart_total);
                    }
                }
            } catch (error) {
                showToast(
                    'No pudimos guardar el detalle en este momento.',
                    'error',
                    {
                        variant: 'error',
                        title: 'No se pudo guardar',
                    },
                );
            } finally {
                button.dataset.loading = 'false';
                button.style.pointerEvents = '';
                button.style.opacity = '';
                if (keepSuccessState) {
                    window.setTimeout(() => {
                        button.classList.remove('is-confirmed');
                        button.innerHTML = originalHtml;
                    }, 760);
                } else {
                    button.innerHTML = originalHtml;
                }
            }
        });

        document.addEventListener('click', async (event) => {
            const catalogLink = event.target.closest('.js-catalog-nav');
            if (!catalogLink) return;
            if (catalogLink.target && catalogLink.target !== '_self') return;
            if (!document.querySelector('#catalogo')) return;

            const targetUrl = new URL(catalogLink.href, window.location.origin);
            const currentUrl = new URL(window.location.href);

            if (
                targetUrl.pathname === currentUrl.pathname &&
                targetUrl.search === currentUrl.search &&
                targetUrl.hash === '#catalogo'
            ) {
                event.preventDefault();
                scrollToCatalogSection();
                return;
            }

            event.preventDefault();
            await fetchCatalogSection(catalogLink.href);
        });

        window.addEventListener('popstate', async () => {
            if (!window.location.pathname.endsWith('/')) return;
            if (!document.querySelector('#catalogo')) return;
            await fetchCatalogSection(window.location.href, { pushState: false });
        });

        window.addEventListener('resize', () => {
            document.querySelectorAll('.js-carousel').forEach((shell) => syncCarousel(shell));
        });

        initCarousels();
        initMobileMenu();
        initMobileCatalogPanels();
        initMobileCategoryMore();
        initAutoplayVideos();
        initAssistant();
