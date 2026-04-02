from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Categoria, Producto


QUIENES_SOMOS = {
    'titulo': 'Detalles personalizados para fechas que merecen algo magico',
    'descripcion': (
        'Casita de Regalos es una tienda online ubicada en Bello, Antioquia, enfocada en convertir '
        'cumpleanos, aniversarios, fechas especiales y sorpresas en experiencias inolvidables. '
        'La marca transmite ternura, cercania y una atencion guiada que acompana cada compra desde '
        'la idea inicial hasta la entrega final.'
    ),
    'cobertura': 'Bello, Medellin y area metropolitana',
    'promesa': 'Personalizacion segun gusto, presupuesto y ocasion',
}

PILARES_SERVICIO = [
    {
        'titulo': 'Detalles personalizados',
        'descripcion': 'Desayunos sorpresa, bandejas, cajas, globos, flores y regalos armados segun la ocasion.',
        'etiqueta': 'Hecho a medida',
    },
    {
        'titulo': 'Asesoria por WhatsApp',
        'descripcion': 'Cada pedido se conversa, se cotiza y se confirma antes de producirse para evitar errores.',
        'etiqueta': 'Atencion directa',
    },
    {
        'titulo': 'Experiencia local premium',
        'descripcion': 'Servicio pensado para Bello, Medellin y fechas especiales con presentacion impecable.',
        'etiqueta': 'Cobertura cercana',
    },
]

LINEAS_DETALLE = [
    {
        'titulo': 'Cumpleanos y desayunos sorpresa',
        'descripcion': 'Bandejas, cajas, globos, frutas, waffles, snacks y mensajes para sorprender.',
    },
    {
        'titulo': 'Amor, aniversario y romanticos',
        'descripcion': 'Rosas, chocolates, corazones, cajas finas y detalles con frases personalizadas.',
    },
    {
        'titulo': 'Infantil y personajes',
        'descripcion': 'Tematicas como Hello Kitty, Mario y propuestas visuales para ninos y celebraciones especiales.',
    },
    {
        'titulo': 'Mini detalles y opciones express',
        'descripcion': 'Alternativas mas accesibles, utiles para regalos rapidos sin perder identidad visual.',
    },
]

PIEZAS_EDITORIALES = [
    {
        'titulo': 'Quienes somos',
        'etiqueta': 'Presentacion de marca',
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
            'El flujo real ya esta claro: explorar referencias, elegir el detalle, recibir asesoria '
            'por WhatsApp y confirmar el pago para entrar a produccion.'
        ),
    },
    {
        'titulo': 'Politicas y condiciones',
        'etiqueta': 'Confianza y claridad',
        'imagen': 'referencias/referencia-20.png',
        'descripcion': (
            'Las reglas visibles ayudan a que la experiencia se vea profesional: anticipo, tiempos, '
            'personalizacion, entregas inmediatas segun disponibilidad y precios variables.'
        ),
    },
]

COLECCIONES_REFERENCIA = [
    {
        'titulo': 'Cumpleanos y desayunos sorpresa',
        'descripcion': (
            'La linea mas fuerte del catalogo visual: cajas, bandejas, globos, frutas, snacks y '
            'desayunos presentados como experiencias listas para regalar.'
        ),
        'mensaje': 'Hola, quiero cotizar una referencia de cumpleanos o desayuno sorpresa.',
        'items': [
            {
                'titulo': 'Cumple azul premium',
                'etiqueta': 'Cumpleanos',
                'precio': '$81.000 COP',
                'imagen': 'referencias/referencia-03.png',
                'descripcion': 'Referencia con caja en madera, globos, mix de fruta, waffles, jugo y decoracion para celebrar con tono elegante.',
                'mensaje': 'Hola, quiero cotizar la referencia Cumple azul premium.',
            },
            {
                'titulo': 'Desayuno globos pastel',
                'etiqueta': 'Desayuno sorpresa',
                'precio': '$80.000 COP',
                'imagen': 'referencias/referencia-04.png',
                'descripcion': 'Bandejas y desayunos sorpresa con globos, yogurt, fruta, sandwich y detalles visuales suaves.',
                'mensaje': 'Hola, quiero cotizar la referencia Desayuno globos pastel.',
            },
            {
                'titulo': 'Rose gold cumpleanero',
                'etiqueta': 'Cumpleanos',
                'precio': '$77.000 COP',
                'imagen': 'referencias/referencia-07.png',
                'descripcion': 'Caja en madera con globos rose gold, frutas, waffles, postre y mensaje para una celebracion delicada.',
                'mensaje': 'Hola, quiero cotizar la referencia Rose gold cumpleanero.',
            },
            {
                'titulo': 'Cumple lila fantasia',
                'etiqueta': 'Cumpleanos',
                'precio': '$75.000 COP',
                'imagen': 'referencias/referencia-08.png',
                'descripcion': 'Opciones juveniles y coloridas con snacks, desayunos y decoracion pensadas para regalos personalizados.',
                'mensaje': 'Hola, quiero cotizar la referencia Cumple lila fantasia.',
            },
            {
                'titulo': 'Black and gold deluxe',
                'etiqueta': 'Premium',
                'precio': '$94.000 COP',
                'imagen': 'referencias/referencia-09.png',
                'descripcion': 'Detalle premium con globos negro y dorado, fruta, cereal y presentacion mas sofisticada.',
                'mensaje': 'Hola, quiero cotizar la referencia Black and gold deluxe.',
            },
            {
                'titulo': 'Desayuno mariposa rosa',
                'etiqueta': 'Cumpleanos',
                'precio': '$89.000 COP',
                'imagen': 'referencias/referencia-17.png',
                'descripcion': 'Mesa o bandeja en madera con globos en helio, mariposas, yogurt, jugo y decoracion femenina.',
                'mensaje': 'Hola, quiero cotizar la referencia Desayuno mariposa rosa.',
            },
            {
                'titulo': 'Combo snack con globos',
                'etiqueta': 'Desayuno sorpresa',
                'precio': '$88.000 COP',
                'imagen': 'referencias/referencia-18.png',
                'descripcion': 'Combinaciones de snacks, globos metalizados y presentaciones compactas para regalos rapidos pero vistosos.',
                'mensaje': 'Hola, quiero cotizar la referencia Combo snack con globos.',
            },
        ],
    },
    {
        'titulo': 'Amor, aniversarios y romanticos',
        'descripcion': (
            'Una linea perfecta para aniversarios, parejas, mensajes especiales y regalos con un look '
            'mas emocional, elegante y memorable.'
        ),
        'mensaje': 'Hola, quiero cotizar una referencia romantica o de aniversario.',
        'items': [
            {
                'titulo': 'Caja aniversario te amo',
                'etiqueta': 'Aniversario',
                'precio': '$75.000 COP',
                'imagen': 'referencias/referencia-05.png',
                'descripcion': 'Caja con globo burbuja, waffles, jugo y mensaje romantico para aniversarios y sorpresas especiales.',
                'mensaje': 'Hola, quiero cotizar la referencia Caja aniversario te amo.',
            },
            {
                'titulo': 'Amor delicado rosa',
                'etiqueta': 'Romantico',
                'precio': '$89.000 COP',
                'imagen': 'referencias/referencia-06.png',
                'descripcion': 'Presentacion suave con tonos rosa, globo y detalles dulces para una sorpresa romantica o de fecha especial.',
                'mensaje': 'Hola, quiero cotizar la referencia Amor delicado rosa.',
            },
            {
                'titulo': 'Trio corazones sorpresa',
                'etiqueta': 'Romantico',
                'precio': '$63.000 COP',
                'imagen': 'referencias/referencia-10.png',
                'descripcion': 'Referencias visuales con corazones, chocolates, rosas y cajas que funcionan muy bien para regalar amor.',
                'mensaje': 'Hola, quiero cotizar la referencia Trio corazones sorpresa.',
            },
            {
                'titulo': 'Buenos dias con amor',
                'etiqueta': 'Detalle especial',
                'precio': '$55.000 COP',
                'imagen': 'referencias/referencia-15.png',
                'descripcion': 'Desayunos pequenos y cajas con snacks, bebidas y mensajes para sorprender desde la manana.',
                'mensaje': 'Hola, quiero cotizar la referencia Buenos dias con amor.',
            },
            {
                'titulo': 'Caja corazon premium',
                'etiqueta': 'Romantico premium',
                'precio': '$122.000 COP',
                'imagen': 'referencias/referencia-19.png',
                'descripcion': 'Caja fina en forma de corazon con sandwich, jugo, rosas, chocolates o peluche para regalos premium.',
                'mensaje': 'Hola, quiero cotizar la referencia Caja corazon premium.',
            },
        ],
    },
    {
        'titulo': 'Tematicos, mini detalles y personajes',
        'descripcion': (
            'Aqui vive la parte mas versatil del catalogo: personajes, mini regalos, cajas express y '
            'detalles que se adaptan bien a presupuestos mas agiles.'
        ),
        'mensaje': 'Hola, quiero cotizar una referencia tematica o mini detalle.',
        'items': [
            {
                'titulo': 'Tematicos con personaje',
                'etiqueta': 'Tematico',
                'precio': '$44.000 COP',
                'imagen': 'referencias/referencia-11.png',
                'descripcion': 'Opciones personalizadas con Hello Kitty, Mario, fotos y personajes elegidos segun el gusto del cliente.',
                'mensaje': 'Hola, quiero cotizar la referencia Tematicos con personaje.',
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
                'titulo': 'Dia especial express',
                'etiqueta': 'Mini detalle',
                'precio': '$28.000 COP',
                'imagen': 'referencias/referencia-16.png',
                'descripcion': 'Detalles pequenos con empaque protagonista, ideales para regalos rapidos, dia de la madre o fechas cortas.',
                'mensaje': 'Hola, quiero cotizar la referencia Dia especial express.',
            },
        ],
    },
    {
        'titulo': 'Frutales, flores y momentos premium',
        'descripcion': (
            'Referencias con mas impacto visual para fechas premium, regalos gourmet, flores, fresas y '
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
                'titulo': 'Bunny y corazon frutal',
                'etiqueta': 'Fecha especial',
                'precio': '$42.000 COP',
                'imagen': 'referencias/referencia-14.png',
                'descripcion': 'Detalles creativos con tematica tierna y tablas frutales en forma de corazon para regalos frescos y diferentes.',
                'mensaje': 'Hola, quiero cotizar la referencia Bunny y corazon frutal.',
            },
        ],
    },
]

PASOS_COMPRA = [
    {
        'numero': '01',
        'titulo': 'Explora el catalogo',
        'descripcion': 'Dirigete a nuestras referencias y revisa opciones de detalles personalizados.',
    },
    {
        'numero': '02',
        'titulo': 'Personaliza tu pedido',
        'descripcion': 'Elige la referencia que mas te guste y ajusta colores, mensaje, extras y presupuesto.',
    },
    {
        'numero': '03',
        'titulo': 'Confirma por WhatsApp',
        'descripcion': 'Contactanos para recibir asesoria, disponibilidad real y cotizacion personalizada.',
    },
    {
        'numero': '04',
        'titulo': 'Reserva y realiza el pago',
        'descripcion': 'Una vez confirmado el pedido, realizas el pago y entramos a prepararlo con dedicacion.',
    },
]

METODOS_PAGO = [
    {
        'titulo': 'Nequi',
        'descripcion': '311 626 2155 a nombre de Monica Gutierrez. Ideal para confirmar rapido y enviar comprobante por WhatsApp.',
    },
    {
        'titulo': 'Bancolombia',
        'descripcion': 'Cuenta de ahorros 58066610009 para reservas y pedidos personalizados confirmados.',
    },
    {
        'titulo': 'Pago validado',
        'descripcion': 'Primero se valida disponibilidad, personalizacion y precio final. Luego se confirma el abono o pago completo.',
    },
]

POLITICAS_CLAVE = [
    'Los pedidos se agendan unicamente si se cancela el 50% del valor total.',
    'No manejamos devoluciones de dinero.',
    'Los pedidos se recomiendan con 1 o 2 dias de anticipacion.',
    'Todas las anchetas y detalles se pueden personalizar segun presupuesto y gusto del cliente.',
    'Si deseas entrega inmediata, primero debes consultar por referencias disponibles.',
    'En cada imagen se evidencia lo que incluye cada detalle y cualquier agotado se avisa antes de confirmar.',
    'Los precios pueden variar segun temporada, materiales y personalizacion.',
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
        'disponibles': productos.filter(stock__gt=0).count(),
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
            ('recientes', 'Mas recientes'),
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
        'resumen': resumen,
    }
    return render(request, 'inicio.html', contexto)


def detalle_producto(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria'),
        id=producto_id,
    )
    relacionados = (
        Producto.objects.select_related('categoria')
        .filter(categoria=producto.categoria)
        .exclude(id=producto.id)
        .order_by('-destacado', 'nombre')[:4]
    )

    return render(
        request,
        'producto_detalle.html',
        {
            'producto': producto,
            'relacionados': relacionados,
        },
    )
