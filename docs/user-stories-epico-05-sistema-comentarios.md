# User Stories - ÉPICO 5: Sistema de Comentários

**Versão:** 1.0 MVP  
**Data:** Janeiro 2026  
**Prioridade:** 3 (Importante para MVP)  
**Status:** Planejamento

---

## 📋 Índice do Épico

- [5.1 Adicionar Comentários](#51-adicionar-comentários)
- [5.2 Visualizar Comentários](#52-visualizar-comentários)
- [5.3 Resolver Comentários](#53-resolver-comentários)
- [5.4 Sistema de Menções](#54-sistema-de-menções)
- [5.5 Gestão de Comentários](#55-gestão-de-comentários)

---

## 📊 Regras de Comentários

### Quem Pode Comentar
```
┌─────────────────┬──────────┬─────────────┬──────────────┐
│ Papel           │ Adicionar│ Visualizar  │ Resolver     │
├─────────────────┼──────────┼─────────────┼──────────────┤
│ Super Admin     │ ✅       │ ✅          │ ✅           │
│ Admin de Grupo  │ ✅       │ ✅          │ ✅           │
│ Revisor         │ ✅       │ ✅          │ ✅           │
│ Editor          │ ❌       │ ✅          │ ✅           │
│ Reader          │ ❌       │ ✅          │ ❌           │
└─────────────────┴──────────┴─────────────┴──────────────┘
```

### Estados do Comentário
- **Ativo (Não Resolvido):** Comentário requer atenção
- **Resolvido:** Comentário foi endereçado/corrigido
- **Deletado:** Comentário removido (soft delete)

### Características MVP
- ✅ Comentários em trechos específicos (seleção de texto)
- ✅ Múltiplos comentários no mesmo trecho
- ✅ @Menções de usuários do grupo
- ✅ Marcar como resolvido/não resolvido
- ❌ Threads de respostas (versão futura)
- ❌ Editar comentário após criar (apenas deletar)
- ❌ Reações/likes (versão futura)

---

## 5.1 Adicionar Comentários

### US-5.1.1: Selecionar Trecho para Comentar (Revisor)

**Como** Revisor,  
**Quero** selecionar trecho específico do documento,  
**Para** adicionar comentário contextualizado.

#### Critérios de Aceitação

**Funcional:**
- [ ] Ao visualizar documento em modo revisão, Revisor pode selecionar texto
- [ ] Após seleção, tooltip ou botão "Adicionar Comentário" aparece
- [ ] Click no botão abre interface de comentário
- [ ] Trecho selecionado fica destacado com background amarelo claro
- [ ] Se já existem comentários no trecho, indicador visual aparece (ex: badge com número)
- [ ] Seleção mínima: 1 palavra
- [ ] Seleção máxima: 500 palavras (configurável)
- [ ] Não permite seleção em múltiplos blocos (deve ser contínua)

**Técnico:**
- [ ] Frontend captura seleção de texto via `window.getSelection()`
- [ ] Cálculo de posição do trecho no documento:
  ```javascript
  function getTextSelection() {
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    
    // Obter container pai (parágrafo, div)
    const container = range.commonAncestorContainer.parentElement;
    
    // Calcular offset no documento
    const startOffset = calculateOffset(container, range.startOffset);
    const endOffset = calculateOffset(container, range.endOffset);
    
    return {
      text: selection.toString(),
      startOffset: startOffset,
      endOffset: endOffset,
      containerSelector: getCSSSelector(container)
    };
  }
  
  function calculateOffset(container, offset) {
    // Implementar cálculo de offset global no documento
    // Considerar todos os caracteres antes do container + offset local
    let globalOffset = 0;
    // ... lógica de cálculo
    return globalOffset;
  }
  ```
- [ ] Armazenar informação de posição para reconstruir highlight:
  - `start_offset`: Posição inicial no texto (número de caracteres)
  - `end_offset`: Posição final no texto
  - `selected_text`: Texto selecionado (para validação)
  - `context_before`: 50 caracteres antes (para validação em versões diferentes)
  - `context_after`: 50 caracteres depois

**Alternativa Técnica (Anchor-Based):**
```javascript
// Usar library como rangy ou draft-js para gerenciar seleções
import Rangy from 'rangy';

function saveSelection() {
  const selection = rangy.getSelection();
  const serialized = rangy.serializeSelection(selection, true);
  return serialized;
}

function restoreSelection(serialized) {
  rangy.deserializeSelection(serialized);
}
```

**UX:**
- [ ] Tooltip aparece próximo ao texto selecionado
- [ ] Tooltip com opção "Adicionar Comentário" + ícone
- [ ] Highlight suave do trecho selecionado
- [ ] Cursor muda para indicar que texto é selecionável
- [ ] Feedback visual ao passar mouse em trechos com comentários

**Prioridade:** Alta  
**Estimativa:** 8 pontos  
**Dependências:** US-4.2.2 (Modo Revisão)

---

### US-5.1.2: Adicionar Comentário em Trecho (Revisor)

**Como** Revisor,  
**Quero** adicionar comentário no trecho selecionado,  
**Para** fornecer feedback específico ao Editor.

#### Critérios de Aceitação

**Funcional:**
- [ ] Interface de comentário abre após selecionar trecho
- [ ] Interface contém:
  - Preview do trecho selecionado (read-only, truncado se grande)
  - Campo de texto (textarea) para comentário
  - Contador de caracteres (máximo 2000 caracteres)
  - Autocomplete para @menções (digitar @ mostra lista de usuários)
  - Checkbox: "☐ Crítico" (marca comentário como crítico/bloqueante)
  - Botões: "Cancelar" e "Adicionar Comentário"
- [ ] Validações:
  - Comentário não pode estar vazio (mínimo 3 caracteres)
  - Máximo 2000 caracteres
  - Trecho selecionado ainda existe no documento (não foi deletado)
- [ ] Ao salvar:
  - Comentário criado e associado ao trecho
  - Trecho destacado com indicador de comentário
  - Notificação enviada ao Editor (e mencionados, se houver)
  - Interface de comentário fecha
- [ ] Mensagem de sucesso: "Comentário adicionado"

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/comments`
- [ ] Payload:
  ```json
  {
    "text": "Esta informação está desatualizada. Por favor, atualizar conforme nova política.",
    "start_offset": 1250,
    "end_offset": 1320,
    "selected_text": "benefícios incluem vale-transporte",
    "context_before": "...todos os funcionários. Os ",
    "context_after": " e vale-refeição no valor...",
    "is_critical": true,
    "mentioned_user_ids": [5, 10]
  }
  ```
- [ ] Resposta: 201 Created com dados do comentário
- [ ] Validações server-side:
  - Documento existe
  - Usuário é Revisor do grupo (ou Admin)
  - start_offset < end_offset
  - selected_text não está vazio
  - text não está vazio (min 3, max 2000 chars)
  - mentioned_user_ids são usuários do grupo
- [ ] Schema de banco:
  ```sql
  CREATE TABLE document_comments (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Posicionamento do comentário
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    selected_text TEXT NOT NULL,
    context_before VARCHAR(100),
    context_after VARCHAR(100),
    
    -- Conteúdo do comentário
    text TEXT NOT NULL,
    is_critical BOOLEAN DEFAULT FALSE,
    
    -- Estado
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES users(id),
    
    -- Soft delete
    deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(id),
    
    -- Metadados
    version_snapshot VARCHAR(20),  -- Versão do doc quando comentário foi criado
    
    CONSTRAINT valid_offset CHECK (start_offset < end_offset)
  );
  
  CREATE TABLE comment_mentions (
    comment_id INTEGER NOT NULL REFERENCES document_comments(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    notified_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (comment_id, user_id)
  );
  
  CREATE INDEX idx_comments_document ON document_comments(document_id);
  CREATE INDEX idx_comments_created_by ON document_comments(created_by);
  CREATE INDEX idx_comments_resolved ON document_comments(resolved);
  CREATE INDEX idx_comments_deleted ON document_comments(deleted);
  CREATE INDEX idx_comment_mentions_user ON comment_mentions(user_id);
  ```
- [ ] Criar comentário:
  ```python
  def create_comment(
    document_id: int,
    user_id: int,
    text: str,
    start_offset: int,
    end_offset: int,
    selected_text: str,
    context_before: str,
    context_after: str,
    is_critical: bool,
    mentioned_user_ids: list[int]
  ) -> int:
    # 1. Inserir comentário
    comment_id = db.execute(
      """
      INSERT INTO document_comments 
      (document_id, created_by, text, start_offset, end_offset, 
       selected_text, context_before, context_after, is_critical,
       version_snapshot)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      RETURNING id
      """,
      document_id, user_id, text, start_offset, end_offset,
      selected_text, context_before, context_after, is_critical,
      get_document_version(document_id)
    )[0][0]
    
    # 2. Inserir menções
    for mentioned_id in mentioned_user_ids:
      db.execute(
        """
        INSERT INTO comment_mentions (comment_id, user_id)
        VALUES ($1, $2)
        """,
        comment_id, mentioned_id
      )
    
    # 3. Notificar Editor
    notify_new_comment(document_id, comment_id, user_id)
    
    # 4. Notificar mencionados
    for mentioned_id in mentioned_user_ids:
      notify_mention(comment_id, mentioned_id, user_id)
    
    return comment_id
  ```
- [ ] Notificações:
  ```python
  def notify_new_comment(document_id: int, comment_id: int, author_id: int):
    document = get_document(document_id)
    author = get_user(author_id)
    
    # Notificar Editor (criador do documento)
    create_notification(
      user_id=document.created_by,
      type='new_comment',
      title=f'Novo comentário: {document.title}',
      message=f'{author.name} adicionou um comentário',
      link=f'/documents/{document_id}#comment-{comment_id}',
      data={'comment_id': comment_id, 'author': author.name}
    )
  ```

**UX:**
- [ ] Textarea expansível (auto-resize)
- [ ] Preview do trecho destacado no topo
- [ ] Autocomplete de @menções com avatares
- [ ] Toggle para "Crítico" com ícone de alerta
- [ ] Contador de caracteres com cores (verde → amarelo → vermelho)
- [ ] Loading indicator ao salvar
- [ ] Modal/sidebar para comentário (não inline)

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-5.1.1

---

### US-5.1.3: Adicionar Comentário Geral (Sem Trecho Específico)

**Como** Revisor,  
**Quero** adicionar comentário geral no documento,  
**Para** feedback que não se aplica a trecho específico.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Adicionar Comentário Geral" no painel de revisão
- [ ] Interface similar a US-5.1.2, mas sem preview de trecho
- [ ] Comentário fica associado ao documento, não a trecho específico
- [ ] Comentários gerais aparecem separados dos comentários em trechos
- [ ] Seção "Comentários Gerais" no topo da lista de comentários

**Técnico:**
- [ ] Mesmo endpoint: `POST /api/v1/documents/{document_id}/comments`
- [ ] Payload sem campos de offset:
  ```json
  {
    "text": "O documento está bem estruturado, mas sugiro adicionar exemplos práticos.",
    "is_general": true,
    "is_critical": false,
    "mentioned_user_ids": []
  }
  ```
- [ ] No banco, comentários gerais têm:
  - `start_offset = NULL`
  - `end_offset = NULL`
  - `selected_text = NULL`
- [ ] Query para listar separadamente:
  ```sql
  -- Comentários gerais
  SELECT * FROM document_comments 
  WHERE document_id = $1 AND start_offset IS NULL 
  ORDER BY created_at DESC;
  
  -- Comentários em trechos
  SELECT * FROM document_comments 
  WHERE document_id = $1 AND start_offset IS NOT NULL 
  ORDER BY start_offset ASC;
  ```

**UX:**
- [ ] Botão destacado no painel
- [ ] Seção "Comentários Gerais" expandível
- [ ] Ícone diferente (💬 vs 📍)

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-5.1.2

---

## 5.2 Visualizar Comentários

### US-5.2.1: Visualizar Comentários Inline (Editor e Revisor)

**Como** Editor ou Revisor,  
**Quero** visualizar comentários no documento,  
**Para** ver feedback contextualizado.

#### Critérios de Aceitação

**Funcional:**
- [ ] Trechos com comentários destacados com background amarelo claro
- [ ] Indicador visual ao lado do trecho (ex: ícone 💬 + número de comentários)
- [ ] Hover no trecho mostra preview rápido do(s) comentário(s)
- [ ] Click no trecho ou indicador abre painel lateral com comentário(s) completo(s)
- [ ] Painel lateral mostra:
  - Trecho comentado (destacado)
  - Lista de comentários naquele trecho
  - Para cada comentário:
    - Autor (nome + avatar)
    - Data/hora relativa ("Há 2 horas")
    - Texto do comentário
    - Badge "Crítico" se is_critical=true
    - Badge "Resolvido" se resolved=true
    - Botão "Marcar como Resolvido" (se não resolvido)
    - Botão "Deletar" (se criador ou Admin)
- [ ] Possibilidade de navegar entre comentários (Next/Previous)
- [ ] Contador total de comentários no documento (topo)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/documents/{document_id}/comments`
- [ ] Query params: `?include_resolved=false&include_deleted=false`
- [ ] Resposta:
  ```json
  {
    "comments": [
      {
        "id": 1,
        "text": "Esta informação está desatualizada",
        "start_offset": 1250,
        "end_offset": 1320,
        "selected_text": "benefícios incluem vale-transporte",
        "is_critical": true,
        "resolved": false,
        "created_by": {
          "id": 10,
          "name": "Maria Santos",
          "avatar_url": "..."
        },
        "created_at": "2024-01-17T10:30:00Z",
        "mentions": [
          {"id": 5, "name": "João Silva"}
        ]
      }
    ],
    "general_comments": [
      {
        "id": 2,
        "text": "Documento bem estruturado",
        "is_critical": false,
        "resolved": false,
        "created_by": {...},
        "created_at": "..."
      }
    ],
    "stats": {
      "total": 15,
      "unresolved": 10,
      "critical": 3,
      "resolved": 5
    }
  }
  ```
- [ ] Renderização de highlights:
  ```javascript
  function highlightComments(documentContent, comments) {
    // Ordenar comentários por start_offset (do fim para o início)
    const sortedComments = comments.sort((a, b) => b.start_offset - a.start_offset);
    
    let highlightedContent = documentContent;
    
    sortedComments.forEach(comment => {
      const before = highlightedContent.substring(0, comment.start_offset);
      const highlighted = highlightedContent.substring(
        comment.start_offset, 
        comment.end_offset
      );
      const after = highlightedContent.substring(comment.end_offset);
      
      // Wrap highlighted text com span
      const wrapper = `<span 
        class="comment-highlight ${comment.is_critical ? 'critical' : ''} ${comment.resolved ? 'resolved' : ''}"
        data-comment-id="${comment.id}"
        data-comment-count="${getCommentsInRange(comment.start_offset, comment.end_offset).length}"
      >
        ${highlighted}
        <span class="comment-indicator">${getCommentsInRange(...).length}</span>
      </span>`;
      
      highlightedContent = before + wrapper + after;
    });
    
    return highlightedContent;
  }
  ```
- [ ] CSS para highlights:
  ```css
  .comment-highlight {
    background-color: #FEF3C7;
    border-bottom: 2px solid #F59E0B;
    cursor: pointer;
    position: relative;
    transition: background-color 0.2s;
  }
  
  .comment-highlight:hover {
    background-color: #FDE68A;
  }
  
  .comment-highlight.critical {
    border-bottom-color: #DC2626;
    background-color: #FEE2E2;
  }
  
  .comment-highlight.resolved {
    opacity: 0.6;
    border-bottom-style: dashed;
  }
  
  .comment-indicator {
    position: absolute;
    top: -8px;
    right: -8px;
    background: #F59E0B;
    color: white;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  ```

**Overlapping Comments:**
- [ ] Se dois comentários se sobrepõem, usar approach de "stacking":
  ```javascript
  // Detectar overlapping
  function hasOverlap(comment1, comment2) {
    return (
      (comment1.start_offset <= comment2.end_offset && 
       comment1.end_offset >= comment2.start_offset)
    );
  }
  
  // Agrupar comentários overlapping
  function groupOverlappingComments(comments) {
    // Implementar algoritmo de agrupamento
    // Exibir todos os comentários do grupo quando clicar
  }
  ```

**UX:**
- [ ] Highlights suaves e não intrusivos
- [ ] Preview em tooltip ao hover (primeiros 100 chars)
- [ ] Painel lateral deslizante (smooth animation)
- [ ] Scroll automático para comentário ativo
- [ ] Breadcrumb de navegação entre comentários
- [ ] Filtros: Mostrar todos / Só não resolvidos / Só críticos

**Prioridade:** Crítica  
**Estimativa:** 13 pontos  
**Dependências:** US-5.1.2

---

### US-5.2.2: Lista de Comentários na Sidebar (Editor e Revisor)

**Como** Editor ou Revisor,  
**Quero** ver lista completa de comentários,  
**Para** ter visão geral de todos os feedbacks.

#### Critérios de Aceitação

**Funcional:**
- [ ] Painel lateral "Comentários" mostra todos os comentários
- [ ] Seções separadas:
  - **Comentários Gerais** (topo)
  - **Comentários Não Resolvidos** (agrupado)
  - **Comentários Resolvidos** (colapsado por padrão)
- [ ] Cada comentário na lista mostra:
  - Preview do trecho (se houver)
  - Texto do comentário (truncado se longo)
  - Autor + avatar
  - Data relativa
  - Badges (Crítico, Resolvido)
  - Click para scroll até trecho no documento
- [ ] Contador por categoria:
  - "5 Não Resolvidos"
  - "3 Críticos"
  - "10 Resolvidos"
- [ ] Ordenação:
  - Padrão: Por posição no documento (start_offset)
  - Opções: Data de criação, Críticos primeiro
- [ ] Busca de comentários (campo de busca)

**Técnico:**
- [ ] Mesmo endpoint de US-5.2.1
- [ ] Componente React/Vue separado para lista
- [ ] Scroll sincronizado: click na lista → scroll no documento

**UX:**
- [ ] Lista com scroll independente
- [ ] Preview expandível (click para ver completo)
- [ ] Hover destaca trecho no documento
- [ ] Filtros rápidos (checkboxes)
- [ ] Campo de busca com highlight de resultados

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-5.2.1

---

## 5.3 Resolver Comentários

### US-5.3.1: Marcar Comentário como Resolvido (Editor e Revisor)

**Como** Editor ou Revisor,  
**Quero** marcar comentário como resolvido,  
**Para** indicar que feedback foi endereçado.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Marcar como Resolvido" visível em cada comentário não resolvido
- [ ] Botão visível para:
  - Editor (criador do documento)
  - Revisor (criador do comentário)
  - Admin de Grupo
  - Super Admin
- [ ] Click no botão marca comentário como resolvido
- [ ] Comentário resolvido:
  - Background muda para cinza claro
  - Badge "✓ Resolvido" aparece
  - Highlight no documento fica tracejado e semi-transparente
  - Move para seção "Resolvidos" (colapsada)
- [ ] Possibilidade de "Marcar como Não Resolvido" (reabrir)
- [ ] Notificação enviada ao criador do comentário (se não foi ele que resolveu)
- [ ] Mensagem de sucesso: "Comentário marcado como resolvido"

**Técnico:**
- [ ] Endpoint: `PUT /api/v1/comments/{comment_id}/resolve`
- [ ] Payload: `{"resolved": true}` ou `{"resolved": false}`
- [ ] Resposta: 200 OK
- [ ] Validações:
  - Comentário existe
  - Usuário tem permissão (Editor do doc, criador do comentário, ou Admin)
  - Comentário não está deletado
- [ ] Atualização no banco:
  ```sql
  UPDATE document_comments 
  SET 
    resolved = $1,
    resolved_at = CASE WHEN $1 = TRUE THEN NOW() ELSE NULL END,
    resolved_by = CASE WHEN $1 = TRUE THEN $2 ELSE NULL END,
    updated_at = NOW()
  WHERE id = $3;
  ```
- [ ] Notificação (se outra pessoa resolveu):
  ```python
  def notify_comment_resolved(comment_id: int, resolved_by: int):
    comment = get_comment(comment_id)
    
    if comment.created_by != resolved_by:
      create_notification(
        user_id=comment.created_by,
        type='comment_resolved',
        title='Comentário resolvido',
        message=f'{resolved_by_name} marcou seu comentário como resolvido',
        link=f'/documents/{comment.document_id}#comment-{comment_id}'
      )
  ```
- [ ] Log de ação:
  ```sql
  INSERT INTO comment_actions (
    comment_id, action, performed_by, performed_at
  ) VALUES ($1, 'resolved', $2, NOW());
  ```

**Schema Adicional:**
```sql
CREATE TABLE comment_actions (
  id SERIAL PRIMARY KEY,
  comment_id INTEGER NOT NULL REFERENCES document_comments(id) ON DELETE CASCADE,
  action VARCHAR(50) NOT NULL,  -- 'created', 'resolved', 'unresolved', 'deleted'
  performed_by INTEGER NOT NULL REFERENCES users(id),
  performed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_comment_actions_comment ON comment_actions(comment_id);
```

**UX:**
- [ ] Botão com ícone de check
- [ ] Animação de transição ao resolver (fade out → move)
- [ ] Tooltip: "Marcar como resolvido"
- [ ] Feedback visual imediato
- [ ] Undo temporário (5 segundos): "Desfazer"

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-5.2.1

---

### US-5.3.2: Marcar Todos os Comentários como Resolvidos (Editor)

**Como** Editor,  
**Quero** marcar todos os comentários como resolvidos de uma vez,  
**Para** agilizar processo após fazer todas as correções.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Marcar Todos como Resolvidos" no topo da lista de comentários
- [ ] Botão visível apenas se há comentários não resolvidos
- [ ] Click abre modal de confirmação:
  - Mensagem: "Marcar todos os X comentários como resolvidos?"
  - Aviso: "Esta ação pode ser desfeita individualmente"
  - Botões: "Cancelar" e "Confirmar"
- [ ] Ao confirmar:
  - Todos os comentários não resolvidos → resolvidos
  - Comentários movem para seção "Resolvidos"
  - Notificações enviadas aos criadores (batch)
- [ ] Mensagem de sucesso: "X comentários marcados como resolvidos"
- [ ] Undo global (opcional): "Desfazer"

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/comments/resolve-all`
- [ ] Resposta: 200 OK com número de comentários resolvidos
- [ ] Atualização em batch:
  ```sql
  UPDATE document_comments 
  SET 
    resolved = TRUE,
    resolved_at = NOW(),
    resolved_by = $1,
    updated_at = NOW()
  WHERE document_id = $2 AND resolved = FALSE AND deleted = FALSE
  RETURNING id;
  ```
- [ ] Notificações em batch (assíncrono):
  ```python
  def notify_bulk_resolved(document_id: int, resolved_by: int, comment_ids: list[int]):
    # Agrupar por criador de comentário
    comments_by_author = group_by_author(comment_ids)
    
    for author_id, comments in comments_by_author.items():
      if author_id != resolved_by:
        create_notification(
          user_id=author_id,
          type='comments_bulk_resolved',
          title=f'{len(comments)} comentários resolvidos',
          message=f'{resolved_by_name} marcou seus comentários como resolvidos',
          link=f'/documents/{document_id}'
        )
  ```

**UX:**
- [ ] Botão secundário (não muito destacado)
- [ ] Confirmação clara
- [ ] Progress indicator se muitos comentários
- [ ] Toast com undo temporário

**Prioridade:** Baixa  
**Estimativa:** 3 pontos  
**Dependências:** US-5.3.1

---

## 5.4 Sistema de Menções

### US-5.4.1: Mencionar Usuário em Comentário (@mention)

**Como** Revisor,  
**Quero** mencionar outros usuários em comentários,  
**Para** chamar atenção específica ou solicitar input.

#### Critérios de Aceitação

**Funcional:**
- [ ] Ao digitar @ no campo de comentário, autocomplete aparece
- [ ] Autocomplete mostra usuários do grupo:
  - Nome
  - Email
  - Avatar
  - Papel no grupo
- [ ] Busca incremental ao continuar digitando (ex: @joa → João)
- [ ] Seleção de usuário insere menção: @João Silva
- [ ] Menção fica destacada no comentário (background azul claro)
- [ ] Múltiplas menções permitidas no mesmo comentário
- [ ] Usuários mencionados recebem notificação
- [ ] Notificação contém link direto para comentário

**Técnico:**
- [ ] Autocomplete via endpoint: `GET /api/v1/groups/{group_id}/users/search?q=joa`
- [ ] Resposta:
  ```json
  {
    "users": [
      {
        "id": 5,
        "name": "João Silva",
        "email": "joao@empresa.com",
        "avatar_url": "...",
        "roles": ["editor"]
      }
    ]
  }
  ```
- [ ] Frontend parse de menções:
  ```javascript
  function parseMentions(text) {
    // Regex para detectar @menções
    const mentionRegex = /@\[([^\]]+)\]\((\d+)\)/g;
    
    // Formato armazenado: @[João Silva](5)
    // Formato exibido: @João Silva
    
    return text.replace(mentionRegex, (match, name, id) => {
      return `<span class="mention" data-user-id="${id}">@${name}</span>`;
    });
  }
  
  function extractMentionIds(text) {
    const mentionRegex = /@\[([^\]]+)\]\((\d+)\)/g;
    const ids = [];
    let match;
    
    while ((match = mentionRegex.exec(text)) !== null) {
      ids.push(parseInt(match[2]));
    }
    
    return ids;
  }
  ```
- [ ] Armazenamento de menções:
  - Texto do comentário com formato especial: `"Cc @[João Silva](5), você pode revisar?"`
  - Tabela `comment_mentions` com user_id extraído
- [ ] Notificação de menção:
  ```python
  def notify_mention(comment_id: int, mentioned_user_id: int, author_id: int):
    comment = get_comment(comment_id)
    author = get_user(author_id)
    
    create_notification(
      user_id=mentioned_user_id,
      type='mention',
      title=f'{author.name} mencionou você',
      message=f'Em comentário no documento "{comment.document.title}"',
      link=f'/documents/{comment.document_id}#comment-{comment_id}',
      priority='high'
    )
  ```

**Formato de Armazenamento:**
```
Texto original do usuário:
"Cc @João Silva, você pode revisar esta seção?"

Texto armazenado no banco:
"Cc @[João Silva](5), você pode revisar esta seção?"

Texto renderizado no HTML:
"Cc <span class="mention" data-user-id="5">@João Silva</span>, você pode revisar esta seção?"
```

**UX:**
- [ ] Autocomplete com dropdown elegante
- [ ] Keyboard navigation (up/down arrows, enter)
- [ ] Menções destacadas visualmente
- [ ] Click em menção abre perfil do usuário (opcional)
- [ ] Badge "Você foi mencionado" em notificações

**Prioridade:** Alta  
**Estimativa:** 8 pontos  
**Dependências:** US-5.1.2

---

### US-5.4.2: Visualizar Comentários Onde Fui Mencionado

**Como** usuário,  
**Quero** visualizar comentários onde fui mencionado,  
**Para** responder rapidamente a solicitações.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Menções" no menu principal
- [ ] Badge com contador de menções não lidas: "Menções (3)"
- [ ] Lista de comentários onde usuário foi mencionado
- [ ] Cada item mostra:
  - Documento (título + link)
  - Autor do comentário
  - Preview do comentário (com menção destacada)
  - Data
  - Status (Lido/Não lido)
  - Botão "Marcar como Lido"
- [ ] Ordenação: Mais recentes primeiro
- [ ] Filtros:
  - Não lidos / Todos
  - Por documento
  - Por período
- [ ] Click no item abre documento com scroll para comentário

**Técnico:**
- [ ] Endpoint: `GET /api/v1/users/me/mentions`
- [ ] Query params: `?unread=true&document_id=123`
- [ ] Resposta:
  ```json
  {
    "mentions": [
      {
        "comment_id": 10,
        "comment_text": "Cc @[João Silva](5), você pode revisar?",
        "document": {
          "id": 123,
          "title": "Política de Férias"
        },
        "author": {
          "id": 10,
          "name": "Maria Santos"
        },
        "created_at": "2024-01-17T10:30:00Z",
        "read": false
      }
    ],
    "unread_count": 3
  }
  ```
- [ ] Query:
  ```sql
  SELECT 
    c.id as comment_id,
    c.text as comment_text,
    c.created_at,
    d.id as document_id,
    d.title as document_title,
    u.id as author_id,
    u.name as author_name,
    cm.notified_at,
    n.read
  FROM comment_mentions cm
  JOIN document_comments c ON cm.comment_id = c.id
  JOIN documents d ON c.document_id = d.id
  JOIN users u ON c.created_by = u.id
  LEFT JOIN notifications n ON 
    n.user_id = cm.user_id AND 
    n.data->>'comment_id' = c.id::text
  WHERE cm.user_id = $1
  ORDER BY c.created_at DESC;
  ```
- [ ] Marcar como lido atualiza notificação correspondente

**UX:**
- [ ] Badge animado no menu quando nova menção
- [ ] Lista com card design
- [ ] Menção destacada em bold no preview
- [ ] Hover preview expandido
- [ ] Action buttons claros

**Prioridade:** Média  
**Estimativa:** 5 pontos  
**Dependências:** US-5.4.1

---

## 5.5 Gestão de Comentários

### US-5.5.1: Deletar Comentário (Criador ou Admin)

**Como** criador do comentário ou Admin,  
**Quero** deletar comentário,  
**Para** remover feedback incorreto ou inadequado.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Deletar" (ícone de lixeira) visível em cada comentário
- [ ] Botão visível apenas para:
  - Criador do comentário
  - Admin de Grupo
  - Super Admin
- [ ] Click abre modal de confirmação:
  - Mensagem: "Deletar este comentário?"
  - Aviso: "Esta ação não pode ser desfeita"
  - Botões: "Cancelar" e "Deletar"
- [ ] Ao confirmar:
  - Comentário soft-deleted (não removido do banco)
  - Comentário desaparece da visualização
  - Highlight do trecho removido (se era único comentário)
  - Contador de comentários atualizado
- [ ] Mensagem de sucesso: "Comentário deletado"

**Técnico:**
- [ ] Endpoint: `DELETE /api/v1/comments/{comment_id}`
- [ ] Resposta: 204 No Content
- [ ] Validações:
  - Usuário é criador ou Admin
  - Comentário não está já deletado
- [ ] Soft delete:
  ```sql
  UPDATE document_comments 
  SET 
    deleted = TRUE,
    deleted_at = NOW(),
    deleted_by = $1,
    updated_at = NOW()
  WHERE id = $2;
  ```
- [ ] Queries devem filtrar deletados por padrão:
  ```sql
  SELECT * FROM document_comments 
  WHERE document_id = $1 AND deleted = FALSE;
  ```
- [ ] Admin pode ver deletados (auditoria):
  ```sql
  SELECT * FROM document_comments 
  WHERE document_id = $1 AND deleted = TRUE;
  ```

**Auditoria de Comentários Deletados:**
```sql
CREATE VIEW deleted_comments_audit AS
SELECT 
  c.id,
  c.text,
  c.created_by,
  c.created_at,
  c.deleted_by,
  c.deleted_at,
  d.title as document_title
FROM document_comments c
JOIN documents d ON c.document_id = d.id
WHERE c.deleted = TRUE;
```

**UX:**
- [ ] Ícone de lixeira discreto (hover)
- [ ] Confirmação clara
- [ ] Animação de fade out
- [ ] Undo temporário (5 seg): "Desfazer"

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-5.2.1

---

### US-5.5.2: Estatísticas de Comentários por Documento

**Como** Editor ou Admin,  
**Quero** ver estatísticas de comentários,  
**Para** acompanhar status de feedback.

#### Critérios de Aceitação

**Funcional:**
- [ ] Widget de estatísticas no topo do painel de comentários
- [ ] Métricas exibidas:
  - Total de comentários
  - Não resolvidos (número + %)
  - Resolvidos (número + %)
  - Críticos não resolvidos (número)
  - Comentários por revisor (lista)
- [ ] Gráfico de pizza (opcional):
  - Resolvidos vs Não Resolvidos
- [ ] Barra de progresso: "60% dos comentários resolvidos"
- [ ] Atualização em tempo real ao resolver comentários

**Técnico:**
- [ ] Endpoint: `GET /api/v1/documents/{document_id}/comments/stats`
- [ ] Resposta:
  ```json
  {
    "total": 15,
    "unresolved": 6,
    "resolved": 9,
    "critical_unresolved": 2,
    "resolution_rate": 60.0,
    "by_reviewer": [
      {
        "reviewer_id": 10,
        "reviewer_name": "Maria Santos",
        "total": 8,
        "unresolved": 3
      }
    ]
  }
  ```
- [ ] Query otimizada:
  ```sql
  SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE resolved = FALSE) as unresolved,
    COUNT(*) FILTER (WHERE resolved = TRUE) as resolved,
    COUNT(*) FILTER (WHERE is_critical = TRUE AND resolved = FALSE) as critical_unresolved,
    ROUND(
      COUNT(*) FILTER (WHERE resolved = TRUE) * 100.0 / COUNT(*), 
      2
    ) as resolution_rate
  FROM document_comments
  WHERE document_id = $1 AND deleted = FALSE;
  ```

**UX:**
- [ ] Cards com ícones e números grandes
- [ ] Cores baseadas em status (verde, amarelo, vermelho)
- [ ] Animação ao atualizar números
- [ ] Tooltip com detalhes ao hover

**Prioridade:** Baixa  
**Estimativa:** 3 pontos  
**Dependências:** US-5.2.1, US-5.3.1

---

### US-5.5.3: Exportar Comentários para PDF/CSV (Admin)

**Como** Admin,  
**Quero** exportar comentários de um documento,  
**Para** compartilhar com stakeholders ou arquivar.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Exportar Comentários" no painel de comentários
- [ ] Visível apenas para Admin de Grupo e Super Admin
- [ ] Modal de opções de export:
  - Formato: PDF ou CSV
  - Incluir resolvidos: Sim/Não
  - Incluir críticos apenas: Sim/Não
  - Ordenação: Posição no documento / Data de criação
  - Botão "Exportar"
- [ ] Ao confirmar:
  - Job assíncrono de exportação iniciado
  - Notificação quando pronto
  - Link de download (expira em 24h)
- [ ] Mensagem: "Exportação iniciada. Você receberá notificação quando estiver pronto."

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/comments/export`
- [ ] Payload:
  ```json
  {
    "format": "pdf",
    "include_resolved": true,
    "critical_only": false,
    "sort_by": "position"
  }
  ```
- [ ] Resposta: 202 Accepted com job_id
- [ ] Task Celery de exportação:
  ```python
  @celery.task
  def export_comments(document_id: int, format: str, options: dict):
    # 1. Buscar comentários
    comments = get_comments(document_id, options)
    
    # 2. Gerar arquivo
    if format == 'pdf':
      file_path = generate_pdf_report(document_id, comments)
    elif format == 'csv':
      file_path = generate_csv_export(comments)
    
    # 3. Upload para S3
    s3_url = upload_to_s3(file_path, bucket='documents-exports')
    
    # 4. Notificar usuário
    notify_export_ready(user_id, s3_url)
    
    return s3_url
  ```
- [ ] Formato PDF:
  ```python
  def generate_pdf_report(document_id: int, comments: list) -> str:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    document = get_document(document_id)
    
    pdf_path = f"/tmp/{document_id}_comments.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Header
    c.drawString(50, 750, f"Comentários: {document.title}")
    c.drawString(50, 735, f"Total: {len(comments)} comentários")
    
    y = 700
    for comment in comments:
      # Trecho selecionado
      c.setFont("Helvetica-Bold", 10)
      c.drawString(50, y, f"Trecho: {comment.selected_text[:50]}...")
      y -= 15
      
      # Comentário
      c.setFont("Helvetica", 9)
      c.drawString(50, y, f"{comment.created_by.name} - {comment.created_at}")
      y -= 12
      c.drawString(50, y, comment.text[:100] + ("..." if len(comment.text) > 100 else ""))
      y -= 20
      
      if y < 100:  # Nova página
        c.showPage()
        y = 750
    
    c.save()
    return pdf_path
  ```
- [ ] Formato CSV:
  ```python
  def generate_csv_export(comments: list) -> str:
    import csv
    
    csv_path = f"/tmp/{uuid.uuid4()}.csv"
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
      writer = csv.writer(f)
      writer.writerow([
        'ID', 'Autor', 'Data', 'Trecho', 'Comentário', 
        'Crítico', 'Resolvido', 'Resolvido Por', 'Data Resolução'
      ])
      
      for c in comments:
        writer.writerow([
          c.id,
          c.created_by.name,
          c.created_at.isoformat(),
          c.selected_text,
          c.text,
          'Sim' if c.is_critical else 'Não',
          'Sim' if c.resolved else 'Não',
          c.resolved_by.name if c.resolved_by else '',
          c.resolved_at.isoformat() if c.resolved_at else ''
        ])
    
    return csv_path
  ```

**UX:**
- [ ] Botão secundário no menu de ações
- [ ] Modal com opções claras
- [ ] Loading indicator ao iniciar
- [ ] Notificação com link de download
- [ ] Link expira em 24h (aviso claro)

**Prioridade:** Baixa  
**Estimativa:** 8 pontos  
**Dependências:** US-5.2.1

---

## 📊 Resumo do Épico 5

### Estatísticas

- **Total de User Stories:** 13
- **Estimativa Total:** 75 pontos
- **Prioridade:** 3 (Importante para MVP)

### Distribuição de Prioridades

- **Crítica:** 2 histórias (15%)
- **Alta:** 5 histórias (38%)
- **Média:** 4 histórias (31%)
- **Baixa:** 2 histórias (16%)

### Distribuição por Seção

1. **Adicionar Comentários:** 3 histórias (19 pontos)
2. **Visualizar Comentários:** 2 histórias (18 pontos)
3. **Resolver Comentários:** 2 histórias (8 pontos)
4. **Sistema de Menções:** 2 histórias (13 pontos)
5. **Gestão de Comentários:** 4 histórias (17 pontos)

### Componentes Principais

#### 🎨 Frontend
- **Seleção de texto** com highlight
- **Tooltip** de comentário
- **Painel lateral** com lista
- **Autocomplete** de @menções
- **Filtros** e ordenação

#### 🔧 Backend
- **3 Tabelas:** document_comments, comment_mentions, comment_actions
- **8+ Endpoints** REST
- **Notificações** para 4 eventos diferentes
- **Export** assíncrono (PDF/CSV)

#### 📱 UX Features
- Highlights com cores (amarelo=ativo, vermelho=crítico, cinza=resolvido)
- Indicadores numéricos de comentários
- Navigation entre comentários
- Undo temporário ao resolver
- Preview em tooltip

### Dependências Principais

```
US-4.2.2 (Modo Revisão)
  └── US-5.1.1 (Selecionar Trecho)
       └── US-5.1.2 (Adicionar Comentário)
            ├── US-5.1.3 (Comentário Geral)
            ├── US-5.2.1 (Visualizar Inline)
            │    ├── US-5.2.2 (Lista Sidebar)
            │    ├── US-5.3.1 (Marcar Resolvido)
            │    │    └── US-5.3.2 (Resolver Todos)
            │    ├── US-5.5.1 (Deletar)
            │    ├── US-5.5.2 (Estatísticas)
            │    └── US-5.5.3 (Exportar)
            └── US-5.4.1 (@Menções)
                 └── US-5.4.2 (Ver Menções)
```

### Checklist de Implementação

#### Sprint 20 - Comentários Básicos
- [ ] US-5.1.1: Selecionar Trecho
- [ ] US-5.1.2: Adicionar Comentário em Trecho
- [ ] US-5.1.3: Adicionar Comentário Geral

#### Sprint 21 - Visualização
- [ ] US-5.2.1: Visualizar Comentários Inline
- [ ] US-5.2.2: Lista de Comentários Sidebar

#### Sprint 22 - Resolução e Menções
- [ ] US-5.3.1: Marcar como Resolvido
- [ ] US-5.3.2: Resolver Todos
- [ ] US-5.4.1: @Menções

#### Sprint 23 - Gestão Avançada
- [ ] US-5.4.2: Ver Menções
- [ ] US-5.5.1: Deletar Comentário
- [ ] US-5.5.2: Estatísticas
- [ ] US-5.5.3: Exportar (opcional)

---

## 🎯 Destaques Técnicos

### Algoritmo de Highlight

```javascript
// Desafio: Comentários overlapping
function renderHighlights(text, comments) {
  // 1. Criar árvore de intervalos
  const intervals = buildIntervalTree(comments);
  
  // 2. Dividir texto em segmentos
  const segments = splitIntoSegments(text, intervals);
  
  // 3. Renderizar cada segmento
  return segments.map(segment => {
    const commentIds = getCommentsForSegment(segment);
    
    if (commentIds.length === 0) {
      return segment.text;
    }
    
    return `<span 
      class="highlight" 
      data-comments="${commentIds.join(',')}"
    >${segment.text}</span>`;
  }).join('');
}
```

### Posicionamento Robusto

Para evitar problemas com edições no documento:

```python
# Armazenar contexto antes/depois
context_before = text[max(0, start_offset-50):start_offset]
context_after = text[end_offset:min(len(text), end_offset+50)]

# Ao renderizar, tentar match com contexto
def find_comment_position(document_text, comment):
  # 1. Tentar posição exata
  if document_text[comment.start_offset:comment.end_offset] == comment.selected_text:
    return comment.start_offset, comment.end_offset
  
  # 2. Buscar com contexto
  pattern = comment.context_before + comment.selected_text + comment.context_after
  match = find_fuzzy_match(document_text, pattern)
  
  if match:
    return match.start, match.end
  
  # 3. Marcar como "posição não encontrada"
  return None, None
```

### @Menções: Parser

```javascript
// Parse @menções no texto
const MENTION_REGEX = /@\[([^\]]+)\]\((\d+)\)/g;

function renderMentions(text) {
  return text.replace(MENTION_REGEX, (match, name, id) => {
    return `<a 
      href="/users/${id}" 
      class="mention" 
      data-user-id="${id}"
    >@${name}</a>`;
  });
}

// Extrair IDs para notificações
function extractMentionIds(text) {
  const matches = [...text.matchAll(MENTION_REGEX)];
  return matches.map(m => parseInt(m[2]));
}
```

---

## 💡 Considerações Importantes

### Performance
- [ ] Index em `document_comments.document_id + deleted`
- [ ] Cache de comentários por documento (Redis, 5 min)
- [ ] Lazy loading de comentários resolvidos
- [ ] Pagination se >100 comentários

### Versionamento
- [ ] Comentários ficam vinculados à versão do documento
- [ ] Ao criar nova versão, comentários não migram automaticamente
- [ ] Opção futura: "Migrar comentários não resolvidos para nova versão"

### Acessibilidade
- [ ] Highlights acessíveis via teclado (tab navigation)
- [ ] Screen reader announces comentários
- [ ] Alto contraste para highlights
- [ ] ARIA labels apropriados

### Mobile
- [ ] Touch para selecionar texto
- [ ] Sidebar responsiva (full screen em mobile)
- [ ] Swipe para navegar entre comentários

---

## 🚀 Total de Épicos Criados

1. ✅ **ÉPICO 1:** Gestão de Usuários & Grupos (86 pts)
2. ✅ **ÉPICO 2:** Gestão de Documentos CRUD (113 pts)
3. ✅ **ÉPICO 3:** Conversão de Documentos (88 pts)
4. ✅ **ÉPICO 4:** Workflow de Aprovação (84 pts)
5. ✅ **ÉPICO 5:** Sistema de Comentários (75 pts)

**TOTAL: 446 pontos** ≈ **45 sprints de 10 pontos!** 🎉

---

## 📝 Próximos Épicos Sugeridos

Quer continuar? Posso criar:

1. **ÉPICO 6: Versionamento Avançado** - Prioridade 5  
   (Histórico, diff visual, restauração, comparação entre versões)

2. **ÉPICO 7: Sistema de Busca** - Prioridade 5  
   (Full-text search, ElasticSearch, filtros avançados, relevância)

3. **ÉPICO 8: Estados Avançados** - Prioridade Baixa  
   (DEPRECATED workflow, ARCHIVED, despublicar)

4. **ÉPICO 9: Embeddings & RAG** - Prioridade Alta (preparação futura)  
   (Geração de embeddings, chunking, vector store)

Me avise se quer continuar! 🚀

---

**Épico preparado por:** Claude (Anthropic)  
**Revisão:** Pendente  
**Status:** Pronto para Desenvolvimento  
**Próximo Épico:** ÉPICO 6 - Versionamento Avançado (Prioridade 5)

