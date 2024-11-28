from datetime import datetime, timedelta
import random
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class TestDataGenerator:
    """Generador de datos de prueba para el sistema de encuestas."""
    
    def __init__(self):
        self.activities = []
        self.participants = []
        self.survey_results = []
        
    def generate_activities(self):
        """Genera actividades de prueba."""
        self.activities = [
            {
                "_id": ObjectId(),
                "name": "Taller de Alfabetización",
                "description": "Clases básicas de lectura y escritura",
                "community": "San Juan",
                "status": "active",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "_id": ObjectId(),
                "name": "Curso de Finanzas Personales",
                "description": "Gestión básica de presupuesto familiar",
                "community": "Santa María",
                "status": "active",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        logger.info(f"Generadas {len(self.activities)} actividades de prueba")
        return self.activities

    def generate_participants(self, participants_per_activity=10):
        """Genera participantes de prueba para cada actividad."""
        if not self.activities:
            self.generate_activities()
            
        self.participants = []
        for activity in self.activities:
            for i in range(participants_per_activity):
                participant = {
                    "_id": ObjectId(),
                    "name": f"Participante {i+1} - {activity['community']}",
                    "community": activity["community"],
                    "age_group": random.choice(["18-30", "31-45", "46-60", "más de 60"]),
                    "gender": random.choice(["Hombre", "Mujer"]),
                    "education_level": random.choice([
                        "Sin educación formal",
                        "Primaria incompleta",
                        "Primaria completa",
                        "Secundaria incompleta",
                        "Secundaria completa"
                    ]),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                self.participants.append(participant)
        
        logger.info(f"Generados {len(self.participants)} participantes de prueba")
        return self.participants

    def generate_survey_results(self, surveys_per_participant=3):
        """Genera resultados de encuestas de prueba."""
        if not self.participants:
            self.generate_participants()
            
        self.survey_results = []
        for participant in self.participants:
            # Encontrar la actividad correspondiente a la comunidad del participante
            activity = next(
                (a for a in self.activities if a["community"] == participant["community"]), 
                random.choice(self.activities)
            )
            
            for _ in range(surveys_per_participant):
                processed_date = datetime.now() - timedelta(days=random.randint(0, 60))
                
                if activity["name"] == "Taller de Alfabetización":
                    responses = {
                        "seguridad_lectura": str(random.randint(1, 5)),
                        "mejora_comprension": str(random.randint(1, 5)),
                        "calidad_vida": str(random.randint(1, 5)),
                        "capacitacion": str(random.randint(1, 5))
                    }
                else:  # Curso de Finanzas Personales
                    responses = {
                        "entendimiento_presupuesto": str(random.randint(1, 5)),
                        "gestion_ingresos": str(random.randint(1, 5)),
                        "calidad_vida": str(random.randint(1, 5)),
                        "capacitacion": str(random.randint(1, 5))
                    }
                
                result = {
                    "_id": ObjectId(),
                    "participant_id": str(participant["_id"]),
                    "activity_id": str(activity["_id"]),
                    "responses": responses,
                    "confidence": round(random.uniform(75.0, 98.0), 2),
                    "processed_at": processed_date,
                    "notes": random.choice([
                        "Participación activa",
                        "Requiere seguimiento",
                        "Excelente progreso",
                        None
                    ])
                }
                self.survey_results.append(result)
        
        logger.info(f"Generados {len(self.survey_results)} resultados de encuestas de prueba")
        return self.survey_results

    def generate_all(self):
        """Genera todos los datos de prueba."""
        self.generate_activities()
        self.generate_participants()
        self.generate_survey_results()
        
        return {
            "activities": self.activities,
            "participants": self.participants,
            "survey_results": self.survey_results
        }