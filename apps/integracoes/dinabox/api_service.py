from __future__ import annotations

from apps.integracoes.dinabox.client import DinaboxAPIClient
from apps.integracoes.dinabox.schemas.api import (
    DinaboxGroupDetail,
    DinaboxGroupListResponse,
    DinaboxProjectDetail,
    DinaboxProjectListResponse,
)


DINABOX_CAPABILITIES = [
    {
        "nome": "Usuario autenticado",
        "endpoint": "/api/v1/user",
        "descricao": "Dados da conta conectada na API.",
        "sample_params": {},
    },
    {
        "nome": "Projetos (lista)",
        "endpoint": "/api/v1/projects",
        "descricao": "Lista de projetos com filtros.",
        "sample_params": {"p": 1},
    },
    {
        "nome": "Projeto (detalhe)",
        "endpoint": "/api/v1/project",
        "descricao": "Detalhe por project_id.",
        "sample_params": {},
    },
    {
        "nome": "Lotes (lista)",
        "endpoint": "/api/v1/project-groups",
        "descricao": "Lista de lotes de projetos.",
        "sample_params": {"p": 1},
    },
    {
        "nome": "Lote (detalhe/acoes)",
        "endpoint": "/api/v1/project-group",
        "descricao": "Detalhe de lote e acoes POST/DELETE.",
        "sample_params": {},
    },
    {
        "nome": "Clientes (lista)",
        "endpoint": "/api/v1/customers",
        "descricao": "Lista paginada de clientes.",
        "sample_params": {"p": 1},
    },
    {
        "nome": "Cliente (detalhe/edicao)",
        "endpoint": "/api/v1/customer",
        "descricao": "GET/PUT/PATCH/DELETE por customer_id.",
        "sample_params": {},
    },
    {
        "nome": "Projetistas (lista)",
        "endpoint": "/api/v1/designers",
        "descricao": "Lista paginada de projetistas.",
        "sample_params": {"p": 1},
    },
    {
        "nome": "Projetista (detalhe/edicao)",
        "endpoint": "/api/v1/designer",
        "descricao": "GET/PUT/PATCH por designer_id.",
        "sample_params": {},
    },
    {
        "nome": "Fornecedores (lista)",
        "endpoint": "/api/v1/providers",
        "descricao": "Lista de fornecedores (pode retornar 404 quando vazio).",
        "sample_params": {"p": 1},
    },
    {
        "nome": "Fornecedor (detalhe/edicao)",
        "endpoint": "/api/v1/provider",
        "descricao": "GET/PUT/PATCH/DELETE por provider_id.",
        "sample_params": {},
    },
    {
        "nome": "Funcionarios (lista)",
        "endpoint": "/api/v1/employees",
        "descricao": "Lista de funcionarios (pode retornar 404 quando vazio).",
        "sample_params": {"p": 1},
    },
    {
        "nome": "Funcionario (detalhe/edicao)",
        "endpoint": "/api/v1/employee",
        "descricao": "GET/PUT/PATCH/DELETE por employee_id.",
        "sample_params": {},
    },
    {
        "nome": "Materiais",
        "endpoint": "/api/v1/materials",
        "descricao": "Catalogo de materiais (type=dinabox|user).",
        "sample_params": {"p": 1, "type": "dinabox"},
    },
    {
        "nome": "Componentes",
        "endpoint": "/api/v1/components",
        "descricao": "Catalogo de componentes (type=dinabox|user).",
        "sample_params": {"p": 1, "type": "user"},
    },
    {
        "nome": "Portas",
        "endpoint": "/api/v1/doors",
        "descricao": "Catalogo de portas (type=dinabox|user).",
        "sample_params": {"p": 1, "type": "dinabox"},
    },
    {
        "nome": "Etiquetas (lista)",
        "endpoint": "/api/v1/labels",
        "descricao": "Lista de etiquetas cadastradas.",
        "sample_params": {"p": 1},
    },
    {
        "nome": "Etiqueta (detalhe/acoes)",
        "endpoint": "/api/v1/label",
        "descricao": "GET/POST/DELETE por label_id.",
        "sample_params": {},
    },
]


class DinaboxApiService:
    """
    Camada de servico da API Dinabox para Projetos/Lotes e diagnostico de capacidades.
    """

    def __init__(self, token: str | None = None):
        self.client = DinaboxAPIClient(token=token)

    def list_projects(
        self,
        page: int = 1,
        search: str | None = None,
        status: str | None = None,
    ) -> DinaboxProjectListResponse:
        payload = self.client.get_projects(page=page, search=search, status=status)
        return DinaboxProjectListResponse(**payload)

    def get_project_detail(self, project_id: str) -> DinaboxProjectDetail:
        payload = self.client.get_project(project_id=project_id)
        return DinaboxProjectDetail(**payload)

    def list_groups(self, page: int = 1, search: str | None = None) -> DinaboxGroupListResponse:
        payload = self.client.get_project_groups(page=page, search=search)
        return DinaboxGroupListResponse(**payload)

    def get_group_detail(self, group_id: str) -> DinaboxGroupDetail:
        payload = self.client.get_project_group(group_id=group_id)
        return DinaboxGroupDetail(**payload)

    def get_service_account_profile(self) -> tuple[dict, dict]:
        token_result = self.client.obter_token()
        profile = self.client.get_user_info()
        return profile, {
            "user_login": token_result.user_login,
            "user_display_name": token_result.user_display_name,
            "user_email": token_result.user_email,
            "expires_in": token_result.expires_in,
            "token_type": token_result.token_type,
            "token_preview": (token_result.token[:6] + "..." + token_result.token[-4:]) if len(token_result.token) >= 12 else "***",
        }

    def discover_capabilities(self) -> list[dict]:
        rows: list[dict] = []

        for item in DINABOX_CAPABILITIES:
            endpoint = item["endpoint"]
            options_meta = self.client.request_meta("OPTIONS", endpoint)
            get_meta = self.client.request_meta("GET", endpoint, params=item.get("sample_params") or {})

            methods = []
            args = []
            options_json = options_meta.get("json")
            if isinstance(options_json, dict):
                methods = options_json.get("methods") or []
                endpoints = options_json.get("endpoints") or []
                if endpoints and isinstance(endpoints, list):
                    first = endpoints[0]
                    if isinstance(first, dict):
                        args = list((first.get("args") or {}).keys())

            get_message = ""
            get_json = get_meta.get("json")
            if isinstance(get_json, dict):
                get_message = str(get_json.get("message") or get_json.get("code") or "")
            if not get_message:
                get_message = (get_meta.get("text") or "")[:120]

            rows.append(
                {
                    "nome": item["nome"],
                    "descricao": item["descricao"],
                    "endpoint": endpoint,
                    "methods": methods,
                    "args": args,
                    "options_status": options_meta.get("status"),
                    "get_status": get_meta.get("status"),
                    "get_message": get_message,
                }
            )

        return rows
