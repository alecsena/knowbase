# Especificação Funcional - Sistema de Gestão de Documentos e Conhecimento

**Versão:** 1.0 MVP  
**Data:** Janeiro 2026  
**Objetivo:** Ferramenta de gestão de documentos e conhecimento com workflow de aprovação para posterior integração com RAG

---

## 📋 Sumário Executivo

Sistema de gestão de documentos baseado em Markdown com workflow de aprovação completo, versionamento, conversão de documentos, sistema de comentários e preparação para integração com RAG (Retrieval-Augmented Generation). O sistema organiza documentos em Grupos (equivalentes a setores) e Pastas, com controle granular de permissões baseado em papéis.

---

## 🎭 1. PERSONAS & PAPÉIS

### 1.1 Papéis Disponíveis

#### Super Admin (Administrador Global)
- **Escopo:** Toda a aplicação
- **Permissões:**
  - Criar e gerenciar Grupos
  - Criar usuários
  - Atribuir usuários aos Grupos com seus respectivos papéis
  - Mover documentos entre Grupos
  - Todas as permissões de Admin de Grupo em todos os Grupos

#### Admin de Grupo (Administrador de Grupo)
- **Escopo:** Grupo específico
- **Permissões:**
  - Criar e gerenciar Pastas dentro do Grupo
  - Adicionar e remover usuários do Grupo
  - Atribuir papéis aos usuários dentro do Grupo
  - Mover documentos entre Pastas do mesmo Grupo
  - Marcar documentos como DEPRECATED
  - Todas as permissões de Editor no Grupo

#### Revisor
- **Escopo:** Grupo específico
- **Permissões:**
  - Visualizar todos os documentos do Grupo (qualquer status)
  - Aprovar ou solicitar mudanças em documentos PENDING_APPROVAL
  - Adicionar comentários em trechos dos documentos
  - Marcar documentos como DEPRECATED
  - Marcar comentários como resolvidos

#### Editor
- **Escopo:** Grupo específico
- **Permissões:**
  - Criar documentos (em branco, upload ou template)
  - Criar e gerenciar Pastas dentro do Grupo
  - Editar documentos em DRAFT
  - Enviar documentos para aprovação (PENDING_APPROVAL)
  - Ver comentários de Revisores
  - Marcar comentários como resolvidos
  - Linkar documentos relacionados
  - Criar templates de documentos
  - Visualizar todos os documentos do Grupo

#### Reader (Leitor)
- **Escopo:** Grupo específico
- **Permissões:**
  - Visualizar documentos em QUALQUER status do Grupo (DRAFT, PENDING_APPROVAL, PUBLISHED, etc.)
  - Ver comentários de Revisores
  - **NÃO pode:** Adicionar comentários, editar, aprovar

### 1.2 Regras de Papéis

- ✅ Um usuário pode ter papéis diferentes em grupos diferentes
  - Exemplo: Editor no "RH" e Revisor no "TI"
- ✅ Um usuário pode ter múltiplos papéis no mesmo Grupo
  - Exemplo: Editor + Revisor no "RH"
- ✅ Super Admin tem poderes globais sobre todos os Grupos
- ✅ Admin de Grupo pode gerenciar usuários apenas do seu Grupo

### 1.3 Criação de Usuários

- **Quem cria:** Apenas Super Admin
- **Método:** NÃO há auto-registro
- **Processo:**
  1. Super Admin cria usuário
  2. Super Admin atribui usuário a um ou mais Grupos com papéis específicos
  3. Admin de Grupo pode adicionar/remover usuários posteriormente dentro do seu Grupo

---

## 📁 2. ESTRUTURA ORGANIZACIONAL

### 2.1 Hierarquia

```
Aplicação
├── Grupo (equivalente a setor - ex: "RH", "TI", "Financeiro")
│   ├── Pasta
│   │   ├── Documento
│   │   ├── Documento
│   │   └── ...
│   ├── Pasta
│   └── ...
├── Grupo
└── ...
```

### 2.2 Permissões de Criação

| Entidade | Quem pode criar |
|----------|-----------------|
| **Grupo** | Super Admin |
| **Pasta** | Admin de Grupo, Editor |
| **Documento** | Editor, Admin de Grupo, Super Admin |
| **Template** | Admin Global, Admin de Grupo, Editor |

### 2.3 Movimentação de Documentos

| Ação | Quem pode executar |
|------|-------------------|
| Mover documento entre Pastas (mesmo Grupo) | Admin de Grupo |
| Mover documento entre Grupos | Super Admin |

### 2.4 Escopo de Templates

- **Templates são GLOBAIS:** Disponíveis para todos os Grupos
- **Quem cria:** Admin Global, Admin de Grupo, Editor
- **Uso:** Ao criar documento, usuário escolhe entre:
  - "Em branco"
  - "Upload" (PDF, DOCX, etc.)
  - "A partir de template"

---

## 📄 3. CICLO DE VIDA DO DOCUMENTO

### 3.1 Diagrama de Estados

```
🆕 NEW (Criado, aguardando conversão se upload)
↓
⏳ PROCESSING (Conversão em andamento)
↓
✏️ DRAFT (Rascunho - em edição)
↓ (Editor clica "Enviar para revisão")
⏳ PENDING_APPROVAL (Aguardando aprovação)
├─→ 📝 CHANGES_REQUESTED (Revisor solicita mudanças)
│    ↓ (Editor edita e reenvia)
│    └─→ ⏳ PENDING_APPROVAL
│
└─→ ✅ APPROVED (Aprovado - vai para fila de publicação)
     ↓
     ✅ PUBLISHED (Publicado e visível)
     ├─→ ✏️ DRAFT (Despublicado manualmente)
     ├─→ ⚠️ DEPRECATED (Marcado como obsoleto)
     │    └─→ 📦 ARCHIVED (Arquivado)
     └─→ 📦 ARCHIVED (Arquivado diretamente)

❌ ERROR (Falha na conversão após 3 tentativas)
```

### 3.2 Descrição Detalhada dos Estados

#### 🆕 NEW
- **Quando ocorre:** Documento criado via upload de arquivo
- **Duração:** Instantâneo - transição automática para PROCESSING
- **Ações disponíveis:** Nenhuma (estado transitório)

#### ⏳ PROCESSING
- **Quando ocorre:** Após upload de arquivo não-Markdown
- **Processo:** Conversão assíncrona via Docling (queue-based)
- **SSE:** Cliente recebe notificação quando status muda
- **Tentativas:** Até 3 tentativas automáticas
- **Transições:**
  - Sucesso → DRAFT
  - Falha (após 3 tentativas) → ERROR
- **Editor recebe notificação:** Sim (em caso de sucesso ou falha)

#### ❌ ERROR
- **Quando ocorre:** Falha na conversão após 3 tentativas
- **Notificação:** Editor recebe notificação de falha
- **Ações disponíveis:**
  - Re-upload do documento
  - Deletar documento
- **Visibilidade:** Apenas para o Editor que criou

#### ✏️ DRAFT
- **Quando ocorre:** 
  - Após conversão bem-sucedida
  - Documento criado "em branco" ou "a partir de template"
  - Documento PUBLISHED despublicado
  - Novo documento criado a partir de edição de PUBLISHED (versionamento)
- **Edição:**
  - Auto-save a cada 1 minuto (configurável)
  - Apenas 1 Editor por vez (documento "locked" para quem iniciou edição)
  - **NÃO há edição colaborativa simultânea no MVP**
- **Ações disponíveis:**
  - Editar conteúdo Markdown
  - Adicionar metadados (tags, categorias, documentos relacionados)
  - Enviar para aprovação
  - Deletar (se ainda não foi enviado para aprovação)
- **Preview:** Via botão "Visualizar" (não em tempo real)

#### ⏳ PENDING_APPROVAL
- **Quando ocorre:** Editor clica "Enviar para revisão"
- **Atribuição de Revisor:** 
  - Sistema **NÃO atribui automaticamente**
  - Qualquer Revisor do Grupo pode revisar
  - Revisor deve ter uma view/filtro de "Documentos Pendentes de Aprovação"
- **Comentários não resolvidos:**
  - Sistema alerta o Editor se há comentários pendentes
  - Editor pode optar por enviar mesmo assim (confirmação)
- **Ações do Revisor:**
  - Aprovar (→ APPROVED)
  - Solicitar mudanças (→ CHANGES_REQUESTED)
  - Adicionar comentários em trechos específicos

#### 📝 CHANGES_REQUESTED
- **Quando ocorre:** Revisor solicita mudanças
- **Notificação:** Editor recebe notificação in-app + email
- **Comentários:**
  - Editor pode VER comentários e trechos marcados
  - Editor **NÃO pode responder** aos comentários (apenas visualizar)
  - Editor pode marcar comentários como "resolvidos"
- **Ações disponíveis:**
  - Editar documento
  - Reenviar para aprovação
- **Versionamento:** Ao reenviar, mantém versão anterior

#### ✅ APPROVED
- **Quando ocorre:** Revisor aprova documento
- **Processo:** Documento vai para **Queue de Publicação**
  - Queue separada do processo de conversão
  - Permite validações futuras antes de publicar
- **Notificação:** Editor recebe notificação de aprovação
- **Transição automática:** APPROVED → PUBLISHED (processado pela queue)

#### ✅ PUBLISHED
- **Quando ocorre:** Documento processado pela queue de publicação
- **Visibilidade:** Visível para todos do Grupo conforme permissões
- **Embeddings:** Gerados automaticamente ao publicar (queue separada)
- **Ações disponíveis:**
  - **Editar:** Cria nova versão (v1.1) em DRAFT, mantendo v1.0 PUBLISHED
  - **Despublicar:** Volta para DRAFT (mantém versionamento)
  - **Depreciar:** Marca como DEPRECATED (Admin de Grupo ou Revisor)
  - **Arquivar:** Move para ARCHIVED (Admin de Grupo ou Super Admin)
- **Integração RAG:** Apenas documentos PUBLISHED vão para RAG

#### ⚠️ DEPRECATED
- **Quando ocorre:** Admin de Grupo ou Revisor marca como obsoleto
- **Quem pode marcar:**
  - ✅ Super Admin
  - ✅ Admin de Grupo
  - ✅ Revisor
  - ❌ Editor (mesmo sendo o criador)
- **Documento substituto:**
  - NÃO é obrigatório linkar documento substituto
  - Se houver, fica visível como "Este documento foi substituído por [link]"
- **Visibilidade:**
  - Permanece visível e pesquisável
  - Marcação clara de "OBSOLETO" ou "DEPRECATED"
  - Aviso no topo do documento
- **Acesso:** Não restrito (qualquer usuário do Grupo pode ver)
- **Uso:** Alerta que NÃO deve ser usado como referência para novas ações
- **Analogia:** Estrada fechada com placa indicando desvio

#### 📦 ARCHIVED
- **Quando ocorre:** 
  - Admin marca documento DEPRECATED ou PUBLISHED como arquivado
  - Cumprimento de ciclo de vida
- **Quem pode arquivar:**
  - ✅ Super Admin
  - ✅ Admin de Grupo
- **Visibilidade:**
  - Removido das buscas e visualizações principais
  - Armazenado em repositório de arquivo
  - Acesso restrito (compliance, auditoria)
- **Objetivo:** Preservação histórica, cumprimento legal/regulatório
- **Analogia:** Arquivo morto - guardado mas não consultado no dia a dia

### 3.3 Tabela Comparativa: DEPRECATED vs ARCHIVED

| Característica | DEPRECATED | ARCHIVED |
|---------------|------------|----------|
| **Visibilidade** | Alta - Visível no sistema principal | Baixa/Restrita - Removido do sistema principal |
| **Objetivo** | Alertar e Redirecionar | Preservar e Remover |
| **Localização** | Repositório Ativo (com marcação) | Repositório de Arquivo / Secundário |
| **Acesso** | Geralmente livre | Frequentemente controlado/restrito |
| **Conexão** | Pode linkar ao substituto (opcional) | Auto-contido |
| **Ciclo de Vida** | Etapa antes do arquivamento | Estágio final |
| **Exemplo** | Manual de software v2.0 quando v3.0 sai | Contrato expirado há 5 anos |

---

## 📝 4. EDITOR DE DOCUMENTOS

### 4.1 Formato de Armazenamento

- **Formato:** Markdown (.md)
- **Conversão:** Documentos em outros formatos são convertidos para MD

### 4.2 Funcionalidades do Editor

#### Preview
- **Tipo:** Não em tempo real
- **Método:** Botão "Visualizar"
- **Formatação suportada:**
  - Tabelas
  - Imagens (upload e referência)
  - Blocos de código com syntax highlighting
  - Headers, listas, links, etc.

#### Auto-save
- **Intervalo:** 1 minuto (configurável na aplicação)
- **Indicador visual:** Sim ("Salvando...", "Salvo às HH:MM")
- **Conflitos:** Não aplicável (edição não é simultânea)

#### Lock de Edição
- **Comportamento:** Documento em DRAFT fica "locked" para quem iniciou edição
- **Outros Editores:** Veem indicador "Em edição por [Nome do Usuário]"
- **Edição simultânea:** NÃO suportada no MVP

#### Metadados do Documento
- **Tags:** Livres (usuário digita o que quiser) - **Opcional**
- **Categorias:** Pré-definidas pelo Admin Global - **Opcional**
- **Documentos relacionados:**
  - Editor pode linkar manualmente
  - Exibido como seção "Ver também"
- **Autor:** Automático (usuário que criou)
- **Data de criação/modificação:** Automático
- **Grupo e Pasta:** Definido na criação

### 4.3 Criação de Documentos

Usuário escolhe entre:
1. **Em branco:** Abre editor vazio
2. **Upload:** Faz upload de arquivo (PDF, DOCX, etc.) → NEW → PROCESSING → DRAFT
3. **A partir de template:** Escolhe template global e abre editor com conteúdo pré-preenchido

---

## 🔄 5. CONVERSÃO DE DOCUMENTOS

### 5.1 Formatos Suportados

- **Fonte:** Todos os formatos suportados pelo **Docling**
  - PDF
  - DOCX
  - HTML
  - TXT
  - MD (direto, sem conversão)
  - Outros conforme Docling
- **Destino:** Markdown (.md)

### 5.2 Processo de Conversão

#### Trigger
- **Evento:** Upload de documento não-Markdown
- **Arquitetura:** Queue-based (ex: RabbitMQ, Celery)

#### Fluxo
1. Usuário faz upload → Documento criado com status NEW
2. Sistema adiciona job na fila de conversão
3. Worker Docling processa conversão
4. **SSE:** Cliente conectado recebe notificação de mudança de status
5. Transições:
   - Sucesso → DRAFT
   - Falha (tentativa 1-2) → Nova tentativa
   - Falha (tentativa 3) → ERROR + Notificação ao Editor

#### Limite de Tamanho
- **Máximo:** 100 MB (configurável na aplicação)
- **Validação:** Frontend e backend

#### Tratamento de Erro
- **Tentativas:** 3 automáticas
- **Status final:** ERROR
- **Notificação:** Editor recebe in-app + email
- **Ações possíveis:**
  - Re-upload do arquivo
  - Deletar documento com erro

### 5.3 SSE (Server-Sent Events)

- **Uso:** Notificar cliente sobre mudança de status do documento
- **Eventos:**
  - `NEW` → `PROCESSING`
  - `PROCESSING` → `DRAFT`
  - `PROCESSING` → `ERROR`
  - `PENDING_APPROVAL` → `APPROVED` → `PUBLISHED`

---

## 💬 6. SISTEMA DE COMENTÁRIOS

### 6.1 Quem Pode Comentar

- ✅ **Revisor:** Pode adicionar comentários
- ❌ **Editor:** Pode VER comentários, mas NÃO pode adicionar nem responder
- ❌ **Reader:** Pode VER comentários, mas NÃO pode adicionar

### 6.2 Funcionalidades de Comentários

#### Comentários em Trechos
- **Seleção:** Revisor marca trecho específico do Markdown
- **Adição:** Adiciona comentário vinculado ao trecho
- **Múltiplos comentários:** Sim, mesmo trecho pode ter múltiplos comentários
- **Threads:** NÃO no MVP (comentários simples)

#### Resolução de Comentários
- **Quem pode marcar como resolvido:**
  - ✅ Editor
  - ✅ Revisor
- **Efeito:** Visual (comentário fica marcado, não desaparece)
- **Objetivo:** Ajudar Editor a rastrear pendências

#### Visualização
- **Editor:** Vê comentários e trechos marcados (read-only)
- **Revisor:** Vê e pode adicionar/marcar como resolvido
- **Reader:** Vê comentários (read-only)

### 6.3 @Menções em Comentários

- **Escopo:** Apenas usuários do mesmo Grupo
- **Notificação:** Pessoa mencionada recebe notificação mesmo sem ter papel direto no documento
- **Uso:** `@nome_usuario` no texto do comentário

---

## 📊 7. VERSIONAMENTO

### 7.1 Estratégia de Versionamento

**Versionamento completo** implementado no MVP.

#### Quando Versiona
- **Ao enviar para aprovação:** Nova versão criada
- **Ao republicar documento PUBLISHED:** Nova versão criada

#### Comportamento ao Editar PUBLISHED
1. Documento está em **PUBLISHED v1.0**
2. Editor clica "Editar"
3. Sistema cria **v1.1 em DRAFT**
4. **v1.0 continua PUBLISHED** (intacta)
5. Editor trabalha em v1.1
6. Ao aprovar v1.1 → v1.1 vai para PUBLISHED
7. **Agora há duas versões PUBLISHED:** v1.0 (antiga) e v1.1 (atual)
   - Sistema marca v1.1 como "versão atual"
   - v1.0 fica acessível no histórico

#### Despublicar
- **Ação:** Botão "Despublicar" em documento PUBLISHED
- **Efeito:** Documento volta para DRAFT
- **Versionamento:** Mantém histórico (versão publicada fica marcada no histórico)

### 7.2 Funcionalidades de Versionamento

#### Histórico de Versões
- **Ver versões anteriores:** Sim
- **Restaurar versão antiga:** Sim (cria nova versão DRAFT com conteúdo da versão restaurada)
- **Diff entre versões:** Sim (comparação lado a lado com marcação de mudanças)

#### CHANGES_REQUESTED
- **Versionamento:** Ao reenviar para aprovação, mantém versão anterior
- **Histórico:** Registra versão rejeitada + comentários

### 7.3 Metadados de Versão

Cada versão mantém:
- Número da versão (v1.0, v1.1, etc.)
- Data e hora da criação
- Autor da versão
- Status no momento (DRAFT, PUBLISHED, etc.)
- Comentários associados (se houver)
- Marcação se foi a versão publicada

---

## 🔍 8. SISTEMA DE BUSCA

### 8.1 Escopo da Busca

- **Permissões:** Busca respeita permissões do usuário
  - Usuário só vê resultados de Grupos aos quais pertence
  - Dentro do Grupo, vê conforme seu papel
- **NÃO é busca global:** Filtra conforme acesso do usuário

### 8.2 Campos Pesquisáveis

#### No MVP, a busca inclui:
- ✅ Busca por título
- ✅ Busca no conteúdo Markdown (full-text)
- ✅ Busca por autor
- ✅ Busca por tags
- ✅ Busca por categorias

### 8.3 Filtros Disponíveis

- ✅ Filtro por status (DRAFT, PUBLISHED, etc.)
- ✅ Filtro por data de criação
- ✅ Filtro por data de modificação
- ✅ Filtro por Grupo (se usuário tem acesso a múltiplos)
- ✅ Filtro por Pasta
- ✅ Filtro por tags
- ✅ Filtro por categorias

### 8.4 Interface de Busca

- **Localização:** Barra de busca global no topo + filtros laterais
- **Resultados:** Lista com:
  - Título do documento
  - Trecho relevante (snippet)
  - Autor
  - Data de modificação
  - Status
  - Grupo/Pasta
  - Tags/Categorias
- **Ordenação:** Relevância, Data (mais recente), Título (A-Z)

---

## 🔔 9. SISTEMA DE NOTIFICAÇÕES

### 9.1 Tipos de Notificação

#### In-App (dentro da aplicação)
- **Localização:** Área de notificações (ícone de sino)
- **Eventos notificados:**
  - Documento aprovado/rejeitado
  - Novos comentários em documentos que você criou
  - @menções em comentários
  - Documento atribuído para revisão (pendente)
  - Falha na conversão de documento
  - Mudança de status de documento (via SSE também)

#### Email
- **Frequência:** Digest diário (configurável: off/diário/semanal)
- **Configuração:** Global (aplicada a todos os usuários)
- **Conteúdo:** Resumo das notificações do dia/semana
- **On/Off:** Usuário pode desabilitar emails (mantém in-app)

### 9.2 Configurações de Notificação

- **Global:** Admin configura padrão
- **Por usuário:** Pode habilitar/desabilitar emails
- **Eventos configuráveis:**
  - Notificações in-app: sempre ativas
  - Notificações por email: on/off + frequência

### 9.3 Notificações Específicas

#### Para Editores
- Documento aprovado
- Documento rejeitado (CHANGES_REQUESTED)
- Novos comentários em seus documentos
- @menções
- Conversão concluída (sucesso ou erro)

#### Para Revisores
- Novo documento PENDING_APPROVAL no Grupo
- @menções em comentários

#### Para Readers
- @menções em comentários

---

## 📊 10. DASHBOARD & INTERFACE

### 10.1 Página Inicial do Usuário

Dashboard personalizado conforme papel:

#### Widgets/Seções
1. **Meus Documentos**
   - Documentos criados pelo usuário
   - Filtros rápidos: Rascunhos, Pendentes, Publicados
   
2. **Pendentes de Revisão** (se for Revisor)
   - Lista de documentos PENDING_APPROVAL do Grupo
   - Indicador de tempo aguardando aprovação

3. **Notificações Recentes**
   - Últimas 5-10 notificações
   - Link "Ver todas"

4. **Documentos do Grupo**
   - Documentos recentes do Grupo com filtros
   - Organização por Pasta
   - Busca rápida

### 10.2 Navegação

#### Sidebar (navegação lateral)
- **Hierarquia:**
  ```
  📁 Grupos
  ├── 👥 RH
  │   ├── 📂 Políticas
  │   ├── 📂 Treinamentos
  │   └── 📄 [Documentos soltos]
  ├── 💻 TI
  │   └── ...
  └── ...
  
  📋 Meus Documentos
  ⏳ Pendentes de Revisão (se Revisor)
  ⚙️ Configurações
  ```

#### Breadcrumbs
- **Localização:** Topo da página de conteúdo
- **Exemplo:** `RH > Políticas > Política de Férias v2.1`
- **Clicável:** Cada nível é link

#### Topbar
- **Barra de busca global**
- **Notificações** (ícone de sino)
- **Perfil do usuário** (foto + nome + menu)
- **Botão "Novo Documento"**

---

## 🎯 11. EMBEDDINGS & INTEGRAÇÃO RAG

### 11.1 Quando Gerar Embeddings

#### Trigger
- Documento vai de **APPROVED → PUBLISHED** (processado pela queue de publicação)

#### Processo
1. Documento aprovado → Queue de Publicação
2. Worker processa publicação
3. Documento vira PUBLISHED
4. **Trigger para Queue de Embeddings**
5. Worker de Embeddings processa documento
6. Embeddings gerados e armazenados
7. Documento pronto para RAG

#### Arquitetura
- **Queue separada:** Embeddings em fila separada da conversão
- **Assíncrono:** Não bloqueia publicação
- **Batch:** Pode processar múltiplos documentos

### 11.2 Modelo de Embedding

- **Padrão:** OpenAI Embeddings (text-embedding-3-large ou similar)
- **Alternativa:** Modelos locais melhores para semantic embedding
- **Configurável:** Admin pode trocar modelo na configuração

### 11.3 Atualização de Embeddings

#### Quando Regenerar
- Documento PUBLISHED é editado e **REAPROVADO**
- Nova versão entra na Queue de Aprovação → PUBLISHED
- Nova versão dispara Queue de Embeddings
- Embeddings regenerados para nova versão

#### Versionamento de Embeddings
- Cada versão PUBLISHED tem seus próprios embeddings
- RAG pode buscar em versão específica ou versão "atual"

### 11.4 Metadados para RAG

Embeddings incluem metadados:
- **Documento:** ID, título, versão
- **Conteúdo:** Texto completo em chunks
- **Autor:** Nome e ID
- **Data:** Criação e última modificação
- **Grupo:** ID e nome
- **Pasta:** ID e nome
- **Tags:** Lista de tags
- **Categoria:** Categoria principal
- **Documentos relacionados:** IDs e títulos
- **Status:** PUBLISHED (apenas documentos publicados vão para RAG)

### 11.5 Apenas PUBLISHED no RAG

- ✅ Documentos **PUBLISHED** → RAG
- ❌ DRAFT, PENDING_APPROVAL, CHANGES_REQUESTED → **NÃO vão para RAG**
- ⚠️ DEPRECATED → **Decisão futura** (pode ir com marcação de "obsoleto")
- ❌ ARCHIVED → **NÃO vão para RAG**

---

## ⚙️ 12. CONFIGURAÇÕES DO SISTEMA

### 12.1 Configurações Globais (Admin)

#### Conversão de Documentos
- **Limite de tamanho de upload:** 100 MB (padrão, configurável)
- **Tentativas de conversão:** 3 (padrão, configurável)
- **Timeout de conversão:** Configurável

#### Editor
- **Auto-save interval:** 1 minuto (padrão, configurável)
- **Preview timeout:** Configurável

#### Notificações
- **Digest de email:** Diário, Semanal, Off
- **Tipos de notificação habilitados:** Checkboxes

#### Embeddings
- **Modelo de embedding:** Seleção (OpenAI, local, etc.)
- **Chunk size:** Configurável
- **Overlap:** Configurável

#### Versionamento
- **Retenção de versões:** Ilimitado (padrão) ou N versões
- **Diff algorithm:** Configurável

### 12.2 Configurações por Usuário

- **Notificações por email:** On/Off
- **Idioma da interface:** Português (padrão), outros
- **Tema:** Claro/Escuro
- **Itens por página:** 10, 25, 50, 100

---

## 🚀 13. PRIORIZAÇÃO DO MVP

### 13.1 Ordem de Prioridade

| Prioridade | Módulo | Justificativa |
|-----------|--------|---------------|
| **1** | Gestão de Usuários & Grupos | Base para todo o sistema |
| **1** | Criação e Edição de Documentos (CRUD) | Core do sistema |
| **1** | Workflow de Aprovação | Diferencial do produto |
| **1** | Conversão de documentos (upload) | Facilitador de adoção |
| **3** | Sistema de Comentários | Importante mas pode vir após CRUD |
| **5** | Versionamento | Pode ser simplificado inicialmente |
| **5** | Sistema de Busca | Importante mas pode vir após MVP básico funcionar |

### 13.2 Fases de Implementação Sugeridas

#### Fase 1 - Core (Prioridade 1)
- Autenticação e autorização
- CRUD de Grupos, Pastas, Documentos
- Editor Markdown básico com auto-save
- Workflow DRAFT → PENDING_APPROVAL → PUBLISHED
- Conversão de documentos (Docling)
- Dashboard básico

#### Fase 2 - Colaboração (Prioridade 3)
- Sistema de Comentários
- Notificações in-app
- Notificações por email

#### Fase 3 - Gestão Avançada (Prioridade 5)
- Versionamento completo com diff
- Sistema de Busca avançado
- Templates de documentos
- Estados DEPRECATED e ARCHIVED

#### Fase 4 - Integração RAG
- Geração de embeddings
- API para RAG
- Metadados otimizados

---

## 📝 14. WORKFLOWS DETALHADOS

### 14.1 Workflow: Criar Documento em Branco

```
1. Usuário (Editor) → Dashboard
2. Clica "Novo Documento"
3. Escolhe "Em branco"
4. Seleciona Grupo e Pasta
5. Sistema cria documento em DRAFT
6. Editor escreve conteúdo
7. Sistema auto-save a cada 1 min
8. Editor clica "Enviar para revisão"
9. Documento → PENDING_APPROVAL
10. Revisor recebe notificação
```

### 14.2 Workflow: Upload de Documento

```
1. Usuário (Editor) → Dashboard
2. Clica "Novo Documento"
3. Escolhe "Upload"
4. Seleciona arquivo (PDF, DOCX, etc.)
5. Seleciona Grupo e Pasta
6. Sistema cria documento em NEW
7. Sistema adiciona job na queue de conversão
8. Documento → PROCESSING
9. SSE notifica cliente (loading indicator)
10. Worker Docling converte para Markdown
11. Sucesso → Documento → DRAFT
12. SSE notifica cliente (documento pronto)
13. Editor recebe notificação in-app
14. Editor pode editar e enviar para aprovação
```

### 14.3 Workflow: Aprovação de Documento

```
1. Documento em PENDING_APPROVAL
2. Revisor vê na lista "Pendentes de Revisão"
3. Revisor abre documento
4. Revisor pode:
   a) APROVAR:
      - Documento → APPROVED
      - Queue de Publicação → PUBLISHED
      - Editor recebe notificação
      - Embeddings gerados
   b) SOLICITAR MUDANÇAS:
      - Revisor adiciona comentários em trechos
      - Clica "Solicitar Mudanças"
      - Documento → CHANGES_REQUESTED
      - Editor recebe notificação
      - Editor vê comentários
      - Editor edita e marca como resolvidos
      - Editor reenvia → PENDING_APPROVAL
```

### 14.4 Workflow: Editar Documento Publicado

```
1. Documento está em PUBLISHED v1.0
2. Editor clica "Editar"
3. Sistema cria v1.1 em DRAFT
4. v1.0 continua PUBLISHED
5. Editor trabalha em v1.1
6. Auto-save a cada 1 min
7. Editor envia para revisão
8. v1.1 → PENDING_APPROVAL
9. Revisor aprova
10. v1.1 → PUBLISHED
11. Agora há v1.0 e v1.1 PUBLISHED
12. v1.1 marcada como "versão atual"
13. Embeddings de v1.1 gerados
```

### 14.5 Workflow: Marcar como DEPRECATED

```
1. Documento está em PUBLISHED
2. Admin de Grupo ou Revisor clica "Marcar como Obsoleto"
3. Modal abre:
   - "Este documento está obsoleto?"
   - Campo opcional: "Documento substituto" (autocomplete)
   - Botão "Confirmar"
4. Admin confirma
5. Documento → DEPRECATED
6. Aviso no topo: "⚠️ OBSOLETO - Este documento não deve ser usado como referência"
7. Se houver substituto: Link "Ver documento atualizado: [Título]"
8. Documento continua pesquisável e visível
9. Usuários veem marcação clara
```

---

## 🔐 15. SEGURANÇA & PERMISSÕES

### 15.1 Matriz de Permissões

| Ação | Super Admin | Admin Grupo | Revisor | Editor | Reader |
|------|-------------|-------------|---------|--------|--------|
| Criar Grupo | ✅ | ❌ | ❌ | ❌ | ❌ |
| Criar Pasta | ✅ | ✅ | ❌ | ✅ | ❌ |
| Criar Documento | ✅ | ✅ | ✅ | ✅ | ❌ |
| Editar DRAFT | ✅ | ✅ | ❌ | ✅ (próprio) | ❌ |
| Enviar para Aprovação | ✅ | ✅ | ❌ | ✅ (próprio) | ❌ |
| Aprovar/Rejeitar | ✅ | ✅ | ✅ | ❌ | ❌ |
| Adicionar Comentários | ✅ | ✅ | ✅ | ❌ | ❌ |
| Ver Comentários | ✅ | ✅ | ✅ | ✅ | ✅ |
| Marcar DEPRECATED | ✅ | ✅ | ✅ | ❌ | ❌ |
| Arquivar | ✅ | ✅ | ❌ | ❌ | ❌ |
| Despublicar | ✅ | ✅ | ❌ | ✅ (próprio) | ❌ |
| Criar Template | ✅ | ✅ | ❌ | ✅ | ❌ |
| Ver DRAFT | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ver PUBLISHED | ✅ | ✅ | ✅ | ✅ | ✅ |
| Adicionar Usuário ao Grupo | ✅ | ✅ | ❌ | ❌ | ❌ |
| Mover entre Pastas | ✅ | ✅ | ❌ | ❌ | ❌ |
| Mover entre Grupos | ✅ | ❌ | ❌ | ❌ | ❌ |

### 15.2 Regras de Negócio

#### Visibilidade de Documentos
- Documentos são **privados ao Grupo por padrão**
- NÃO há compartilhamento entre Grupos no MVP
- NÃO há documentos públicos (toda organização) no MVP
- Usuário vê apenas documentos dos Grupos aos quais pertence

#### Lock de Edição
- Documento em DRAFT pode ser editado por 1 usuário por vez
- Se Editor A está editando, Editor B vê "Em edição por [Editor A]"
- Lock é liberado ao:
  - Editor salvar e fechar
  - Timeout (ex: 30 min de inatividade)
  - Editor enviar para aprovação

#### Versionamento e Edição
- Editar documento PUBLISHED cria nova versão em DRAFT
- Versão PUBLISHED original permanece intacta
- Ao aprovar nova versão, ambas ficam PUBLISHED com marcação de "versão atual"

---

## 📚 16. STACK TECNOLÓGICO SUGERIDO

### 16.1 Backend
- **Framework:** FastAPI (Python)
- **Banco de Dados:** PostgreSQL
- **Cache:** Redis
- **Queue:** Celery + RabbitMQ
- **Conversão:** Docling
- **Embeddings:** OpenAI API ou modelo local

### 16.2 Frontend
- **Framework:** React ou Vue.js
- **Editor Markdown:** react-markdown-editor-lite ou similar
- **Diff Viewer:** react-diff-viewer
- **SSE:** EventSource API

### 16.3 Infraestrutura
- **Containerização:** Docker
- **Storage:** S3 ou similar para arquivos originais
- **CDN:** Opcional para assets

---

## 📋 17. CHECKLIST DE ENTREGA DO MVP

### 17.1 Funcionalidades Core
- [ ] Autenticação e autorização
- [ ] CRUD de Usuários (Super Admin)
- [ ] CRUD de Grupos (Super Admin)
- [ ] CRUD de Pastas (Admin Grupo, Editor)
- [ ] CRUD de Documentos (Editor)
- [ ] Editor Markdown com auto-save
- [ ] Upload de documentos com conversão (Docling)
- [ ] Workflow DRAFT → PENDING_APPROVAL → PUBLISHED
- [ ] Sistema de Comentários
- [ ] Notificações in-app e email
- [ ] Dashboard personalizado por papel
- [ ] Navegação (sidebar + breadcrumbs)

### 17.2 Funcionalidades Avançadas
- [ ] Versionamento completo com diff
- [ ] Sistema de Busca avançado
- [ ] Templates de documentos
- [ ] Estados DEPRECATED e ARCHIVED
- [ ] Despublicar documentos
- [ ] @Menções em comentários
- [ ] SSE para mudanças de status

### 17.3 Integração RAG
- [ ] Geração de embeddings ao publicar
- [ ] Queue de embeddings separada
- [ ] Metadados completos para RAG
- [ ] API para consulta RAG (futuro)

---

## 🎯 18. PRÓXIMOS PASSOS

1. **Validação desta especificação** com stakeholders
2. **Criação de User Stories** organizadas por épicos
3. **Definição de critérios de aceitação** detalhados
4. **Arquitetura técnica** (diagramas de componentes, BD, APIs)
5. **Prototipação de interfaces** (wireframes, mockups)
6. **Desenvolvimento em sprints** conforme priorização

---

**Documento preparado por:** Claude (Anthropic)  
**Revisão:** Pendente  
**Status:** Versão 1.0 - Especificação Funcional Completa para MVP  
**Próxima etapa:** Criação de User Stories por Épico

