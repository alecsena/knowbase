# User Stories - ÉPICO 4: Workflow de Aprovação

**Versão:** 1.0 MVP  
**Data:** Janeiro 2026  
**Prioridade:** 1 (Crítico para MVP)  
**Status:** Planejamento

---

## 📋 Índice do Épico

- [4.1 Enviar para Aprovação](#41-enviar-para-aprovação)
- [4.2 Visualização de Documentos Pendentes](#42-visualização-de-documentos-pendentes)
- [4.3 Aprovar Documento](#43-aprovar-documento)
- [4.4 Solicitar Mudanças](#44-solicitar-mudanças)
- [4.5 Processar Mudanças e Reenviar](#45-processar-mudanças-e-reenviar)
- [4.6 Publicação de Documentos](#46-publicação-de-documentos)
- [4.7 Notificações de Workflow](#47-notificações-de-workflow)
- [4.8 Gestão de Aprovações](#48-gestão-de-aprovações)

---

## 📊 Diagrama de Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW DE APROVAÇÃO                     │
└─────────────────────────────────────────────────────────────┘

    NEW (Upload)
      ↓
   PROCESSING (Conversão)
      ↓
    DRAFT ←──────────────────┐
      ↓                      │
      │ (Editor: "Enviar     │ (Editor: "Cancelar
      │  para Revisão")      │  Envio")
      ↓                      │
  PENDING_APPROVAL           │
      ↓                      │
      ├─→ (Revisor: Aprovar) │
      │         ↓            │
      │      APPROVED        │
      │         ↓            │
      │    (Queue Pub)       │
      │         ↓            │
      │     PUBLISHED        │
      │                      │
      └─→ (Revisor: Solicitar Mudanças)
                ↓
         CHANGES_REQUESTED
                ↓
         (Editor revisa,
          marca como resolvido,
          reenvia)
                ↓
         PENDING_APPROVAL
                ↓
              (loop)

PUBLISHED
   ├─→ (Editar) → Cria nova versão em DRAFT
   ├─→ (Despublicar) → DRAFT
   ├─→ (Depreciar) → DEPRECATED
   └─→ (Arquivar) → ARCHIVED
```

---

## 4.1 Enviar para Aprovação

### US-4.1.1: Enviar Documento DRAFT para Aprovação (Editor)

**Como** Editor,  
**Quero** enviar documento em DRAFT para revisão,  
**Para** que um Revisor aprove e publique o conteúdo.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Enviar para Revisão" visível no editor de documentos DRAFT
- [ ] Ao clicar, sistema verifica se há comentários não resolvidos (se documento já foi rejeitado antes)
- [ ] Se há comentários pendentes, modal de aviso:
  - Mensagem: "Há X comentários não resolvidos. Deseja enviar mesmo assim?"
  - Lista de comentários pendentes (resumo)
  - Botões: "Cancelar", "Marcar Todos como Resolvidos", "Enviar Assim Mesmo"
- [ ] Se não há comentários ou Editor confirma, modal de confirmação final:
  - Mensagem: "Enviar documento [Título] para aprovação?"
  - Informação: "O documento ficará bloqueado para edição até ser aprovado ou rejeitado"
  - Campo opcional: "Mensagem para o revisor" (textarea)
  - Botões: "Cancelar" e "Enviar para Revisão"
- [ ] Ao confirmar:
  - Documento status → PENDING_APPROVAL
  - Lock de edição aplicado (Editor não pode mais editar)
  - Timestamp `submitted_for_approval_at` registrado
  - Registro de submissão criado em tabela de histórico
  - Notificações enviadas a todos os Revisores do grupo
- [ ] Mensagem de sucesso: "Documento enviado para revisão! Os revisores foram notificados."
- [ ] Redirecionado para visualização do documento (modo leitura)
- [ ] Badge "Pendente de Aprovação" visível no documento

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/submit-for-approval`
- [ ] Payload:
  ```json
  {
    "reviewer_message": "Por favor, revisar seção de benefícios atualizada"
  }
  ```
- [ ] Resposta: 200 OK com novo status
- [ ] Validações server-side:
  - Documento em status DRAFT
  - Usuário é Editor do grupo ou Admin
  - Documento não está vazio (content não NULL ou vazio)
  - Título não está vazio
  - Grupo tem pelo menos 1 Revisor
- [ ] Atualização no banco:
  ```sql
  UPDATE documents 
  SET 
    status = 'pending_approval',
    submitted_for_approval_at = NOW(),
    submitted_by = $1,
    reviewer_message = $2,
    updated_at = NOW()
  WHERE id = $3 AND status = 'draft';
  ```
- [ ] Criar registro de submissão:
  ```sql
  INSERT INTO approval_submissions (
    document_id,
    submitted_by,
    submitted_at,
    reviewer_message,
    version_snapshot
  ) VALUES ($1, $2, NOW(), $3, $4);
  ```
- [ ] Schema adicional:
  ```sql
  ALTER TABLE documents 
  ADD COLUMN submitted_for_approval_at TIMESTAMP,
  ADD COLUMN submitted_by INTEGER REFERENCES users(id),
  ADD COLUMN reviewer_message TEXT,
  ADD COLUMN reviewed_by INTEGER REFERENCES users(id),
  ADD COLUMN reviewed_at TIMESTAMP,
  ADD COLUMN review_decision VARCHAR(50),  -- 'approved', 'changes_requested'
  ADD COLUMN review_notes TEXT;
  
  CREATE TABLE approval_submissions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    submitted_by INTEGER NOT NULL REFERENCES users(id),
    submitted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewer_message TEXT,
    version_snapshot TEXT,  -- Snapshot do conteúdo no momento da submissão
    unresolved_comments_count INTEGER DEFAULT 0,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES users(id)
  );
  
  CREATE INDEX idx_approval_submissions_document ON approval_submissions(document_id);
  CREATE INDEX idx_approval_submissions_resolved ON approval_submissions(resolved, submitted_at);
  ```
- [ ] Enviar notificações:
  ```python
  # Buscar todos os Revisores do grupo
  reviewers = get_group_reviewers(document.group_id)
  
  for reviewer in reviewers:
    # Notificação in-app
    create_notification(
      user_id=reviewer.id,
      type='document_pending_approval',
      title=f'Documento pendente de aprovação: {document.title}',
      message=f'{submitted_by.name} enviou um documento para revisão',
      link=f'/documents/{document.id}',
      data={'document_id': document.id, 'submitted_by': submitted_by.name}
    )
    
    # Email (se habilitado)
    if reviewer.email_notifications_enabled:
      queue_email(
        to=reviewer.email,
        template='document_pending_approval',
        context={
          'reviewer_name': reviewer.name,
          'document_title': document.title,
          'submitted_by': submitted_by.name,
          'reviewer_message': reviewer_message,
          'document_url': f'{base_url}/documents/{document.id}'
        }
      )
  ```
- [ ] Log de ação: `user_id`, `document_id`, `action='submitted_for_approval'`, `timestamp`

**Verificação de Comentários Não Resolvidos:**
```python
def count_unresolved_comments(document_id: int) -> int:
  """Count comments that are not marked as resolved"""
  result = db.execute(
    """
    SELECT COUNT(*) 
    FROM document_comments 
    WHERE document_id = $1 AND resolved = FALSE
    """,
    document_id
  )
  return result[0][0]
```

**UX:**
- [ ] Botão destacado (cor primária) no editor
- [ ] Tooltip explicativo: "Enviar documento para que um revisor aprove"
- [ ] Modal de aviso de comentários com lista expandível
- [ ] Campo de mensagem com placeholder: "Adicione contexto para o revisor (opcional)"
- [ ] Loading indicator ao enviar
- [ ] Animação de transição para modo leitura
- [ ] Notificação toast de sucesso

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-2.4.1 (Editor DRAFT)

---

### US-4.1.2: Cancelar Envio para Aprovação (Editor)

**Como** Editor que enviou documento para aprovação,  
**Quero** cancelar o envio antes que seja revisado,  
**Para** fazer mais alterações sem esperar rejeição.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Cancelar Envio" visível em documento PENDING_APPROVAL
- [ ] Botão visível apenas para Editor que enviou (submitted_by) ou Admin de Grupo
- [ ] Botão visível apenas se documento ainda não foi revisado
- [ ] Modal de confirmação:
  - Mensagem: "Cancelar envio para aprovação?"
  - Aviso: "O documento voltará para rascunho e você poderá editá-lo novamente"
  - Botões: "Não, Manter em Revisão" e "Sim, Cancelar Envio"
- [ ] Ao confirmar:
  - Documento status → DRAFT
  - Lock de edição removido
  - Registro de cancelamento criado
  - Notificações enviadas aos Revisores que ainda não revisaram
- [ ] Mensagem de sucesso: "Envio cancelado. O documento voltou para rascunho."
- [ ] Redirecionado para editor

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/cancel-submission`
- [ ] Validações:
  - Documento em PENDING_APPROVAL
  - Usuário é quem enviou (submitted_by) ou Admin
  - Documento ainda não foi revisado (reviewed_at IS NULL)
- [ ] Atualização no banco:
  ```sql
  UPDATE documents 
  SET 
    status = 'draft',
    submitted_for_approval_at = NULL,
    submitted_by = NULL,
    reviewer_message = NULL,
    updated_at = NOW()
  WHERE id = $1 AND status = 'pending_approval' AND reviewed_at IS NULL;
  ```
- [ ] Marcar submissão como cancelada:
  ```sql
  UPDATE approval_submissions 
  SET 
    resolved = TRUE,
    resolved_at = NOW(),
    resolved_by = $1
  WHERE document_id = $2 AND resolved = FALSE;
  
  -- Ou adicionar campo specific para cancelamento
  ALTER TABLE approval_submissions 
  ADD COLUMN cancelled BOOLEAN DEFAULT FALSE,
  ADD COLUMN cancelled_at TIMESTAMP,
  ADD COLUMN cancelled_by INTEGER REFERENCES users(id);
  ```
- [ ] Notificar Revisores:
  ```python
  notify_reviewers(
    document_id=document.id,
    type='submission_cancelled',
    message=f'{user.name} cancelou o envio do documento "{document.title}"'
  )
  ```
- [ ] Log: `user_id`, `document_id`, `action='cancelled_submission'`, `timestamp`

**UX:**
- [ ] Botão secundário (não destaque)
- [ ] Confirmação clara
- [ ] Feedback visual imediato

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-4.1.1

---

## 4.2 Visualização de Documentos Pendentes

### US-4.2.1: Listar Documentos Pendentes de Aprovação (Revisor)

**Como** Revisor,  
**Quero** visualizar todos os documentos pendentes de revisão,  
**Para** priorizar e gerenciar minhas aprovações.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Pendentes de Revisão" no dashboard
- [ ] Badge com contador no menu: "Pendentes (5)"
- [ ] Lista de documentos PENDING_APPROVAL do grupo do Revisor
- [ ] Cada item exibe:
  - Título do documento
  - Autor (quem enviou)
  - Data de envio
  - Tempo decorrido (ex: "Há 2 dias")
  - Mensagem do revisor (se houver)
  - Grupo e Pasta
  - Botões: "Revisar", "Ver Documento"
- [ ] Ordenação:
  - Padrão: Mais antigos primeiro (FIFO)
  - Opções: Data de envio, Título, Autor
- [ ] Filtros:
  - Grupo (se Revisor de múltiplos grupos)
  - Autor
  - Data de envio (range)
- [ ] Indicador de urgência (opcional):
  - Vermelho: > 7 dias aguardando
  - Amarelo: > 3 dias
  - Verde: < 3 dias
- [ ] Estado vazio: "Nenhum documento pendente de revisão" (com ilustração)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/documents/pending-approval`
- [ ] Query params:
  ```
  ?group_id=1
  &author_id=5
  &sort_by=submitted_at
  &sort_order=asc
  &submitted_after=2024-01-01
  &submitted_before=2024-12-31
  ```
- [ ] Resposta:
  ```json
  {
    "documents": [
      {
        "id": 123,
        "title": "Política de Férias 2024",
        "status": "pending_approval",
        "author": {
          "id": 45,
          "name": "João Silva",
          "email": "joao@empresa.com"
        },
        "group": {
          "id": 1,
          "name": "RH"
        },
        "folder": {
          "id": 5,
          "name": "Políticas"
        },
        "submitted_at": "2024-01-15T10:30:00Z",
        "submitted_by": {
          "id": 45,
          "name": "João Silva"
        },
        "reviewer_message": "Por favor revisar seção de benefícios",
        "unresolved_comments_count": 0,
        "days_pending": 2
      }
    ],
    "total": 5
  }
  ```
- [ ] Query:
  ```sql
  SELECT 
    d.*,
    u.name as author_name,
    u.email as author_email,
    g.name as group_name,
    f.name as folder_name,
    EXTRACT(DAY FROM (NOW() - d.submitted_for_approval_at)) as days_pending,
    (SELECT COUNT(*) FROM document_comments 
     WHERE document_id = d.id AND resolved = FALSE) as unresolved_comments_count
  FROM documents d
  JOIN users u ON d.created_by = u.id
  JOIN groups g ON d.group_id = g.id
  LEFT JOIN folders f ON d.folder_id = f.id
  WHERE d.status = 'pending_approval'
    AND d.group_id IN (
      SELECT group_id FROM user_groups 
      WHERE user_id = $1 AND 'revisor' = ANY(roles)
    )
  ORDER BY d.submitted_for_approval_at ASC;
  ```
- [ ] Autorização: Apenas Revisores veem documentos de grupos onde têm papel de Revisor

**Dashboard Widget:**
- [ ] Widget "Pendentes de Revisão" no dashboard principal
- [ ] Mostra últimos 5 documentos pendentes
- [ ] Link "Ver Todos" para página completa

**UX:**
- [ ] Cards ou tabela responsiva
- [ ] Highlight de documentos urgentes (> 7 dias)
- [ ] Click no card abre documento
- [ ] Botão "Revisar Agora" destacado
- [ ] Mensagem do revisor em tooltip ou expandível
- [ ] Loading skeleton

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-4.1.1

---

### US-4.2.2: Visualizar Documento em Modo Revisão (Revisor)

**Como** Revisor,  
**Quero** visualizar documento em modo revisão,  
**Para** ler conteúdo e avaliar antes de aprovar ou rejeitar.

#### Critérios de Aceitação

**Funcional:**
- [ ] Ao abrir documento PENDING_APPROVAL, interface de revisão é exibida
- [ ] Interface de revisão contém:
  - **Header:**
    - Título do documento
    - Badge "Pendente de Aprovação" (laranja)
    - Autor e data de envio
    - Mensagem do revisor (se houver)
    - Breadcrumb
  - **Sidebar direita (Painel de Revisão):**
    - Informações do documento (metadados)
    - Histórico de submissões (se já foi rejeitado antes)
    - Comentários existentes (se houver)
    - Botão "Adicionar Comentário" (do Épico 5)
    - **Ações:**
      - Botão "Aprovar" (verde, destaque)
      - Botão "Solicitar Mudanças" (amarelo)
      - Botão "Voltar para Lista"
  - **Conteúdo:**
    - Markdown renderizado (igual modo leitura)
    - Trechos com comentários destacados (se houver)
- [ ] Diferença visual entre modo leitura normal e modo revisão:
  - Background do painel de revisão diferente
  - Indicador claro "Você está revisando este documento"
- [ ] Possibilidade de fazer scroll infinito entre documentos pendentes (navegação)
  - Setas "Anterior" e "Próximo" no topo

**Técnico:**
- [ ] Endpoint: `GET /api/v1/documents/{document_id}/review`
- [ ] Resposta inclui:
  ```json
  {
    "document": {
      "id": 123,
      "title": "...",
      "content": "...",
      "status": "pending_approval",
      ...
    },
    "submission": {
      "submitted_by": {...},
      "submitted_at": "...",
      "reviewer_message": "...",
      "previous_rejections_count": 2
    },
    "comments": [...],
    "previous_submissions": [
      {
        "id": 1,
        "submitted_at": "2024-01-10T10:00:00Z",
        "reviewed_at": "2024-01-11T14:30:00Z",
        "decision": "changes_requested",
        "review_notes": "Ajustar seção X"
      }
    ],
    "navigation": {
      "previous_document_id": 122,
      "next_document_id": 124
    }
  }
  ```
- [ ] Autorização: Apenas Revisores do grupo podem acessar modo revisão

**UX:**
- [ ] Layout claro com painel de revisão fixo
- [ ] Scroll independente entre conteúdo e painel
- [ ] Botões de ação sempre visíveis (sticky)
- [ ] Highlight de comentários existentes
- [ ] Histórico de submissões expandível
- [ ] Navegação entre documentos fluida

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-4.2.1

---

## 4.3 Aprovar Documento

### US-4.3.1: Aprovar Documento (Revisor)

**Como** Revisor,  
**Quero** aprovar documento,  
**Para** que seja publicado e disponibilizado.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Aprovar" visível no painel de revisão
- [ ] Ao clicar, modal de confirmação:
  - Mensagem: "Aprovar documento [Título]?"
  - Informação: "O documento será publicado e ficará disponível para todos do grupo"
  - Campo opcional: "Notas de aprovação" (textarea)
    - Placeholder: "Adicione comentários sobre a aprovação (opcional)"
  - Botões: "Cancelar" e "Confirmar Aprovação"
- [ ] Ao confirmar:
  - Documento status → APPROVED
  - Timestamp `reviewed_at` e `approved_at` registrados
  - Revisor registrado em `reviewed_by`
  - Notas de aprovação salvas em `review_notes`
  - Job adicionado à fila de publicação
  - Notificação enviada ao Editor que criou
  - Registro de aprovação criado no histórico
- [ ] Mensagem de sucesso: "Documento aprovado! Será publicado em breve."
- [ ] Redirecionado para lista de pendentes

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/approve`
- [ ] Payload:
  ```json
  {
    "review_notes": "Documento bem estruturado, aprovado para publicação"
  }
  ```
- [ ] Resposta: 200 OK
- [ ] Validações:
  - Documento em PENDING_APPROVAL
  - Usuário é Revisor do grupo
  - Documento ainda não foi revisado (reviewed_at IS NULL)
- [ ] Atualização no banco:
  ```sql
  UPDATE documents 
  SET 
    status = 'approved',
    reviewed_at = NOW(),
    reviewed_by = $1,
    review_decision = 'approved',
    review_notes = $2,
    approved_at = NOW(),
    updated_at = NOW()
  WHERE id = $3 AND status = 'pending_approval';
  ```
- [ ] Marcar submissão como resolvida:
  ```sql
  UPDATE approval_submissions 
  SET 
    resolved = TRUE,
    resolved_at = NOW(),
    resolved_by = $1
  WHERE document_id = $2 AND resolved = FALSE;
  ```
- [ ] Adicionar job de publicação:
  ```python
  from tasks import publish_document
  
  task_id = publish_document.apply_async(
    args=[document_id],
    queue='documents.publishing'
  )
  
  # Salvar task_id
  db.execute(
    "UPDATE documents SET publishing_task_id = $1 WHERE id = $2",
    task_id, document_id
  )
  ```
- [ ] Notificar Editor:
  ```python
  create_notification(
    user_id=document.created_by,
    type='document_approved',
    title=f'Documento aprovado: {document.title}',
    message=f'{reviewer.name} aprovou seu documento',
    link=f'/documents/{document.id}',
    data={'reviewed_by': reviewer.name, 'review_notes': review_notes}
  )
  
  # Email
  if creator.email_notifications_enabled:
    queue_email(
      to=creator.email,
      template='document_approved',
      context={
        'author_name': creator.name,
        'document_title': document.title,
        'reviewer_name': reviewer.name,
        'review_notes': review_notes,
        'document_url': f'{base_url}/documents/{document.id}'
      }
    )
  ```
- [ ] Log: `user_id`, `document_id`, `action='approved'`, `timestamp`

**Schema Adicional:**
```sql
ALTER TABLE documents 
ADD COLUMN approved_at TIMESTAMP,
ADD COLUMN published_at TIMESTAMP,
ADD COLUMN publishing_task_id VARCHAR(255);

CREATE TABLE approval_history (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  submission_id INTEGER REFERENCES approval_submissions(id),
  action VARCHAR(50) NOT NULL,  -- 'submitted', 'approved', 'rejected', 'cancelled'
  performed_by INTEGER NOT NULL REFERENCES users(id),
  performed_at TIMESTAMP NOT NULL DEFAULT NOW(),
  notes TEXT,
  document_version_snapshot TEXT
);

CREATE INDEX idx_approval_history_document ON approval_history(document_id);
CREATE INDEX idx_approval_history_action ON approval_history(action);
```

**Criar Registro de Histórico:**
```python
def create_approval_history(
  document_id: int,
  action: str,
  performed_by: int,
  notes: str = None
):
  db.execute(
    """
    INSERT INTO approval_history 
    (document_id, action, performed_by, notes)
    VALUES ($1, $2, $3, $4)
    """,
    document_id, action, performed_by, notes
  )
```

**UX:**
- [ ] Botão verde destacado
- [ ] Modal com campo de notas expansível
- [ ] Loading indicator ao aprovar
- [ ] Animação de sucesso
- [ ] Redirecionamento suave

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-4.2.2

---

## 4.4 Solicitar Mudanças

### US-4.4.1: Solicitar Mudanças em Documento (Revisor)

**Como** Revisor,  
**Quero** solicitar mudanças em documento,  
**Para** que Editor corrija problemas antes de aprovar.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Solicitar Mudanças" visível no painel de revisão
- [ ] Ao clicar, modal de solicitação de mudanças:
  - Mensagem: "Solicitar mudanças no documento [Título]?"
  - Informação: "O documento voltará para o editor com seus comentários e solicitações"
  - Campo obrigatório: "Motivo da rejeição" (textarea)
    - Placeholder: "Descreva as mudanças necessárias"
    - Validação: mínimo 10 caracteres
  - Resumo de comentários adicionados (se houver):
    - "Você adicionou X comentários neste documento"
    - Link: "Ver comentários"
  - Checkbox: "☐ Notificar editor imediatamente"
  - Botões: "Cancelar" e "Solicitar Mudanças"
- [ ] Ao confirmar:
  - Documento status → CHANGES_REQUESTED
  - Timestamp `reviewed_at` registrado
  - Revisor registrado em `reviewed_by`
  - Motivo salvo em `review_notes`
  - Lock de edição removido (Editor pode editar novamente)
  - Notificação enviada ao Editor
  - Registro no histórico
- [ ] Mensagem de sucesso: "Mudanças solicitadas. O editor foi notificado."
- [ ] Redirecionado para lista de pendentes

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/request-changes`
- [ ] Payload:
  ```json
  {
    "review_notes": "Por favor, ajustar seção de benefícios conforme comentários. Adicionar exemplos práticos.",
    "notify_immediately": true
  }
  ```
- [ ] Resposta: 200 OK
- [ ] Validações:
  - Documento em PENDING_APPROVAL
  - Usuário é Revisor do grupo
  - review_notes não vazio (mínimo 10 caracteres)
- [ ] Atualização no banco:
  ```sql
  UPDATE documents 
  SET 
    status = 'changes_requested',
    reviewed_at = NOW(),
    reviewed_by = $1,
    review_decision = 'changes_requested',
    review_notes = $2,
    updated_at = NOW()
  WHERE id = $3 AND status = 'pending_approval';
  ```
- [ ] Marcar submissão como resolvida:
  ```sql
  UPDATE approval_submissions 
  SET 
    resolved = TRUE,
    resolved_at = NOW(),
    resolved_by = $1
  WHERE document_id = $2 AND resolved = FALSE;
  ```
- [ ] Notificar Editor:
  ```python
  create_notification(
    user_id=document.created_by,
    type='changes_requested',
    title=f'Mudanças solicitadas: {document.title}',
    message=f'{reviewer.name} solicitou mudanças no seu documento',
    link=f'/documents/{document.id}',
    data={
      'reviewed_by': reviewer.name,
      'review_notes': review_notes,
      'comments_count': count_unresolved_comments(document.id)
    }
  )
  
  # Email
  if creator.email_notifications_enabled:
    queue_email(
      to=creator.email,
      template='changes_requested',
      context={
        'author_name': creator.name,
        'document_title': document.title,
        'reviewer_name': reviewer.name,
        'review_notes': review_notes,
        'comments_count': count_unresolved_comments(document.id),
        'document_url': f'{base_url}/documents/{document.id}'
      }
    )
  ```
- [ ] Criar registro de histórico:
  ```python
  create_approval_history(
    document_id=document.id,
    action='rejected',
    performed_by=reviewer.id,
    notes=review_notes
  )
  ```
- [ ] Log: `user_id`, `document_id`, `action='requested_changes'`, `timestamp`

**Template de Email "Mudanças Solicitadas":**
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .container { max-width: 600px; margin: 0 auto; }
    .header { background: #FCD34D; padding: 20px; }
    .content { padding: 20px; }
    .review-notes { 
      background: #FEF3C7; 
      padding: 15px; 
      border-left: 4px solid #F59E0B;
      margin: 20px 0;
    }
    .button { 
      background: #3B82F6; 
      color: white; 
      padding: 12px 24px; 
      text-decoration: none;
      border-radius: 6px;
      display: inline-block;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>⚠️ Mudanças Solicitadas</h2>
    </div>
    <div class="content">
      <p>Olá {{ author_name }},</p>
      
      <p>{{ reviewer_name }} revisou seu documento <strong>"{{ document_title }}"</strong> e solicitou algumas mudanças antes da aprovação.</p>
      
      <div class="review-notes">
        <strong>Motivo:</strong>
        <p>{{ review_notes }}</p>
      </div>
      
      {% if comments_count > 0 %}
      <p>O revisor adicionou <strong>{{ comments_count }} comentário(s)</strong> no documento para guiar as correções.</p>
      {% endif %}
      
      <p>Você pode visualizar os comentários e fazer as correções necessárias:</p>
      
      <a href="{{ document_url }}" class="button">Ver Documento e Comentários</a>
      
      <p style="margin-top: 30px; color: #6B7280; font-size: 14px;">
        Após fazer as correções, envie o documento novamente para revisão.
      </p>
    </div>
  </div>
</body>
</html>
```

**UX:**
- [ ] Botão amarelo (cor de atenção, não erro)
- [ ] Modal com campo de notas obrigatório
- [ ] Contador de caracteres (mínimo 10)
- [ ] Resumo de comentários com link
- [ ] Loading indicator ao enviar
- [ ] Feedback visual claro

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-4.2.2

---

## 4.5 Processar Mudanças e Reenviar

### US-4.5.1: Visualizar Mudanças Solicitadas (Editor)

**Como** Editor,  
**Quero** visualizar mudanças solicitadas pelo Revisor,  
**Para** entender o que precisa ser corrigido.

#### Critérios de Aceitação

**Funcional:**
- [ ] Ao abrir documento CHANGES_REQUESTED, interface especial é exibida
- [ ] Banner de alerta no topo:
  - Ícone de atenção (amarelo)
  - Mensagem: "⚠️ Mudanças Solicitadas por [Nome do Revisor]"
  - Data de revisão
  - Botão "Ver Histórico de Revisões"
- [ ] Painel lateral "Solicitação de Mudanças":
  - **Revisão Atual:**
    - Revisor que solicitou
    - Data e hora
    - Motivo completo (review_notes)
  - **Comentários (se houver):**
    - Lista de comentários não resolvidos
    - Link para cada comentário (scroll to)
    - Contador: "X comentários pendentes"
  - **Histórico de Revisões Anteriores (se houver):**
    - Lista de submissões e rejeições anteriores
    - Expandível/colapsável
  - **Ações:**
    - Botão "Editar Documento" (destaque)
    - Botão "Marcar Todos como Resolvidos"
- [ ] Conteúdo do documento em modo leitura
- [ ] Comentários inline destacados com fundo amarelo
- [ ] Possibilidade de marcar comentários como resolvidos individualmente

**Técnico:**
- [ ] Endpoint: `GET /api/v1/documents/{document_id}/changes-requested`
- [ ] Resposta:
  ```json
  {
    "document": {...},
    "current_review": {
      "reviewed_by": {
        "id": 10,
        "name": "Maria Santos"
      },
      "reviewed_at": "2024-01-16T14:30:00Z",
      "review_notes": "Por favor ajustar seção X...",
      "comments_count": 5,
      "unresolved_comments_count": 5
    },
    "comments": [
      {
        "id": 1,
        "text": "Esta informação está desatualizada",
        "line_start": 45,
        "line_end": 50,
        "created_by": {...},
        "created_at": "...",
        "resolved": false
      }
    ],
    "previous_reviews": [
      {
        "submitted_at": "2024-01-10T10:00:00Z",
        "reviewed_at": "2024-01-11T14:30:00Z",
        "reviewed_by": {...},
        "review_notes": "Adicionar mais detalhes na seção Y"
      }
    ]
  }
  ```
- [ ] Autorização: Apenas Editor que criou ou Admin de Grupo

**UX:**
- [ ] Banner de alerta destacado
- [ ] Painel de revisão com informação clara
- [ ] Histórico expandível
- [ ] Comentários linkáveis (click scroll to)
- [ ] Visual diferenciado para comentários não resolvidos
- [ ] Botão "Editar" destacado em verde

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-4.4.1

---

### US-4.5.2: Editar Documento com Mudanças Solicitadas (Editor)

**Como** Editor,  
**Quero** editar documento após solicitação de mudanças,  
**Para** fazer correções necessárias.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar Documento" abre editor
- [ ] Editor funciona normalmente (igual DRAFT)
- [ ] Banner persistente no topo do editor:
  - Mensagem: "📝 Você está corrigindo mudanças solicitadas"
  - Link: "Ver solicitação completa"
- [ ] Painel lateral mostra comentários não resolvidos
- [ ] Ao fazer edições, auto-save funciona normalmente
- [ ] Possibilidade de marcar comentários como resolvidos durante edição:
  - Checkbox ao lado de cada comentário
  - Atalho: Click no comentário inline → "Marcar como Resolvido"
- [ ] Contador de comentários não resolvidos atualiza em tempo real
- [ ] Botão "Reenviar para Revisão" (substitui "Enviar para Revisão")

**Técnico:**
- [ ] Mesmo endpoint de edição: `PATCH /api/v1/documents/{document_id}`
- [ ] Documento permanece em status CHANGES_REQUESTED durante edição
- [ ] Apenas muda para PENDING_APPROVAL ao reenviar
- [ ] Marcar comentário como resolvido:
  ```python
  # Endpoint: PUT /api/v1/comments/{comment_id}/resolve
  db.execute(
    """
    UPDATE document_comments 
    SET 
      resolved = TRUE,
      resolved_at = NOW(),
      resolved_by = $1
    WHERE id = $2
    """,
    user_id, comment_id
  )
  ```

**UX:**
- [ ] Banner no topo sempre visível
- [ ] Comentários acessíveis facilmente
- [ ] Checkbox de resolução com feedback visual
- [ ] Contador atualizado em tempo real
- [ ] Botão de reenvio destacado

**Prioridade:** Alta  
**Estimativa:** 3 pontos  
**Dependências:** US-4.5.1

---

### US-4.5.3: Reenviar Documento para Aprovação Após Mudanças (Editor)

**Como** Editor,  
**Quero** reenviar documento após fazer correções,  
**Para** solicitar nova revisão.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Reenviar para Revisão" visível no editor
- [ ] Ao clicar, verificação de comentários não resolvidos:
  - Se há comentários pendentes: modal de aviso (igual US-4.1.1)
  - Opções: Marcar todos como resolvidos, Enviar assim mesmo, Cancelar
- [ ] Modal de reenvio:
  - Mensagem: "Reenviar documento para revisão?"
  - Informação: "Você fez as correções solicitadas por [Revisor]"
  - Campo opcional: "Resumo das mudanças" (textarea)
    - Placeholder: "Descreva as correções que você fez (opcional)"
  - Checkbox: "☑ Já resolvi todos os comentários" (pré-marcado se todos resolvidos)
  - Botões: "Cancelar" e "Reenviar para Revisão"
- [ ] Ao confirmar:
  - Documento status → PENDING_APPROVAL
  - Nova submissão criada
  - Revisor anterior notificado (prioridade para mesmo revisor)
  - Lock de edição aplicado
- [ ] Mensagem: "Documento reenviado para revisão!"
- [ ] Redirecionado para visualização

**Técnico:**
- [ ] Mesmo endpoint: `POST /api/v1/documents/{document_id}/submit-for-approval`
- [ ] Validação adicional:
  - Documento em CHANGES_REQUESTED
- [ ] Atualização:
  ```sql
  UPDATE documents 
  SET 
    status = 'pending_approval',
    submitted_for_approval_at = NOW(),
    submitted_by = $1,
    reviewer_message = $2,
    -- Limpar revisão anterior
    reviewed_at = NULL,
    reviewed_by = NULL,
    review_decision = NULL,
    review_notes = NULL,
    updated_at = NOW()
  WHERE id = $3 AND status = 'changes_requested';
  ```
- [ ] Criar nova submissão:
  ```sql
  INSERT INTO approval_submissions (
    document_id,
    submitted_by,
    submitted_at,
    reviewer_message,
    is_resubmission,
    previous_reviewer_id
  ) VALUES ($1, $2, NOW(), $3, TRUE, $4);
  ```
- [ ] Notificar revisor anterior (prioridade):
  ```python
  # Notificar revisor que solicitou mudanças
  create_notification(
    user_id=previous_reviewer.id,
    type='document_resubmitted',
    title=f'Documento corrigido: {document.title}',
    message=f'{editor.name} fez as correções e reenviou o documento',
    link=f'/documents/{document.id}',
    priority='high'  # Alta prioridade para mesmo revisor
  )
  
  # Notificar outros revisores também (prioridade normal)
  for reviewer in other_reviewers:
    create_notification(reviewer.id, ...)
  ```
- [ ] Registro de histórico:
  ```python
  create_approval_history(
    document_id=document.id,
    action='resubmitted',
    performed_by=editor.id,
    notes=reviewer_message
  )
  ```

**Schema Adicional:**
```sql
ALTER TABLE approval_submissions 
ADD COLUMN is_resubmission BOOLEAN DEFAULT FALSE,
ADD COLUMN previous_reviewer_id INTEGER REFERENCES users(id);
```

**UX:**
- [ ] Botão destacado (verde ou azul)
- [ ] Modal com resumo de mudanças
- [ ] Checkbox de confirmação de resolução
- [ ] Loading indicator
- [ ] Feedback de sucesso

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-4.5.2

---

## 4.6 Publicação de Documentos

### US-4.6.1: Worker de Publicação Processa Documento Aprovado

**Como** worker de publicação,  
**Quero** processar documentos aprovados,  
**Para** publicá-los e gerar embeddings.

#### Critérios de Aceitação

**Funcional:**
- [ ] Worker recebe job de publicação quando documento é aprovado
- [ ] Worker atualiza status: APPROVED → PUBLISHED
- [ ] Worker registra timestamp de publicação
- [ ] Worker dispara job de geração de embeddings (para RAG futuro)
- [ ] Worker notifica Editor sobre publicação
- [ ] Se falhar, documento volta para APPROVED e notifica admins

**Técnico:**
- [ ] Task Celery de publicação:
  ```python
  # tasks.py
  @celery.task(
    bind=True,
    name='documents.tasks.publish_document',
    max_retries=3
  )
  def publish_document(self, document_id: int):
    """
    Publish approved document
    """
    try:
      # 1. Verificar que documento está APPROVED
      document = get_document(document_id)
      
      if document.status != 'approved':
        logger.warning(f"Document {document_id} is not approved, skipping publication")
        return
      
      # 2. Criar versão snapshot antes de publicar
      create_version_snapshot(document_id)
      
      # 3. Atualizar status para PUBLISHED
      db.execute(
        """
        UPDATE documents 
        SET 
          status = 'published',
          published_at = NOW(),
          updated_at = NOW()
        WHERE id = $1
        """,
        document_id
      )
      
      # 4. Criar registro de publicação
      db.execute(
        """
        INSERT INTO publication_history 
        (document_id, published_by, published_at)
        VALUES ($1, $2, NOW())
        """,
        document_id, document.reviewed_by
      )
      
      # 5. Disparar job de embeddings (RAG)
      generate_embeddings.apply_async(
        args=[document_id],
        queue='documents.embedding'
      )
      
      # 6. Notificar criador
      notify_publication(document_id)
      
      # 7. Log
      logger.info(f"Document {document_id} published successfully")
      
    except Exception as exc:
      logger.error(f"Publication failed for document {document_id}: {str(exc)}")
      
      # Retry
      if self.request.retries < self.max_retries:
        raise self.retry(exc=exc, countdown=60)
      else:
        # Falha permanente
        db.execute(
          "UPDATE documents SET status = 'approved' WHERE id = $1",
          document_id
        )
        notify_publication_failed(document_id)
        raise
  ```
- [ ] Schema de publicação:
  ```sql
  CREATE TABLE publication_history (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    published_by INTEGER REFERENCES users(id),
    published_at TIMESTAMP NOT NULL DEFAULT NOW(),
    version VARCHAR(20),
    embedding_generated BOOLEAN DEFAULT FALSE,
    embedding_generated_at TIMESTAMP
  );
  
  CREATE INDEX idx_publication_history_document ON publication_history(document_id);
  CREATE INDEX idx_publication_history_published_at ON publication_history(published_at);
  ```
- [ ] Notificação de publicação:
  ```python
  def notify_publication(document_id: int):
    document = get_document(document_id)
    
    create_notification(
      user_id=document.created_by,
      type='document_published',
      title=f'Documento publicado: {document.title}',
      message='Seu documento foi aprovado e está disponível',
      link=f'/documents/{document.id}'
    )
    
    # Email
    if creator.email_notifications_enabled:
      queue_email(
        to=creator.email,
        template='document_published',
        context={
          'author_name': creator.name,
          'document_title': document.title,
          'reviewer_name': reviewer.name,
          'published_at': document.published_at,
          'document_url': f'{base_url}/documents/{document.id}'
        }
      )
  ```

**Versionamento ao Publicar:**
```python
def create_version_snapshot(document_id: int):
  """Create version snapshot before publishing"""
  document = get_document(document_id)
  
  db.execute(
    """
    INSERT INTO document_versions 
    (document_id, version, title, content, tags, category_id, 
     created_at, created_by, published_at, is_current_published)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), TRUE)
    """,
    document.id,
    document.version,
    document.title,
    document.content,
    document.tags,
    document.category_id,
    document.created_at,
    document.created_by
  )
  
  # Marcar versões anteriores como não-current
  db.execute(
    """
    UPDATE document_versions 
    SET is_current_published = FALSE 
    WHERE document_id = $1 AND id != $2
    """,
    document.id, new_version_id
  )
```

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-4.3.1

---

### US-4.6.2: Notificação de Publicação (Editor)

**Como** Editor,  
**Quero** receber notificação quando documento for publicado,  
**Para** saber que está disponível.

#### Critérios de Aceitação

**Funcional:**
- [ ] Notificação in-app quando documento é publicado
- [ ] Email (se habilitado) informando publicação
- [ ] Notificação contém:
  - Título do documento
  - Revisor que aprovou
  - Data e hora de publicação
  - Link direto para documento publicado
- [ ] Click na notificação abre documento

**Técnico:**
- [ ] Implementado em US-4.6.1 (função `notify_publication`)
- [ ] Template de email já definido

**Template de Email "Documento Publicado":**
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .container { max-width: 600px; margin: 0 auto; }
    .header { background: #34D399; padding: 20px; color: white; }
    .content { padding: 20px; }
    .success-box { 
      background: #D1FAE5; 
      padding: 15px; 
      border-left: 4px solid #10B981;
      margin: 20px 0;
    }
    .button { 
      background: #3B82F6; 
      color: white; 
      padding: 12px 24px; 
      text-decoration: none;
      border-radius: 6px;
      display: inline-block;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>✅ Documento Publicado!</h2>
    </div>
    <div class="content">
      <p>Olá {{ author_name }},</p>
      
      <p>Ótimas notícias! Seu documento foi aprovado e publicado.</p>
      
      <div class="success-box">
        <strong>Documento:</strong> {{ document_title }}<br>
        <strong>Aprovado por:</strong> {{ reviewer_name }}<br>
        <strong>Publicado em:</strong> {{ published_at }}
      </div>
      
      <p>O documento está agora disponível para todos os membros do grupo.</p>
      
      <a href="{{ document_url }}" class="button">Ver Documento Publicado</a>
      
      <p style="margin-top: 30px; color: #6B7280; font-size: 14px;">
        Parabéns pelo trabalho!
      </p>
    </div>
  </div>
</body>
</html>
```

**Prioridade:** Média  
**Estimativa:** 2 pontos  
**Dependências:** US-4.6.1

---

## 4.7 Notificações de Workflow

### US-4.7.1: Centro de Notificações de Workflow

**Como** usuário,  
**Quero** visualizar todas as notificações de workflow,  
**Para** acompanhar status de documentos.

#### Critérios de Aceitação

**Funcional:**
- [ ] Ícone de notificações no topbar (sino)
- [ ] Badge com contador de não lidas: "🔔 (3)"
- [ ] Click no ícone abre dropdown de notificações
- [ ] Dropdown exibe últimas 10 notificações
- [ ] Cada notificação mostra:
  - Ícone baseado no tipo
  - Título
  - Mensagem resumida
  - Tempo decorrido ("Há 2 horas")
  - Indicador de lida/não lida
- [ ] Tipos de notificação de workflow:
  - 📝 Documento pendente de aprovação (Revisor)
  - ✅ Documento aprovado (Editor)
  - ⚠️ Mudanças solicitadas (Editor)
  - 📤 Documento reenviado (Revisor)
  - 🎉 Documento publicado (Editor)
  - 💬 Novo comentário (Editor/Revisor)
  - 👤 Menção em comentário (Qualquer usuário)
- [ ] Click na notificação:
  - Marca como lida
  - Navega para documento
- [ ] Link "Ver Todas" no rodapé do dropdown
- [ ] Página completa de notificações com filtros

**Técnico:**
- [ ] Schema de notificações:
  ```sql
  CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(500),
    data JSONB,
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
  );
  
  CREATE INDEX idx_notifications_user ON notifications(user_id);
  CREATE INDEX idx_notifications_read ON notifications(user_id, read, created_at);
  CREATE INDEX idx_notifications_type ON notifications(type);
  ```
- [ ] Endpoint: `GET /api/v1/notifications`
- [ ] Query params: `?unread=true&type=document_pending_approval&limit=10`
- [ ] Resposta:
  ```json
  {
    "notifications": [
      {
        "id": 1,
        "type": "document_approved",
        "title": "Documento aprovado: Política de Férias",
        "message": "Maria Santos aprovou seu documento",
        "link": "/documents/123",
        "data": {
          "document_id": 123,
          "reviewed_by": "Maria Santos"
        },
        "read": false,
        "created_at": "2024-01-17T10:30:00Z",
        "time_ago": "Há 2 horas"
      }
    ],
    "unread_count": 3,
    "total": 25
  }
  ```
- [ ] Endpoint para marcar como lida: `PUT /api/v1/notifications/{id}/read`
- [ ] Endpoint para marcar todas como lidas: `PUT /api/v1/notifications/mark-all-read`
- [ ] WebSocket/SSE para notificações em tempo real (opcional):
  ```python
  # Quando criar notificação, emitir evento
  emit_notification_event(user_id, notification)
  ```

**Ícones de Notificação:**
- 📝 PENDING_APPROVAL: Documento amarelo
- ✅ APPROVED: Check verde
- ⚠️ CHANGES_REQUESTED: Triângulo amarelo
- 📤 RESUBMITTED: Seta circular azul
- 🎉 PUBLISHED: Confete verde
- 💬 COMMENT: Balão de fala
- 👤 MENTION: Arroba azul

**UX:**
- [ ] Badge animado quando nova notificação chega
- [ ] Dropdown com scroll (max-height)
- [ ] Notificações não lidas com background destacado
- [ ] Hover effect em cada notificação
- [ ] Loading skeleton ao carregar
- [ ] Estado vazio: "Nenhuma notificação"

**Prioridade:** Alta  
**Estimativa:** 8 pontos  
**Dependências:** US-4.1.1, US-4.3.1, US-4.4.1

---

### US-4.7.2: Configurações de Notificações por Email

**Como** usuário,  
**Quero** configurar quais notificações recebo por email,  
**Para** controlar volume de mensagens.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Configurações > Notificações"
- [ ] Seção "Notificações de Workflow"
- [ ] Checkbox para cada tipo de notificação:
  - ☑ Documento pendente de aprovação
  - ☑ Documento aprovado
  - ☑ Mudanças solicitadas
  - ☑ Documento publicado
  - ☑ Novos comentários
  - ☑ Menções em comentários
- [ ] Toggle global: "Receber notificações por email"
- [ ] Opção de frequência (futuro):
  - Imediata
  - Digest diário
  - Digest semanal
- [ ] Botão "Salvar Preferências"
- [ ] Mensagem de sucesso ao salvar

**Técnico:**
- [ ] Schema:
  ```sql
  CREATE TABLE user_notification_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT TRUE,
    email_frequency VARCHAR(20) DEFAULT 'immediate',  -- 'immediate', 'daily', 'weekly'
    notification_types JSONB DEFAULT '{"document_pending_approval": true, "document_approved": true, ...}'::jsonb,
    updated_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] Endpoint: `GET /api/v1/users/me/notification-preferences`
- [ ] Endpoint: `PUT /api/v1/users/me/notification-preferences`
- [ ] Payload:
  ```json
  {
    "email_enabled": true,
    "email_frequency": "immediate",
    "notification_types": {
      "document_pending_approval": true,
      "document_approved": true,
      "changes_requested": true,
      "document_published": false,
      "new_comment": true,
      "mention": true
    }
  }
  ```
- [ ] Ao enviar email, verificar preferências:
  ```python
  def should_send_email(user_id: int, notification_type: str) -> bool:
    prefs = get_user_notification_preferences(user_id)
    
    if not prefs.email_enabled:
      return False
    
    if notification_type not in prefs.notification_types:
      return True  # Default: enviar
    
    return prefs.notification_types[notification_type]
  ```

**UX:**
- [ ] Toggle switches para cada tipo
- [ ] Descrição de cada tipo de notificação
- [ ] Preview de email ao lado (opcional)
- [ ] Salvar automaticamente ao mudar (debounce)
- [ ] Feedback visual de salvamento

**Prioridade:** Baixa  
**Estimativa:** 5 pontos  
**Dependências:** US-4.7.1

---

## 4.8 Gestão de Aprovações

### US-4.8.1: Visualizar Histórico de Aprovações (Editor e Revisor)

**Como** Editor ou Revisor,  
**Quero** visualizar histórico completo de aprovações de um documento,  
**Para** entender o processo de revisão.

#### Critérios de Aceitação

**Funcional:**
- [ ] Aba "Histórico de Aprovações" na página do documento
- [ ] Timeline visual mostrando todas as ações:
  - Submissão para aprovação
  - Aprovação
  - Solicitação de mudanças
  - Reenvio
  - Publicação
  - Cancelamento
- [ ] Cada evento na timeline mostra:
  - Data e hora
  - Usuário que realizou ação
  - Ação executada
  - Notas/comentários (se houver)
  - Versão do documento (se aplicável)
- [ ] Ordenação cronológica (mais recente primeiro)
- [ ] Possibilidade de expandir evento para ver detalhes
- [ ] Link para versão do documento no momento da ação (se disponível)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/documents/{document_id}/approval-history`
- [ ] Resposta:
  ```json
  {
    "history": [
      {
        "id": 10,
        "action": "published",
        "performed_by": {
          "id": 10,
          "name": "Maria Santos"
        },
        "performed_at": "2024-01-17T10:30:00Z",
        "notes": null,
        "version": "1.0"
      },
      {
        "id": 9,
        "action": "approved",
        "performed_by": {
          "id": 10,
          "name": "Maria Santos"
        },
        "performed_at": "2024-01-17T10:25:00Z",
        "notes": "Documento bem estruturado, aprovado",
        "version": "1.0"
      },
      {
        "id": 8,
        "action": "resubmitted",
        "performed_by": {
          "id": 5,
          "name": "João Silva"
        },
        "performed_at": "2024-01-16T14:00:00Z",
        "notes": "Ajustei conforme solicitado",
        "version": "1.0"
      },
      {
        "id": 7,
        "action": "rejected",
        "performed_by": {
          "id": 10,
          "name": "Maria Santos"
        },
        "performed_at": "2024-01-15T16:30:00Z",
        "notes": "Por favor ajustar seção de benefícios",
        "version": "1.0"
      },
      {
        "id": 6,
        "action": "submitted",
        "performed_by": {
          "id": 5,
          "name": "João Silva"
        },
        "performed_at": "2024-01-15T10:00:00Z",
        "notes": "Primeira versão para revisão",
        "version": "1.0"
      }
    ]
  }
  ```
- [ ] Query:
  ```sql
  SELECT * FROM approval_history 
  WHERE document_id = $1 
  ORDER BY performed_at DESC;
  ```

**UX:**
- [ ] Timeline vertical com ícones
- [ ] Cores baseadas em ação (verde=aprovado, amarelo=rejeitado, azul=submetido)
- [ ] Expandir/colapsar detalhes
- [ ] Avatar do usuário que realizou ação
- [ ] Tempo relativo ("Há 2 dias")

**Prioridade:** Baixa  
**Estimativa:** 5 pontos  
**Dependências:** US-4.3.1, US-4.4.1

---

### US-4.8.2: Relatório de Documentos Aprovados/Rejeitados (Admin)

**Como** Admin de Grupo ou Super Admin,  
**Quero** visualizar relatório de aprovações e rejeições,  
**Para** analisar performance do workflow.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Relatórios > Workflow de Aprovação"
- [ ] Métricas gerais:
  - Total de documentos submetidos (período)
  - Taxa de aprovação (%)
  - Taxa de rejeição (%)
  - Tempo médio até aprovação
  - Documentos pendentes atualmente
- [ ] Gráficos:
  - Linha: Submissões ao longo do tempo
  - Pizza: Aprovados vs Rejeitados vs Pendentes
  - Barras: Tempo médio até aprovação por Revisor
  - Barras: Documentos por Revisor
- [ ] Filtros:
  - Período (último mês, trimestre, ano, customizado)
  - Grupo (se Super Admin)
  - Revisor
  - Editor
- [ ] Tabela de documentos:
  - Título
  - Autor
  - Revisor
  - Status
  - Tempo até aprovação
  - Número de rejeições antes de aprovar
- [ ] Exportar relatório (CSV, PDF - futuro)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/reports/approval-workflow`
- [ ] Query params: `?group_id=1&start_date=2024-01-01&end_date=2024-12-31`
- [ ] Resposta:
  ```json
  {
    "metrics": {
      "total_submitted": 150,
      "total_approved": 120,
      "total_rejected": 20,
      "currently_pending": 10,
      "approval_rate": 80.0,
      "rejection_rate": 13.3,
      "avg_time_to_approval_hours": 48.5
    },
    "by_reviewer": [
      {
        "reviewer_id": 10,
        "reviewer_name": "Maria Santos",
        "approved": 50,
        "rejected": 10,
        "avg_time_hours": 36.2
      }
    ],
    "timeline": [
      {
        "date": "2024-01-01",
        "submitted": 5,
        "approved": 4,
        "rejected": 1
      }
    ]
  }
  ```
- [ ] Queries complexas com agregações:
  ```sql
  -- Taxa de aprovação
  SELECT 
    COUNT(*) FILTER (WHERE review_decision = 'approved') * 100.0 / COUNT(*) as approval_rate
  FROM approval_history
  WHERE action IN ('approved', 'rejected')
    AND performed_at BETWEEN $1 AND $2;
  
  -- Tempo médio até aprovação
  SELECT 
    AVG(EXTRACT(EPOCH FROM (approved_at - submitted_for_approval_at)) / 3600) as avg_hours
  FROM documents
  WHERE approved_at IS NOT NULL
    AND submitted_for_approval_at BETWEEN $1 AND $2;
  ```

**UX:**
- [ ] Dashboard com cards de métricas
- [ ] Gráficos interativos (Chart.js ou Recharts)
- [ ] Filtros com datepickers
- [ ] Tabela paginada e ordenável
- [ ] Loading indicators

**Prioridade:** Baixa  
**Estimativa:** 8 pontos  
**Dependências:** US-4.8.1

---

## 📊 Resumo do Épico 4

### Estatísticas

- **Total de User Stories:** 17
- **Estimativa Total:** 84 pontos
- **Prioridade:** 1 (Crítico para MVP)

### Distribuição de Prioridades

- **Crítica:** 8 histórias (47%)
- **Alta:** 4 histórias (24%)
- **Média:** 2 histórias (12%)
- **Baixa:** 3 histórias (17%)

### Distribuição por Seção

1. **Enviar para Aprovação:** 2 histórias (11 pontos)
2. **Documentos Pendentes:** 2 histórias (10 pontos)
3. **Aprovar Documento:** 1 história (5 pontos)
4. **Solicitar Mudanças:** 1 história (5 pontos)
5. **Processar Mudanças:** 3 histórias (13 pontos)
6. **Publicação:** 2 histórias (7 pontos)
7. **Notificações:** 2 histórias (13 pontos)
8. **Gestão de Aprovações:** 2 histórias (13 pontos)

### Estados de Workflow Implementados

```
✅ DRAFT → Documento em edição
⏳ PENDING_APPROVAL → Aguardando revisão
📝 CHANGES_REQUESTED → Mudanças solicitadas
✅ APPROVED → Aprovado (aguardando publicação)
🎉 PUBLISHED → Publicado e disponível
```

### Transições de Status

| De | Para | Ação | Quem |
|----|------|------|------|
| DRAFT | PENDING_APPROVAL | Enviar para revisão | Editor |
| PENDING_APPROVAL | DRAFT | Cancelar envio | Editor |
| PENDING_APPROVAL | APPROVED | Aprovar | Revisor |
| PENDING_APPROVAL | CHANGES_REQUESTED | Solicitar mudanças | Revisor |
| CHANGES_REQUESTED | PENDING_APPROVAL | Reenviar | Editor |
| APPROVED | PUBLISHED | Publicar | Worker |

### Dependências Principais

```
US-2.4.1 (Editor DRAFT)
  └── US-4.1.1 (Enviar para Aprovação)
       ├── US-4.1.2 (Cancelar Envio)
       └── US-4.2.1 (Listar Pendentes)
            └── US-4.2.2 (Modo Revisão)
                 ├── US-4.3.1 (Aprovar)
                 │    └── US-4.6.1 (Worker Publicação)
                 │         └── US-4.6.2 (Notif Publicação)
                 └── US-4.4.1 (Solicitar Mudanças)
                      └── US-4.5.1 (Visualizar Mudanças)
                           └── US-4.5.2 (Editar c/ Mudanças)
                                └── US-4.5.3 (Reenviar)

US-4.1.1 + US-4.3.1 + US-4.4.1
  └── US-4.7.1 (Centro de Notificações)
       └── US-4.7.2 (Config Notificações)
       └── US-4.8.1 (Histórico)
            └── US-4.8.2 (Relatórios)
```

### Checklist de Implementação

#### Sprint 16 - Envio e Visualização
- [ ] US-4.1.1: Enviar para Aprovação
- [ ] US-4.1.2: Cancelar Envio
- [ ] US-4.2.1: Listar Pendentes
- [ ] US-4.2.2: Modo Revisão

#### Sprint 17 - Aprovação e Rejeição
- [ ] US-4.3.1: Aprovar Documento
- [ ] US-4.4.1: Solicitar Mudanças
- [ ] US-4.5.1: Visualizar Mudanças
- [ ] US-4.5.2: Editar com Mudanças

#### Sprint 18 - Reenvio e Publicação
- [ ] US-4.5.3: Reenviar Documento
- [ ] US-4.6.1: Worker de Publicação
- [ ] US-4.6.2: Notificação de Publicação

#### Sprint 19 - Notificações e Gestão
- [ ] US-4.7.1: Centro de Notificações
- [ ] US-4.7.2: Configurações Notificações
- [ ] US-4.8.1: Histórico de Aprovações
- [ ] US-4.8.2: Relatórios (opcional)

---

## 🎯 Features Principais

### ✨ Destaques Funcionais

1. **Workflow Completo**
   - DRAFT → PENDING → APPROVED → PUBLISHED
   - CHANGES_REQUESTED com reenvio
   - Cancelamento de envio

2. **Notificações Inteligentes**
   - In-app + Email
   - Configuráveis por tipo
   - Priorização de revisor anterior

3. **Histórico e Auditoria**
   - Timeline completa de aprovações
   - Snapshot de versões
   - Logs de todas as ações

4. **UX Otimizada**
   - Lista de pendentes para Revisores
   - Modo revisão dedicado
   - Navegação entre documentos
   - Indicadores de urgência

### 🔧 Componentes Técnicos

- **Schemas:** 5 novas tabelas (approval_submissions, approval_history, publication_history, notifications, user_notification_preferences)
- **Workers:** 1 novo worker (publish_document)
- **Endpoints:** 15+ endpoints REST
- **Templates Email:** 3 templates HTML responsivos
- **Notificações:** 7 tipos diferentes

---

## ⚠️ Considerações Importantes

### Performance
- [ ] Index em `documents.status` para queries de pendentes
- [ ] Index em `notifications.user_id + read` para consultas rápidas
- [ ] Cache de contador de pendentes por revisor

### Segurança
- [ ] Validar que apenas Revisores do grupo podem aprovar
- [ ] Validar que apenas Editor que criou pode cancelar
- [ ] Audit trail completo de todas as ações

### Escalabilidade
- [ ] Queue separada para publicação (`documents.publishing`)
- [ ] Batch de notificações se muitos revisores
- [ ] Paginação em histórico de aprovações

### UX
- [ ] Feedback imediato em todas as ações
- [ ] Loading states claros
- [ ] Mensagens de erro amigáveis
- [ ] Confirmações antes de ações irreversíveis

---

## 🚀 Arquivos Criados

Você agora tem **4 épicos completos**:
1. ✅ ÉPICO 1: Gestão de Usuários & Grupos (86 pontos)
2. ✅ ÉPICO 2: Gestão de Documentos CRUD (113 pontos)
3. ✅ ÉPICO 3: Conversão de Documentos (88 pontos)
4. ✅ ÉPICO 4: Workflow de Aprovação (84 pontos)

**Total até agora: 371 pontos** ≈ 37 sprints! 🎉

---

**Épico preparado por:** Claude (Anthropic)  
**Revisão:** Pendente  
**Status:** Pronto para Desenvolvimento  
**Próximo Épico:** ÉPICO 5 - Sistema de Comentários (Prioridade 3)

