"""
Sistema de plantillas para extracción de datos de PDFs.
"""

from .template_base import PDFTemplate
from .vida_laboral_template import VidaLaboralTemplate
from .vida_laboral_complete import VidaLaboralCompleteTemplate
from .vida_laboral_final import VidaLaboralFinalTemplate
from .vida_laboral_secuencia import VidaLaboralSecuenciaTemplate  # Template con secuencia completa

# Usar la plantilla de secuencia que ejecuta ambos scripts que funcionan
__all__ = ['PDFTemplate', 'VidaLaboralTemplate', 'VidaLaboralCompleteTemplate', 'VidaLaboralFinalTemplate', 'VidaLaboralSecuenciaTemplate']
