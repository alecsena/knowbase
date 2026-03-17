# User Stories - Sistema de Gestão de Documentos e Conhecimento

**Versão:** 1.0 MVP  
**Data:** Janeiro 2026  
**Baseado em:** Especificação Funcional v1.0

---

## 📋 Índice de Épicos

1. [ÉPICO 1: Gestão de Usuários, Grupos e Papéis](#épico-1-gestão-de-usuários-grupos-e-papéis) - **Prioridade 1**
2. [ÉPICO 2: Gestão de Pastas](#épico-2-gestão-de-pastas) - **Prioridade 1**
3. [ÉPICO 3: Criação e Edição de Documentos](#épico-3-criação-e-edição-de-documentos) - **Prioridade 1**
4. [ÉPICO 4: Conversão de Documentos](#épico-4-conversão-de-documentos) - **Prioridade 1**
5. [ÉPICO 5: Workflow de Aprovação](#épico-5-workflow-de-aprovação) - **Prioridade 1**
6. [ÉPICO 6: Sistema de Comentários](#épico-6-sistema-de-comentários) - **Prioridade 3**
7. [ÉPICO 7: Versionamento](#épico-7-versionamento) - **Prioridade 5**
8. [ÉPICO 8: Estados Avançados (DEPRECATED e ARCHIVED)](#épico-8-estados-avançados-deprecated-e-archived) - **Prioridade 5**
9. [ÉPICO 9: Sistema de Busca](#épico-9-sistema-de-busca) - **Prioridade 5**
10. [ÉPICO 10: Notificações](#épico-10-notificações) - **Prioridade 3**
11. [ÉPICO 11: Dashboard e Navegação](#épico-11-dashboard-e-navegação) - **Prioridade 1**
12. [ÉPICO 12: Templates de Documentos](#épico-12-templates-de-documentos) - **Prioridade 3**
13. [ÉPICO 13: Embeddings e Preparação RAG](#épico-13-embeddings-e-preparação-rag) - **Prioridade 5**

---

## ÉPICO 1: Gestão de Usuários, Grupos e Papéis

**Prioridade:** 1 (Crítico)  
**Descrição:** Permitir a criação e gestão de usuários, grupos organizacionais e atribuição de papéis com controle granular de permissões.

---

### US-001: Criar Usuário no Sistema

**Como** Super Admin  
**Eu quero** criar novos usuários no sistema  
**Para** que possam acessar e utilizar a plataforma conforme suas responsabilidades

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Apenas Super Admin pode acessar a página de criação de usuários
   - Menu "Gerenciar Usuários" visível apenas para Super Admin
   - Tentativa de acesso direto via URL por não-Super Admin retorna 403 Forbidden

2. **Formulário de Criação**
   - Campos obrigatórios:
     - Nome completo (min: 3 caracteres, max: 100)
     - Email (validação de formato válido, único no sistema)
     - Senha inicial (min: 8 caracteres, 1 maiúscula, 1 número, 1 caractere especial)
   - Campos opcionais:
     - Telefone
     - Departamento/Setor
     - Cargo

3. **Validações de Negócio**
   - Email deve ser único no sistema (mensagem: "Este email já está cadastrado")
   - Senha deve atender requisitos de segurança
   - Nome não pode conter apenas números ou caracteres especiais

4. **Confirmação**
   - Após criação, modal de confirmação: "Usuário [Nome] criado com sucesso"
   - Exibir próxima ação sugerida: "Deseja atribuir este usuário a um Grupo agora?"
   - Opções: "Sim, atribuir" | "Não, criar outro usuário" | "Fechar"

5. **Email de Boas-Vindas**
   - Sistema envia email automático ao usuário com:
     - Link de primeiro acesso
     - Instruções para redefinir senha
     - Informações básicas sobre a plataforma

6. **Estado Inicial**
   - Usuário criado sem papéis (não pertence a nenhum Grupo)
   - Status: "Ativo"
   - Primeiro login força mudança de senha

7. **Lista de Usuários Atualizada**
   - Novo usuário aparece na lista de "Usuários" imediatamente
   - Indicador visual de "Sem Grupo atribuído"

**Testes de Aceitação:**
- [ ] Super Admin consegue criar usuário com dados válidos
- [ ] Email duplicado é rejeitado com mensagem apropriada
- [ ] Senha fraca é rejeitada com requisitos exibidos
- [ ] Email de boas-vindas é enviado corretamente
- [ ] Usuário não-Super Admin não consegue acessar a funcionalidade

---

### US-002: Criar Grupo (Setor)

**Como** Super Admin  
**Eu quero** criar Grupos organizacionais  
**Para** estruturar a organização de documentos por setores/departamentos

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Apenas Super Admin pode criar Grupos
   - Botão "Novo Grupo" visível apenas para Super Admin
   - Acesso via menu "Gerenciar Grupos"

2. **Formulário de Criação**
   - Campos obrigatórios:
     - Nome do Grupo (min: 3 caracteres, max: 50, único)
     - Descrição (max: 500 caracteres)
   - Campos opcionais:
     - Ícone/Emoji representativo
     - Cor de identificação (picker de cores)

3. **Validações de Negócio**
   - Nome do Grupo deve ser único (case-insensitive)
   - Não pode conter apenas números
   - Caracteres especiais permitidos: hífen, underline, espaço

4. **Hierarquia Inicial**
   - Grupo criado sem Pastas
   - Grupo criado sem usuários atribuídos
   - Status: "Ativo"

5. **Confirmação**
   - Modal: "Grupo [Nome] criado com sucesso"
   - Próxima ação sugerida: "Deseja adicionar usuários agora?"
   - Opções: "Sim, adicionar usuários" | "Não, criar outro Grupo" | "Fechar"

6. **Navegação Atualizada**
   - Novo Grupo aparece na sidebar imediatamente
   - Ícone/cor selecionados exibidos
   - Indicador de "Grupo vazio (0 documentos, 0 usuários)"

7. **Auditoria**
   - Log registrado: "Super Admin [Nome] criou Grupo [Nome do Grupo]"
   - Data e hora da criação registradas

**Testes de Aceitação:**
- [ ] Super Admin cria Grupo com nome único
- [ ] Nome duplicado é rejeitado
- [ ] Grupo aparece na sidebar corretamente
- [ ] Cor e ícone são aplicados
- [ ] Não-Super Admin não vê opção de criar Grupo

---

### US-003: Atribuir Usuário a Grupo com Papel

**Como** Super Admin  
**Eu quero** atribuir usuários a Grupos com papéis específicos  
**Para** definir permissões de acesso e ações dentro de cada setor

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Super Admin e Admin de Grupo podem atribuir usuários
   - Super Admin: pode atribuir a qualquer Grupo
   - Admin de Grupo: pode atribuir apenas ao(s) seu(s) Grupo(s)

2. **Interface de Atribuição**
   - Página de detalhes do Grupo tem tab "Membros"
   - Botão "+ Adicionar Membro"
   - Modal com:
     - Campo de busca de usuários (autocomplete)
     - Seleção de papel(is): Admin de Grupo, Revisor, Editor, Reader (multi-select)
     - Botão "Adicionar"

3. **Validações de Negócio**
   - Usuário pode ser membro de múltiplos Grupos
   - Usuário pode ter múltiplos papéis no mesmo Grupo
   - Não pode adicionar usuário já membro (exibir mensagem: "Usuário já pertence a este Grupo")
   - Pelo menos 1 papel deve ser selecionado

4. **Múltiplos Papéis**
   - Checkboxes para cada papel
   - Usuário pode ser simultaneamente: Editor + Revisor, por exemplo
   - Indicador visual dos papéis selecionados (tags coloridas)

5. **Confirmação**
   - Mensagem: "Usuário [Nome] adicionado ao Grupo [Nome Grupo] como [Papéis]"
   - Lista de membros atualizada imediatamente
   - Usuário recebe notificação in-app e email

6. **Email de Notificação**
   - Assunto: "Você foi adicionado ao grupo [Nome Grupo]"
   - Corpo:
     - Papéis atribuídos
     - Link para acessar o Grupo
     - Resumo de permissões

7. **Lista de Membros**
   - Exibe: Nome, Email, Papéis (tags), Data de adição
   - Filtro por papel
   - Ordenação por nome, data de adição

8. **Auditoria**
   - Log: "[Admin] adicionou [Usuário] ao Grupo [Nome] com papéis [Lista]"

**Testes de Aceitação:**
- [ ] Super Admin adiciona usuário a qualquer Grupo
- [ ] Admin de Grupo adiciona usuário apenas ao seu Grupo
- [ ] Múltiplos papéis são atribuídos corretamente
- [ ] Usuário duplicado é rejeitado
- [ ] Notificações são enviadas

---

### US-004: Remover Usuário de Grupo

**Como** Admin de Grupo  
**Eu quero** remover usuários do meu Grupo  
**Para** gerenciar a equipe e revogar acessos quando necessário

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Super Admin pode remover de qualquer Grupo
   - Admin de Grupo pode remover apenas do seu Grupo
   - Botão "Remover" ao lado de cada membro na lista

2. **Confirmação de Segurança**
   - Modal de confirmação: "Tem certeza que deseja remover [Usuário] do Grupo [Nome]?"
   - Aviso: "O usuário perderá acesso a todos os documentos deste Grupo"
   - Botões: "Cancelar" | "Confirmar Remoção" (vermelho)

3. **Validações de Negócio**
   - Não pode remover o último Admin de Grupo (mensagem: "Não é possível remover o último Admin do Grupo")
   - Ao remover, todas as permissões no Grupo são revogadas
   - Documentos criados pelo usuário permanecem no Grupo

4. **Impacto em Documentos**
   - Se usuário tinha documentos em DRAFT: Ficam órfãos (Admin pode reatribuir)
   - Se usuário tinha documentos em PENDING_APPROVAL: Continuam aguardando outro Revisor
   - Histórico de autoria é mantido

5. **Notificação**
   - Usuário removido recebe notificação in-app e email
   - Email: "Você foi removido do Grupo [Nome]"
   - Lista de membros atualizada imediatamente

6. **Auditoria**
   - Log: "[Admin] removeu [Usuário] do Grupo [Nome]"
   - Data e hora registradas

**Testes de Aceitação:**
- [ ] Admin de Grupo remove usuário com sucesso
- [ ] Último Admin não pode ser removido
- [ ] Documentos do usuário permanecem no Grupo
- [ ] Notificação é enviada ao usuário removido
- [ ] Acesso ao Grupo é revogado imediatamente

---

### US-005: Modificar Papéis de Usuário em Grupo

**Como** Admin de Grupo  
**Eu quero** alterar os papéis de usuários no meu Grupo  
**Para** ajustar permissões conforme mudanças de responsabilidade

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Super Admin pode modificar papéis em qualquer Grupo
   - Admin de Grupo pode modificar apenas no seu Grupo
   - Botão "Editar Papéis" ao lado de cada membro

2. **Interface de Edição**
   - Modal com checkboxes dos 4 papéis: Admin de Grupo, Revisor, Editor, Reader
   - Papéis atuais vêm pré-selecionados
   - Pode adicionar ou remover papéis

3. **Validações de Negócio**
   - Não pode remover todos os papéis (ao menos 1 deve permanecer)
   - Não pode remover papel "Admin de Grupo" se for o último Admin
   - Pode adicionar múltiplos papéis simultaneamente

4. **Confirmação**
   - Mensagem: "Papéis de [Usuário] atualizados para: [Lista de Papéis]"
   - Lista de membros reflete mudanças imediatamente
   - Tags de papéis são atualizadas

5. **Notificação**
   - Usuário recebe notificação: "Seus papéis no Grupo [Nome] foram atualizados"
   - Detalhamento: Papéis adicionados / Papéis removidos
   - Link para ver novo resumo de permissões

6. **Impacto em Ações Pendentes**
   - Se perder papel "Revisor": Documentos PENDING_APPROVAL que estava revisando continuam visíveis mas não pode aprovar
   - Se ganhar papel "Editor": Pode criar documentos a partir de agora
   - Permissões são aplicadas imediatamente

7. **Auditoria**
   - Log: "[Admin] modificou papéis de [Usuário] no Grupo [Nome]: [Antes] → [Depois]"

**Testes de Aceitação:**
- [ ] Admin modifica papéis com sucesso
- [ ] Último Admin não pode perder papel de Admin
- [ ] Notificação é enviada
- [ ] Permissões são aplicadas imediatamente
- [ ] Lista de membros reflete mudanças

---

## ÉPICO 2: Gestão de Pastas

**Prioridade:** 1 (Crítico)  
**Descrição:** Permitir a organização hierárquica de documentos através de pastas dentro de Grupos.

---

### US-006: Criar Pasta em Grupo

**Como** Editor  
**Eu quero** criar pastas dentro de Grupos  
**Para** organizar documentos por tema ou projeto

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Editor, Admin de Grupo e Super Admin podem criar Pastas
   - Botão "+ Nova Pasta" visível na view do Grupo
   - Reader NÃO vê opção de criar Pasta

2. **Formulário de Criação**
   - Campos obrigatórios:
     - Nome da Pasta (min: 3 caracteres, max: 50)
   - Campos opcionais:
     - Descrição (max: 200 caracteres)
     - Ícone/Emoji

3. **Validações de Negócio**
   - Nome da Pasta deve ser único dentro do Grupo (pode repetir em Grupos diferentes)
   - Não pode conter caracteres especiais de path: / \ : * ? " < > |
   - Permite espaços, hífen, underline

4. **Hierarquia**
   - Pasta é criada diretamente no Grupo (não há sub-pastas no MVP)
   - Pasta criada vazia (0 documentos)

5. **Confirmação**
   - Toast notification: "Pasta [Nome] criada com sucesso"
   - Pasta aparece na sidebar sob o Grupo imediatamente
   - Ordem: Alfabética

6. **Navegação**
   - Sidebar atualizada com nova Pasta
   - Breadcrumb: [Grupo] > [Pasta]
   - Contador de documentos: "(0 documentos)"

7. **Auditoria**
   - Log: "[Usuário] criou Pasta [Nome] no Grupo [Nome Grupo]"

**Testes de Aceitação:**
- [ ] Editor cria Pasta com sucesso
- [ ] Nome duplicado no mesmo Grupo é rejeitado
- [ ] Nome com caracteres inválidos é rejeitado
- [ ] Pasta aparece na sidebar
- [ ] Reader não vê opção de criar Pasta

---

### US-007: Renomear Pasta

**Como** Admin de Grupo  
**Eu quero** renomear Pastas  
**Para** corrigir nomes ou reorganizar a estrutura

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Admin de Grupo e Super Admin podem renomear
   - Botão de contexto (3 pontos) ao lado do nome da Pasta
   - Opção "Renomear" no menu

2. **Interface de Renomeação**
   - Modal com campo pré-preenchido com nome atual
   - Botão "Salvar" | "Cancelar"

3. **Validações de Negócio**
   - Novo nome deve ser único no Grupo
   - Mesmas regras de validação da criação
   - Não pode ser vazio

4. **Impacto em Documentos**
   - Documentos dentro da Pasta não são afetados
   - Breadcrumbs dos documentos são atualizados automaticamente

5. **Confirmação**
   - Toast: "Pasta renomeada para [Novo Nome]"
   - Sidebar atualizada imediatamente
   - Ordem alfabética recalculada

6. **Auditoria**
   - Log: "[Admin] renomeou Pasta [Nome Antigo] para [Nome Novo] no Grupo [Nome]"

**Testes de Aceitação:**
- [ ] Admin renomeia Pasta com sucesso
- [ ] Nome duplicado é rejeitado
- [ ] Documentos mantêm referência à Pasta
- [ ] Sidebar é atualizada

---

### US-008: Deletar Pasta

**Como** Admin de Grupo  
**Eu quero** deletar Pastas  
**Para** remover organizações que não são mais necessárias

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Admin de Grupo e Super Admin podem deletar
   - Botão de contexto > "Deletar"

2. **Validações de Negócio**
   - Não pode deletar Pasta com documentos
   - Mensagem: "Não é possível deletar. Esta Pasta contém [N] documentos. Mova ou delete os documentos primeiro."

3. **Confirmação de Segurança**
   - Modal: "Tem certeza que deseja deletar a Pasta [Nome]?"
   - Aviso: "Esta ação não pode ser desfeita"
   - Botões: "Cancelar" | "Deletar" (vermelho)

4. **Deleção**
   - Pasta vazia é deletada imediatamente
   - Removida da sidebar
   - Toast: "Pasta [Nome] deletada com sucesso"

5. **Auditoria**
   - Log: "[Admin] deletou Pasta [Nome] do Grupo [Nome Grupo]"

**Testes de Aceitação:**
- [ ] Admin deleta Pasta vazia
- [ ] Pasta com documentos NÃO pode ser deletada
- [ ] Confirmação é exigida
- [ ] Sidebar é atualizada

---

## ÉPICO 3: Criação e Edição de Documentos

**Prioridade:** 1 (Crítico)  
**Descrição:** Permitir criação, edição e gerenciamento do ciclo de vida básico de documentos em Markdown.

---

### US-009: Criar Documento em Branco

**Como** Editor  
**Eu quero** criar documentos em branco  
**Para** começar a escrever conteúdo do zero

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Botão "+ Novo Documento" visível para Editor, Admin de Grupo, Super Admin
   - Disponível na topbar e dentro de Pastas/Grupos
   - Reader NÃO vê este botão

2. **Modal de Seleção de Tipo**
   - Opções: "Em branco" | "Upload" | "A partir de template"
   - Usuário clica em "Em branco"

3. **Formulário de Criação**
   - Campos obrigatórios:
     - Título do Documento (min: 3 caracteres, max: 200)
     - Grupo (select com Grupos aos quais o usuário pertence como Editor)
     - Pasta (select com Pastas do Grupo selecionado) - Opcional
   - Campos opcionais:
     - Tags (campo livre, autocomplete de tags existentes)
     - Categoria (select de categorias pré-definidas)
     - Descrição breve (max: 500 caracteres)

4. **Metadados Automáticos**
   - Autor: Usuário que está criando (automático)
   - Data de criação: Timestamp atual (automático)
   - Status inicial: DRAFT
   - Versão: v1.0 (automático)

5. **Editor Markdown**
   - Abre editor com conteúdo vazio
   - Toolbar com opções de formatação: Bold, Italic, Headers, Lists, Links, Images, Code, Tables
   - Área de edição (70% largura) + Preview (30% largura, via botão "Visualizar")
   - Auto-save a cada 1 minuto (configurável)
   - Indicador visual: "Salvando..." | "Salvo às HH:MM"

6. **Lock de Edição**
   - Documento fica "locked" para o Editor que criou
   - Outros Editores do Grupo veem: "Em edição por [Nome do Editor]"

7. **Confirmação**
   - Ao salvar pela primeira vez (ou auto-save), toast: "Documento [Título] criado em DRAFT"
   - Documento aparece na lista de "Meus Documentos" e na Pasta/Grupo

8. **Navegação**
   - Breadcrumb: [Grupo] > [Pasta] > [Título do Documento]
   - Documento aparece na sidebar sob a Pasta

**Testes de Aceitação:**
- [ ] Editor cria documento em branco com sucesso
- [ ] Auto-save funciona corretamente
- [ ] Documento aparece em DRAFT na lista
- [ ] Preview de Markdown funciona
- [ ] Reader não vê botão de criar documento
- [ ] Lock de edição impede edição simultânea

---

### US-010: Editar Documento em DRAFT

**Como** Editor  
**Eu quero** editar documentos em DRAFT  
**Para** desenvolver e melhorar o conteúdo antes de enviar para aprovação

#### Critérios de Aceitação:

1. **Acesso à Funcionalidade**
   - Editor que criou o documento pode editar
   - Admin de Grupo pode editar qualquer documento DRAFT do seu Grupo
   - Super Admin pode editar qualquer documento DRAFT
   - Revisor e Reader NÃO podem editar (apenas visualizar)

2. **Lock de Edição**
   - Ao clicar em "Editar", documento é "locked" para o usuário
   - Outros Editores veem indicador: "Em edição por [Nome]"
   - Tentativa de editar documento locked exibe mensagem: "Este documento está sendo editado por [Nome]. Tente novamente mais tarde."

3. **Editor Markdown**
   - Mesma interface da criação
   - Conteúdo atual carregado
   - Auto-save a cada 1 minuto
   - Indicador de última salvamento: "Salvo às HH:MM"

4. **Edição de Metadados**
   - Pode editar: Título, Tags, Categoria, Descrição, Documentos relacionados
   - Não pode editar: Autor, Data de criação, Versão (campos read-only)
   - Pode mover para outra Pasta do mesmo Grupo

5. **Botões de Ação**
   - "Salvar e Fechar" (salva e libera lock)
   - "Visualizar" (abre preview em modal ou painel lateral)
   - "Enviar para Revisão" (transição para PENDING_APPROVAL)
   - "Deletar Documento" (se ainda não foi enviado para aprovação)

6. **Auto-save**
   - A cada 1 minuto salva automaticamente
   - Ao fechar navegador sem "Salvar e Fechar", exibe alerta: "Você tem alterações não salvas. Deseja sair mesmo assim?"
   - Se confirmado, auto-save garante que última versão foi salva

7. **Timeout de Lock**
   - Se usuário fica inativo por 30 min, lock é liberado automaticamente
   - Mensagem ao tentar salvar após timeout: "Sua sessão de edição expirou. O documento foi salvo automaticamente até [hora]."

8. **Histórico de Edições**
   - Sistema registra cada auto-save como "snapshot"
   - Possibilita recuperação em caso de perda acidental

**Testes de Aceitação:**
- [ ] Editor edita documento DRAFT com sucesso
- [ ] Auto-save funciona a cada 1 min
- [ ] Lock impede edição simultânea
- [ ] Timeout de lock funciona
- [ ] Metadados são editáveis
- [ ] Revisor não pode editar, apenas visualizar

---

[Continua com as demais User Stories do documento completo...]

---

## 📊 Resumo de Prioridades

| Prioridade | Épicos |
|-----------|--------|
| **1 (Crítico)** | Gestão de Usuários & Grupos, Gestão de Pastas, Criação e Edição de Documentos, Conversão de Documentos, Workflow de Aprovação, Dashboard e Navegação |
| **3 (Importante)** | Sistema de Comentários, Notificações, Templates |
| **5 (Desejável)** | Versionamento, Estados Avançados (DEPRECATED/ARCHIVED), Sistema de Busca, Embeddings e RAG |

---

**Total de User Stories:** 46  
**Épicos:** 13  
**Documento preparado por:** Claude (Anthropic)  
**Status:** Versão 1.0 - User Stories Completas para MVP  
