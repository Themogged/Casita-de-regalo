import json

from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Producto
from .selectors import (
    CATALOG_ATTRIBUTE_OPTIONS,
    CATALOG_FILTER_LABELS,
    CATALOG_OCCASION_OPTIONS,
    CATALOG_ORDER_OPTIONS,
    CATALOG_PERSON_OPTIONS,
    CATALOG_PRICE_OPTIONS,
    CATALOG_TIME_OPTIONS,
    CATALOG_TYPE_OPTIONS,
    get_active_process_videos,
    get_catalog_queryset,
    get_featured_products,
    paginate_products,
)
from .whatsapp import build_whatsapp_url


QUIENES_SOMOS = {
    'titulo': 'Regalos personalizados en Bello y Medellín para fechas que se sienten especiales',
    'descripcion': (
        'Somos una tienda online ubicada en Bello, Antioquia. Creamos desayunos sorpresa, cajas '
        'personalizadas, regalos románticos y detalles temáticos para cumpleaños, aniversarios y '
        'momentos importantes. Te acompañamos por WhatsApp desde la idea inicial hasta la confirmación '
        'del pedido.'
    ),
    'cobertura': 'Bello, Medellín y área metropolitana',
    'promesa': 'Cada detalle se ajusta según gusto, presupuesto, temática y ocasión',
}

PILARES_SERVICIO = [
    {
        'titulo': 'Detalles personalizados',
        'descripcion': 'Desayunos sorpresa, bandejas, cajas, globos, flores y regalos armados según la ocasión.',
        'etiqueta': 'Hecho a medida',
    },
    {
        'titulo': 'Asesoría por WhatsApp',
        'descripcion': 'Cada pedido se conversa, se cotiza y se confirma antes de producirse para evitar errores.',
        'etiqueta': 'Atención directa',
    },
    {
        'titulo': 'Experiencia local cuidada',
        'descripcion': 'Servicio pensado para Bello, Medellín y fechas especiales con presentación impecable.',
        'etiqueta': 'Cobertura cercana',
    },
]

LINEAS_DETALLE = [
    {
        'titulo': 'Cumpleaños y desayunos sorpresa',
        'descripcion': 'Bandejas, cajas, globos, frutas, waffles, snacks y mensajes para sorprender.',
    },
    {
        'titulo': 'Amor, aniversario y románticos',
        'descripcion': 'Rosas, chocolates, corazones, cajas finas y detalles con frases personalizadas.',
    },
    {
        'titulo': 'Infantil y personajes',
        'descripcion': 'Temáticas como Hello Kitty, Mario y propuestas visuales para niños y celebraciones especiales.',
    },
    {
        'titulo': 'Mini detalles y opciones express',
        'descripcion': 'Alternativas más accesibles, útiles para regalos rápidos sin perder identidad visual.',
    },
]

PIEZAS_EDITORIALES = [
    {
        'titulo': 'Quiénes somos',
        'etiqueta': 'Presentación de marca',
        'imagen': 'referencias/referencia-01.png',
        'descripcion': (
            'La marca se presenta como tienda online en Bello, Antioquia, con enfoque en hacer '
            'inolvidables las fechas especiales por medio de detalles personalizados.'
        ),
    },
    {
        'titulo': 'Proceso de compra',
        'etiqueta': 'Compra guiada',
        'imagen': 'referencias/referencia-02.png',
        'descripcion': (
            'El flujo real ya está claro: explorar referencias, elegir el detalle, recibir asesoría '
            'por WhatsApp y confirmar el pago para entrar a producción.'
        ),
    },
    {
        'titulo': 'Políticas y condiciones',
        'etiqueta': 'Confianza y claridad',
        'imagen': 'referencias/referencia-20.png',
        'descripcion': (
            'Las reglas visibles ayudan a que la experiencia se vea profesional: anticipo, tiempos, '
            'personalización, entregas inmediatas según disponibilidad y precios variables.'
        ),
    },
]

COLECCIONES_REFERENCIA = [
    {
        'titulo': 'Cumpleaños y desayunos sorpresa',
        'descripcion': (
            'La línea más fuerte del catálogo visual: cajas, bandejas, globos, frutas, snacks y '
            'desayunos presentados como experiencias listas para regalar.'
        ),
        'mensaje': 'Hola, quiero cotizar una referencia de cumpleaños o desayuno sorpresa.',
        'items': [
            {
                'titulo': 'Cumple azul en madera',
                'etiqueta': 'Cumpleaños',
                'precio': '$81.000 COP',
                'imagen': 'referencias/referencia-03.png',
                'descripcion': 'Referencia con caja en madera, globos, mix de fruta, waffles, jugo y decoración para celebrar con tono elegante.',
                'mensaje': 'Hola, quiero cotizar la referencia Cumple azul en madera.',
            },
            {
                'titulo': 'Desayuno globos pastel',
                'etiqueta': 'Desayuno sorpresa',
                'precio': '$80.000 COP',
                'imagen': 'referencias/referencia-04.png',
                'descripcion': 'Bandejas y desayunos sorpresa con globos, yogurt, fruta, sándwich y detalles visuales suaves.',
                'mensaje': 'Hola, quiero cotizar la referencia Desayuno globos pastel.',
            },
            {
                'titulo': 'Rose gold cumpleañero',
                'etiqueta': 'Cumpleaños',
                'precio': '$77.000 COP',
                'imagen': 'referencias/referencia-07.png',
                'descripcion': 'Caja en madera con globos rose gold, frutas, waffles, postre y mensaje para una celebración delicada.',
                'mensaje': 'Hola, quiero cotizar la referencia Rose gold cumpleañero.',
            },
            {
                'titulo': 'Cumple lila fantasía',
                'etiqueta': 'Cumpleaños',
                'precio': '$75.000 COP',
                'imagen': 'referencias/referencia-08.png',
                'descripcion': 'Opciones juveniles y coloridas con snacks, desayunos y decoración pensadas para regalos personalizados.',
                'mensaje': 'Hola, quiero cotizar la referencia Cumple lila fantasía.',
            },
            {
                'titulo': 'Black and gold deluxe',
                'etiqueta': 'Selección especial',
                'precio': '$94.000 COP',
                'imagen': 'referencias/referencia-09.png',
                'descripcion': 'Detalle con globos negro y dorado, fruta, cereal y una presentación más sofisticada.',
                'mensaje': 'Hola, quiero cotizar la referencia Black and gold deluxe.',
            },
            {
                'titulo': 'Desayuno mariposa rosa',
                'etiqueta': 'Cumpleaños',
                'precio': '$89.000 COP',
                'imagen': 'referencias/referencia-17.png',
                'descripcion': 'Mesa o bandeja en madera con globos en helio, mariposas, yogurt, jugo y decoración femenina.',
                'mensaje': 'Hola, quiero cotizar la referencia Desayuno mariposa rosa.',
            },
            {
                'titulo': 'Combo snack con globos',
                'etiqueta': 'Desayuno sorpresa',
                'precio': '$88.000 COP',
                'imagen': 'referencias/referencia-18.png',
                'descripcion': 'Combinaciones de snacks, globos metalizados y presentaciones compactas para regalos rápidos pero vistosos.',
                'mensaje': 'Hola, quiero cotizar la referencia Combo snack con globos.',
            },
        ],
    },
    {
        'titulo': 'Amor, aniversarios y románticos',
        'descripcion': (
            'Una línea perfecta para aniversarios, parejas, mensajes especiales y regalos con un look '
            'más emocional, elegante y memorable.'
        ),
        'mensaje': 'Hola, quiero cotizar una referencia romántica o de aniversario.',
        'items': [
            {
                'titulo': 'Caja aniversario te amo',
                'etiqueta': 'Aniversario',
                'precio': '$75.000 COP',
                'imagen': 'referencias/referencia-05.png',
                'descripcion': 'Caja con globo burbuja, waffles, jugo y mensaje romántico para aniversarios y sorpresas especiales.',
                'mensaje': 'Hola, quiero cotizar la referencia Caja aniversario te amo.',
            },
            {
                'titulo': 'Amor delicado rosa',
                'etiqueta': 'Romántico',
                'precio': '$89.000 COP',
                'imagen': 'referencias/referencia-06.png',
                'descripcion': 'Presentación suave con tonos rosa, globo y detalles dulces para una sorpresa romántica o de fecha especial.',
                'mensaje': 'Hola, quiero cotizar la referencia Amor delicado rosa.',
            },
            {
                'titulo': 'Trío corazones sorpresa',
                'etiqueta': 'Romántico',
                'precio': '$63.000 COP',
                'imagen': 'referencias/referencia-10.png',
                'descripcion': 'Referencias visuales con corazones, chocolates, rosas y cajas que funcionan muy bien para regalar amor.',
                'mensaje': 'Hola, quiero cotizar la referencia Trío corazones sorpresa.',
            },
            {
                'titulo': 'Buenos días con amor',
                'etiqueta': 'Detalle especial',
                'precio': '$55.000 COP',
                'imagen': 'referencias/referencia-15.png',
                'descripcion': 'Desayunos pequeños y cajas con snacks, bebidas y mensajes para sorprender desde la mañana.',
                'mensaje': 'Hola, quiero cotizar la referencia Buenos días con amor.',
            },
            {
                'titulo': 'Caja corazón especial',
                'etiqueta': 'Romántico',
                'precio': '$122.000 COP',
                'imagen': 'referencias/referencia-19.png',
                'descripcion': 'Caja fina en forma de corazón con sándwich, jugo, rosas, chocolates o peluche para un detalle romántico.',
                'mensaje': 'Hola, quiero cotizar la referencia Caja corazón especial.',
            },
        ],
    },
    {
        'titulo': 'Temáticos, mini detalles y personajes',
        'descripcion': (
            'Aquí vive la parte más versátil del catálogo: personajes, mini regalos, cajas express y '
            'detalles que se adaptan bien a presupuestos más ágiles.'
        ),
        'mensaje': 'Hola, quiero cotizar una referencia temática o mini detalle.',
        'items': [
            {
                'titulo': 'Temáticos con personaje',
                'etiqueta': 'Temático',
                'precio': '$44.000 COP',
                'imagen': 'referencias/referencia-11.png',
                'descripcion': 'Opciones personalizadas con Hello Kitty, Mario, fotos y personajes elegidos según el gusto del cliente.',
                'mensaje': 'Hola, quiero cotizar la referencia Temáticos con personaje.',
            },
            {
                'titulo': 'Mini detalles con globo',
                'etiqueta': 'Express',
                'precio': '$27.000 COP',
                'imagen': 'referencias/referencia-12.png',
                'descripcion': 'Mini regalos listos para fechas puntuales, con globos, snacks, mensajes y formato compacto.',
                'mensaje': 'Hola, quiero cotizar la referencia Mini detalles con globo.',
            },
            {
                'titulo': 'Día especial express',
                'etiqueta': 'Mini detalle',
                'precio': '$28.000 COP',
                'imagen': 'referencias/referencia-16.png',
                'descripcion': 'Detalles pequeños con empaque protagonista, ideales para regalos rápidos, día de la madre o fechas cortas.',
                'mensaje': 'Hola, quiero cotizar la referencia Día especial express.',
            },
        ],
    },
    {
        'titulo': 'Frutales, flores y momentos especiales',
        'descripcion': (
            'Referencias con más impacto visual para fechas especiales, regalos gourmet, flores, fresas y '
            'combinaciones memorables.'
        ),
        'mensaje': 'Hola, quiero cotizar una referencia frutal, con flores o gourmet.',
        'items': [
            {
                'titulo': 'Rosas y fresas especiales',
                'etiqueta': 'Flores y fresas',
                'precio': '$173.000 COP',
                'imagen': 'referencias/referencia-13.png',
                'descripcion': 'Propuestas con rosas, fresas cubiertas, licor y presentaciones cuidadas para sorprender con alto impacto.',
                'mensaje': 'Hola, quiero cotizar la referencia Rosas y fresas especiales.',
            },
            {
                'titulo': 'Bunny y corazón frutal',
                'etiqueta': 'Fecha especial',
                'precio': '$42.000 COP',
                'imagen': 'referencias/referencia-14.png',
                'descripcion': 'Detalles creativos con temática tierna y tablas frutales en forma de corazón para regalos frescos y diferentes.',
                'mensaje': 'Hola, quiero cotizar la referencia Bunny y corazón frutal.',
            },
        ],
    },
]

PASOS_COMPRA = [
    {
        'numero': '01',
        'titulo': 'Explora el catálogo',
        'descripcion': 'Busca por categoría, ocasión o tipo de detalle y guarda tus opciones favoritas.',
    },
    {
        'numero': '02',
        'titulo': 'Personaliza tu pedido',
        'descripcion': 'Elige colores, nombres, temática, mensaje para tarjeta y extras según tu idea.',
    },
    {
        'numero': '03',
        'titulo': 'Confirma por WhatsApp',
        'descripcion': 'Te confirmamos disponibilidad, precio final, domicilio y tiempo de preparación.',
    },
    {
        'numero': '04',
        'titulo': 'Reserva y realiza el pago',
        'descripcion': 'El pedido queda reservado al validar el abono del 50% o el pago total acordado.',
    },
]

METODOS_PAGO = [
    {
        'titulo': 'Nequi',
        'descripcion': '311 626 2155 a nombre de Mónica Gutiérrez. Ideal para confirmar rápido y enviar comprobante por WhatsApp.',
        'logo': 'productos/img/logo-nequi.svg',
    },
    {
        'titulo': 'Bancolombia',
        'descripcion': 'Cuenta de ahorros 58066610009 para reservas y pedidos personalizados confirmados.',
        'logo': 'productos/img/logo-bancolombia.svg',
    },
    {
        'titulo': 'Pago validado',
        'descripcion': 'Primero se valida disponibilidad, personalización y precio final. Luego se confirma el abono o pago completo.',
        'logo': 'productos/img/icon-payment-ok.svg',
    },
]

POLITICAS_CLAVE = [
    'Los pedidos se agendan cuando se confirma disponibilidad y se abona el 50% del valor total.',
    'Por ser detalles personalizados, no se realizan devoluciones una vez iniciado el proceso de elaboración.',
    'Recomendamos hacer pedidos con 1 o 2 días de anticipación para prepararlos con mejor cuidado.',
    'Todas las anchetas y detalles pueden ajustarse según presupuesto, gusto y ocasión del cliente.',
    'Si deseas entrega inmediata, primero consultamos qué referencias e insumos están disponibles.',
    'En cada referencia se muestra lo que incluye el detalle; cualquier cambio o agotado se avisa antes de confirmar.',
    'Los precios publicados son valores base desde y pueden variar según temporada, materiales y personalización.',
]

PREGUNTAS_FRECUENTES = [
    {
        'pregunta': '¿Con cuánto tiempo debo pedir?',
        'respuesta': 'Lo ideal es reservar con 1 o 2 días de anticipación. Si necesitas algo urgente, primero validamos disponibilidad por WhatsApp.',
    },
    {
        'pregunta': '¿Hacen domicilios?',
        'respuesta': 'Sí. Coordinamos entregas en Bello, Medellín y el área metropolitana. El valor del domicilio depende de la zona y se confirma antes de cerrar el pedido.',
    },
    {
        'pregunta': '¿Puedo personalizar colores y temática?',
        'respuesta': 'Sí. Puedes ajustar colores, temática, nombre, mensaje para tarjeta y algunos detalles según disponibilidad y presupuesto.',
    },
    {
        'pregunta': '¿Cómo confirmo mi pedido?',
        'respuesta': 'La selección se revisa por WhatsApp. Allí confirmamos disponibilidad, personalización, domicilio, precio final y el abono o pago acordado.',
    },
    {
        'pregunta': '¿Qué métodos de pago manejan?',
        'respuesta': 'Trabajamos principalmente con Nequi y Bancolombia. Los datos se comparten cuando el detalle queda definido y validado.',
    },
    {
        'pregunta': '¿El precio puede cambiar?',
        'respuesta': 'Sí. Los precios publicados son valores base desde y pueden variar según personalización, temporada, insumos, flores, globos o extras elegidos.',
    },
]

TERMINOS_CONDICIONES = [
    {
        'titulo': 'Confirmación del pedido',
        'descripcion': 'El pedido queda reservado cuando se valida disponibilidad y se abona el 50% o el valor total acordado.',
    },
    {
        'titulo': 'Personalización',
        'descripcion': 'El cliente debe enviar nombres, colores, temática, frases y revisar que la información esté correcta.',
    },
    {
        'titulo': 'Tiempo de preparación',
        'descripcion': 'Recomendamos pedir con 1 o 2 días de anticipación. Los pedidos urgentes dependen de disponibilidad.',
    },
    {
        'titulo': 'Cambios',
        'descripcion': 'Los cambios se reciben únicamente antes de iniciar la elaboración del detalle.',
    },
    {
        'titulo': 'Disponibilidad y sustituciones',
        'descripcion': 'Insumos como dulces, flores, globos o empaques pueden variar; se ofrecen reemplazos similares.',
    },
    {
        'titulo': 'Precios',
        'descripcion': 'Los valores publicados son base desde y pueden cambiar por personalización, temporada o extras.',
    },
    {
        'titulo': 'Entregas',
        'descripcion': 'Las entregas se coordinan por WhatsApp y el domicilio depende de la zona.',
    },
    {
        'titulo': 'No devoluciones',
        'descripcion': 'Por tratarse de productos personalizados, no hay devoluciones ni reembolsos una vez iniciado el proceso.',
    },
    {
        'titulo': 'Cancelaciones',
        'descripcion': 'Si el pedido se cancela con elaboración avanzada, el anticipo no se devuelve.',
    },
    {
        'titulo': 'Responsabilidad del cliente',
        'descripcion': 'El cliente debe brindar correctamente nombres, frases, dirección, horarios y datos de contacto.',
    },
    {
        'titulo': 'Variaciones',
        'descripcion': 'Las fotos son referencias; pueden existir ligeras diferencias por disponibilidad y elaboración manual.',
    },
    {
        'titulo': 'Uso de imágenes',
        'descripcion': 'Casita de Regalos puede usar fotos de los productos entregados para promoción, salvo solicitud contraria del cliente.',
    },
    {
        'titulo': 'Aceptación',
        'descripcion': 'Al confirmar el pedido por WhatsApp, el cliente acepta estos términos y condiciones.',
    },
]


def _build_home_schema(request):
    site_url = request.build_absolute_uri('/')
    schema = {
        '@context': 'https://schema.org',
        '@type': 'LocalBusiness',
        'name': 'Casita de Regalos',
        'url': site_url,
        'telephone': '+57 311 626 2155',
        'priceRange': '$$',
        'description': (
            'Regalos personalizados, desayunos sorpresa, detalles románticos y regalos de cumpleaños '
            'para Bello, Medellín y el área metropolitana.'
        ),
        'address': {
            '@type': 'PostalAddress',
            'addressLocality': 'Bello',
            'addressRegion': 'Antioquia',
            'addressCountry': 'CO',
        },
        'areaServed': [
            {'@type': 'City', 'name': 'Bello'},
            {'@type': 'City', 'name': 'Medellín'},
            {'@type': 'AdministrativeArea', 'name': 'Área metropolitana del Valle de Aburrá'},
        ],
        'sameAs': ['https://www.instagram.com/casitaregalos/'],
        'knowsAbout': [
            'Regalos personalizados',
            'Desayunos sorpresa',
            'Detalles románticos',
            'Regalos de cumpleaños',
            'Anchetas personalizadas',
        ],
    }
    return json.dumps(schema, ensure_ascii=False)


def _build_faq_schema():
    questions = [
        {
            '@type': 'Question',
            'name': item['pregunta'],
            'acceptedAnswer': {
                '@type': 'Answer',
                'text': item['respuesta'],
            },
        }
        for item in PREGUNTAS_FRECUENTES
    ]
    schema = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': questions,
    }
    return json.dumps(schema, ensure_ascii=False)


def _build_how_to_schema(request):
    schema = {
        '@context': 'https://schema.org',
        '@type': 'HowTo',
        'name': 'Cómo comprar en Casita de Regalos',
        'description': (
            'Proceso para elegir, personalizar y confirmar un regalo personalizado '
            'en Bello, Medellín y el área metropolitana.'
        ),
        'totalTime': 'P1D',
        'step': [
            {
                '@type': 'HowToStep',
                'position': index,
                'name': paso['titulo'],
                'text': paso['descripcion'],
                'url': request.build_absolute_uri(reverse('como_comprar')),
            }
            for index, paso in enumerate(PASOS_COMPRA, start=1)
        ],
    }
    return json.dumps(schema, ensure_ascii=False)


def _truncate_text(value, limit=155):
    text = ' '.join(str(value or '').split())
    if len(text) <= limit:
        return text
    return f'{text[: limit - 1].rstrip()}…'


def _build_product_schema(request, producto):
    product_url = request.build_absolute_uri(reverse('detalle_producto', args=[producto.id]))
    schema = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': producto.nombre,
        'description': _truncate_text(
            producto.descripcion
            or 'Detalle personalizado de Casita de Regalos para Bello, Medellín y el área metropolitana.',
            300,
        ),
        'brand': {
            '@type': 'Brand',
            'name': 'Casita de Regalos',
        },
        'category': producto.categoria.nombre if producto.categoria else 'Regalos personalizados',
        'url': product_url,
        'offers': {
            '@type': 'Offer',
            'url': product_url,
            'priceCurrency': 'COP',
            'price': str(producto.precio),
            'availability': 'https://schema.org/InStock' if producto.disponible else 'https://schema.org/OutOfStock',
            'itemCondition': 'https://schema.org/NewCondition',
        },
        'areaServed': [
            {'@type': 'City', 'name': 'Bello'},
            {'@type': 'City', 'name': 'Medellín'},
            {'@type': 'AdministrativeArea', 'name': 'Área metropolitana del Valle de Aburrá'},
        ],
    }
    if producto.imagen:
        schema['image'] = [request.build_absolute_uri(producto.imagen.url)]
    return json.dumps(schema, ensure_ascii=False)


def _product_text(producto):
    return ' '.join(
        filter(
            None,
            [
                producto.nombre,
                producto.descripcion,
                producto.categoria.nombre if producto.categoria else '',
            ],
        )
    ).lower()


def _build_product_badges(producto):
    text = _product_text(producto)
    badges = ['Personalizable']

    if producto.destacado:
        badges.append('Más pedido')
    if producto.disponible:
        badges.append('Pedido 1-2 días')

    token_badges = [
        (('flor', 'flores', 'rosa', 'girasol'), 'Con flores'),
        (('peluche',), 'Con peluche'),
        (('globo', 'globos', 'arco'), 'Con globos'),
        (('desayuno', 'waffle', 'wafle', 'jugo'), 'Desayuno'),
        (('fruta', 'fresas', 'manzana', 'pera'), 'Con frutas'),
        (('luces', 'luz'), 'Con luces'),
    ]

    for tokens, label in token_badges:
        if any(token in text for token in tokens):
            badges.append(label)

    unique_badges = []
    for badge in badges:
        if badge not in unique_badges:
            unique_badges.append(badge)
    return unique_badges[:5]


def _build_product_microcopy(producto):
    text = _product_text(producto)
    include_rules = [
        (('desayuno', 'waffle', 'wafle', 'jugo', 'milo', 'bonyurt'), 'Incluye base de desayuno, bebida y presentación decorada.'),
        (('flor', 'flores', 'rosa', 'rosas', 'girasol', 'ramo'), 'Incluye flores de temporada y acabado decorativo según disponibilidad.'),
        (('stitch', 'toy story', 'hello kitty', 'bob esponja', 'kuromi', 'infantil'), 'Incluye decoración temática y detalles personalizados para la ocasión.'),
        (('globo', 'globos', 'burbuja', 'arco'), 'Incluye globos decorativos y composición visual lista para sorprender.'),
        (('fruta', 'frutas', 'fresas', 'manzana', 'pera'), 'Incluye fruta seleccionada y presentación cuidada para entrega.'),
        (('caja', 'cajita', 'madera', 'acetato'), 'Incluye base tipo caja y acabados decorativos a juego.'),
    ]
    include = 'Incluye base decorada y detalles ajustados a la referencia.'
    for tokens, copy in include_rules:
        if any(token in text for token in tokens):
            include = copy
            break

    if any(token in text for token in ('desayuno', 'waffle', 'wafle', 'jugo')):
        timing = 'Preparación sugerida: reservar con 1-2 días.'
    elif producto.destacado:
        timing = 'Referencia destacada: confirmar agenda y personalización por WhatsApp.'
    elif producto.disponible:
        timing = 'Precio base sujeto a personalización y disponibilidad.'
    else:
        timing = 'Disponibilidad por confirmar antes de tomar el pedido.'

    return [include, timing]


def _build_designer_tags(producto):
    text = _product_text(producto)
    tag_rules = [
        (('cumple', 'cumpleaños'), 'cumpleanos'),
        (('aniversario', 'pareja', 'amor', 'romántico', 'romantico'), 'amor'),
        (('niño', 'niños', 'infantil', 'stitch', 'toy story', 'hello kitty'), 'ninos'),
        (('mamá', 'mama', 'madre'), 'mama'),
        (('desayuno', 'waffle', 'jugo', 'milo', 'bonyurt'), 'desayuno'),
        (('caja', 'cajita', 'madera', 'acetato'), 'caja'),
        (('flor', 'flores', 'rosa', 'rosas', 'girasol'), 'flores'),
        (('peluche',), 'peluche'),
        (('globo', 'globos', 'arco'), 'globos'),
        (('fruta', 'frutas', 'fresas'), 'frutas'),
        (('luces', 'luz'), 'luces'),
        (('hombre', 'hombres', 'sobrio'), 'hombre'),
    ]
    tags = []
    for tokens, tag in tag_rules:
        if any(token in text for token in tokens):
            tags.append(tag)
    return ' '.join(dict.fromkeys(tags))


def _get_designer_products(limit=12):
    products = list(
        Producto.objects.select_related('categoria')
        .filter(stock__gt=0)
        .order_by('-destacado', 'precio', 'nombre')[:limit]
    )
    for producto in products:
        producto.designer_tags = _build_designer_tags(producto)
    return products


def _option_label(options, selected_value):
    return dict(options).get(selected_value, '')


def _build_active_filter_labels(filters):
    labels = []
    if filters['q']:
        labels.append(f'Búsqueda: {filters["q"]}')

    option_groups = [
        (CATALOG_PRICE_OPTIONS, filters['presupuesto']),
        (CATALOG_OCCASION_OPTIONS, filters['ocasion']),
        (CATALOG_PERSON_OPTIONS, filters['persona']),
        (CATALOG_TYPE_OPTIONS, filters['tipo']),
        (CATALOG_TIME_OPTIONS, filters['tiempo']),
    ]
    for options, selected_value in option_groups:
        label = _option_label(options, selected_value)
        if label:
            labels.append(label)

    for attribute in filters['atributos']:
        label = CATALOG_FILTER_LABELS.get(attribute)
        if label:
            labels.append(label)

    return labels


def inicio(request):
    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    orden = request.GET.get('orden', 'destacados')
    presupuesto = request.GET.get('presupuesto', '').strip()
    ocasion = request.GET.get('ocasion', '').strip()
    persona = request.GET.get('persona', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    tiempo = request.GET.get('tiempo', '').strip()
    atributos = [value.strip() for value in request.GET.getlist('atributos') if value.strip()]

    productos, categorias, categoria_actual = get_catalog_queryset(
        search=busqueda,
        category_id=categoria_id,
        order=orden,
        price_range=presupuesto,
        occasion=ocasion,
        person=persona,
        product_type=tipo,
        time_filter=tiempo,
        attributes=atributos,
    )
    destacados = get_featured_products(
        productos,
        search=busqueda,
        current_category=categoria_actual,
    )
    videos_elaboracion = get_active_process_videos()
    resumen = {
        'total_productos': Producto.objects.count(),
        'categorias': categorias.count(),
    }

    page_obj = paginate_products(productos, request.GET.get('page'))
    productos_pagina = list(page_obj.object_list)
    for producto in productos_pagina:
        producto.catalog_badges = _build_product_badges(producto)
        producto.catalog_microcopy = _build_product_microcopy(producto)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    catalog_query_base = query_params.urlencode()
    catalog_page_prefix = f'{catalog_query_base}&' if catalog_query_base else ''
    active_filter_labels = _build_active_filter_labels(
        {
            'q': busqueda,
            'presupuesto': presupuesto,
            'ocasion': ocasion,
            'persona': persona,
            'tipo': tipo,
            'tiempo': tiempo,
            'atributos': atributos,
        }
    )

    contexto = {
        'categorias': categorias,
        'categoria_actual': categoria_actual,
        'destacados': destacados,
        'filtros': {
            'q': busqueda,
            'categoria_id': categoria_actual.id if categoria_actual else '',
            'orden': orden,
            'presupuesto': presupuesto,
            'ocasion': ocasion,
            'persona': persona,
            'tipo': tipo,
            'tiempo': tiempo,
            'atributos': atributos,
        },
        'opciones_orden': CATALOG_ORDER_OPTIONS,
        'opciones_presupuesto': CATALOG_PRICE_OPTIONS,
        'opciones_ocasion': CATALOG_OCCASION_OPTIONS,
        'opciones_persona': CATALOG_PERSON_OPTIONS,
        'opciones_tipo': CATALOG_TYPE_OPTIONS,
        'opciones_tiempo': CATALOG_TIME_OPTIONS,
        'opciones_atributos': CATALOG_ATTRIBUTE_OPTIONS,
        'filtros_activos': active_filter_labels,
        'catalog_page_prefix': catalog_page_prefix,
        'page_obj': page_obj,
        'productos': productos_pagina,
        'quienes_somos': QUIENES_SOMOS,
        'pilares_servicio': PILARES_SERVICIO,
        'lineas_detalle': LINEAS_DETALLE,
        'piezas_editoriales': PIEZAS_EDITORIALES,
        'colecciones_referencia': COLECCIONES_REFERENCIA,
        'pasos_compra': PASOS_COMPRA,
        'metodos_pago': METODOS_PAGO,
        'politicas_clave': POLITICAS_CLAVE,
        'terminos_condiciones': TERMINOS_CONDICIONES,
        'videos_elaboracion': videos_elaboracion,
        'seo_schema_json': _build_home_schema(request),
        'resumen': resumen,
    }
    return render(request, 'inicio.html', contexto)


def disena_regalo(request):
    disenador_productos = _get_designer_products(limit=16)
    contexto = {
        'disenador_productos': disenador_productos,
    }
    return render(request, 'disena_regalo.html', contexto)


def detalle_producto(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria').prefetch_related('imagenes'),
        id=producto_id,
    )
    navegacion_qs = Producto.objects.select_related('categoria').order_by('-destacado', 'nombre', 'id')
    if producto.categoria_id:
        navegacion_qs = navegacion_qs.filter(categoria=producto.categoria)

    navegacion_ids = list(navegacion_qs.values_list('id', flat=True))
    posicion_producto = 1
    total_en_navegacion = len(navegacion_ids)
    producto_anterior = None
    producto_siguiente = None

    if producto.id in navegacion_ids:
        indice_actual = navegacion_ids.index(producto.id)
        posicion_producto = indice_actual + 1

        if indice_actual > 0:
            producto_anterior = navegacion_qs.filter(id=navegacion_ids[indice_actual - 1]).first()

        if indice_actual < total_en_navegacion - 1:
            producto_siguiente = navegacion_qs.filter(id=navegacion_ids[indice_actual + 1]).first()

    relacionados = (
        Producto.objects.select_related('categoria')
        .filter(categoria=producto.categoria)
        .exclude(id=producto.id)
        .order_by('-destacado', 'nombre')[:8]
    )

    galeria_imagenes = []
    if producto.imagen:
        galeria_imagenes.append(
            {
                'url': producto.imagen.url,
                'alt': producto.nombre,
            }
        )

    for imagen in producto.imagenes.all():
        galeria_imagenes.append(
            {
                'url': imagen.imagen.url,
                'alt': imagen.titulo or producto.nombre,
            }
        )

    product_meta_description = _truncate_text(
        producto.descripcion
        or f'{producto.nombre} en Casita de Regalos. Cotiza regalos personalizados en Bello, Medellín y el área metropolitana.',
        155,
    )
    product_og_image_url = request.build_absolute_uri(producto.imagen.url) if producto.imagen else ''
    producto_whatsapp_url = build_whatsapp_url(
        (
            f'Hola, quiero cotizar la referencia "{producto.nombre}". '
            'Me gustaría confirmar disponibilidad, personalización y entrega.'
        )
    )

    return render(
        request,
        'producto_detalle.html',
        {
            'producto': producto,
            'producto_anterior': producto_anterior,
            'producto_siguiente': producto_siguiente,
            'posicion_producto': posicion_producto,
            'total_en_navegacion': total_en_navegacion,
            'relacionados': relacionados,
            'galeria_imagenes': galeria_imagenes,
            'product_meta_description': product_meta_description,
            'product_og_image_url': product_og_image_url,
            'product_schema_json': _build_product_schema(request, producto),
            'producto_whatsapp_url': producto_whatsapp_url,
        },
    )


def preguntas_frecuentes(request):
    return render(
        request,
        'preguntas_frecuentes.html',
        {
            'preguntas_frecuentes': PREGUNTAS_FRECUENTES,
            'faq_schema_json': _build_faq_schema(),
        },
    )


def como_comprar(request):
    return render(
        request,
        'como_comprar.html',
        {
            'pasos_compra': PASOS_COMPRA,
            'metodos_pago': METODOS_PAGO,
            'politicas_clave': POLITICAS_CLAVE,
            'how_to_schema_json': _build_how_to_schema(request),
        },
    )


def terminos_condiciones(request):
    return render(
        request,
        'terminos_condiciones.html',
        {
            'terminos_condiciones': TERMINOS_CONDICIONES,
        },
    )


def aviso_privacidad(request):
    return render(request, 'aviso_privacidad.html')
