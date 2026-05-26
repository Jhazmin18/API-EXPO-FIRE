from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from empresas.models import Empresa
from empresas.serializers import ContactoSerializer, EmpresaSerializer
from extintores.models import Extintor


ESTADO_PRIORIDAD = {
    'rojo': 0,
    'amarillo': 1,
    'verde': 2,
}

ESTADO_FILL = {
    'rojo': PatternFill('solid', fgColor='FCA5A5'),
    'amarillo': PatternFill('solid', fgColor='FEF08A'),
    'verde': PatternFill('solid', fgColor='BBF7D0'),
}

HEADER_FILL = PatternFill('solid', fgColor='E5E7EB')
TITLE_FILL = PatternFill('solid', fgColor='1F2937')


class InventarioReporteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa_id = request.query_params.get('empresa_id')
        if not empresa_id:
            return Response({'detail': 'Debe enviar empresa_id.'}, status=400)

        empresa = get_object_or_404(
            Empresa.objects.prefetch_related('contactos'),
            id=empresa_id,
        )
        contacto_principal = empresa.contactos.order_by('created_at', 'id').first()
        extintores = list(
            Extintor.objects.filter(empresa=empresa)
            .select_related('empresa')
            .order_by('codigo')
        )

        resumen = {
            'total': len(extintores),
            'verde': 0,
            'amarillo': 0,
            'rojo': 0,
        }

        inventario = []
        for extintor in extintores:
            estado = extintor.estado
            resumen[estado] += 1
            inventario.append(self._serialize_extintor(extintor))

        inventario.sort(
            key=lambda item: (
                ESTADO_PRIORIDAD.get(item['estado'], 99),
                item['dias_para_revision'] if item['dias_para_revision'] is not None else 999999,
                item['dias_para_vencer'] if item['dias_para_vencer'] is not None else 999999,
                item['codigo'],
            )
        )
        alertas = [
            item for item in inventario
            if item['estado'] in {'rojo', 'amarillo'}
        ]

        data = {
            'fecha_generacion': timezone.localdate().isoformat(),
            'archivo_sugerido': self._build_filename(empresa),
            'empresa': EmpresaSerializer(empresa, context={'request': request}).data,
            'contacto_principal': (
                ContactoSerializer(contacto_principal).data
                if contacto_principal else None
            ),
            'resumen_estados': resumen,
            'inventario': inventario,
            'alertas': alertas,
        }

        if request.query_params.get('formato') == 'xlsx':
            return self._excel_response(data)

        return Response(data)

    def _serialize_extintor(self, extintor):
        return {
            'id': str(extintor.id),
            'codigo': extintor.codigo,
            'ubicacion': extintor.ubicacion,
            'agente': extintor.tipo,
            'agente_display': extintor.get_tipo_display(),
            'capacidad': extintor.capacidad,
            'fecha_fabricacion': self._date(extintor.fecha_fabricacion),
            'fecha_vencimiento': self._date(extintor.fecha_vencimiento),
            'proxima_revision': self._date(extintor.proxima_revision),
            'fecha_prueba_hidrostatica': self._date(extintor.fecha_prueba_hidrostatica),
            'dias_para_vencer': extintor.dias_para_vencer,
            'dias_para_revision': extintor.dias_para_revision,
            'estado': extintor.estado,
            'observaciones': extintor.observaciones,
        }

    def _date(self, value):
        return value.isoformat() if value else None

    def _build_filename(self, empresa):
        fecha = timezone.localdate().isoformat()
        nombre = ''.join(
            char if char.isalnum() else '_'
            for char in empresa.nombre.strip()
        ).strip('_')
        return f'Reporte_Extintores_{nombre}_{fecha}.xlsx'

    def _excel_response(self, data):
        workbook = Workbook()
        resumen_sheet = workbook.active
        resumen_sheet.title = 'Resumen'
        inventario_sheet = workbook.create_sheet('Inventario completo')
        alertas_sheet = workbook.create_sheet('Alertas')

        self._write_resumen(resumen_sheet, data)
        self._write_extintores(inventario_sheet, data['inventario'])
        self._write_extintores(alertas_sheet, data['alertas'])

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{data["archivo_sugerido"]}"'
        return response

    def _write_resumen(self, sheet, data):
        empresa = data['empresa']
        contacto = data['contacto_principal'] or {}
        resumen = data['resumen_estados']

        sheet.merge_cells('A1:D1')
        sheet['A1'] = 'Reporte de Inventario de Extintores'
        sheet['A1'].font = Font(bold=True, color='FFFFFF', size=14)
        sheet['A1'].fill = TITLE_FILL
        sheet['A1'].alignment = Alignment(horizontal='center')

        rows = [
            ('Empresa', empresa.get('nombre')),
            ('Razón social', empresa.get('razon_social')),
            ('Tipo de inmueble', empresa.get('tipo_inmueble')),
            ('Fecha de generación', data['fecha_generacion']),
            ('Contacto principal', contacto.get('nombre')),
            ('Correo principal', contacto.get('correo_principal')),
            ('Teléfono principal', contacto.get('telefono_principal')),
            ('', ''),
            ('Total extintores', resumen['total']),
            ('Verde', resumen['verde']),
            ('Amarillo', resumen['amarillo']),
            ('Rojo', resumen['rojo']),
        ]

        for row_number, row in enumerate(rows, start=3):
            sheet.cell(row=row_number, column=1, value=row[0])
            sheet.cell(row=row_number, column=2, value=row[1] or '')
            sheet.cell(row=row_number, column=1).font = Font(bold=True)

        sheet.column_dimensions['A'].width = 24
        sheet.column_dimensions['B'].width = 44

    def _write_extintores(self, sheet, rows):
        columns = [
            ('Código', 'codigo'),
            ('Ubicación', 'ubicacion'),
            ('Agente', 'agente_display'),
            ('Capacidad', 'capacidad'),
            ('Fecha Fabricación', 'fecha_fabricacion'),
            ('Fecha Vencimiento', 'fecha_vencimiento'),
            ('Próxima Revisión', 'proxima_revision'),
            ('Prueba Hidrostática', 'fecha_prueba_hidrostatica'),
            ('Días para Vencer', 'dias_para_vencer'),
            ('Días para Revisión', 'dias_para_revision'),
            ('Estado', 'estado'),
            ('Observaciones', 'observaciones'),
        ]

        for column_number, (header, _) in enumerate(columns, start=1):
            cell = sheet.cell(row=1, column=column_number, value=header)
            cell.font = Font(bold=True)
            cell.fill = HEADER_FILL
            cell.alignment = Alignment(horizontal='center')

        for row_number, item in enumerate(rows, start=2):
            for column_number, (_, key) in enumerate(columns, start=1):
                cell = sheet.cell(row=row_number, column=column_number, value=item.get(key))
                cell.alignment = Alignment(vertical='top', wrap_text=True)

            estado_cell = sheet.cell(row=row_number, column=11)
            estado_cell.fill = ESTADO_FILL.get(item.get('estado'), HEADER_FILL)
            estado_cell.font = Font(bold=True)

        widths = [16, 32, 26, 14, 18, 18, 18, 20, 18, 20, 14, 42]
        for column_number, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(column_number)].width = width

        sheet.freeze_panes = 'A2'
        sheet.auto_filter.ref = sheet.dimensions
