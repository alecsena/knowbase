# User Stories - ÉPICO 2: Gestão de Documentos (CRUD)

**Versão:** 1.0 MVP  
**Data:** Janeiro 2026  
**Prioridade:** 1 (Crítico para MVP)  
**Status:** Planejamento

---

## 📋 Índice do Épico

- [2.1 Gestão de Pastas](#21-gestão-de-pastas)
- [2.2 Criação de Documentos](#22-criação-de-documentos)
- [2.3 Visualização de Documentos](#23-visualização-de-documentos)
- [2.4 Edição de Documentos](#24-edição-de-documentos)
- [2.5 Metadados e Organização](#25-metadados-e-organização)
- [2.6 Templates de Documentos](#26-templates-de-documentos)
- [2.7 Exclusão e Arquivamento](#27-exclusão-e-arquivamento)

---

## 2.1 Gestão de Pastas

### US-2.1.1: Criar Pasta (Admin de Grupo e Editor)

**Como** Admin de Grupo ou Editor,  
**Quero** criar pastas dentro do meu grupo,  
**Para** organizar documentos por categorias ou temas.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Nova Pasta" visível na página de detalhes do Grupo
- [ ] Botão "Nova Pasta" também disponível dentro de uma pasta (criar subpasta)
- [ ] Modal de criação contém campos:
  - Nome da pasta (obrigatório)
  - Descrição (opcional)
  - Pasta pai (dropdown - opcional, se criar subpasta)
- [ ] Nome da pasta deve ser único dentro do mesmo nível (mesma pasta pai)
- [ ] Hierarquia máxima: 5 níveis de profundidade
- [ ] Ao criar pasta, sistema cria registro e atualiza hierarquia
- [ ] Mensagem de sucesso: "Pasta [Nome] criada com sucesso"
- [ ] Árvore de pastas atualiza automaticamente

**Técnico:**
- [ ] Endpoint: `POST /api/v1/groups/{group_id}/folders`
- [ ] Payload:
  ```json
  {
    "name": "string",
    "description": "string|null",
    "parent_folder_id": "integer|null"
  }
  ```
- [ ] Resposta: 201 Created com dados da pasta
- [ ] Validações server-side:
  - Nome não vazio (mínimo 3 caracteres)
  - Nome único no mesmo nível (mesmo parent_folder_id)
  - parent_folder_id existe e pertence ao mesmo grupo
  - Profundidade máxima não excedida (validar nível recursivamente)
  - Usuário tem permissão (Admin de Grupo ou Editor) no grupo
- [ ] Schema de banco:
  ```sql
  CREATE TABLE folders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    parent_folder_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(group_id, parent_folder_id, name)
  );
  
  CREATE INDEX idx_folders_group ON folders(group_id);
  CREATE INDEX idx_folders_parent ON folders(parent_folder_id);
  ```
- [ ] Log de criação: `user_id`, `group_id`, `folder_id`, `timestamp`

**Hierarquia de Pastas:**
```
Grupo RH
├── Políticas (nível 1)
│   ├── Benefícios (nível 2)
│   │   ├── Saúde (nível 3)
│   │   └── Vale-transporte (nível 3)
│   └── Férias (nível 2)
├── Treinamentos (nível 1)
└── Processos (nível 1)
```

**UX:**
- [ ] Validação em tempo real (nome único)
- [ ] Preview da hierarquia ao selecionar pasta pai
- [ ] Breadcrumb visual mostrando caminho completo
- [ ] Loading indicator ao salvar
- [ ] Modal fecha automaticamente após sucesso

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-1.3.1 (Criar Grupo)

---

### US-2.1.2: Listar Pastas em Árvore Hierárquica

**Como** usuário com acesso ao grupo,  
**Quero** visualizar pastas em estrutura de árvore,  
**Para** navegar facilmente pela organização de documentos.

#### Critérios de Aceitação

**Funcional:**
- [ ] Sidebar exibe árvore de pastas do grupo atual
- [ ] Pastas exibem ícone de pasta + nome
- [ ] Pastas com subpastas têm indicador expansível (▶/▼)
- [ ] Click na pasta expande/colapsa subpastas
- [ ] Click no nome da pasta navega para conteúdo (documentos)
- [ ] Pasta selecionada fica destacada (background diferente)
- [ ] Contador de documentos ao lado do nome da pasta: "Políticas (23)"
- [ ] Pastas vazias exibem "(0)"
- [ ] Estado de expansão é mantido na sessão (localStorage)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/groups/{group_id}/folders/tree`
- [ ] Resposta (estrutura hierárquica):
  ```json
  {
    "folders": [
      {
        "id": 1,
        "name": "Políticas",
        "description": "string",
        "documents_count": 23,
        "parent_folder_id": null,
        "children": [
          {
            "id": 2,
            "name": "Benefícios",
            "documents_count": 10,
            "parent_folder_id": 1,
            "children": []
          }
        ]
      }
    ]
  }
  ```
- [ ] Query recursiva para construir árvore (CTE - Common Table Expression)
- [ ] Agregação de contagem de documentos por pasta (incluindo subpastas ou apenas diretos?)
- [ ] Cache de resultado (Redis) por 5 minutos, invalidar ao criar/editar pasta/documento
- [ ] Ordenação alfabética por nome em cada nível

**SQL para Árvore Recursiva:**
```sql
WITH RECURSIVE folder_tree AS (
  -- Base case: pastas raiz
  SELECT id, name, parent_folder_id, group_id, 1 as level
  FROM folders
  WHERE parent_folder_id IS NULL AND group_id = $1
  
  UNION ALL
  
  -- Recursive case: subpastas
  SELECT f.id, f.name, f.parent_folder_id, f.group_id, ft.level + 1
  FROM folders f
  INNER JOIN folder_tree ft ON f.parent_folder_id = ft.id
  WHERE ft.level < 5  -- Limite de profundidade
)
SELECT * FROM folder_tree ORDER BY level, name;
```

**UX:**
- [ ] Loading skeleton durante carregamento inicial
- [ ] Animação suave de expansão/colapso
- [ ] Indentação visual clara para subníveis (padding esquerdo incremental)
- [ ] Hover effect em pastas
- [ ] Ícones distintos para pasta expandida/colapsada
- [ ] Drag & drop para mover pastas (opcional para MVP)

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-2.1.1

---

### US-2.1.3: Editar Pasta (Admin de Grupo e Editor)

**Como** Admin de Grupo ou Editor que criou a pasta,  
**Quero** editar nome e descrição da pasta,  
**Para** manter organização atualizada.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar" (ícone de lápis) ao fazer hover na pasta
- [ ] Modal de edição pré-preenchido com dados atuais
- [ ] Campos editáveis:
  - Nome da pasta
  - Descrição
- [ ] NÃO é possível mover pasta (mudar parent_folder_id) nesta US (feature futura)
- [ ] Nome deve ser único no mesmo nível
- [ ] Mensagem de sucesso: "Pasta [Nome] atualizada com sucesso"
- [ ] Árvore de pastas atualiza automaticamente

**Técnico:**
- [ ] Endpoint: `PUT /api/v1/folders/{folder_id}`
- [ ] Payload:
  ```json
  {
    "name": "string",
    "description": "string|null"
  }
  ```
- [ ] Resposta: 200 OK com dados atualizados
- [ ] Validações server-side:
  - Nome não vazio (mínimo 3 caracteres)
  - Nome único no mesmo nível (exceto a própria pasta)
  - Usuário tem permissão (Admin de Grupo ou Editor que criou)
- [ ] Log de edição: `user_id`, `folder_id`, `changed_fields`, `timestamp`
- [ ] Cache de árvore de pastas invalidado

**Permissões:**
- [ ] Admin de Grupo: pode editar qualquer pasta do grupo
- [ ] Editor: pode editar apenas pastas que criou
- [ ] Super Admin: pode editar qualquer pasta

**UX:**
- [ ] Validação em tempo real (nome único)
- [ ] Loading indicator ao salvar
- [ ] Modal fecha automaticamente após sucesso

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-2.1.2

---

### US-2.1.4: Deletar Pasta Vazia (Admin de Grupo)

**Como** Admin de Grupo,  
**Quero** deletar pastas vazias,  
**Para** manter estrutura organizacional limpa.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Deletar" (ícone de lixeira) visível apenas para Admin de Grupo
- [ ] Botão "Deletar" habilitado apenas para pastas vazias (sem documentos e sem subpastas)
- [ ] Modal de confirmação:
  - Mensagem: "Tem certeza que deseja deletar a pasta [Nome]?"
  - Aviso: "Esta ação não pode ser desfeita."
  - Botões: "Cancelar" e "Confirmar Exclusão"
- [ ] Ao confirmar, pasta é deletada
- [ ] Mensagem de sucesso: "Pasta [Nome] deletada com sucesso"
- [ ] Árvore de pastas atualiza automaticamente

**Técnico:**
- [ ] Endpoint: `DELETE /api/v1/folders/{folder_id}`
- [ ] Resposta: 204 No Content
- [ ] Validações server-side:
  - Pasta não contém documentos (COUNT documents WHERE folder_id = 0)
  - Pasta não contém subpastas (COUNT folders WHERE parent_folder_id = 0)
  - Usuário é Admin de Grupo ou Super Admin
- [ ] Se pasta contém documentos ou subpastas: retorna 409 Conflict com mensagem clara
  - "Não é possível deletar pasta com documentos. Mova ou delete os documentos primeiro."
  - "Não é possível deletar pasta com subpastas. Delete as subpastas primeiro."
- [ ] DELETE em cascata configurado no schema (mas validação impede)
- [ ] Log de deleção: `user_id`, `folder_id`, `folder_name`, `timestamp`
- [ ] Cache invalidado

**UX:**
- [ ] Botão desabilitado com tooltip explicativo se pasta não estiver vazia
- [ ] Confirmação clara antes da ação
- [ ] Loading indicator durante deleção
- [ ] Feedback visual imediato (pasta desaparece da árvore)

**Prioridade:** Baixa  
**Estimativa:** 3 pontos  
**Dependências:** US-2.1.2

---

## 2.2 Criação de Documentos

### US-2.2.1: Criar Documento em Branco (Editor)

**Como** Editor,  
**Quero** criar um documento em branco,  
**Para** começar a escrever novo conteúdo do zero.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Novo Documento" visível no dashboard e na página do grupo
- [ ] Click abre modal de seleção:
  - Opção: "Em branco" (ícone de página vazia)
  - Opção: "A partir de template" (ícone de template)
  - Opção: "Upload de arquivo" (ícone de upload)
- [ ] Ao selecionar "Em branco", modal de configuração inicial aparece:
  - Título do documento (obrigatório)
  - Grupo (dropdown - pré-selecionado se vier da página do grupo)
  - Pasta (dropdown hierárquico - opcional)
  - Tags (campo livre, separadas por vírgula - opcional)
  - Categoria (dropdown de categorias pré-definidas - opcional)
- [ ] Botão "Criar Documento" cria documento e abre editor
- [ ] Documento criado em status DRAFT
- [ ] Mensagem de boas-vindas: "Documento criado! Comece a escrever..."
- [ ] Auto-save ativado automaticamente

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents`
- [ ] Payload:
  ```json
  {
    "title": "string",
    "group_id": 1,
    "folder_id": 5,
    "tags": ["política", "rh"],
    "category_id": 3,
    "content": ""  // Vazio inicialmente
  }
  ```
- [ ] Resposta: 201 Created com ID do documento
- [ ] Validações server-side:
  - Título não vazio (mínimo 3 caracteres)
  - Título único dentro do grupo/pasta (validação flexível ou permitir duplicados?)
  - group_id existe e usuário tem papel de Editor
  - folder_id (se fornecido) existe e pertence ao grupo
  - category_id (se fornecido) existe
  - Tags são strings válidas (sem caracteres especiais maliciosos)
- [ ] Schema de banco:
  ```sql
  CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,  -- Markdown
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by INTEGER REFERENCES users(id),
    locked_by INTEGER REFERENCES users(id),  -- Para lock de edição
    locked_at TIMESTAMP,
    version INTEGER DEFAULT 1,
    published_version_id INTEGER REFERENCES document_versions(id)
  );
  
  CREATE TABLE document_tags (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    PRIMARY KEY (document_id, tag)
  );
  
  CREATE INDEX idx_documents_group ON documents(group_id);
  CREATE INDEX idx_documents_folder ON documents(folder_id);
  CREATE INDEX idx_documents_status ON documents(status);
  CREATE INDEX idx_documents_created_by ON documents(created_by);
  ```
- [ ] Ao criar documento, registrar em `documents` e `document_tags`
- [ ] Log de criação: `user_id`, `document_id`, `timestamp`
- [ ] Redireciona para página do editor: `/documents/{document_id}/edit`

**Status Inicial:**
- [ ] Status: `draft`
- [ ] Content: vazio
- [ ] Version: 1
- [ ] locked_by: NULL (não locado inicialmente)

**UX:**
- [ ] Modal de criação com etapas claras
- [ ] Campos obrigatórios marcados com *
- [ ] Autocomplete para tags (sugerir tags existentes)
- [ ] Dropdown de categorias organizado
- [ ] Preview do título em tempo real
- [ ] Loading indicator ao criar
- [ ] Transição suave para o editor

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-2.1.1

---

### US-2.2.2: Criar Documento a partir de Template (Editor)

**Como** Editor,  
**Quero** criar documento a partir de um template,  
**Para** economizar tempo usando estrutura pré-definida.

#### Critérios de Aceitação

**Funcional:**
- [ ] Ao selecionar "A partir de template" no modal de criação
- [ ] Lista de templates globais é exibida com:
  - Nome do template
  - Descrição
  - Preview (primeiros parágrafos do conteúdo)
  - Autor que criou
  - Data de criação
- [ ] Busca de templates por nome ou descrição
- [ ] Ao selecionar template, modal de configuração aparece (igual US-2.2.1):
  - Título do documento
  - Grupo
  - Pasta
  - Tags
  - Categoria
- [ ] Botão "Criar a partir deste Template"
- [ ] Documento criado em DRAFT com conteúdo do template pré-preenchido
- [ ] Editor abre com conteúdo do template
- [ ] Mensagem: "Documento criado a partir do template [Nome]. Edite conforme necessário."

**Técnico:**
- [ ] Endpoint para listar templates: `GET /api/v1/templates`
- [ ] Resposta:
  ```json
  {
    "templates": [
      {
        "id": 1,
        "name": "Política de Férias",
        "description": "Template padrão para políticas de férias",
        "content_preview": "# Política de Férias\n\n## Objetivo...",
        "created_by": "João Silva",
        "created_at": "ISO8601"
      }
    ]
  }
  ```
- [ ] Endpoint de criação: `POST /api/v1/documents` (mesmo da US-2.2.1)
- [ ] Payload adicional:
  ```json
  {
    "title": "string",
    "group_id": 1,
    "folder_id": 5,
    "template_id": 3,  // Template a usar
    "tags": [],
    "category_id": null
  }
  ```
- [ ] Validações:
  - template_id existe
  - Usuário tem acesso ao template (templates são globais)
- [ ] Ao criar documento:
  - Copiar `content` do template para o novo documento
  - Copiar tags padrão do template (se houver)
  - Setar `created_from_template_id` (para rastreamento)
- [ ] Schema adicional:
  ```sql
  ALTER TABLE documents 
  ADD COLUMN created_from_template_id INTEGER REFERENCES templates(id);
  ```
- [ ] Log de criação incluindo template usado

**Templates Schema:**
```sql
CREATE TABLE templates (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  description TEXT,
  content TEXT NOT NULL,  -- Markdown
  default_tags JSONB,  -- ["política", "rh"]
  default_category_id INTEGER REFERENCES categories(id),
  created_at TIMESTAMP DEFAULT NOW(),
  created_by INTEGER REFERENCES users(id),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**UX:**
- [ ] Cards de templates com preview visual
- [ ] Botão "Preview Completo" abre modal com conteúdo completo do template
- [ ] Busca com debounce
- [ ] Loading indicator ao carregar templates
- [ ] Indicador de template usado no documento (badge "Criado a partir de: [Template]")

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-2.2.1, US-2.6.1

---

### US-2.2.3: Navegar para Criar Documento via Upload

**Como** Editor,  
**Quero** selecionar a opção de criar documento via upload,  
**Para** converter arquivos existentes em documentos Markdown.

#### Critérios de Aceitação

**Funcional:**
- [ ] Ao selecionar "Upload de arquivo" no modal de criação
- [ ] Interface de upload é exibida:
  - Área de drag & drop (arrastar arquivo)
  - Botão "Selecionar Arquivo"
  - Texto: "Formatos suportados: PDF, DOCX, HTML, TXT, MD" (conforme Docling)
  - Texto: "Tamanho máximo: 100 MB"
- [ ] Ao selecionar arquivo, validação client-side:
  - Formato suportado
  - Tamanho < 100 MB
- [ ] Se validação OK, modal de configuração aparece (igual US-2.2.1):
  - Título (pré-preenchido com nome do arquivo sem extensão)
  - Grupo
  - Pasta
  - Tags
  - Categoria
- [ ] Botão "Criar e Converter Documento"
- [ ] Documento criado em status NEW
- [ ] Mensagem: "Documento criado! Conversão em andamento..."
- [ ] SSE conectado para receber atualizações de status
- [ ] Loading indicator com barra de progresso (indeterminado)
- [ ] Quando conversão concluir: redirecionado para editor (status → DRAFT)
- [ ] Se conversão falhar: redirecionado para página de erro (status → ERROR)

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/upload`
- [ ] Content-Type: `multipart/form-data`
- [ ] Payload:
  ```
  file: [binary]
  title: "string"
  group_id: 1
  folder_id: 5
  tags: ["tag1", "tag2"]
  category_id: 3
  ```
- [ ] Resposta: 201 Created com ID do documento e status NEW
- [ ] Validações server-side:
  - Arquivo presente
  - Tamanho < 100 MB (configurável)
  - Formato suportado (validar extensão e MIME type)
  - Título, group_id, folder_id válidos
- [ ] Fluxo de processamento:
  1. Salvar arquivo original em S3/storage: `/uploads/{group_id}/{document_id}/original.{ext}`
  2. Criar registro em `documents` com status='new'
  3. Adicionar job na fila de conversão (Celery queue)
  4. Retornar resposta 201 imediatamente
- [ ] Job de conversão (worker assíncrono):
  1. Atualizar status → 'processing'
  2. Chamar Docling para conversão
  3. Se sucesso: 
     - Salvar conteúdo Markdown em `documents.content`
     - Atualizar status → 'draft'
     - Emitir evento SSE: `{type: 'status_change', status: 'draft'}`
  4. Se falha (após 3 tentativas):
     - Atualizar status → 'error'
     - Salvar erro em `documents.conversion_error`
     - Emitir evento SSE: `{type: 'status_change', status: 'error', error: 'message'}`
- [ ] Schema adicional:
  ```sql
  ALTER TABLE documents 
  ADD COLUMN original_file_url VARCHAR(500),
  ADD COLUMN original_file_name VARCHAR(255),
  ADD COLUMN original_file_size BIGINT,
  ADD COLUMN conversion_attempts INTEGER DEFAULT 0,
  ADD COLUMN conversion_error TEXT;
  ```

**SSE Endpoint:**
- [ ] `GET /api/v1/documents/{document_id}/status-stream`
- [ ] Eventos emitidos:
  ```
  event: status_change
  data: {"status": "processing", "timestamp": "ISO8601"}
  
  event: status_change
  data: {"status": "draft", "timestamp": "ISO8601"}
  
  event: status_change
  data: {"status": "error", "error": "Conversão falhou", "timestamp": "ISO8601"}
  ```

**UX:**
- [ ] Drag & drop com visual claro (borda tracejada, ícone de upload)
- [ ] Preview do arquivo selecionado (nome, tamanho, tipo)
- [ ] Validação em tempo real (arquivo muito grande, formato não suportado)
- [ ] Barra de progresso durante upload (se arquivo grande)
- [ ] Loading indicator durante conversão com mensagem: "Convertendo documento... Isso pode levar alguns minutos."
- [ ] SSE conectado automaticamente após criação
- [ ] Botão "Cancelar" durante conversão (cancela job e deleta documento)
- [ ] Mensagem de erro clara se conversão falhar com opções: "Tentar novamente" ou "Deletar"

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-2.2.1, ÉPICO 3 (Conversão)

---

## 2.3 Visualização de Documentos

### US-2.3.1: Visualizar Lista de Documentos (Todos os Usuários)

**Como** usuário com acesso ao grupo,  
**Quero** visualizar lista de documentos,  
**Para** encontrar e acessar documentos relevantes.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Documentos" exibe tabela/cards com documentos do grupo
- [ ] Filtro por pasta (sidebar com árvore de pastas - já implementado em US-2.1.2)
- [ ] Colunas/campos exibidos:
  - Título do documento
  - Status (badge colorido: DRAFT=amarelo, PUBLISHED=verde, etc.)
  - Autor
  - Última modificação (data e hora)
  - Tags (badges)
  - Categoria
  - Ações (Ver, Editar, Deletar - conforme permissões)
- [ ] Paginação: 25 documentos por página (configurável: 10, 25, 50, 100)
- [ ] Ordenação por coluna: Título, Data de modificação, Autor, Status
- [ ] Filtros avançados (painel lateral ou dropdown):
  - Status (DRAFT, PUBLISHED, PENDING_APPROVAL, etc.)
  - Autor (autocomplete)
  - Tags (múltipla seleção)
  - Categoria (dropdown)
  - Data de criação (range)
  - Data de modificação (range)
- [ ] Busca rápida por título (campo no topo)
- [ ] View switcher: Tabela ou Cards (toggle)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/groups/{group_id}/documents`
- [ ] Query params:
  ```
  ?folder_id=5
  &page=1
  &per_page=25
  &sort_by=updated_at
  &sort_order=desc
  &search=política
  &status=draft,published
  &author_id=3
  &tags=rh,férias
  &category_id=2
  &created_after=2024-01-01
  &created_before=2024-12-31
  &updated_after=2024-06-01
  &updated_before=2024-12-31
  ```
- [ ] Resposta:
  ```json
  {
    "documents": [
      {
        "id": 1,
        "title": "Política de Férias 2024",
        "status": "published",
        "author": {
          "id": 3,
          "name": "João Silva"
        },
        "folder": {
          "id": 5,
          "name": "Políticas",
          "path": "RH > Políticas"
        },
        "tags": ["política", "férias", "rh"],
        "category": {
          "id": 2,
          "name": "Políticas Internas"
        },
        "created_at": "ISO8601",
        "updated_at": "ISO8601",
        "version": 2
      }
    ],
    "total": 230,
    "page": 1,
    "per_page": 25,
    "total_pages": 10
  }
  ```
- [ ] Autorização: Usuário vê apenas documentos de grupos aos quais pertence
- [ ] Filtros aplicados via WHERE clauses
- [ ] Tags filtradas via JOIN com `document_tags`
- [ ] Query otimizada com INDEXes apropriados
- [ ] Cache de resultados (Redis) por 2 minutos, invalidar ao criar/editar documento

**Cores de Status (Badges):**
- [ ] DRAFT: Amarelo (#FCD34D)
- [ ] PENDING_APPROVAL: Laranja (#FB923C)
- [ ] CHANGES_REQUESTED: Vermelho (#F87171)
- [ ] APPROVED: Azul (#60A5FA)
- [ ] PUBLISHED: Verde (#34D399)
- [ ] DEPRECATED: Cinza (#9CA3AF)
- [ ] ARCHIVED: Cinza escuro (#6B7280)
- [ ] ERROR: Vermelho escuro (#DC2626)

**UX:**
- [ ] Loading skeleton durante carregamento
- [ ] Estado vazio: "Nenhum documento encontrado nesta pasta" (com ilustração)
- [ ] Filtros colapsáveis (accordion)
- [ ] Badge de quantidade de filtros ativos: "Filtros (3)"
- [ ] Botão "Limpar Filtros"
- [ ] Highlight de linha ao hover
- [ ] Click na linha abre documento (view mode)
- [ ] Ícones de ação (olho=ver, lápis=editar, lixeira=deletar)
- [ ] Tooltips em ícones
- [ ] Indicador visual de documento "locked" (se alguém estiver editando)

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-2.2.1

---

### US-2.3.2: Visualizar Documento (Modo Leitura)

**Como** usuário com acesso ao documento,  
**Quero** visualizar conteúdo do documento,  
**Para** ler informações sem editar.

#### Critérios de Aceitação

**Funcional:**
- [ ] Click no título ou botão "Ver" abre documento em modo leitura
- [ ] Página de visualização exibe:
  - **Header:**
    - Título do documento
    - Status (badge)
    - Breadcrumb: "Grupo > Pasta > Documento"
    - Versão atual (ex: "v2.1")
  - **Metadados (sidebar ou topo):**
    - Autor
    - Data de criação
    - Última modificação
    - Tags (clicáveis para filtrar outros docs)
    - Categoria
    - Documentos relacionados ("Ver também")
  - **Conteúdo:**
    - Markdown renderizado como HTML
    - Formatação rica (headers, listas, tabelas, código, imagens)
    - Links clicáveis
    - Imagens carregadas
  - **Ações (toolbar):**
    - Botão "Editar" (se usuário tiver permissão)
    - Botão "Histórico de Versões"
    - Botão "Exportar" (PDF, DOCX - feature futura)
    - Botão "Compartilhar" (gerar link - feature futura)
    - Botão "Imprimir"
- [ ] Se documento tem versão PUBLISHED anterior, aviso no topo: "⚠️ Esta é a versão em rascunho. Ver versão publicada: [link]"
- [ ] Se documento está DEPRECATED, aviso no topo: "⚠️ OBSOLETO - Este documento não deve ser usado como referência. Ver documento atualizado: [link]"
- [ ] Comentários visíveis (se houver) em sidebar ou inline (feature do Épico 5)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/documents/{document_id}`
- [ ] Resposta:
  ```json
  {
    "id": 1,
    "title": "Política de Férias 2024",
    "content": "# Política de Férias\n\n## Objetivo...",
    "status": "published",
    "version": 2,
    "author": {
      "id": 3,
      "name": "João Silva",
      "email": "joao@empresa.com"
    },
    "group": {
      "id": 1,
      "name": "RH"
    },
    "folder": {
      "id": 5,
      "name": "Políticas",
      "path": "RH > Políticas"
    },
    "tags": ["política", "férias", "rh"],
    "category": {
      "id": 2,
      "name": "Políticas Internas"
    },
    "related_documents": [
      {
        "id": 10,
        "title": "Política de Ponto",
        "url": "/documents/10"
      }
    ],
    "created_at": "ISO8601",
    "updated_at": "ISO8601",
    "published_version_id": 5,  // Se houver versão publicada diferente
    "deprecated_by": {  // Se DEPRECATED
      "document_id": 20,
      "title": "Política de Férias 2025"
    }
  }
  ```
- [ ] Autorização: Usuário deve ter acesso ao grupo
- [ ] Renderização Markdown server-side ou client-side (library: marked.js, react-markdown)
- [ ] Sanitização de HTML (prevenir XSS) se renderizar client-side
- [ ] Imagens no Markdown referenciadas via URL absoluta ou S3
- [ ] Syntax highlighting para blocos de código (library: Prism.js, highlight.js)

**Markdown Rendering:**
- [ ] Headers (H1-H6)
- [ ] Listas (ordered, unordered, checklists)
- [ ] Tabelas
- [ ] Blocos de código com syntax highlighting
- [ ] Imagens (inline e blocos)
- [ ] Links (internos e externos)
- [ ] Citações (blockquotes)
- [ ] Texto formatado (bold, italic, strikethrough)
- [ ] Linhas horizontais

**UX:**
- [ ] Loading skeleton durante carregamento
- [ ] Layout responsivo (leitura confortável)
- [ ] Tipografia otimizada para leitura (fonte serifada para corpo?)
- [ ] Breadcrumb clicável
- [ ] Botões de ação claramente visíveis
- [ ] Aviso de DEPRECATED com destaque visual (borda vermelha, background amarelo)
- [ ] Links de "Ver também" abrem em nova aba (ou modal preview)
- [ ] Scroll suave para âncoras internas

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-2.3.1

---

## 2.4 Edição de Documentos

### US-2.4.1: Editar Documento DRAFT com Lock de Edição (Editor)

**Como** Editor,  
**Quero** editar documento em DRAFT,  
**Para** criar e atualizar conteúdo antes de enviar para aprovação.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar" visível apenas para usuários com permissão (Editor que criou ou Admin)
- [ ] Ao clicar "Editar" em documento DRAFT:
  - Verificar se documento já está locked por outro usuário
  - Se locked: exibir mensagem "Documento em edição por [Nome do Usuário] desde [HH:MM]"
  - Se não locked: aplicar lock e abrir editor
- [ ] Editor Markdown exibido com conteúdo atual
- [ ] Toolbar do editor com ações:
  - Bold, Italic, Strikethrough
  - Headers (H1-H6)
  - Lista ordenada, Lista não ordenada
  - Link, Imagem
  - Código inline, Bloco de código
  - Citação
  - Tabela
  - Linha horizontal
- [ ] Painel lateral com metadados editáveis:
  - Título
  - Tags
  - Categoria
  - Documentos relacionados
- [ ] Auto-save a cada 1 minuto (configurável)
- [ ] Indicador de auto-save: "Salvando..." → "Salvo às HH:MM:SS"
- [ ] Botão "Preview" abre modal com renderização Markdown
- [ ] Botão "Salvar e Fechar" (salva e volta para lista)
- [ ] Botão "Cancelar" (volta sem salvar - confirma se há mudanças não salvas)
- [ ] Botão "Enviar para Revisão" (transição para PENDING_APPROVAL - feature do Épico 4)
- [ ] Lock é liberado ao:
  - Usuário clicar "Salvar e Fechar"
  - Usuário clicar "Cancelar"
  - Timeout de inatividade (30 minutos sem interação)
  - Usuário fechar navegador (heartbeat via SSE/WebSocket)

**Técnico:**
- [ ] Endpoint de lock: `POST /api/v1/documents/{document_id}/lock`
- [ ] Resposta: 200 OK ou 409 Conflict (se já locked)
- [ ] Ao adquirir lock:
  - UPDATE documents SET locked_by={user_id}, locked_at=NOW() WHERE id={document_id} AND locked_by IS NULL
  - Se UPDATE afetou 0 linhas: documento já locked (race condition)
  - Retornar 409 com info de quem está editando
- [ ] Heartbeat: `POST /api/v1/documents/{document_id}/heartbeat` a cada 30 segundos
  - Atualiza locked_at=NOW()
  - Se falhar (conexão perdida), lock expira após 30 min
- [ ] Job de limpeza (cron): libera locks com locked_at > 30 min
- [ ] Endpoint de unlock: `POST /api/v1/documents/{document_id}/unlock`
  - UPDATE documents SET locked_by=NULL, locked_at=NULL WHERE id={document_id} AND locked_by={user_id}
- [ ] Endpoint de auto-save: `PATCH /api/v1/documents/{document_id}`
  - Payload:
    ```json
    {
      "content": "string",
      "title": "string",
      "tags": ["tag1"],
      "category_id": 3,
      "related_document_ids": [5, 10]
    }
    ```
  - Validações:
    - Documento está locked pelo usuário atual
    - Documento em status DRAFT (não pode editar PUBLISHED diretamente - ver US-2.4.2)
  - Atualiza updated_at=NOW(), updated_by={user_id}
- [ ] WebSocket/SSE para notificar outros usuários se tentarem abrir documento locked

**Lock Management:**
```sql
-- Verificar se pode adquirir lock
SELECT locked_by, locked_at 
FROM documents 
WHERE id = $1 
FOR UPDATE;

-- Adquirir lock
UPDATE documents 
SET locked_by = $1, locked_at = NOW() 
WHERE id = $2 AND locked_by IS NULL;

-- Heartbeat
UPDATE documents 
SET locked_at = NOW() 
WHERE id = $1 AND locked_by = $2;

-- Liberar lock
UPDATE documents 
SET locked_by = NULL, locked_at = NULL 
WHERE id = $1 AND locked_by = $2;

-- Limpar locks expirados (cron job)
UPDATE documents 
SET locked_by = NULL, locked_at = NULL 
WHERE locked_at < NOW() - INTERVAL '30 minutes';
```

**Editor Markdown:**
- [ ] Library: SimpleMDE, Toast UI Editor, ou custom (Monaco Editor)
- [ ] Split view opcional: Editor | Preview lado a lado
- [ ] Syntax highlighting para código
- [ ] Upload de imagens (drag & drop ou botão)
  - Salvar em S3: `/documents/{document_id}/images/{filename}`
  - Inserir URL no Markdown: `![alt text](https://cdn.com/path/image.png)`
- [ ] Autocomplete para links internos (buscar outros documentos)
- [ ] Atalhos de teclado (Ctrl+B = bold, Ctrl+I = italic, etc.)

**UX:**
- [ ] Loading skeleton ao carregar editor
- [ ] Indicador visual de lock ativo (cadeado verde no topo)
- [ ] Contador de palavras/caracteres (opcional)
- [ ] Scroll sync entre editor e preview (se split view)
- [ ] Confirmação ao sair com mudanças não salvas ("Você tem alterações não salvas. Deseja salvar antes de sair?")
- [ ] Notificação toast ao auto-save ("Salvo automaticamente")
- [ ] Ícone de loading durante auto-save
- [ ] Breadcrumb clicável no topo
- [ ] Toolbar fixa ao scroll (sticky)

**Prioridade:** Crítica  
**Estimativa:** 13 pontos  
**Dependências:** US-2.3.2

---

### US-2.4.2: Editar Documento PUBLISHED (Cria Nova Versão)

**Como** Editor ou Admin,  
**Quero** editar documento PUBLISHED,  
**Para** atualizar conteúdo e criar nova versão.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar" visível em documento PUBLISHED
- [ ] Ao clicar "Editar", modal de confirmação:
  - Mensagem: "Este documento está publicado. Ao editar, uma nova versão será criada."
  - Informação: "Versão atual: v2.1 (publicada em DD/MM/YYYY)"
  - Informação: "Nova versão: v2.2 (rascunho)"
  - Checkbox: "☐ Despublicar versão atual" (opcional)
  - Botões: "Cancelar" e "Criar Nova Versão e Editar"
- [ ] Ao confirmar:
  - Sistema cria nova versão do documento em DRAFT
  - Versão anterior permanece PUBLISHED (ou despublicada se checkbox marcado)
  - Novo DRAFT é uma cópia completa do PUBLISHED (conteúdo, metadados, tags)
  - Número de versão incrementado (v2.1 → v2.2)
  - Editor abre com novo DRAFT
- [ ] Mensagem: "Nova versão v2.2 criada. Versão v2.1 continua publicada."
- [ ] Todas as funcionalidades de edição aplicam (igual US-2.4.1)
- [ ] Link para "Ver versão publicada" visível no editor

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/create-draft-version`
- [ ] Payload:
  ```json
  {
    "unpublish_current": false
  }
  ```
- [ ] Resposta: 201 Created com ID da nova versão
- [ ] Fluxo de versionamento:
  1. Inserir em `document_versions` a versão PUBLISHED atual (snapshot)
  2. Criar novo registro em `documents` com:
     - Mesmo title, content, tags, etc. (cópia)
     - status='draft'
     - version=incrementado (2.2)
     - parent_version_id={id do published}
     - created_by={current_user}
  3. Se `unpublish_current=true`:
     - UPDATE documento PUBLISHED: status='draft'
  4. Retornar novo document_id
- [ ] Schema de versionamento:
  ```sql
  CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,  -- "1.0", "2.1", etc.
    title VARCHAR(500) NOT NULL,
    content TEXT,
    status VARCHAR(50) NOT NULL,
    tags JSONB,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP NOT NULL,
    created_by INTEGER REFERENCES users(id),
    published_at TIMESTAMP,
    is_current_published BOOLEAN DEFAULT FALSE,
    UNIQUE(document_id, version)
  );
  
  CREATE INDEX idx_doc_versions_document ON document_versions(document_id);
  CREATE INDEX idx_doc_versions_current ON document_versions(document_id, is_current_published);
  ```
- [ ] Estratégia de versionamento:
  - Versão major.minor: 1.0, 1.1, 2.0
  - Incremento minor ao criar draft de published: 2.1 → 2.2
  - Incremento major ao fazer grandes mudanças (opcional/manual)
- [ ] Log de criação de versão: `user_id`, `document_id`, `new_version`, `parent_version_id`, `timestamp`

**Alternativa: Despublicar**
- [ ] Botão "Despublicar" separado (não ao editar)
- [ ] Modal de confirmação: "Tem certeza que deseja despublicar este documento? Ele voltará para rascunho."
- [ ] Ao confirmar: UPDATE status='draft', published_at=NULL
- [ ] Apenas Admin de Grupo e Super Admin podem despublicar

**UX:**
- [ ] Modal de confirmação clara com preview das versões
- [ ] Indicador de versão no editor (badge "Editando v2.2 (rascunho)")
- [ ] Link "Ver versão publicada v2.1" abre em nova aba
- [ ] Aviso persistente: "Esta é uma nova versão. A versão publicada continua disponível."
- [ ] Breadcrumb inclui versão: "Grupo > Pasta > Documento > v2.2 (rascunho)"

**Prioridade:** Alta  
**Estimativa:** 8 pontos  
**Dependências:** US-2.4.1, Épico 6 (Versionamento)

---

## 2.5 Metadados e Organização

### US-2.5.1: Adicionar e Editar Tags em Documento

**Como** Editor,  
**Quero** adicionar e editar tags em documentos,  
**Para** facilitar organização e busca.

#### Critérios de Aceitação

**Funcional:**
- [ ] Campo "Tags" visível no editor e no modal de criação de documento
- [ ] Tags são inseridas como texto livre, separadas por vírgula ou Enter
- [ ] Autocomplete sugere tags já existentes no sistema (busca incremental)
- [ ] Ao digitar tag nova (não existe), criar automaticamente
- [ ] Tags exibidas como badges removíveis (X para remover)
- [ ] Limite de 20 tags por documento
- [ ] Tags convertidas para lowercase e sem espaços extras (normalização)
- [ ] Tags são case-insensitive ("RH" = "rh")
- [ ] Auto-save aplica ao adicionar/remover tags

**Técnico:**
- [ ] Endpoint para autocomplete: `GET /api/v1/tags/search?q=féri`
- [ ] Resposta:
  ```json
  {
    "tags": ["férias", "feriados", "período de férias"]
  }
  ```
- [ ] Query de busca:
  ```sql
  SELECT DISTINCT tag 
  FROM document_tags 
  WHERE tag ILIKE $1 || '%'
  ORDER BY tag
  LIMIT 10;
  ```
- [ ] Ao salvar documento, tags são armazenadas em `document_tags`:
  - DELETE FROM document_tags WHERE document_id={id}
  - INSERT INTO document_tags (document_id, tag) VALUES ({id}, {tag}) para cada tag
- [ ] Normalização de tags:
  ```python
  def normalize_tag(tag: str) -> str:
      return tag.strip().lower()
  ```
- [ ] Validações:
  - Tag não vazia
  - Tag com máximo 100 caracteres
  - Sem caracteres especiais maliciosos (sanitização)
  - Máximo 20 tags por documento

**UX:**
- [ ] Input de tags com chips (React TagInput, ou similar)
- [ ] Autocomplete dropdown abaixo do input
- [ ] Tags coloridas (cores aleatórias mas consistentes por tag)
- [ ] Click na tag na lista de documentos filtra por essa tag
- [ ] Indicador de limite: "10/20 tags"

**Prioridade:** Média  
**Estimativa:** 5 pontos  
**Dependências:** US-2.4.1

---

### US-2.5.2: Associar Categoria ao Documento

**Como** Editor,  
**Quero** associar categoria ao documento,  
**Para** classificar documentos em tipos pré-definidos.

#### Critérios de Aceitação

**Funcional:**
- [ ] Campo "Categoria" visível no editor e no modal de criação
- [ ] Dropdown com categorias pré-definidas
- [ ] Categorias organizadas hierarquicamente (opcional: categoria pai > subcategoria)
- [ ] Apenas 1 categoria por documento
- [ ] Categoria é opcional (pode ser NULL)
- [ ] Super Admin pode criar novas categorias (US separada)
- [ ] Auto-save aplica ao mudar categoria

**Técnico:**
- [ ] Endpoint para listar categorias: `GET /api/v1/categories`
- [ ] Resposta:
  ```json
  {
    "categories": [
      {
        "id": 1,
        "name": "Políticas Internas",
        "parent_id": null
      },
      {
        "id": 2,
        "name": "Benefícios",
        "parent_id": 1
      }
    ]
  }
  ```
- [ ] Schema de categorias:
  ```sql
  CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    UNIQUE(name)
  );
  ```
- [ ] Documento referencia categoria via `category_id` (foreign key)
- [ ] Se categoria for deletada, documentos ficam com category_id=NULL (ON DELETE SET NULL)

**UX:**
- [ ] Dropdown com busca (searchable select)
- [ ] Categorias hierárquicas exibidas como "Políticas > Benefícios"
- [ ] Preview da categoria selecionada (descrição em tooltip)
- [ ] Botão "Limpar" para remover categoria

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-2.4.1

---

### US-2.5.3: Linkar Documentos Relacionados

**Como** Editor,  
**Quero** linkar documentos relacionados,  
**Para** criar referências cruzadas entre documentos.

#### Critérios de Aceitação

**Funcional:**
- [ ] Seção "Documentos Relacionados" no editor (sidebar ou aba)
- [ ] Botão "Adicionar Documento Relacionado"
- [ ] Modal de busca/seleção de documentos:
  - Busca por título
  - Filtro por grupo/pasta
  - Lista de resultados com título, grupo, pasta
  - Checkbox para selecionar múltiplos
- [ ] Documentos selecionados aparecem na lista de relacionados
- [ ] Botão "Remover" (X) em cada documento relacionado
- [ ] Limite de 10 documentos relacionados
- [ ] Relacionamento é unidirecional (Doc A aponta para Doc B, mas Doc B não aponta automaticamente para Doc A)
- [ ] Auto-save aplica ao adicionar/remover relacionados

**Técnico:**
- [ ] Schema de relacionamentos:
  ```sql
  CREATE TABLE document_relationships (
    source_document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'related',  -- Futuro: 'supersedes', 'referenced_by'
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    PRIMARY KEY (source_document_id, target_document_id),
    CHECK (source_document_id != target_document_id)  -- Não pode relacionar consigo mesmo
  );
  
  CREATE INDEX idx_relationships_source ON document_relationships(source_document_id);
  CREATE INDEX idx_relationships_target ON document_relationships(target_document_id);
  ```
- [ ] Endpoint de busca para relacionados: `GET /api/v1/documents/search?q=política&group_id=1`
- [ ] Ao salvar, relacionamentos são armazenados:
  - DELETE FROM document_relationships WHERE source_document_id={id}
  - INSERT para cada documento relacionado
- [ ] Validações:
  - target_document_id existe
  - Usuário tem acesso ao documento relacionado
  - Máximo 10 relacionamentos

**Visualização (Modo Leitura):**
- [ ] Seção "Ver também" exibe documentos relacionados como links clicáveis
- [ ] Click abre documento relacionado

**UX:**
- [ ] Modal de busca com autocomplete
- [ ] Preview do documento ao hover (título completo, descrição)
- [ ] Drag & drop para reordenar relacionados (opcional)
- [ ] Indicador de limite: "5/10 documentos"

**Prioridade:** Baixa  
**Estimativa:** 5 pontos  
**Dependências:** US-2.4.1

---

## 2.6 Templates de Documentos

### US-2.6.1: Criar Template de Documento (Admin Global, Admin de Grupo, Editor)

**Como** Admin Global, Admin de Grupo ou Editor,  
**Quero** criar templates de documentos,  
**Para** padronizar criação de documentos recorrentes.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Templates" acessível no menu principal
- [ ] Botão "Novo Template" abre formulário de criação
- [ ] Formulário contém campos:
  - Nome do template (obrigatório, único)
  - Descrição (obrigatório)
  - Conteúdo Markdown (obrigatório) - editor igual ao de documentos
  - Tags padrão (opcional) - pré-preencher ao criar doc a partir do template
  - Categoria padrão (opcional)
- [ ] Preview do template disponível
- [ ] Botão "Salvar Template"
- [ ] Mensagem de sucesso: "Template [Nome] criado com sucesso"
- [ ] Template fica disponível globalmente para todos os usuários

**Técnico:**
- [ ] Endpoint: `POST /api/v1/templates`
- [ ] Payload:
  ```json
  {
    "name": "Política de Férias",
    "description": "Template padrão para políticas de férias",
    "content": "# Política de Férias\n\n## Objetivo\n\n...",
    "default_tags": ["política", "rh"],
    "default_category_id": 2
  }
  ```
- [ ] Resposta: 201 Created com ID do template
- [ ] Validações:
  - Nome único
  - Nome não vazio (mínimo 3 caracteres)
  - Descrição não vazia
  - Conteúdo não vazio
  - Categoria existe (se fornecida)
- [ ] Schema já definido anteriormente:
  ```sql
  CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    content TEXT NOT NULL,
    default_tags JSONB,
    default_category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] Templates são globais (não pertencem a grupo específico)
- [ ] Log de criação: `user_id`, `template_id`, `timestamp`

**Quem pode criar:**
- [ ] Super Admin: sempre
- [ ] Admin de Grupo: sempre
- [ ] Editor: sempre (mas pode ser restrito no futuro)

**UX:**
- [ ] Editor Markdown com preview
- [ ] Validação em tempo real (nome único)
- [ ] Loading indicator ao salvar
- [ ] Breadcrumb: "Templates > Novo Template"

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-2.4.1

---

### US-2.6.2: Listar e Buscar Templates

**Como** usuário,  
**Quero** visualizar e buscar templates disponíveis,  
**Para** escolher template ao criar documento.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Templates" lista todos os templates
- [ ] Cards de templates exibem:
  - Nome
  - Descrição (truncada)
  - Autor que criou
  - Data de criação
  - Ações (Visualizar, Editar se tiver permissão, Deletar se Admin)
- [ ] Busca por nome ou descrição
- [ ] Ordenação: Nome (A-Z), Data de criação
- [ ] Click no card abre preview do template
- [ ] Botão "Usar Template" no preview cria documento a partir do template

**Técnico:**
- [ ] Endpoint: `GET /api/v1/templates` (já definido em US-2.2.2)
- [ ] Query params: `?search=política&sort_by=name&sort_order=asc`
- [ ] Resposta: lista de templates com metadados

**UX:**
- [ ] Cards com layout atraente
- [ ] Preview em modal ou sidebar
- [ ] Highlight de busca nos resultados
- [ ] Loading skeleton

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-2.6.1

---

### US-2.6.3: Editar Template (Criador ou Admin)

**Como** criador do template ou Admin,  
**Quero** editar templates,  
**Para** melhorar e atualizar conteúdo padrão.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar" visível apenas para criador ou Admin
- [ ] Modal/página de edição com mesmos campos da criação
- [ ] Ao salvar, template é atualizado
- [ ] Mensagem de sucesso: "Template atualizado"
- [ ] Documentos já criados a partir do template NÃO são afetados (snapshot)

**Técnico:**
- [ ] Endpoint: `PUT /api/v1/templates/{template_id}`
- [ ] Payload: mesmo da criação
- [ ] Validações: nome único (exceto o próprio)
- [ ] Log de edição

**Prioridade:** Baixa  
**Estimativa:** 3 pontos  
**Dependências:** US-2.6.2

---

### US-2.6.4: Deletar Template (Admin Global)

**Como** Admin Global,  
**Quero** deletar templates obsoletos,  
**Para** manter biblioteca de templates organizada.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Deletar" visível apenas para Admin Global
- [ ] Modal de confirmação
- [ ] Ao confirmar, template é deletado
- [ ] Documentos criados a partir do template NÃO são afetados
- [ ] Mensagem de sucesso: "Template deletado"

**Técnico:**
- [ ] Endpoint: `DELETE /api/v1/templates/{template_id}`
- [ ] Validações: apenas Super Admin
- [ ] ON DELETE SET NULL em documents.created_from_template_id (ou manter ID mesmo após deleção)
- [ ] Log de deleção

**Prioridade:** Baixa  
**Estimativa:** 2 pontos  
**Dependências:** US-2.6.2

---

## 2.7 Exclusão e Arquivamento

### US-2.7.1: Deletar Documento DRAFT (Editor ou Admin)

**Como** Editor que criou o documento ou Admin,  
**Quero** deletar documentos em DRAFT,  
**Para** remover rascunhos descartados.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Deletar" visível para documentos em status DRAFT
- [ ] Botão visível apenas para:
  - Editor que criou o documento
  - Admin de Grupo
  - Super Admin
- [ ] Modal de confirmação:
  - Mensagem: "Tem certeza que deseja deletar [Título]?"
  - Aviso: "Esta ação não pode ser desfeita."
  - Botões: "Cancelar" e "Confirmar Exclusão"
- [ ] Ao confirmar, documento é deletado permanentemente
- [ ] Mensagem de sucesso: "Documento deletado com sucesso"
- [ ] Lista de documentos atualiza automaticamente

**Técnico:**
- [ ] Endpoint: `DELETE /api/v1/documents/{document_id}`
- [ ] Validações:
  - Documento em status DRAFT (não pode deletar PUBLISHED diretamente)
  - Usuário tem permissão (criador, Admin de Grupo, Super Admin)
- [ ] DELETE em cascata:
  - document_tags
  - document_relationships
  - document_versions (se houver)
  - Arquivos relacionados em S3 (original_file_url, imagens)
- [ ] Log de deleção: `user_id`, `document_id`, `document_title`, `timestamp`

**Restrições:**
- [ ] Não pode deletar documento PUBLISHED (usar arquivamento)
- [ ] Não pode deletar documento PENDING_APPROVAL (rejeitar primeiro)

**UX:**
- [ ] Confirmação clara
- [ ] Loading indicator
- [ ] Feedback visual imediato

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-2.3.1

---

### US-2.7.2: Arquivar Documento PUBLISHED (Admin de Grupo)

**Como** Admin de Grupo,  
**Quero** arquivar documentos PUBLISHED,  
**Para** remover do repositório ativo mantendo histórico.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Arquivar" visível para documentos PUBLISHED
- [ ] Botão visível apenas para Admin de Grupo e Super Admin
- [ ] Modal de confirmação:
  - Mensagem: "Arquivar documento [Título]?"
  - Aviso: "O documento será removido das buscas e visualizações principais, mas permanecerá acessível em 'Arquivados'."
  - Botões: "Cancelar" e "Confirmar Arquivamento"
- [ ] Ao confirmar:
  - Documento status → ARCHIVED
  - Documento removido de buscas padrão
  - Disponível em aba/filtro "Arquivados"
- [ ] Mensagem de sucesso: "Documento arquivado"

**Técnico:**
- [ ] Endpoint: `PATCH /api/v1/documents/{document_id}/archive`
- [ ] Validações:
  - Documento em status PUBLISHED ou DEPRECATED
  - Usuário é Admin de Grupo ou Super Admin
- [ ] UPDATE: status='archived', archived_at=NOW(), archived_by={user_id}
- [ ] Schema adicional:
  ```sql
  ALTER TABLE documents 
  ADD COLUMN archived_at TIMESTAMP,
  ADD COLUMN archived_by INTEGER REFERENCES users(id);
  ```
- [ ] Query de listagem padrão filtra: WHERE status != 'archived'
- [ ] Endpoint separado para listar arquivados: `GET /api/v1/documents/archived`
- [ ] Log de arquivamento

**Visualização de Arquivados:**
- [ ] Aba "Arquivados" na lista de documentos
- [ ] Filtro visual (badge cinza escuro)
- [ ] Botão "Desarquivar" (restaura para DRAFT ou PUBLISHED?)

**UX:**
- [ ] Confirmação clara
- [ ] Indicador visual de documento arquivado

**Prioridade:** Baixa  
**Estimativa:** 3 pontos  
**Dependências:** US-2.3.1

---

## 📊 Resumo do Épico 2

### Estatísticas

- **Total de User Stories:** 21
- **Estimativa Total:** 113 pontos
- **Prioridade:** 1 (Crítico para MVP)

### Distribuição de Prioridades

- **Crítica:** 6 histórias (29%)
- **Alta:** 6 histórias (29%)
- **Média:** 6 histórias (29%)
- **Baixa:** 3 histórias (13%)

### Distribuição por Seção

1. **Gestão de Pastas:** 4 histórias (19 pontos)
2. **Criação de Documentos:** 3 histórias (18 pontos)
3. **Visualização de Documentos:** 2 histórias (16 pontos)
4. **Edição de Documentos:** 2 histórias (21 pontos)
5. **Metadados e Organização:** 3 histórias (13 pontos)
6. **Templates de Documentos:** 4 histórias (13 pontos)
7. **Exclusão e Arquivamento:** 2 histórias (6 pontos)

### Dependências Principais

```
US-1.3.1 (Criar Grupo)
  └── US-2.1.1 (Criar Pasta)
       └── US-2.1.2 (Listar Pastas)
            └── US-2.1.3 (Editar Pasta)
            └── US-2.1.4 (Deletar Pasta)
            └── US-2.2.1 (Criar Doc em Branco)
                 └── US-2.2.2 (Criar Doc de Template)
                 └── US-2.2.3 (Criar Doc via Upload)
                 └── US-2.3.1 (Listar Documentos)
                      └── US-2.3.2 (Visualizar Documento)
                           └── US-2.4.1 (Editar DRAFT)
                                └── US-2.4.2 (Editar PUBLISHED)
                                └── US-2.5.1 (Tags)
                                └── US-2.5.2 (Categorias)
                                └── US-2.5.3 (Relacionados)
                                └── US-2.6.1 (Criar Template)
                                     └── US-2.6.2 (Listar Templates)
                                          └── US-2.6.3 (Editar Template)
                                          └── US-2.6.4 (Deletar Template)
                           └── US-2.7.1 (Deletar DRAFT)
                           └── US-2.7.2 (Arquivar PUBLISHED)
```

### Checklist de Implementação

#### Sprint 6 - Gestão de Pastas
- [ ] US-2.1.1: Criar Pasta
- [ ] US-2.1.2: Listar Pastas em Árvore
- [ ] US-2.1.3: Editar Pasta
- [ ] US-2.1.4: Deletar Pasta Vazia

#### Sprint 7 - CRUD Documentos Básico
- [ ] US-2.2.1: Criar Documento em Branco
- [ ] US-2.3.1: Listar Documentos
- [ ] US-2.3.2: Visualizar Documento
- [ ] US-2.7.1: Deletar Documento DRAFT

#### Sprint 8 - Editor Markdown
- [ ] US-2.4.1: Editar Documento DRAFT com Lock
- [ ] US-2.5.1: Adicionar Tags
- [ ] US-2.5.2: Associar Categoria

#### Sprint 9 - Templates e Versionamento
- [ ] US-2.6.1: Criar Template
- [ ] US-2.6.2: Listar Templates
- [ ] US-2.2.2: Criar Doc a partir de Template
- [ ] US-2.4.2: Editar PUBLISHED (nova versão)

#### Sprint 10 - Features Avançadas
- [ ] US-2.5.3: Linkar Documentos Relacionados
- [ ] US-2.6.3: Editar Template
- [ ] US-2.6.4: Deletar Template
- [ ] US-2.7.2: Arquivar Documento
- [ ] US-2.2.3: Criar Doc via Upload (integra com Épico 3)

---

## 🎯 Próximos Passos

1. **Validação:** Revisar histórias com stakeholders
2. **Refinamento Técnico:** Definir biblioteca de editor Markdown (SimpleMDE vs Monaco vs Toast UI)
3. **Design:** Criar wireframes do editor e interfaces
4. **Desenvolvimento:** Iniciar Sprint 6 com gestão de pastas

---

**Épico preparado por:** Claude (Anthropic)  
**Revisão:** Pendente  
**Status:** Pronto para Desenvolvimento  
**Próximo Épico:** ÉPICO 3 - Conversão de Documentos

