from datetime import datetime

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import redirect, render

from apps.estoque.models import Produto, Movimentacao, Reserva
from apps.estoque.selectors.estoque_selectors import (
    get_movimentacoes_recentes,
    get_produtos_baixo_estoque,
    listar_movimentacoes,
)
from apps.estoque.services.movimentacao_services import processar_movimentacao
from apps.estoque.services.reserva_service import (
    cancelar_reserva,
    consumir_reserva,
    criar_reserva,
    get_quantidade_reservada,
    get_saldo_disponivel,
)

TIPOS_MOV = [
    ('entrada', 'Entrada'),
    ('saida', 'Saída'),
    ('ajuste', 'Ajuste'),
    ('transferencia', 'Transferência'),
]


def _produtos_com_saldo(qs=None):
    """Retorna lista de dicts com produto, reservado e disponivel."""
    if qs is None:
        qs = Produto.objects.all().order_by('nome')
    return [
        {
            'produto': p,
            'reservado': get_quantidade_reservada(p.id),
            'disponivel': get_saldo_disponivel(p),
        }
        for p in qs
    ]


# ──────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────
def dashboard(request):
    total_reservado = Reserva.objects.filter(status='ativa').aggregate(
        total=Sum('quantidade')
    )['total'] or 0

    ctx = {
        'total_produtos': Produto.objects.count(),
        'total_em_estoque': Produto.objects.aggregate(t=Sum('quantidade'))['t'] or 0,
        'baixo_estoque': get_produtos_baixo_estoque()[:10],
        'movimentacoes_recentes': get_movimentacoes_recentes(limite=8),
        'reservas_ativas': Reserva.objects.filter(status='ativa').select_related('produto')[:10],
        'total_reservado': total_reservado,
    }
    return render(request, 'estoque/dashboard.html', ctx)


# ──────────────────────────────────────────
# Produtos
# ──────────────────────────────────────────
def lista_produtos(request):
    qs = Produto.objects.all().order_by('nome')

    q = request.GET.get('q')
    if q:
        qs = qs.filter(nome__icontains=q) | qs.filter(sku__icontains=q)

    if request.GET.get('alerta') == '1':
        from django.db.models import F
        qs = qs.filter(quantidade__lte=F('estoque_minimo'))

    ctx = {'produtos': _produtos_com_saldo(qs)}
    return render(request, 'estoque/produtos.html', ctx)


def novo_produto(request):
    from apps.estoque.services.produto_service import criar_produto
    erro = None
    if request.method == 'POST':
        try:
            criar_produto({
                'nome': request.POST['nome'],
                'sku': request.POST['sku'],
                'quantidade': int(request.POST.get('quantidade', 0)),
                'estoque_minimo': int(request.POST.get('estoque_minimo', 0)),
            })
            messages.success(request, 'Produto criado com sucesso.')
            return redirect('estoque-produtos')
        except Exception as e:
            erro = str(e)

    return render(request, 'estoque/produto_form.html', {'erro': erro})


# ──────────────────────────────────────────
# Movimentação
# ──────────────────────────────────────────
def movimentar(request):
    erro = None
    if request.method == 'POST':
        try:
            processar_movimentacao(
                data={
                    'produto_id': int(request.POST['produto_id']),
                    'quantidade': int(request.POST['quantidade']),
                    'tipo': request.POST['tipo'],
                    'observacao': request.POST.get('observacao') or None,
                },
                usuario_id=request.user.id if request.user.is_authenticated else None,
            )
            messages.success(request, 'Movimentação registrada com sucesso.')
            return redirect('estoque-dashboard')
        except (ValueError, Exception) as e:
            erro = str(e)

    ctx = {
        'produtos': Produto.objects.all().order_by('nome'),
        'tipos': TIPOS_MOV,
        'produto_id_pre': request.GET.get('produto_id', ''),
        'erro': erro,
    }
    return render(request, 'estoque/movimentar.html', ctx)


# ──────────────────────────────────────────
# Histórico
# ──────────────────────────────────────────
def historico(request):
    params = request.GET
    LIMIT = 50

    try:
        produto_id = int(params['produto_id']) if params.get('produto_id') else None
        offset = int(params.get('offset', 0))
    except (ValueError, TypeError):
        produto_id, offset = None, 0

    tipo = params.get('tipo') or None

    data_inicio = data_fim = None
    if params.get('data_inicio'):
        try:
            data_inicio = datetime.fromisoformat(params['data_inicio'])
        except ValueError:
            pass
    if params.get('data_fim'):
        try:
            data_fim = datetime.fromisoformat(params['data_fim'])
        except ValueError:
            pass

    qs = listar_movimentacoes(
        produto_id=produto_id,
        tipo=tipo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    total = qs.count()
    movimentacoes = qs[offset:offset + LIMIT]

    ctx = {
        'movimentacoes': movimentacoes,
        'produtos': Produto.objects.all().order_by('nome'),
        'tipos': TIPOS_MOV,
        'total': total,
        'offset': offset,
        'tem_proxima': (offset + LIMIT) < total,
    }
    return render(request, 'estoque/historico.html', ctx)


# ──────────────────────────────────────────
# Reservas
# ──────────────────────────────────────────
def reservas(request):
    erro = None

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'criar':
            try:
                criar_reserva(
                    produto_id=int(request.POST['produto_id']),
                    projeto=request.POST['projeto'],
                    quantidade=int(request.POST['quantidade']),
                    usuario_id=request.user.id if request.user.is_authenticated else None,
                    observacao=request.POST.get('observacao') or None,
                )
                messages.success(request, 'Reserva criada com sucesso.')
                return redirect('estoque-reservas')
            except (ValueError, Exception) as e:
                erro = str(e)

        elif acao == 'cancelar':
            try:
                cancelar_reserva(int(request.POST['reserva_id']))
                messages.success(request, 'Reserva cancelada.')
                return redirect('estoque-reservas')
            except Exception as e:
                messages.error(request, str(e))
                return redirect('estoque-reservas')

        elif acao == 'consumir':
            try:
                consumir_reserva(int(request.POST['reserva_id']))
                messages.success(request, 'Reserva consumida — saída registrada no estoque.')
                return redirect('estoque-reservas')
            except Exception as e:
                messages.error(request, str(e))
                return redirect('estoque-reservas')

    # Filtros de listagem
    qs = Reserva.objects.select_related('produto', 'usuario').order_by('-criado_em')
    if request.GET.get('status'):
        qs = qs.filter(status=request.GET['status'])
    if request.GET.get('projeto'):
        qs = qs.filter(projeto__icontains=request.GET['projeto'])
    if request.GET.get('produto_id'):
        qs = qs.filter(produto_id=request.GET['produto_id'])

    ctx = {
        'reservas': qs,
        'produtos': _produtos_com_saldo(),
        'produto_id_pre': request.GET.get('produto_id', ''),
        'erro': erro,
    }
    return render(request, 'estoque/reservas.html', ctx)
