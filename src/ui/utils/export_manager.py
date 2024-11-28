import csv
import logging
from tkinter import Image
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import matplotlib.pyplot as plt
import io

logger = logging.getLogger(__name__)

class ExportManager:
    @staticmethod
    def prepare_export_data(results: List[Dict], participants: Dict, activities: Dict) -> List[Dict]:
        """Prepara los datos para exportación en un formato uniforme."""
        export_data = []
        for result in results:
            participant = participants.get(result['participant_id'], {})
            activity = activities.get(result['activity_id'], {})
            
            base_row = {
                "Participante": participant.get('name', 'Desconocido'),
                "Comunidad": participant.get('community', 'Desconocida'),
                "Actividad": activity.get('name', 'Desconocida'),
                "Confianza": f"{result.get('confidence', 0):.1f}%",
                "Fecha": result.get('processed_at', datetime.now()).strftime("%Y-%m-%d"),
                "Notas": result.get('notes', '')
            }
            
            # Expandir las respuestas en filas individuales
            for question, answer in result.get('responses', {}).items():
                row = base_row.copy()
                row.update({
                    "Pregunta": question,
                    "Respuesta": answer
                })
                export_data.append(row)
                
        return export_data

    @staticmethod
    def export_to_csv(filename: str, data: List[Dict]) -> bool:
        """Exporta los datos a un archivo CSV."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                if not data:
                    raise ValueError("No hay datos para exportar")
                
                # Validar datos antes de exportar
                for row in data:
                    if any(pd.isna(value) for value in row.values()):
                        raise ValueError("Datos inválidos en el conjunto de datos")
                        
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            return True
        except FileNotFoundError:
            logger.error(f"No se pudo crear el archivo: {filename}")
            raise IOError("No se pudo crear el archivo")
        except Exception as e:
            logger.error(f"Error exportando a CSV: {e}")
            raise

    @staticmethod
    def export_to_excel(filename: str, data: List[Dict], charts: Dict = None) -> bool:
        """
        Exporta los datos a un archivo Excel con múltiples hojas y gráficos.
        
        Args:
            filename: Ruta del archivo a crear
            data: Lista de diccionarios con los datos
            charts: Diccionario de figuras de matplotlib para incluir
        """
        try:
            # Crear un escritor de Excel con opciones de formato
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                # Convertir datos a DataFrame
                df = pd.DataFrame(data)
                
                # Escribir datos principales
                df.to_excel(writer, sheet_name='Resultados', index=False)
                
                # Crear hoja de resumen
                summary_data = {
                    'Total Respuestas': len(data),
                    'Comunidades Únicas': len(df['Comunidad'].unique()),
                    'Actividades Únicas': len(df['Actividad'].unique()),
                    'Participantes Únicos': len(df['Participante'].unique()),
                }
                pd.Series(summary_data).to_excel(writer, sheet_name='Resumen')
                
                # Añadir gráficos si se proporcionaron
                if charts:
                    worksheet = writer.book.add_worksheet('Gráficos')
                    row = 0
                    for title, fig in charts.items():
                        # Convertir figura de matplotlib a imagen
                        imgdata = io.BytesIO()
                        fig.savefig(imgdata, format='png')
                        worksheet.insert_image(row, 0, '', {'image_data': imgdata})
                        row += 40  # Espacio para el siguiente gráfico
                
                # Ajustar formato
                workbook = writer.book
                worksheet = writer.sheets['Resultados']
                
                # Formato para encabezados
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'bg_color': '#D9EAD3',
                    'border': 1
                })
                
                # Aplicar formato a encabezados
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)  # Ajustar ancho de columna
                
            return True
        except Exception as e:
            logger.error(f"Error exportando a Excel: {e}")
            raise

    @staticmethod
    def export_to_pdf(filename: str, data: List[Dict], charts: Dict = None, title: str = "Reporte de Resultados") -> bool:
        """
        Exporta los datos a un archivo PDF con formato profesional.
        
        Args:
            filename: Ruta del archivo a crear
            data: Lista de diccionarios con los datos
            charts: Diccionario de figuras de matplotlib para incluir
            title: Título del reporte
        """
        try:
            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            
            # Elementos del documento
            elements = []
            
            # Título
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 12))
            
            # Resumen
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=20
            )
            
            summary_text = f"""
            Total de Respuestas: {len(data)}
            Comunidades Únicas: {len(set(d['Comunidad'] for d in data))}
            Actividades Únicas: {len(set(d['Actividad'] for d in data))}
            Participantes Únicos: {len(set(d['Participante'] for d in data))}
            """
            elements.append(Paragraph(summary_text, summary_style))
            elements.append(Spacer(1, 20))
            
            # Tabla de datos
            if data:
                # Preparar datos de tabla
                table_data = [list(data[0].keys())]  # Encabezados
                for row in data:
                    table_data.append([str(x) for x in row.values()])
                
                # Crear tabla
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
            
            # Añadir gráficos
            if charts:
                elements.append(Spacer(1, 30))
                for title, fig in charts.items():
                    imgdata = io.BytesIO()
                    fig.savefig(imgdata, format='png', dpi=300, bbox_inches='tight')
                    elements.append(Paragraph(title, styles['Heading2']))
                    elements.append(Image(imgdata))
                    elements.append(Spacer(1, 20))
            
            # Generar PDF
            doc.build(elements)
            return True
            
        except Exception as e:
            logger.error(f"Error exportando a PDF: {e}")
            raise