# src/utils/survey_generator.py

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black, white, grey
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
from io import BytesIO
from typing import Dict, List, Optional
import os
from datetime import datetime

class SurveyGenerator:
    def __init__(self):
        self.width, self.height = letter
        self.margin = 50
        self.line_height = 20
        self.font_size = 12
        self.current_y = self.height - self.margin
        
    def generate_survey_pdf(
        self,
        participant_id: str,
        survey_name: str,
        participant_name: str,
        activity_data: Dict,
        output_path: str
    ) -> str:
        """
        Genera un PDF de encuesta para un participante específico.
        
        Args:
            participant_id: ID único del participante
            survey_name: Nombre de la encuesta
            participant_name: Nombre del participante
            activity_data: Datos de la actividad
            output_path: Ruta donde guardar el PDF
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        # Crear el PDF
        c = canvas.Canvas(output_path, pagesize=letter)
        self.current_y = self.height - self.margin
        
        # Generar y añadir código QR
        qr_data = f"{participant_id}_{datetime.now().strftime('%Y%m%d')}"
        qr_path = self._generate_qr(qr_data)
        c.drawImage(qr_path, self.width - 100, self.height - 100, 80, 80)
        
        # Encabezado
        self._draw_header(c, participant_id, survey_name, participant_name)
        
        # Título principal
        self._draw_title(c, "ENCUESTA DE EVALUACIÓN DE ACTIVIDADES DE ENLACE RURAL")
        
        # Instrucciones
        self._draw_instructions(c)
        
        # Información del proyecto
        self._draw_section_title(c, "INFORMACIÓN DEL PROYECTO")
        self._draw_project_info(c, activity_data)
        
        # Datos personales
        self._draw_section_title(c, "DATOS PERSONALES")
        self._draw_personal_info(c)
        
        # Finalizar PDF
        c.save()
        return output_path
        
    def _generate_qr(self, data: str) -> str:
        """Genera un código QR y lo guarda temporalmente"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        temp_path = "temp_qr.png"
        img.save(temp_path)
        return temp_path
        
    def _draw_header(self, c: canvas.Canvas, participant_id: str, survey_name: str, participant_name: str):
        """Dibuja el encabezado del formulario"""
        c.setFont("Helvetica-Bold", 12)
        
        # ID y nombre de encuesta
        c.drawString(self.margin, self.current_y, f"ID_PARTICIPANTE: {participant_id}")
        self.current_y -= self.line_height
        c.drawString(self.margin, self.current_y, f"NOMBRE DE LA ENCUESTA: {survey_name}")
        self.current_y -= self.line_height
        c.drawString(self.margin, self.current_y, f"NOMBRE COMPLETO: {participant_name}")
        self.current_y -= self.line_height * 1.5
        
    def _draw_title(self, c: canvas.Canvas, title: str):
        """Dibuja el título principal"""
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.margin, self.current_y, title)
        self.current_y -= self.line_height * 2
        
    def _draw_instructions(self, c: canvas.Canvas):
        """Dibuja las instrucciones"""
        c.setFont("Helvetica", 10)
        instructions = ("INSTRUCCIONES: A CONTINUACIÓN ENCONTRARÁS UNA SERIE DE PREGUNTAS. "
                       "MARCA CON UNA \"X\" EL ESPACIO QUE MEJOR REFLEJE TU RESPUESTA.")
        c.drawString(self.margin, self.current_y, instructions)
        self.current_y -= self.line_height * 2
        
    def _draw_section_title(self, c: canvas.Canvas, title: str):
        """Dibuja el título de una sección"""
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin, self.current_y, title)
        self.current_y -= self.line_height * 1.5
        
    def _draw_project_info(self, c: canvas.Canvas, activity_data: Dict):
        """Dibuja la sección de información del proyecto"""
        c.setFont("Helvetica", 10)
        
        # Nombre del proyecto
        c.drawString(self.margin, self.current_y, "NOMBRE DEL PROYECTO")
        self.current_y -= self.line_height
        for project in activity_data.get("projects", []):
            c.drawString(self.margin + 20, self.current_y, f"□ {project}")
            self.current_y -= self.line_height
            
        # Fecha
        self.current_y -= self.line_height
        today = datetime.now()
        c.drawString(self.margin, self.current_y, 
                    f"FECHA ACTUAL: DÍA {today.day} MES {today.month} AÑO {today.year}")
        
        # Comunidad
        self.current_y -= self.line_height * 1.5
        c.drawString(self.margin, self.current_y, "NOMBRE DE LA COMUNIDAD")
        self.current_y -= self.line_height
        for community in activity_data.get("communities", []):
            c.drawString(self.margin + 20, self.current_y, f"□ {community}")
            self.current_y -= self.line_height
            
        # Rol
        self.current_y -= self.line_height
        c.drawString(self.margin, self.current_y, "ROL EN EL PROYECTO")
        self.current_y -= self.line_height
        c.drawString(self.margin + 20, self.current_y, "□ VOLUNTARIO    □ PARTICIPANTE")
        
    def _draw_personal_info(self, c: canvas.Canvas):
        """Dibuja la sección de información personal"""
        c.setFont("Helvetica", 10)
        
        fields = [
            ("FECHA DE NACIMIENTO (NÚMERO)", "DÍA __ MES __ AÑO ____"),
            ("EDAD", ["MENOS DE 18", "18-30", "31-45", "46-60", "MÁS DE 60"]),
            ("GÉNERO", ["HOMBRE", "MUJER", "OTRO"]),
            ("ESTADO CIVIL", ["SOLTERO/A", "CASADO/A", "UNIÓN LIBRE", 
                            "SEPARADO/A O DIVORCIADO/A", "VIUDO/A"]),
            ("NIVEL EDUCATIVO ALCANZADO", ["SIN EDUCACIÓN FORMAL", "PRIMARIA INCOMPLETA",
                                         "PRIMARIA COMPLETA", "SECUNDARIA INCOMPLETA",
                                         "SECUNDARIA COMPLETA", "PREPARATORIA",
                                         "EDUCACIÓN SUPERIOR"]),
            ("NÚMERO DE HIJOS", ["NINGUNO", "1-2", "3-4", "5 O MÁS"])
        ]
        
        for field, options in fields:
            self.current_y -= self.line_height
            c.drawString(self.margin, self.current_y, field)
            self.current_y -= self.line_height
            
            if isinstance(options, str):
                c.drawString(self.margin + 20, self.current_y, options)
            else:
                for option in options:
                    c.drawString(self.margin + 20, self.current_y, f"□ {option}")
                    self.current_y -= self.line_height
            
            self.current_y -= self.line_height/2