from django.utils.dateparse import parse_date
from rest_framework import serializers

from empresas.models import Empresa
from extintores.models import Extintor
from usuarios.models import Perfil
from .models import (
    FormTemplate,
    Question,
    QuestionOption,
    FormRun,
)


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('valor', 'etiqueta', 'orden')


class QuestionSerializer(serializers.ModelSerializer):
    opciones = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = (
            'clave',
            'etiqueta',
            'tipo',
            'requerido',
            'orden',
            'ayuda',
            'reglas_visibilidad',
            'reglas_validacion',
            'opciones',
        )


class FormTemplateSerializer(serializers.ModelSerializer):
    preguntas = QuestionSerializer(many=True, read_only=True)
    empresas_permitidas = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    header = serializers.SerializerMethodField()

    class Meta:
        model = FormTemplate
        fields = (
            'id',
            'codigo',
            'titulo',
            'version',
            'activo',
            'descripcion',
            'header_requiere_en_establecimiento',
            'header',
            'roles_permitidos',
            'empresas_permitidas',
            'preguntas',
        )

    def get_header(self, obj):
        if not obj.header_requiere_en_establecimiento:
            return {"requiere_en_establecimiento": False}
        return {
            "requiere_en_establecimiento": True,
            "pregunta": {
                "clave": "en_establecimiento",
                "etiqueta": "¿Te encuentras en el establecimiento?",
                "tipo": "seleccion",
                "opciones": [
                    {"valor": "si", "etiqueta": "Sí (iniciar recorrido)"},
                    {
                        "valor": "no",
                        "etiqueta": "No (proporcionar datos de quien refiere al cliente)",
                    },
                ],
            },
            "si_no_entonces": {
                "clave": "quien_refiere_cliente",
                "etiqueta": "¿Quién refiere al cliente?",
                "tipo": "texto",
            },
        }


class FormRunSerializer(serializers.ModelSerializer):
    tecnico = serializers.PrimaryKeyRelatedField(read_only=True)
    template = serializers.PrimaryKeyRelatedField(queryset=FormTemplate.objects.all())
    empresa = serializers.PrimaryKeyRelatedField(queryset=Empresa.objects.all())
    respuestas_json = serializers.JSONField()

    CONTEXTO_ESPERADO = {'agente_extintor'}

    class Meta:
        model = FormRun
        fields = (
            'id',
            'template',
            'empresa',
            'tecnico',
            'estado',
            'scope_type',
            'scope_id',
            'tipo_servicio',
            'respuestas_json',
            'tiene_incidencias',
            'creado_en',
            'actualizado_en',
        )
        read_only_fields = ('tecnico', 'tiene_incidencias', 'creado_en', 'actualizado_en')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        template = attrs.get('template') or getattr(self.instance, 'template', None)
        if not template:
            raise serializers.ValidationError(
                {'template': 'La plantilla es obligatoria.'}
            )
        request = self.context.get('request')
        empresa_obj = attrs.get('empresa') or getattr(self.instance, 'empresa', None)
        empresa_id = empresa_obj.id if empresa_obj else None
        if request and not template.is_available_for(request.user, empresa_id=empresa_id):
            raise serializers.ValidationError(
                {'template': 'No tienes permisos para usar esta plantilla.'}
            )

        respuestas = attrs.get('respuestas_json')
        if respuestas is None:
            respuestas = getattr(self.instance, 'respuestas_json', {}) or {}
        if not isinstance(respuestas, dict):
            raise serializers.ValidationError(
                {'respuestas_json': 'El campo respuestas_json debe ser un objeto.'}
            )

        scope_type = attrs.get('scope_type') or getattr(self.instance, 'scope_type', None)
        scope_id = attrs.get('scope_id') or getattr(self.instance, 'scope_id', None)
        tipo_servicio = attrs.get('tipo_servicio') or getattr(self.instance, 'tipo_servicio', None)
        extintor = self._obtener_extintor(scope_type, scope_id)

        agente_extintor = self._resolver_agente(respuestas, extintor)
        preguntas = template.preguntas.prefetch_related('opciones').all()
        mapa_preguntas = {p.clave: p for p in preguntas}
        opciones_por_pregunta = {
            p.clave: [op.valor for op in p.opciones.all()] for p in preguntas
        }

        claves_invalidas = set(respuestas.keys()) - set(mapa_preguntas.keys()) - self.CONTEXTO_ESPERADO
        if claves_invalidas:
            raise serializers.ValidationError({
                'respuestas_json': [
                    f"Las claves {', '.join(sorted(claves_invalidas))} no existen en la plantilla."
                ]
            })

        contexto_base = {
            'respuestas': respuestas,
            'tipo_servicio': tipo_servicio,
            'agente_extintor': agente_extintor,
        }

        errores = {}
        respuestas_limpias = {}
        for clave, valor in respuestas.items():
            pregunta = mapa_preguntas.get(clave)
            if not pregunta:
                if clave in self.CONTEXTO_ESPERADO:
                    respuestas_limpias[clave] = valor
                continue

            aplica = self._pregunta_aplica(pregunta, contexto_base)
            if not aplica:
                continue

            if valor is None:
                respuestas_limpias.pop(clave, None)
                continue

            try:
                valor_validado = self._validar_tipo(pregunta, valor, opciones_por_pregunta.get(clave, []))
            except serializers.ValidationError as exc:
                errores[clave] = exc.detail
                continue

            if pregunta.tipo == Question.TIPO_TEXTO:
                valor_validado = valor_validado.strip()

            errores_validacion_reglas = self._validar_reglas(pregunta, valor_validado, contexto_base)
            if errores_validacion_reglas:
                errores[clave] = errores_validacion_reglas
                continue

            respuestas_limpias[clave] = valor_validado

        if errores:
            raise serializers.ValidationError({'respuestas_json': errores})

        estado = attrs.get('estado') or getattr(self.instance, 'estado', FormRun.ESTADO_BORRADOR)
        contexto_final = {
            'respuestas': respuestas_limpias,
            'tipo_servicio': tipo_servicio,
            'agente_extintor': agente_extintor,
        }

        errores_requeridos = {}
        if estado == FormRun.ESTADO_COMPLETADO:
            for clave, pregunta in mapa_preguntas.items():
                if not self._pregunta_aplica(pregunta, contexto_final):
                    continue

                requerido = pregunta.requerido or self._es_requerido_condicional(
                    pregunta, contexto_final
                )
                if requerido and clave not in respuestas_limpias:
                    errores_requeridos[clave] = (
                        f"El campo '{pregunta.etiqueta}' es obligatorio en estado completado."
                    )

        if errores_requeridos:
            raise serializers.ValidationError({'respuestas_json': errores_requeridos})

        attrs['respuestas_json'] = respuestas_limpias
        attrs['tiene_incidencias'] = self._calcular_incidencias(
            respuestas_limpias, mapa_preguntas, contexto_final
        )
        return attrs

    def create(self, validated_data):
        validated_data['tecnico'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'tecnico' not in validated_data:
            validated_data['tecnico'] = instance.tecnico
        return super().update(instance, validated_data)

    def _obtener_extintor(self, scope_type, scope_id):
        if scope_type != FormRun.SCOPE_EXTINTOR or not scope_id:
            return None
        try:
            return Extintor.objects.get(pk=scope_id)
        except Extintor.DoesNotExist:
            return None

    def _resolver_agente(self, respuestas, extintor):
        agente = respuestas.get('agente_extintor')
        if agente:
            return self._normalizar_agente(agente)
        if extintor:
            return self._normalizar_agente(extintor.tipo)
        return None

    def _normalizar_agente(self, valor):
        texto = str(valor).strip().upper()
        if 'CO2' in texto:
            return 'CO2'
        if 'PQS' in texto:
            return 'PQS'
        return texto

    def _pregunta_aplica(self, pregunta, contexto):
        reglas = pregunta.reglas_visibilidad or {}
        condiciones = reglas.get('mostrar_si', [])
        if not condiciones:
            return True
        for condicion in condiciones:
            campo = condicion.get('campo')
            operador = condicion.get('operador', '==')
            valor_objetivo = condicion.get('valor')
            valor_actual = self._obtener_valor_contexto(campo, contexto)
            if not self._evaluar_operador(valor_actual, operador, valor_objetivo):
                return False
        return True

    def _obtener_valor_contexto(self, campo, contexto):
        if campo in contexto:
            return contexto[campo]
        if campo in contexto.get('respuestas', {}):
            return contexto['respuestas'][campo]
        return None

    def _evaluar_operador(self, actual, operador, objetivo):
        if operador == '==' and actual == objetivo:
            return True
        if operador == '!=' and actual != objetivo:
            return True
        if operador == 'in' and isinstance(objetivo, (list, tuple)) and actual in objetivo:
            return True
        if operador == 'not_in' and isinstance(objetivo, (list, tuple)) and actual not in objetivo:
            return True
        return False

    def _validar_tipo(self, pregunta, valor, opciones):
        tipo = pregunta.tipo
        if tipo == Question.TIPO_BOOLEANO:
            if isinstance(valor, bool):
                return valor
            raise serializers.ValidationError('El valor debe ser booleano.')
        if tipo == Question.TIPO_NUMERO:
            if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                return float(valor) if isinstance(valor, float) else int(valor)
            raise serializers.ValidationError('El valor debe ser numérico.')
        if tipo == Question.TIPO_FECHA:
            if isinstance(valor, str):
                fecha = parse_date(valor)
                if fecha:
                    return fecha.isoformat()
            raise serializers.ValidationError('La fecha debe estar en formato YYYY-MM-DD.')
        if tipo == Question.TIPO_TEXTO:
            if isinstance(valor, str):
                return valor
            raise serializers.ValidationError('El valor debe ser un texto.')
        if tipo == Question.TIPO_SELECCION:
            if isinstance(valor, str) and valor in opciones:
                return valor
            raise serializers.ValidationError('El valor debe coincidir con una opción válida.')
        if tipo == Question.TIPO_MULTI:
            if isinstance(valor, (list, tuple)) and all(isinstance(item, str) for item in valor):
                faltantes = [item for item in valor if item not in opciones]
                if faltantes:
                    raise serializers.ValidationError('Las opciones seleccionadas no son válidas.')
                return list(valor)
            raise serializers.ValidationError('El valor debe ser una lista de opciones válidas.')
        if tipo == Question.TIPO_ARCHIVO:
            if isinstance(valor, str):
                return valor
            raise serializers.ValidationError('El valor debe ser una referencia de archivo (cadena).')
        raise serializers.ValidationError('Tipo de pregunta desconocido.')

    def _validar_reglas(self, pregunta, valor, contexto):
        reglas = pregunta.reglas_validacion or {}
        errores = []
        if pregunta.tipo == Question.TIPO_TEXTO and isinstance(valor, str):
            min_long = reglas.get('min_longitud')
            if min_long and len(valor.strip()) < min_long:
                errores.append(f"El campo '{pregunta.etiqueta}' requiere al menos {min_long} caracteres.")

        requerido_si = reglas.get('requerido_si')
        if requerido_si:
            campo = requerido_si.get('campo')
            operador = requerido_si.get('operador', '==')
            objetivo = requerido_si.get('valor')
            valor_campo = self._obtener_valor_contexto(campo, contexto)
            if self._evaluar_operador(valor_campo, operador, objetivo) and valor in [None, '', [], {}]:
                errores.append(f"El campo '{pregunta.etiqueta}' es obligatorio según la regla de validación.")

        return errores

    def _es_requerido_condicional(self, pregunta, contexto):
        reglas = pregunta.reglas_validacion or {}
        requerido_si = reglas.get('requerido_si')
        if not requerido_si:
            return False
        campo = requerido_si.get('campo')
        operador = requerido_si.get('operador', '==')
        objetivo = requerido_si.get('valor')
        valor_campo = self._obtener_valor_contexto(campo, contexto)
        return self._evaluar_operador(valor_campo, operador, objetivo)

    def _calcular_incidencias(self, respuestas, preguntas, contexto):
        if not respuestas:
            return False

        if respuestas.get('tiene_senaletica') is False:
            return True
        if respuestas.get('danos_cilindro') is True:
            return True
        if respuestas.get('vigente_mantenimiento_recarga') is False:
            return True

        pregunta_presion = preguntas.get('presion_optima')
        if pregunta_presion and self._pregunta_aplica(pregunta_presion, contexto):
            presion = respuestas.get('presion_optima')
            if presion is False:
                return True

        return False


class QuestionOptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('valor', 'etiqueta', 'orden')


class QuestionCreateSerializer(serializers.ModelSerializer):
    opciones = QuestionOptionCreateSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = (
            'clave',
            'etiqueta',
            'tipo',
            'requerido',
            'orden',
            'ayuda',
            'reglas_visibilidad',
            'reglas_validacion',
            'opciones',
        )


class FormTemplateCreateSerializer(serializers.ModelSerializer):
    preguntas = QuestionCreateSerializer(many=True, required=False)
    empresas_permitidas = serializers.PrimaryKeyRelatedField(
        queryset=Empresa.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = FormTemplate
        fields = (
            'codigo',
            'titulo',
            'version',
            'activo',
            'descripcion',
            'header_requiere_en_establecimiento',
            'roles_permitidos',
            'empresas_permitidas',
            'preguntas',
        )

    def validate_roles_permitidos(self, value):
        if value in [None, '']:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('roles_permitidos debe ser una lista.')
        allowed = {choice[0] for choice in Perfil.ROLE_CHOICES}
        invalid = sorted({role for role in value if role not in allowed})
        if invalid:
            raise serializers.ValidationError(
                f"Roles inválidos: {', '.join(invalid)}."
            )
        return value

    def create(self, validated_data):
        preguntas_data = validated_data.pop('preguntas', [])
        empresas_data = validated_data.pop('empresas_permitidas', [])
        template = FormTemplate.objects.create(**validated_data)
        if empresas_data:
            template.empresas_permitidas.set(empresas_data)
        for pregunta_data in preguntas_data:
            opciones_data = pregunta_data.pop('opciones', [])
            pregunta = Question.objects.create(template=template, **pregunta_data)
            for opcion_data in opciones_data:
                QuestionOption.objects.create(pregunta=pregunta, **opcion_data)
        return template
