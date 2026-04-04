# Mapeamento de Inconsistências — Tarugo (Estoque e Reservas)

## 1. Estoque (MDF e Chapas)
- **Inconsistência de Tipos**: `movimentacao_create` converte quantidade para `int`, enquanto `reserva_create` usa `Decimal`. Para chapas de MDF, o ideal é `int` (unidades de chapa), mas ferragens podem usar `Decimal`.
- **Saldo Agregado vs. Saldo por Espessura**: O modelo `Produto` mantém um campo `quantidade` que é a soma de todas as espessuras, mas as validações de saída em `movimentacao_form.html` usam esse total em vez do saldo específico da espessura selecionada.
- **Cálculo de Status**: `lista_produtos.html` e `ProdutoSelector` calculam "Baixo Estoque" baseados no `Produto.quantidade` total, ignorando se uma espessura específica de MDF está zerada.
- **Atributos de Cadastro**: O formulário de produto usa nomes de categoria ("MDF", "Compensado") para decidir quais campos mostrar, o que é frágil. Deveria usar a `FamiliaProduto`.

## 2. Reservas (MVP)
- **Validação contra Estoque**: O `ReservaService.criar_reserva` permite reservas preventivas (mesmo sem estoque), mas o usuário solicitou "validação contra o estoque" no MVP. Precisamos decidir se permitimos reserva negativa ou se bloqueamos.
- **Usuário da Reserva**: A view `reserva_create` não passa o `request.user` para o service, deixando o campo `usuario` na reserva como nulo.
- **Interface de Reserva**: O formulário atual já tem suporte a espessura, mas a lógica de "reserva por projeto" precisa ser mais robusta, garantindo que o débito real (saída) consuma a reserva.

## 3. Arquitetura (Tarugo Architecture)
- **API vs Views**: A API DRF (`api/serializers.py`) está defasada em relação às Views HTML. Não suporta `espessura` nas movimentações.
- **Regras de Negócio**: Algumas conversões de dados (como `int(espessura)`) estão nas Views, quando deveriam estar nos Schemas/Services.

## 4. Plano de Correção
1. **Backend**:
   - Ajustar `MovimentacaoService` e `ReservaService` para usar tipos consistentes.
   - Implementar validação rigorosa de estoque nas reservas (se solicitado).
   - Garantir que `SaldoMDF` seja a fonte da verdade para MDF.
2. **Frontend**:
   - Corrigir `movimentacao_form.html` para validar `max` baseado na espessura selecionada.
   - Melhorar `lista_produtos.html` para destacar espessuras críticas.
   - Refinar `reserva_form.html` para ser "conciso e realista".
