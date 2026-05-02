from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Categoria, Producto


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
        'titulo': 'Experiencia local premium',
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
                'titulo': 'Cumple azul premium',
                'etiqueta': 'Cumpleaños',
                'precio': '$81.000 COP',
                'imagen': 'referencias/referencia-03.png',
                'descripcion': 'Referencia con caja en madera, globos, mix de fruta, waffles, jugo y decoración para celebrar con tono elegante.',
                'mensaje': 'Hola, quiero cotizar la referencia Cumple azul premium.',
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
                'etiqueta': 'Premium',
                'precio': '$94.000 COP',
                'imagen': 'referencias/referencia-09.png',
                'descripcion': 'Detalle premium con globos negro y dorado, fruta, cereal y presentación más sofisticada.',
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
                'titulo': 'Trio corazones sorpresa',
                'etiqueta': 'Romántico',
                'precio': '$63.000 COP',
                'imagen': 'referencias/referencia-10.png',
                'descripcion': 'Referencias visuales con corazones, chocolates, rosas y cajas que funcionan muy bien para regalar amor.',
                'mensaje': 'Hola, quiero cotizar la referencia Trio corazones sorpresa.',
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
                'titulo': 'Caja corazón premium',
                'etiqueta': 'Romántico premium',
                'precio': '$122.000 COP',
                'imagen': 'referencias/referencia-19.png',
                'descripcion': 'Caja fina en forma de corazón con sándwich, jugo, rosas, chocolates o peluche para regalos premium.',
                'mensaje': 'Hola, quiero cotizar la referencia Caja corazón premium.',
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
        'titulo': 'Frutales, flores y momentos premium',
        'descripcion': (
            'Referencias con más impacto visual para fechas premium, regalos gourmet, flores, fresas y '
            'combinaciones memorables.'
        ),
        'mensaje': 'Hola, quiero cotizar una referencia premium, frutal o con flores.',
        'items': [
            {
                'titulo': 'Rosas y fresas premium',
                'etiqueta': 'Premium floral',
                'precio': '$173.000 COP',
                'imagen': 'referencias/referencia-13.png',
                'descripcion': 'Propuestas con rosas, fresas cubiertas, licor y presentaciones premium para sorprender con alto impacto.',
                'mensaje': 'Hola, quiero cotizar la referencia Rosas y fresas premium.',
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
        'descripcion': 'Busca por categoría, ocasión o presupuesto y guarda tus opciones favoritas.',
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


ORDENES_CATALOGO = {
    'destacados': ('-destacado', 'nombre'),
    'precio_asc': ('precio', 'nombre'),
    'precio_desc': ('-precio', 'nombre'),
    'recientes': ('-fecha_creacion', 'nombre'),
    'nombre': ('nombre',),
}


def inicio(request):
    busqueda = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    orden = request.GET.get('orden', 'destacados')

    productos = Producto.objects.select_related('categoria').all()
    categorias = (
        Categoria.objects.annotate(total_productos=Count('producto'))
        .filter(total_productos__gt=0)
        .order_by('nombre')
    )

    categoria_actual = None

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
            | Q(categoria__nombre__icontains=busqueda)
        )

    if categoria_id.isdigit():
        categoria_actual = categorias.filter(id=int(categoria_id)).first()
        if categoria_actual:
            productos = productos.filter(categoria=categoria_actual)

    productos = productos.order_by(*ORDENES_CATALOGO.get(orden, ORDENES_CATALOGO['destacados']))

    destacados = productos.filter(destacado=True)[:3]
    if not destacados and not (busqueda or categoria_actual):
        destacados = Producto.objects.select_related('categoria').filter(destacado=True)[:3]

    resumen = {
        'total_productos': productos.count(),
        'categorias': categorias.count(),
    }

    paginator = Paginator(productos, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    contexto = {
        'categorias': categorias,
        'categoria_actual': categoria_actual,
        'destacados': destacados,
        'filtros': {
            'q': busqueda,
            'categoria_id': categoria_actual.id if categoria_actual else '',
            'orden': orden,
        },
        'opciones_orden': [
            ('destacados', 'Destacados'),
            ('precio_asc', 'Precio: menor a mayor'),
            ('precio_desc', 'Precio: mayor a menor'),
            ('recientes', 'Más recientes'),
            ('nombre', 'Nombre'),
        ],
        'page_obj': page_obj,
        'productos': page_obj.object_list,
        'quienes_somos': QUIENES_SOMOS,
        'pilares_servicio': PILARES_SERVICIO,
        'lineas_detalle': LINEAS_DETALLE,
        'piezas_editoriales': PIEZAS_EDITORIALES,
        'colecciones_referencia': COLECCIONES_REFERENCIA,
        'pasos_compra': PASOS_COMPRA,
        'metodos_pago': METODOS_PAGO,
        'politicas_clave': POLITICAS_CLAVE,
        'terminos_condiciones': TERMINOS_CONDICIONES,
        'resumen': resumen,
    }
    return render(request, 'inicio.html', contexto)


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
