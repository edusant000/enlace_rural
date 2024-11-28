import asyncio
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QPushButton, 
                           QComboBox, QLabel, QFrame, QHeaderView,
                           QTabWidget, QGridLayout, QFileDialog)
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import logging
from typing import Dict, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import csv
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import QTimer

from ..utils.export_manager import ExportManager
from src.ui.utils.notification_manager import NotificationManager
from src.ui.widgets.loading_indicator import LoadingIndicator

# Configurar matplotlib para limpiar figuras automáticamente
plt.style.use('default')
plt.rcParams['figure.max_open_warning'] = 0

logger = logging.getLogger(__name__)

class SurveyResultsView(QWidget):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_activity_id = None
        self.current_results = []
        self.figures = {}  # Almacenar las figuras de matplotlib
        self.loading_indicator = LoadingIndicator(self)
        self.notification_manager = NotificationManager()
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.hide_loading)
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        main_layout = QVBoxLayout(self)

        # Panel de filtros
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        filter_layout = QHBoxLayout(filter_frame)
        
        # Filtros
        self.activity_combo = QComboBox()
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems([
            "Último mes", "Últimos 3 meses", "Últimos 6 meses", "Todo"
        ])
        self.community_combo = QComboBox()
        self.community_combo.addItem("Todas las comunidades")
        
        # Botones
        self.export_btn = QPushButton("Exportar Resultados")
        self.refresh_btn = QPushButton("Actualizar")

        filter_layout.addWidget(QLabel("Actividad:"))
        filter_layout.addWidget(self.activity_combo)
        filter_layout.addWidget(QLabel("Periodo:"))
        filter_layout.addWidget(self.date_range_combo)
        filter_layout.addWidget(QLabel("Comunidad:"))
        filter_layout.addWidget(self.community_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(self.refresh_btn)
        filter_layout.addWidget(self.export_btn)

        main_layout.addWidget(filter_frame)

        # Estadísticas generales
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        stats_layout = QGridLayout(stats_frame)

        self.total_surveys_label = QLabel("Total Encuestas: 0")
        self.avg_confidence_label = QLabel("Confianza Promedio: 0%")
        self.completion_rate_label = QLabel("Tasa de Completitud: 0%")
        self.total_participants_label = QLabel("Total Participantes: 0")
        
        stats_layout.addWidget(self.total_surveys_label, 0, 0)
        stats_layout.addWidget(self.avg_confidence_label, 0, 1)
        stats_layout.addWidget(self.completion_rate_label, 1, 0)
        stats_layout.addWidget(self.total_participants_label, 1, 1)

        main_layout.addWidget(stats_frame)

        # Pestañas para diferentes vistas
        self.tab_widget = QTabWidget()
        
        # Tab de Resumen
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        # Gráficos para el resumen
        charts_layout = QHBoxLayout()
        
        # Crear figuras de matplotlib
        self.figures['responses'] = plt.figure(figsize=(6, 4))
        self.figures['progress'] = plt.figure(figsize=(6, 4))
        
        # Crear canvas para los gráficos
        responses_canvas = FigureCanvas(self.figures['responses'])
        progress_canvas = FigureCanvas(self.figures['progress'])
        
        charts_layout.addWidget(responses_canvas)
        charts_layout.addWidget(progress_canvas)
        summary_layout.addLayout(charts_layout)
        
        # Tabla de resultados detallados
        self.results_table = QTableWidget()
        self.setup_results_table()
        summary_layout.addWidget(self.results_table)
        
        self.tab_widget.addTab(summary_tab, "Resumen")

        # Tab de Demografía
        demo_tab = QWidget()
        demo_layout = QGridLayout(demo_tab)
        
        # Crear figuras para demografía
        self.figures['age'] = plt.figure(figsize=(5, 4))
        self.figures['gender'] = plt.figure(figsize=(5, 4))
        self.figures['education'] = plt.figure(figsize=(10, 4))
        
        demo_layout.addWidget(FigureCanvas(self.figures['age']), 0, 0)
        demo_layout.addWidget(FigureCanvas(self.figures['gender']), 0, 1)
        demo_layout.addWidget(FigureCanvas(self.figures['education']), 1, 0, 1, 2)
        
        self.tab_widget.addTab(demo_tab, "Demografía")

        # Tab de Tendencias
        trends_tab = QWidget()
        trends_layout = QVBoxLayout(trends_tab)
        
        # Crear figuras para tendencias
        self.figures['trends'] = plt.figure(figsize=(10, 4))
        self.figures['confidence'] = plt.figure(figsize=(10, 4))
        
        trends_layout.addWidget(FigureCanvas(self.figures['trends']))
        trends_layout.addWidget(FigureCanvas(self.figures['confidence']))
        
        self.tab_widget.addTab(trends_tab, "Tendencias")

        main_layout.addWidget(self.tab_widget)

        # Conectar señales usando lambdas para manejar coroutinas
        self.activity_combo.currentIndexChanged.connect(
            lambda idx: asyncio.create_task(self.on_activity_changed(idx))
        )
        self.date_range_combo.currentIndexChanged.connect(
            lambda: asyncio.create_task(self.load_results())
        )
        self.community_combo.currentIndexChanged.connect(
            lambda: asyncio.create_task(self.load_results())
        )
        self.export_btn.clicked.connect(
            lambda: asyncio.create_task(self.export_results())
        )
        self.refresh_btn.clicked.connect(
            lambda: asyncio.create_task(self.load_results())
        )

    def setup_results_table(self):
        """Configura la tabla de resultados"""
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Participante", "Comunidad", "Pregunta", 
            "Respuesta", "Confianza", "Fecha"
        ])
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def update_charts(self):
        """Actualiza todos los gráficos con los datos actuales"""
        if not self.current_results:
            return

        # Convertir resultados a DataFrame para facilitar el análisis
        df = pd.DataFrame([
            {
                'participant_id': r['participant_id'],
                'activity_id': r['activity_id'],
                'confidence': r['confidence'],
                'processed_at': r['processed_at'],
                **r['responses']
            }
            for r in self.current_results
        ])

        # Actualizar gráficos
        self.update_response_distribution(df)
        self.update_progress_chart(df)
        self.update_demographic_charts()
        self.update_trends_charts(df)

        # Actualizar todos los canvas
        for fig in self.figures.values():
            fig.canvas.draw()

    async def export_results(self):
        """Exporta los resultados en varios formatos."""
        if not self.current_results:
            self.notification_manager.show_warning(
                self,
                "Exportación",
                "No hay resultados para exportar"
            )
            return

        try:
            self.show_loading("Preparando exportación...")
            
            # Preparar datos para exportación
            export_rows = []
            headers = ["Participante", "Comunidad", "Actividad", 
                      "Pregunta", "Respuesta", "Confianza", "Fecha", "Notas"]
            
            for result in self.current_results:
                participant = await self.data_manager.get_participant(result['participant_id'])
                activity = await self.data_manager.get_activity(result['activity_id'])
                
                for question, answer in result['responses'].items():
                    row = {
                        "Participante": participant.get('name', 'Desconocido'),
                        "Comunidad": participant.get('community', 'Desconocida'),
                        "Actividad": activity.get('name', 'Desconocida'),
                        "Pregunta": question,
                        "Respuesta": answer,
                        "Confianza": f"{result.get('confidence', '0')}%",
                        "Fecha": result['processed_at'].strftime("%Y-%m-%d") if isinstance(result.get('processed_at'), datetime) else str(result.get('processed_at', '')),
                        "Notas": result.get('notes', '')
                    }
                    export_rows.append(row)

            # Mostrar diálogo de exportación
            filename, selected_format = QFileDialog.getSaveFileName(
                self,
                "Guardar Resultados",
                "",
                "CSV (*.csv);;Excel (*.xlsx);;PDF (*.pdf)"
            )
            
            if not filename:
                return

            # Asegurarse de que el directorio existe
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Exportar según el formato seleccionado
            if selected_format == "CSV (*.csv)":
                if not filename.endswith('.csv'):
                    filename += '.csv'
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(export_rows)
            elif selected_format == "Excel (*.xlsx)":
                if not filename.endswith('.xlsx'):
                    filename += '.xlsx'
                pd.DataFrame(export_rows).to_excel(filename, index=False)
            elif selected_format == "PDF (*.pdf)":
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
                df = pd.DataFrame(export_rows)
                # TODO: Implementar exportación a PDF
                pass
            
            self.notification_manager.show_info(
                self,
                "Exportación Exitosa",
                f"Los resultados fueron exportados a {filename}"
            )
            
        except Exception as e:
            logger.error(f"Error al exportar resultados: {e}")
            self.notification_manager.show_error(
                self,
                "Error",
                f"Error al exportar resultados: {str(e)}"
            )
        finally:
            self.hide_loading()

            
    def get_date_range(self):
        """Obtiene el rango de fechas según el filtro seleccionado"""
        current_text = self.date_range_combo.currentText()
        end_date = datetime.now()
        
        if current_text == "Último mes":
            start_date = end_date - timedelta(days=30)
        elif current_text == "Últimos 3 meses":
            start_date = end_date - timedelta(days=90)
        elif current_text == "Últimos 6 meses":
            start_date = end_date - timedelta(days=180)
        else:  # Todo
            start_date = datetime.min
            
        return start_date, end_date

    async def load_activities(self):
        """Carga la lista de actividades y comunidades"""
        try:
            self.show_loading("Cargando actividades...")
            activities = await self.data_manager.get_all_activities()
            self.activity_combo.clear()
            
            for activity in activities:
                self.activity_combo.addItem(
                    activity['name'], 
                    activity['_id']
                )
                
            # Cargar comunidades únicas
            communities = set()
            participants = await self.data_manager.get_all_participants()
            
            for participant in participants:
                communities.add(participant['community'])
            
            self.community_combo.clear()
            self.community_combo.addItem("Todas las comunidades")
            self.community_combo.addItems(sorted(communities))
            
            self.notification_manager.show_info(
                self, 
                "Datos Cargados",
                f"Se cargaron {len(activities)} actividades y {len(communities)} comunidades"
            )
            
        except Exception as e:
            logger.error(f"Error al cargar actividades: {e}")
            self.notification_manager.show_error(
                self,
                "Error",
                f"Error al cargar actividades: {str(e)}"
            )
        finally:
            self.hide_loading()


    async def on_activity_changed(self, index):
        """Maneja el cambio de actividad seleccionada"""
        if index < 0:
            return

        try:
            activity_id = self.activity_combo.currentData()
            self.current_activity_id = activity_id
            await self.load_results()
        except Exception as e:
            logger.error(f"Error al cambiar actividad: {e}")

    def update_response_distribution(self, df):
        """Actualiza el gráfico de distribución de respuestas"""
        fig = self.figures['responses']
        fig.clear()
        ax = fig.add_subplot(111)

        # Obtener todas las preguntas y sus respuestas
        response_cols = [col for col in df.columns if col not in ['participant_id', 'activity_id', 'confidence', 'processed_at']]
        
        # Crear matriz de distribución de respuestas
        response_dist = pd.DataFrame()
        for col in response_cols:
            response_dist[col] = df[col].value_counts(normalize=True) * 100

        # Graficar barras apiladas
        response_dist.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title('Distribución de Respuestas')
        ax.set_xlabel('Valor de Respuesta')
        ax.set_ylabel('Porcentaje')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        fig.tight_layout()

    def update_progress_chart(self, df):
        """Actualiza el gráfico de progreso promedio por pregunta"""
        fig = self.figures['progress']
        fig.clear()
        ax = fig.add_subplot(111)

        # Calcular promedios por pregunta
        response_cols = [col for col in df.columns if col not in ['participant_id', 'activity_id', 'confidence', 'processed_at']]
        averages = df[response_cols].astype(float).mean()

        # Crear gráfico de barras
        averages.plot(kind='bar', ax=ax)
        ax.set_title('Promedio por Pregunta')
        ax.set_xlabel('Pregunta')
        ax.set_ylabel('Promedio')
        ax.set_ylim(0, 5)  # Asumiendo escala de 1-5
        
        # Rotar etiquetas para mejor legibilidad
        plt.xticks(rotation=45, ha='right')
        fig.tight_layout()

    async def update_demographic_charts(self):
        """Actualiza los gráficos demográficos"""
        try:
            # Obtener datos demográficos de los participantes
            participant_ids = set(r['participant_id'] for r in self.current_results)
            participants_data = []
            
            for pid in participant_ids:
                participant = await self.data_manager.get_participant(pid)
                if participant:
                    participants_data.append(participant)

            if not participants_data:
                return

            df_participants = pd.DataFrame(participants_data)

            # Gráfico de distribución por edad
            fig = self.figures['age']
            fig.clear()
            ax = fig.add_subplot(111)
            df_participants['age_group'].value_counts().plot(kind='pie', ax=ax)
            ax.set_title('Distribución por Edad')

            # Gráfico de distribución por género
            fig = self.figures['gender']
            fig.clear()
            ax = fig.add_subplot(111)
            df_participants['gender'].value_counts().plot(kind='pie', ax=ax)
            ax.set_title('Distribución por Género')

            # Gráfico de nivel educativo
            fig = self.figures['education']
            fig.clear()
            ax = fig.add_subplot(111)
            education_counts = df_participants['education_level'].value_counts()
            education_counts.plot(kind='barh', ax=ax)
            ax.set_title('Distribución por Nivel Educativo')
            fig.tight_layout()

        except Exception as e:
            logger.error(f"Error al actualizar gráficos demográficos: {e}")

    def update_trends_charts(self, df):
        """Actualiza los gráficos de tendencias"""
        # Gráfico de tendencias temporales
        fig = self.figures['trends']
        fig.clear()
        ax = fig.add_subplot(111)

        # Agrupar por fecha y calcular promedios
        df['date'] = pd.to_datetime(df['processed_at']).dt.date
        daily_averages = df.groupby('date')[df.select_dtypes(include=[np.number]).columns].mean()

        daily_averages.plot(ax=ax)
        ax.set_title('Tendencias de Respuestas')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Valor Promedio')
        plt.xticks(rotation=45)
        fig.tight_layout()

        # Gráfico de niveles de confianza
        fig = self.figures['confidence']
        fig.clear()
        ax = fig.add_subplot(111)

        df['confidence'].hist(bins=20, ax=ax)
        ax.set_title('Distribución de Niveles de Confianza OCR')
        ax.set_xlabel('Nivel de Confianza (%)')
        ax.set_ylabel('Frecuencia')
        fig.tight_layout()

    async def load_results(self):
        """Carga los resultados de las encuestas según los filtros actuales"""
        if not self.current_activity_id:
            return

        try:
            self.show_loading("Cargando resultados...")
            
            # Obtener rango de fechas
            start_date, end_date = self.get_date_range()

            # Construir query
            query = {
                'activity_id': self.current_activity_id,
                'processed_at': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }

            # Aplicar filtro de comunidad si está seleccionada
            selected_community = self.community_combo.currentText()
            if selected_community != "Todas las comunidades":
                participants = await self.data_manager.get_participants_by_community(
                    selected_community
                )
                participant_ids = [str(p['_id']) for p in participants]
                query['participant_id'] = {'$in': participant_ids}

            # Obtener resultados
            results = await self.data_manager.get_survey_results_by_query(query)
            self.current_results = results

            if not self.current_results:
                self.notification_manager.show_warning(
                    self,
                    "Sin Resultados",
                    "No se encontraron resultados para los filtros seleccionados"
                )
                return

            # Actualizar estadísticas
            self.update_statistics()
            
            # Actualizar tabla - ahora esperamos la actualización
            await self.update_results_table(self.current_results)
            
            # Actualizar gráficos
            self.update_charts()

        except Exception as e:
            logger.error(f"Error al cargar resultados: {e}")
            self.notification_manager.show_error(
                self,
                "Error",
                f"Error al cargar resultados: {str(e)}"
            )
        finally:
            self.hide_loading()


    def is_survey_complete(self, result: Dict) -> bool:
        """Verifica si una encuesta está completa"""
        responses = result.get('responses', {})
        return all(bool(str(answer).strip()) for answer in responses.values())
    
    def show_loading(self, message="Cargando..."):
        """Muestra el indicador de carga con un mensaje específico."""
        self.loading_indicator.set_message(message)
        self.loading_indicator.show()
        # Centrar el loading indicator en el widget padre
        geo = self.geometry()
        loading_geo = self.loading_indicator.geometry()
        x = geo.x() + (geo.width() - loading_geo.width()) // 2
        y = geo.y() + (geo.height() - loading_geo.height()) // 2
        self.loading_indicator.move(x, y)
        
    def hide_loading(self):
        """Oculta el indicador de carga."""
        self.loading_indicator.hide()
        self.loading_timer.stop()
    
    def update_statistics(self):
        """Actualiza las estadísticas mostradas"""
        if not self.current_results:
            return

        try:
            total_surveys = len(self.current_results)
            total_participants = len(set(r['participant_id'] for r in self.current_results))
            avg_confidence = sum(float(r['confidence']) for r in self.current_results) / total_surveys if total_surveys > 0 else 0
            completed_surveys = sum(1 for r in self.current_results if self.is_survey_complete(r))
            completion_rate = (completed_surveys / total_surveys) * 100 if total_surveys > 0 else 0

            self.total_surveys_label.setText(f"Total Encuestas: {total_surveys}")
            self.total_participants_label.setText(f"Total Participantes: {total_participants}")
            self.avg_confidence_label.setText(f"Confianza Promedio: {avg_confidence:.1f}%")
            self.completion_rate_label.setText(f"Tasa de Completitud: {completion_rate:.1f}%")

        except Exception as e:
            logger.error(f"Error al actualizar estadísticas: {e}")
            self.notification_manager.show_error(
                self,
                "Error",
                "Error al actualizar estadísticas"
            )

    async def update_results_table(self, results):
        """Actualiza la tabla con los resultados"""
        self.results_table.setRowCount(0)  # Limpiar tabla
        
        try:
            for result in results:
                participant_id = result.get('participant_id', '')
                responses = result.get('responses', {})
                confidence = result.get('confidence', 0)
                date = result.get('processed_at', '')
                
                # Obtener información del participante
                participant = await self.data_manager.get_participant(participant_id)
                participant_name = participant.get('name', 'Desconocido') if participant else 'Desconocido'
                participant_community = participant.get('community', 'Desconocida') if participant else 'Desconocida'
                
                for question, answer in responses.items():
                    row = self.results_table.rowCount()
                    self.results_table.insertRow(row)
                    
                    # Insertar datos en la tabla
                    items = [
                        participant_name,
                        participant_community,
                        question,
                        str(answer),
                        f"{float(confidence):.1f}%",
                        date.strftime("%Y-%m-%d") if isinstance(date, datetime) else str(date)
                    ]
                    
                    for col, item in enumerate(items):
                        table_item = QTableWidgetItem(str(item))
                        table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Hacer no editable
                        self.results_table.setItem(row, col, table_item)
                        
            self.results_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error al actualizar tabla: {e}")
            self.notification_manager.show_error(
                self,
                "Error",
                f"Error al actualizar tabla: {str(e)}"
            )