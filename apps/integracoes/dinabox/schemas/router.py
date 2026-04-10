"""
ROUTER DE SCHEMAS DINABOX

Coordena o parsing do JSON para os 3 schemas especializados (Administrativo, Operacional, Logístico).
Cada schema extrai só os dados relevantes para seu domínio.

Uso:
    from apps.integracoes.dinabox.schemas.router import DinaboxRouter
    
    router = DinaboxRouter(raw_json)
    
    admin_data = router.administrativo()  # Para PCP/Financeiro
    ops_data = router.operacional()       # Para Bipagem/Fábrica
    log_data = router.logistico()         # Para Expedição
"""

from typing import Dict, Any
from datetime import datetime

from .dinabox_administrativo import DinaboxProjectAdministrativo
from .dinabox_operacional import DinaboxProjectOperacional
from .dinabox_logistico import DinaboxProjectLogistico


class DinaboxRouter:
    """Router que distribui dados Dinabox para os 3 schemas especializados."""
    
    def __init__(self, raw_json: Dict[str, Any]):
        """
        Inicializa router com JSON bruto do Dinabox.
        
        Args:
            raw_json: Dicionário/JSON da resposta Dinabox
        """
        self.raw_json = raw_json
        self._validated = False
        self._errors = []
    
    def administrativo(self) -> DinaboxProjectAdministrativo:
        """Retorna dados validados para contexto administrativo (PCP, Financeiro, Compras)."""
        try:
            return DinaboxProjectAdministrativo.model_validate(self.raw_json)
        except Exception as e:
            self._errors.append(f"Administrativo: {str(e)}")
            raise
    
    def operacional(self) -> DinaboxProjectOperacional:
        """Retorna dados validados para contexto operacional (Bipagem, Fabricação)."""
        try:
            return DinaboxProjectOperacional.model_validate(self.raw_json)
        except Exception as e:
            self._errors.append(f"Operacional: {str(e)}")
            raise
    
    def logistico(self) -> DinaboxProjectLogistico:
        """Retorna dados validados para contexto logístico (Expedição, Viagens)."""
        try:
            return DinaboxProjectLogistico.model_validate(self.raw_json)
        except Exception as e:
            self._errors.append(f"Logístico: {str(e)}")
            raise
    
    def validate_all(self) -> bool:
        """Valida em todos os 3 schemas. Retorna True se OK, False se houver erros."""
        self._errors = []
        
        try:
            self.administrativo()
        except Exception as e:
            self._errors.append(f"Administrativo: {str(e)}")
        
        try:
            self.operacional()
        except Exception as e:
            self._errors.append(f"Operacional: {str(e)}")
        
        try:
            self.logistico()
        except Exception as e:
            self._errors.append(f"Logístico: {str(e)}")
        
        self._validated = True
        return len(self._errors) == 0
    
    @property
    def errors(self):
        """Retorna lista de erros de validação"""
        return self._errors
    
    def get_all(self) -> Dict[str, Any]:
        """Retorna todos os 3 schemas validados como dicionário."""
        return {
            "administrativo": self.administrativo().model_dump(),
            "operacional": self.operacional().model_dump(),
            "logistico": self.logistico().model_dump(),
        }


__all__ = ["DinaboxRouter"]
