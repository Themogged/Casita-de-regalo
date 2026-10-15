(() => {
    'use strict';

    const dangerousActions = {
        marcar_agotado: 'Los productos seleccionados dejarán de aparecer como disponibles. ¿Deseas continuar?',
        restablecer_stock_100: 'El stock de los productos seleccionados cambiará a 100. ¿Deseas continuar?',
        desactivar_videos: 'Los videos seleccionados dejarán de mostrarse en la tienda. ¿Deseas continuar?',
    };

    const enhanceActions = () => {
        document.querySelectorAll('#changelist-form .actions').forEach((container) => {
            const button = container.querySelector('button[type="submit"]');
            if (button && ['run', 'go', 'ejecutar'].includes(button.textContent.trim().toLowerCase())) {
                button.textContent = 'Aplicar acción';
            }

            const select = container.querySelector('select[name="action"]');
            if (select && !select.getAttribute('aria-label')) {
                select.setAttribute('aria-label', 'Acción para los registros seleccionados');
            }
        });

        const form = document.querySelector('#changelist-form');
        if (!form) return;
        form.addEventListener('submit', (event) => {
            const action = form.querySelector('select[name="action"]')?.value;
            const message = dangerousActions[action];
            if (!message) return;
            const selected = form.querySelectorAll('input.action-select:checked').length;
            if (selected && !window.confirm(message)) event.preventDefault();
        });
    };

    const enhanceSearch = () => {
        const search = document.querySelector('#searchbar');
        if (!search) return;

        const placeholders = [
            ['model-producto', 'Buscar producto por nombre o descripción'],
            ['model-videoelaboracion', 'Buscar video por título o descripción'],
            ['model-pedido', 'Buscar pedido, cliente o teléfono'],
            ['model-categoria', 'Buscar categoría'],
        ];
        const match = placeholders.find(([bodyClass]) => document.body.classList.contains(bodyClass));
        search.placeholder = match?.[1] || 'Buscar en esta sección';
        search.setAttribute('aria-label', search.placeholder);
    };

    const addFilePreview = (input, mediaType) => {
        if (!input || input.dataset.casitaPreviewReady === 'true') return;
        input.dataset.casitaPreviewReady = 'true';
        const preview = document.createElement('div');
        preview.className = 'casita-file-preview';
        input.insertAdjacentElement('afterend', preview);
        let objectUrl = null;

        input.addEventListener('change', () => {
            if (objectUrl) URL.revokeObjectURL(objectUrl);
            objectUrl = null;
            preview.replaceChildren();
            preview.classList.remove('is-visible');

            const file = input.files?.[0];
            if (!file) return;
            objectUrl = URL.createObjectURL(file);
            const element = document.createElement(mediaType);
            element.src = objectUrl;
            element.alt = mediaType === 'img' ? 'Vista previa del archivo seleccionado' : '';
            if (mediaType === 'video') {
                element.controls = true;
                element.muted = true;
                element.preload = 'metadata';
            }
            preview.appendChild(element);
            preview.classList.add('is-visible');
        });
    };

    const enhanceFileInputs = () => {
        addFilePreview(document.querySelector('#id_imagen'), 'img');
        addFilePreview(document.querySelector('#id_portada'), 'img');
        addFilePreview(document.querySelector('#id_video'), 'video');
    };

    document.addEventListener('DOMContentLoaded', () => {
        enhanceActions();
        enhanceSearch();
        enhanceFileInputs();
    });
})();
