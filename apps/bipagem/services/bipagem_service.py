# apps/bipagem/services/bipagem_service.py
from typing import Dict
from apps.bipagem.models import Peca


def registrar_bipagem(codigo_peca: str, usuario: str = 'SISTEMA', localizacao: str = '') -> Dict:
    """
    Serviço central de bipagem - contém toda regra de negócio
    """
    try:
        peca = Peca.objects.get(id_peca=codigo_peca)
        
        # Regra de negócio: só bipa se não estiver bipada
        if peca.status == 'BIPADA':
            return {
                'sucesso': True,
                'mensagem': 'Peça já foi bipada!',
                'peca': peca
            }
        
        peca.bipa(usuario=usuario, localizacao=localizacao)
        
        return {
            'sucesso': True,
            'peca': peca
        }
        
    except Peca.DoesNotExist:
        return {
            'sucesso': False,
            'erro': f'Peça com código {codigo_peca} não encontrada'
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': f'Erro ao registrar bipagem: {str(e)}'
        }