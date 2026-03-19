import argparse
import os
import sys
from pathlib import Path


def bootstrap_django():
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    import django

    django.setup()


def pregunta_en_establecimiento(orden):
    return {
        "clave": "en_establecimiento",
        "etiqueta": "¿Te encuentras en el establecimiento?",
        "tipo": "seleccion",
        "requerido": True,
        "orden": orden,
        "ayuda": "Si respondes 'No', indica quién refiere al cliente.",
        "opciones": [
            {"valor": "si", "etiqueta": "Sí (iniciar recorrido)", "orden": 1},
            {
                "valor": "no",
                "etiqueta": "No (proporcionar datos de quien refiere al cliente)",
                "orden": 2,
            },
        ],
    }


PREGUNTAS_ANGRI = [
    pregunta_en_establecimiento(1),
    {
        "clave": "quien_refiere_cliente",
        "etiqueta": "¿Quién refiere al cliente?",
        "tipo": "texto",
        "requerido": False,
        "orden": 2,
        "reglas_visibilidad": {
            "mostrar_si": [{"campo": "en_establecimiento", "operador": "==", "valor": "no"}]
        },
        "reglas_validacion": {
            "requerido_si": {"campo": "en_establecimiento", "operador": "==", "valor": "no"},
            "min_longitud": 3,
        },
    },
    {
        "clave": "tipo_inmueble_m2_total",
        "etiqueta": "Tipo de inmueble y metros cuadrados de todo el establecimiento",
        "tipo": "texto",
        "requerido": True,
        "orden": 3,
    },
    {
        "clave": "metros_cuadrados_analisis",
        "etiqueta": "Metros cuadrados del establecimiento (análisis de riesgo)",
        "tipo": "texto",
        "requerido": True,
        "orden": 4,
    },
    {
        "clave": "perimetro_establecimiento",
        "etiqueta": "Perímetro del establecimiento",
        "tipo": "texto",
        "requerido": True,
        "orden": 5,
    },
    {
        "clave": "m2_estacionamiento_patios_cajones",
        "etiqueta": "M2 de estacionamiento/patios y cantidad de cajones",
        "tipo": "texto",
        "requerido": False,
        "orden": 6,
    },
    {
        "clave": "materiales_combustibles_solido",
        "etiqueta": "Material combustible sólido (descripción)",
        "tipo": "texto",
        "requerido": False,
        "orden": 7,
    },
    {
        "clave": "materiales_combustibles_solido_cantidad",
        "etiqueta": "Cantidad de material sólido (kg o toneladas)",
        "tipo": "texto",
        "requerido": False,
        "orden": 8,
    },
    {
        "clave": "liquidos_derivados_petroleo",
        "etiqueta": "Líquidos derivados del petróleo (descripción)",
        "tipo": "texto",
        "requerido": False,
        "orden": 9,
    },
    {
        "clave": "liquidos_sustancias_peligrosas",
        "etiqueta": "Sustancias químico peligrosas (descripción)",
        "tipo": "texto",
        "requerido": False,
        "orden": 10,
    },
    {
        "clave": "liquidos_hds_nombre_tecnico",
        "etiqueta": "Nombre técnico de sustancia (si aplica HDS)",
        "tipo": "texto",
        "requerido": False,
        "orden": 11,
        "reglas_validacion": {
            "requerido_si": {
                "campo": "liquidos_sustancias_peligrosas",
                "operador": "!=",
                "valor": "",
            }
        },
    },
    {
        "clave": "liquidos_cantidad_litros",
        "etiqueta": "Cantidad de líquidos (litros)",
        "tipo": "texto",
        "requerido": False,
        "orden": 12,
    },
    {
        "clave": "gaseoso_descripcion",
        "etiqueta": "Material combustible gaseoso (descripción)",
        "tipo": "texto",
        "requerido": False,
        "orden": 13,
    },
    {
        "clave": "gaseoso_capacidad",
        "etiqueta": "Capacidad de material gaseoso",
        "tipo": "texto",
        "requerido": False,
        "orden": 14,
    },
]


def upsert_template(version: int, activar: bool):
    from forms.models import FormTemplate, Question, QuestionOption

    template, _ = FormTemplate.objects.update_or_create(
        codigo="GRADO_RIESGO_ANGRI",
        version=version,
        defaults={
            "titulo": "Grado de Riesgo de Incendio ANGRI",
            "activo": activar,
            "header_requiere_en_establecimiento": True,
            "descripcion": (
                "Plantilla ANGRI para levantamiento de riesgo de incendio. "
                "No incluye preguntas redundantes de técnico/empresa/contacto "
                "porque esos datos ya existen en el sistema."
            ),
        },
    )

    for data in PREGUNTAS_ANGRI:
        opciones = data.get("opciones", [])
        defaults = {
            "etiqueta": data["etiqueta"],
            "tipo": data["tipo"],
            "requerido": data.get("requerido", False),
            "orden": data["orden"],
            "ayuda": data.get("ayuda"),
            "reglas_visibilidad": data.get("reglas_visibilidad"),
            "reglas_validacion": data.get("reglas_validacion"),
        }
        question, _ = Question.objects.update_or_create(
            template=template,
            clave=data["clave"],
            defaults=defaults,
        )
        for opcion in opciones:
            QuestionOption.objects.update_or_create(
                pregunta=question,
                valor=opcion["valor"],
                defaults={
                    "etiqueta": opcion["etiqueta"],
                    "orden": opcion.get("orden", 0),
                },
            )

    if activar:
        template.activo = True
        template.save()

    return template


def main():
    parser = argparse.ArgumentParser(
        description="Crea/actualiza plantilla GRADO_RIESGO_ANGRI sin duplicar preguntas."
    )
    parser.add_argument("--version", type=int, default=1, help="Versión del template.")
    parser.add_argument(
        "--activar",
        action="store_true",
        help="Activa esta versión (desactiva otras del mismo código).",
    )
    args = parser.parse_args()

    bootstrap_django()
    template = upsert_template(version=args.version, activar=args.activar)
    print(
        f"Template listo: codigo={template.codigo}, version={template.version}, activo={template.activo}"
    )


if __name__ == "__main__":
    main()
