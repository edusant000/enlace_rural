import hashlib
from datetime import datetime
import re
import unicodedata

class ParticipantIDGenerator:
    """
    Clase para generar y validar IDs únicos de participantes basados en su nombre y fecha de nacimiento.
    """
    
    @staticmethod
    def clean_name(name):
        """
        Limpia y normaliza el nombre eliminando espacios extras, caracteres especiales y acentos.
        
        Args:
            name (str): Nombre a limpiar
            
        Returns:
            str: Nombre limpio y normalizado
        """
        # Convertir a minúsculas
        name = name.lower()
        
        # Eliminar acentos y caracteres especiales
        name = unicodedata.normalize('NFKD', name)
        name = name.encode('ASCII', 'ignore').decode('ASCII')
        
        # Eliminar caracteres no alfabéticos y espacios extras
        name = re.sub(r'[^a-z\s]', '', name)
        
        # Eliminar espacios múltiples y espacios al inicio/final
        name = ' '.join(name.split())
        
        return name

    @staticmethod
    def validate_date(date_str):
        """
        Valida que la fecha tenga el formato correcto (DD/MM/YYYY).
        
        Args:
            date_str (str): Fecha en formato DD/MM/YYYY
            
        Returns:
            bool: True si la fecha es válida, False en caso contrario
        """
        try:
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                return False
            datetime.strptime(date_str, '%d/%m/%Y')
            return True
        except ValueError:
            return False

    def generate_id(self, name, birth_date):
        """
        Genera un ID único basado en el nombre y fecha de nacimiento.
        
        Args:
            name (str): Nombre completo del participante
            birth_date (str): Fecha de nacimiento en formato DD/MM/YYYY
            
        Returns:
            str: ID único de 8 caracteres
            
        Raises:
            ValueError: Si el formato de la fecha es incorrecto o los datos están vacíos
        """
        # Validar datos de entrada
        if not name or not birth_date:
            raise ValueError("El nombre y la fecha de nacimiento son obligatorios")
            
        if not self.validate_date(birth_date):
            raise ValueError("Formato de fecha incorrecto. Use DD/MM/YYYY")
            
        clean_name = self.clean_name(name)
        combined = f"{clean_name}_{birth_date}"
        
        # Generar hash y tomar los primeros 8 caracteres
        hash_object = hashlib.sha256(combined.encode())
        return hash_object.hexdigest()[:8]
