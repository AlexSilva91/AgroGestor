# AgroGestor - Documentacao de Integracao

## Objetivo

Este documento orienta a integracao completa do AgroGestor como uma plataforma multi-tenant para pequenos produtores, com suporte a multiplas culturas, permissionamento por fazenda, manejo minucioso, sanidade, nutricao, producao e controle financeiro por lote/plantel.

Use este documento como guia de implementacao incremental. Cada etapa contem objetivo, regras, criterios de aceite e um prompt recomendado para continuar o desenvolvimento com Codex.

## Estado Atual

O projeto e um monolito Django com os apps principais:

- `core`: usuario, fazenda, acessos por fazenda, modulos liberaveis e autenticacao.
- `rebanho`: estrutura legada para rebanhos, animais e historico.
- `pastagem`: estrutura legada para pastagens e movimentacoes.
- `financeiro`: lancamentos financeiros.
- `gestao`: novo nucleo multi-cultura.
- `iot`: reservado para sensores e automacoes.

O ambiente de desenvolvimento deve usar SQLite. PostgreSQL fica reservado para ambientes fora de desenvolvimento via `DJANGO_ENV`.

## Principios Arquiteturais

1. Todo dado operacional pertence a uma fazenda.
2. Super admin ve tudo, mas toda escrita deve exigir confirmacao explicita.
3. Admin/dono da fazenda ve e faz tudo apenas dentro das fazendas dele.
4. Operador ve e altera apenas o que o admin da fazenda liberar.
5. Modulos devem ser liberados por fazenda pelo super admin.
6. A UI deve esconder o que nao esta liberado, mas a seguranca real deve ficar no backend.
7. Nenhuma view operacional deve usar query global sem filtro por fazenda.
8. Relacionamentos entre registros de fazendas diferentes devem ser bloqueados.
9. Toda nova tela deve ter criterio claro de permissao, fazenda ativa e modulo ativo.
10. Financeiro deve ser conectado a plantel/lote, cultura, producao, manejo, racao e sanidade.

## Multi-Tenant

### Modelos existentes

- `Fazenda`: unidade produtiva/tenant operacional.
- `Usuario`: usuario do sistema.
- `FazendaAcesso`: vincula usuario a fazenda e permissoes.
- `ModuloSistema`: cadastro global dos modulos.
- `FazendaModulo`: libera ou bloqueia modulo por fazenda.

### Regra de acesso

Super admin:

- Pode ver todos os dados.
- Pode alterar dados apenas apos confirmacao.
- Deve ver aviso antes de qualquer acao de escrita.

Admin da fazenda:

- Pode ver e alterar tudo dentro das fazendas associadas.
- Nao pode ver dados de outra fazenda.
- Pode definir operadores e suas permissoes.

Operador:

- Pode ver e alterar conforme flags em `FazendaAcesso`.
- Nao pode ativar modulos.
- Nao pode acessar fazenda fora do seu vinculo.

### Checklist tecnico obrigatorio para novas views

- Usar `module_queryset(...)` para listagens.
- Usar `tenant_get_or_404(...)` para detalhe/edicao/exclusao.
- Usar `ensure_farm_permission(...)` antes de criar/editar/excluir.
- Usar `ensure_super_admin_confirmation(...)` em escrita.
- Validar que FKs com `farm` pertencem a mesma fazenda do registro principal.
- Retornar `403` para permissao negada.

## Modulos do Sistema

Modulos atuais:

- `avicultura`
- `suinocultura`
- `ovinocultura`
- `bovinocultura`
- `gestao`
- `manejo`
- `nutricao`
- `sanidade`
- `producao`
- `financeiro`
- `iot`

Cada modulo deve ter:

- Liberacao por fazenda em `FazendaModulo`.
- Permissoes por operador em `FazendaAcesso`.
- Menu visivel apenas quando liberado.
- Backend bloqueando acesso quando nao liberado.

## Dominio Multi-Cultura

O app `gestao` deve ser o nucleo futuro da aplicacao.

### Cadastros globais

- `Cultura`
- `Especie`
- `FinalidadeProdutiva`
- `RegraCapacidade`
- `ProtocoloManejo`
- `EtapaManejo`
- `TarefaManejo`

Cadastros globais devem ser alterados apenas pelo super admin.

### Cadastros por fazenda

- `Instalacao`
- `Plantel`
- `AnimalIndividual`
- `MovimentacaoPlantel`
- `AgendaManejo`
- `ExecucaoManejo`
- `Ingrediente`
- `FormulaRacao`
- `FormulaRacaoItem`
- `OrdemFabricacaoRacao`
- `MovimentoEstoque`
- `ConsumoRacao`
- `OcorrenciaSanitaria`
- `IsolamentoSanitario`
- `TratamentoSanitario`
- `CalendarioTratamento`
- `AltaSanitaria`
- `PesagemPlantel`
- `ProducaoOvos`
- `ProducaoCorte`

## Fluxos Funcionais

### 1. Fazenda ativa

Objetivo: usuario com mais de uma fazenda deve escolher a fazenda ativa.

Regras:

- A fazenda ativa deve aparecer no topo do sistema.
- Todas as criacoes devem enviar `farm_id`.
- Se o usuario tiver uma unica fazenda, ela pode ser selecionada automaticamente.
- Super admin deve poder escolher qualquer fazenda.

Criterios de aceite:

- Admin com duas fazendas alterna entre elas.
- Listagens mudam conforme fazenda ativa.
- Criacao grava na fazenda ativa.
- Operador nao consegue selecionar fazenda sem acesso.

Prompt:

```text
Implemente a selecao de fazenda ativa no AgroGestor. Use o multi-tenant ja existente em core.permissions. Adicione endpoint para listar fazendas permitidas do usuario, endpoint para definir fazenda ativa na sessao, componente no navbar mostrando a fazenda atual e seletor quando houver mais de uma. Garanta que todas as criacoes dos modulos existentes enviem farm_id da fazenda ativa. Nao quebre as permissoes atuais. Valide com Django Client: admin alterna fazenda, operador nao acessa fazenda indevida, super admin escolhe qualquer uma.
```

### 2. Liberacao de modulos por super admin

Objetivo: super admin libera os modulos contratados/permitidos para cada fazenda.

Regras:

- Apenas super admin altera `FazendaModulo`.
- A tela deve exigir confirmacao antes de salvar.
- Menus de modulos bloqueados nao aparecem para usuarios normais.
- Backend deve continuar bloqueando mesmo se o usuario chamar URL manualmente.

Criterios de aceite:

- Modulo bloqueado desaparece da UI.
- Endpoint retorna `403` quando modulo esta bloqueado.
- Super admin consegue bloquear/liberar modulo.
- Admin da fazenda nao consegue liberar modulo.

Prompt:

```text
Crie a tela de liberacao de modulos por fazenda para super admin. Use ModuloSistema e FazendaModulo. A tela deve listar fazendas, listar modulos por fazenda, permitir alternar liberado/bloqueado e exigir confirmacao de super admin antes de salvar. Atualize o navbar/dashboard para esconder abas de modulos bloqueados. O backend deve continuar usando core.permissions para bloquear acesso. Inclua testes de modulo liberado e bloqueado.
```

### 3. Permissoes do operador

Objetivo: admin da fazenda define o que cada operador pode ver/criar/editar/excluir.

Regras:

- Admin da fazenda pode alterar permissoes apenas de usuarios das suas fazendas.
- Operador nao pode editar permissoes.
- Super admin pode alterar tudo com confirmacao.
- Permissoes devem ser por modulo e acao.

Criterios de aceite:

- Admin libera operador para ver manejo, mas nao editar.
- Operador ve menu, mas botoes de escrita ficam ocultos/desabilitados.
- Se chamar endpoint de escrita manualmente, recebe `403`.

Prompt:

```text
Implemente a tela de permissoes de operadores por fazenda. Use FazendaAcesso. Permita que o admin da fazenda edite permissoes can_view, can_create, can_update e can_delete para gestao, manejo, nutricao, sanidade, producao, financeiro, rebanho e pastagem. A tela deve respeitar fazenda ativa. O backend deve validar que o admin so altera operadores das suas fazendas. Inclua testes para operador bloqueado e operador liberado.
```

### 4. Plantel e instalacoes

Objetivo: registrar plantel/lote por galpao, baia, piquete, enfermaria ou outra instalacao.

Regras:

- Instalacao pertence a fazenda.
- Plantel pertence a fazenda.
- Plantel nao pode ser associado a instalacao de outra fazenda.
- Plantel deve guardar cultura, finalidade, quantidade inicial e quantidade atual.
- Movimentacoes alteram quantidade atual quando aplicavel.

Criterios de aceite:

- Admin cria galpao.
- Admin cria plantel de aves de postura no galpao.
- Sistema bloqueia plantel com instalacao de outra fazenda.
- Movimentacao de mortalidade reduz quantidade atual.
- Movimentacao de transferencia muda instalacao.

Prompt:

```text
Crie telas completas para Instalacao, Plantel e MovimentacaoPlantel usando as APIs do app gestao. A tela deve permitir cadastrar galpoes, baias, piquetes, enfermarias e quarentenas; cadastrar plantel por cultura e finalidade; movimentar plantel entre instalacoes; registrar mortalidade, descarte, venda, abate, isolamento e retorno. Atualize quantidade_atual conforme movimentacao. Bloqueie relacoes entre fazendas diferentes. Inclua alertas de permissao e modulo bloqueado.
```

### 5. Capacidade recomendada

Objetivo: informar quantos animais cabem por instalacao conforme cultura/fase.

Regras:

- `RegraCapacidade` define densidade e recomendacoes.
- Capacidade pode ser calculada por area.
- Sistema deve alertar superlotacao.
- Regras globais sao mantidas pelo super admin.

Criterios de aceite:

- Super admin cadastra regra para avicultura de postura.
- Admin cria galpao com area.
- Ao cadastrar plantel, sistema mostra capacidade recomendada.
- Se quantidade exceder, sistema exibe alerta.

Prompt:

```text
Implemente calculo de capacidade recomendada. Use RegraCapacidade, Instalacao.area_m2, cultura e finalidade do plantel. Ao criar/editar plantel, exiba capacidade recomendada, ocupacao atual e alerta de superlotacao. Crie endpoint para calcular capacidade antes de salvar. Apenas super admin pode criar/editar regras globais. Inclua testes para capacidade normal, limite e excedida.
```

### 6. Calendario de manejo

Objetivo: programar manejo por semana/fase automaticamente.

Regras:

- Protocolo tem etapas.
- Etapa tem semana inicial e final.
- Tarefa define acao, semana e dia.
- Ao aplicar protocolo a plantel, gerar `AgendaManejo`.
- Execucao registra quem fez, quando e resultado.

Criterios de aceite:

- Criar protocolo para aves de postura.
- Definir etapa inicial, recria, pre-postura e postura.
- Definir tarefas de racao, vacina, pesagem e inspecao.
- Aplicar protocolo ao plantel.
- Agenda aparece em calendario.
- Tarefa atrasada fica marcada.

Prompt:

```text
Implemente o motor de calendario de manejo. Crie tela para ProtocoloManejo, EtapaManejo e TarefaManejo. Crie acao "Aplicar protocolo ao plantel", gerando AgendaManejo com datas calculadas a partir de Plantel.data_alojamento, semana e dia_da_semana. Crie tela de calendario com filtros por fazenda, plantel, status e tipo de tarefa. Permita concluir tarefa criando ExecucaoManejo. Marque tarefas atrasadas. Inclua testes de geracao de agenda.
```

### 7. Nutricao, formula e fabricacao propria de racao

Objetivo: controlar ingredientes, formula, fabricacao e consumo.

Regras:

- Ingrediente pertence a fazenda.
- Formula pertence a fazenda e cultura.
- Itens da formula devem somar 100%.
- Ordem de fabricacao baixa ingredientes e gera custo total.
- Consumo de racao pode ser vinculado a plantel.
- Consumo deve alimentar custo do lote.

Criterios de aceite:

- Admin cadastra ingredientes.
- Admin cria formula com percentuais.
- Sistema impede formula diferente de 100%.
- Fabricacao gera movimentos de estoque.
- Consumo por plantel reduz estoque.
- Financeiro registra custo por plantel.

Prompt:

```text
Implemente nutricao e fabricacao propria de racao. Crie telas para Ingrediente, FormulaRacao, FormulaRacaoItem, OrdemFabricacaoRacao, MovimentoEstoque e ConsumoRacao. Valide que a soma dos itens da formula e 100%. Ao produzir racao, baixe estoque dos ingredientes proporcionalmente, calcule custo total e registre movimento de fabricacao. Ao consumir racao no plantel, registre consumo, baixe estoque e crie lancamento financeiro de custo vinculado ao plantel. Inclua testes de formula invalida, fabricacao e consumo.
```

### 8. Sanidade e enfermaria

Objetivo: registrar doencas, sintomas, isolamento, tratamento e alta.

Regras:

- Ocorrencia sanitaria pode ser de plantel ou animal individual.
- Isolamento move para instalacao do tipo `ENFERMARIA` ou `QUARENTENA`.
- Tratamento gera calendario de aplicacoes.
- Alta define retorno, obito, descarte ou venda.
- Carencia deve ser registrada.

Criterios de aceite:

- Admin registra ocorrencia.
- Admin move plantel/animal para enfermaria.
- Sistema cria movimentacao de isolamento.
- Tratamento gera calendario.
- Aplicacao de medicamento muda status.
- Alta encerra ocorrencia e retorna ou baixa quantidade.

Prompt:

```text
Implemente o fluxo completo de sanidade e enfermaria. Crie telas para OcorrenciaSanitaria, IsolamentoSanitario, TratamentoSanitario, CalendarioTratamento e AltaSanitaria. Ao isolar, mova plantel/animal para instalacao de enfermaria/quarentena e registre MovimentacaoPlantel. Ao criar tratamento, gere calendario de aplicacoes conforme frequencia e dias_tratamento. Permita registrar aplicacao, atraso e alta. Se destino for obito/descarte, atualize quantidade do plantel. Inclua testes do fluxo completo.
```

### 9. Producao de aves de postura e corte

Objetivo: controlar producao produtiva por plantel.

Regras:

- Postura usa `ProducaoOvos`.
- Corte usa `ProducaoCorte`.
- Pesagem usa `PesagemPlantel`.
- Indicadores devem considerar quantidade atual, consumo e idade.

Criterios de aceite:

- Registrar ovos por dia.
- Classificar ovos comerciais, descartados e trincados.
- Registrar peso medio de lote de corte.
- Calcular mortalidade, ganho de peso e conversao alimentar.
- Gerar graficos por plantel e instalacao.

Prompt:

```text
Implemente as telas de producao. Para aves de postura, crie lancamento diario de ProducaoOvos com total, comerciais, descartados e trincados. Para corte, crie ProducaoCorte com peso medio, ganho diario, conversao alimentar e mortalidade. Integre PesagemPlantel. Crie indicadores por plantel: producao por ave, mortalidade acumulada, consumo por animal, conversao alimentar e evolucao de peso. Inclua testes de calculos basicos.
```

### 10. Financeiro e lucro por plantel

Objetivo: mostrar lucro real por cultura, plantel, galpao e periodo.

Regras:

- Lancamento financeiro pode se vincular a plantel.
- Custos de racao, sanidade, mao de obra e insumos devem entrar no resultado.
- Receita de ovos, venda, abate ou descarte deve entrar no resultado.
- Relatorio deve filtrar por fazenda, cultura, plantel e periodo.

Criterios de aceite:

- Relatorio mostra receita, custo, lucro e margem.
- Custo de racao fabricada entra no plantel.
- Receita de ovos entra no plantel.
- Admin ve apenas fazendas dele.
- Super admin ve todas com aviso antes de alterar dados.

Prompt:

```text
Implemente relatorios financeiros por plantel. Use LancamentoFinanceiro.plantel, ConsumoRacao, OrdemFabricacaoRacao, ProducaoOvos e ProducaoCorte. Crie endpoint e tela com filtros por fazenda ativa, cultura, plantel e periodo. Exiba receita, custo total, custo de racao, custo sanitario, lucro, margem, custo por kg, custo por duzia e custo por animal. Garanta isolamento multi-tenant. Inclua testes de agregacao.
```

### 11. Dashboard operacional

Objetivo: substituir o dashboard antigo por uma visao operacional por fazenda e cultura.

Deve exibir:

- fazenda ativa
- modulos liberados
- plantéis ativos
- alertas de manejo atrasado
- alertas sanitarios
- estoque baixo
- superlotacao
- producao do dia
- resultado financeiro do periodo

Prompt:

```text
Reestruture o dashboard do AgroGestor para usar o novo app gestao. Mostre cards de plantéis ativos, tarefas de manejo pendentes/atrasadas, ocorrencias sanitarias abertas, estoque baixo, producao diaria e resultado financeiro. Respeite fazenda ativa, modulos liberados e permissoes do usuario. Remova dependencia visual dos modulos antigos quando houver equivalentes no app gestao.
```

## APIs atuais do app gestao

Padrao:

- `GET /gestao/<recurso>/`
- `POST /gestao/<recurso>/criar/`
- `GET /gestao/<recurso>/<uuid>/`
- `PUT /gestao/<recurso>/<uuid>/editar/`
- `DELETE /gestao/<recurso>/<uuid>/excluir/`

Recursos disponiveis:

- `culturas`
- `instalacoes`
- `regras-capacidade`
- `planteis`
- `animais`
- `movimentacoes`
- `protocolos`
- `agendas`
- `ingredientes`
- `formulas-racao`
- `ordens-racao`
- `consumos-racao`
- `ocorrencias-sanitarias`
- `isolamentos`
- `pesagens`
- `producao-ovos`
- `producao-corte`

## Seeds iniciais

Execute:

```sh
python manage.py seed_agrogestor
```

Esse comando cria/atualiza:

- modulos do sistema
- culturas iniciais
- especies iniciais
- finalidades produtivas iniciais
- liberacao inicial de modulos para fazendas existentes

## Testes Obrigatorios

Todo novo modulo/tela deve incluir testes para:

- admin ve somente fazendas dele
- operador sem permissao recebe `403`
- operador com permissao executa acao permitida
- super admin sem confirmacao recebe `403`
- super admin com confirmacao executa
- modulo bloqueado para fazenda recebe `403`
- relacionamento entre fazendas diferentes e rejeitado
- criacao grava `farm_id` correto

## Criterio de Conclusao do Produto

O AgroGestor pode ser considerado funcionalmente completo quando:

1. Super admin consegue cadastrar fazendas, liberar modulos e gerenciar tudo.
2. Admin da fazenda consegue gerenciar usuarios, permissoes, plantéis, instalacoes e operacao.
3. Operador so consegue executar o que foi liberado.
4. Plantel pode ser controlado por cultura, instalacao e fase.
5. Manejo programado gera calendario automaticamente.
6. Racao propria controla formula, estoque, fabricacao, consumo e custo.
7. Sanidade permite ocorrencia, isolamento, tratamento, calendario e alta.
8. Producao de postura/corte/pesagem alimenta indicadores.
9. Financeiro mostra lucro por plantel, cultura, instalacao e periodo.
10. Todas as telas respeitam fazenda ativa, modulo liberado e permissao.

## Prompt Mestre

Use este prompt quando for iniciar uma etapa grande:

```text
Continue a implementacao do AgroGestor seguindo docs/integracao-agrogestor.md. Antes de alterar arquivos, leia a documentacao e os arquivos envolvidos. Preserve o isolamento multi-tenant existente. Toda nova view/API deve respeitar fazenda ativa, modulo liberado, FazendaAcesso e confirmacao de super admin. Implemente a proxima etapa completa, com models se necessario, migrations, views/APIs, templates/JS, seed se aplicavel e testes/validacoes. Rode python manage.py check, makemigrations --check --dry-run, migrate quando houver migrations, e teste funcional com Django Client. Nao pare em plano: implemente e valide.
```

