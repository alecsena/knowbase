# User Stories - ÉPICO 1: Gestão de Usuários & Grupos

**Versão:** 1.0 MVP  
**Data:** Janeiro 2026  
**Prioridade:** 1 (Crítico para MVP)  
**Status:** Planejamento

---

## 📋 Índice do Épico

- [1.1 Autenticação e Autorização](#11-autenticação-e-autorização)
- [1.2 Gestão de Usuários](#12-gestão-de-usuários)
- [1.3 Gestão de Grupos](#13-gestão-de-grupos)
- [1.4 Atribuição de Papéis](#14-atribuição-de-papéis)
- [1.5 Perfil do Usuário](#15-perfil-do-usuário)

---

## 1.1 Autenticação e Autorização

### US-1.1.1: Login de Usuário

**Como** usuário cadastrado no sistema,  
**Quero** fazer login com email e senha,  
**Para** acessar o sistema de gestão de documentos.

#### Critérios de Aceitação

**Funcional:**
- [ ] Sistema apresenta tela de login com campos "Email" e "Senha"
- [ ] Campo de email valida formato de email (validação client-side e server-side)
- [ ] Campo de senha é do tipo "password" (caracteres ocultos)
- [ ] Botão "Mostrar/Ocultar Senha" funciona corretamente
- [ ] Ao clicar "Entrar", sistema valida credenciais no backend
- [ ] Login bem-sucedido redireciona para Dashboard do usuário
- [ ] Login com credenciais inválidas exibe mensagem de erro clara: "Email ou senha incorretos"
- [ ] Sistema bloqueia login após 5 tentativas falhas consecutivas por 15 minutos
- [ ] Mensagem de bloqueio informa: "Conta temporariamente bloqueada. Tente novamente em X minutos"

**Técnico:**
- [ ] Senha é hasheada com bcrypt ou argon2 (nunca armazenada em texto plano)
- [ ] Token JWT é gerado após login bem-sucedido com expiração de 24 horas
- [ ] Token contém: user_id, email, papéis em cada grupo
- [ ] Sistema registra log de tentativas de login (sucesso e falha) com timestamp e IP
- [ ] Rate limiting: máximo 10 requisições de login por IP em 1 minuto
- [ ] HTTPS obrigatório para endpoint de login
- [ ] Proteção contra timing attacks (tempo de resposta constante)

**Segurança:**
- [ ] Proteção contra SQL Injection
- [ ] Proteção contra XSS em campos de entrada
- [ ] CSRF token implementado
- [ ] Headers de segurança configurados (X-Frame-Options, X-Content-Type-Options, etc.)

**UX:**
- [ ] Loading indicator durante validação de login
- [ ] Auto-focus no campo de email ao carregar página
- [ ] Enter key envia formulário
- [ ] Mensagens de erro aparecem abaixo do campo relevante

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** Nenhuma

---

### US-1.1.2: Logout de Usuário

**Como** usuário autenticado,  
**Quero** fazer logout do sistema,  
**Para** encerrar minha sessão de forma segura.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão/link "Sair" visível no menu do usuário (topbar)
- [ ] Ao clicar "Sair", sistema invalida token JWT
- [ ] Usuário é redirecionado para tela de login
- [ ] Mensagem de confirmação exibida: "Você saiu do sistema com sucesso"
- [ ] Tentativa de acessar página protegida após logout redireciona para login

**Técnico:**
- [ ] Token JWT é adicionado a blacklist (Redis) até expiração natural
- [ ] Blacklist de tokens expira automaticamente após tempo de vida do token (24h)
- [ ] Frontend remove token do localStorage/sessionStorage
- [ ] Backend retorna 401 Unauthorized para tokens na blacklist
- [ ] Log de logout registrado com timestamp

**UX:**
- [ ] Confirmação visual antes de logout (modal opcional: "Tem certeza?")
- [ ] Mensagem de sucesso desaparece após 3 segundos
- [ ] Não há perda de dados não salvos (avisar se houver edição em andamento)

**Prioridade:** Alta  
**Estimativa:** 2 pontos  
**Dependências:** US-1.1.1

---

### US-1.1.3: Controle de Acesso Baseado em Papéis (RBAC)

**Como** sistema,  
**Quero** validar permissões do usuário em cada ação,  
**Para** garantir que apenas usuários autorizados executem determinadas operações.

#### Critérios de Aceitação

**Funcional:**
- [ ] Sistema verifica papel do usuário antes de executar qualquer ação sensível
- [ ] Usuário só vê ações permitidas para seu papel (botões/menus condicionais)
- [ ] Tentativa de ação não autorizada retorna erro 403 Forbidden
- [ ] Mensagem de erro clara: "Você não tem permissão para executar esta ação"

**Técnico:**
- [ ] Middleware de autorização valida permissões em cada endpoint protegido
- [ ] Permissões verificadas tanto no frontend (UX) quanto backend (segurança)
- [ ] Token JWT contém lista de papéis do usuário por grupo: `{"group_id": 1, "roles": ["editor", "revisor"]}`
- [ ] Decoradores/middlewares por papel implementados: `@require_role("super_admin")`, `@require_role_in_group("admin")`
- [ ] Sistema verifica escopo do grupo: usuário só pode agir em grupos aos quais pertence
- [ ] Logs de tentativas de acesso não autorizado registrados com user_id, ação tentada, timestamp

**Matriz de Permissões Implementada:**
| Ação | Super Admin | Admin Grupo | Revisor | Editor | Reader |
|------|-------------|-------------|---------|--------|--------|
| Criar Grupo | ✅ | ❌ | ❌ | ❌ | ❌ |
| Criar Pasta | ✅ | ✅ | ❌ | ✅ | ❌ |
| Criar Documento | ✅ | ✅ | ✅ | ✅ | ❌ |
| Aprovar/Rejeitar | ✅ | ✅ | ✅ | ❌ | ❌ |
| Adicionar Comentários | ✅ | ✅ | ✅ | ❌ | ❌ |
| Ver Documentos | ✅ | ✅ | ✅ | ✅ | ✅ |

**Segurança:**
- [ ] Validação server-side sempre executada (nunca confiar apenas no frontend)
- [ ] Operações críticas logadas em audit trail
- [ ] Proteção contra privilege escalation

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-1.1.1

---

## 1.2 Gestão de Usuários

### US-1.2.1: Criar Novo Usuário (Super Admin)

**Como** Super Admin,  
**Quero** criar novos usuários no sistema,  
**Para** permitir que funcionários da organização acessem a plataforma.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Gestão de Usuários" acessível apenas para Super Admin
- [ ] Botão "Novo Usuário" abre modal/formulário
- [ ] Formulário contém campos obrigatórios:
  - Nome completo
  - Email (validação de formato)
  - Senha inicial (mínimo 8 caracteres, pelo menos 1 número e 1 caractere especial)
  - Confirmar senha (deve ser igual à senha)
- [ ] Formulário contém campos opcionais:
  - Telefone
  - Cargo/Função
- [ ] Email deve ser único no sistema (validação no backend)
- [ ] Senha inicial pode ser gerada automaticamente (botão "Gerar Senha")
- [ ] Ao criar usuário, sistema envia email de boas-vindas com instruções de primeiro acesso
- [ ] Usuário criado mas ainda não atribuído a nenhum grupo
- [ ] Mensagem de sucesso: "Usuário [Nome] criado com sucesso. Email de boas-vindas enviado."

**Técnico:**
- [ ] Endpoint: `POST /api/v1/users`
- [ ] Payload:
  ```json
  {
    "full_name": "string",
    "email": "string",
    "password": "string",
    "phone": "string|null",
    "job_title": "string|null"
  }
  ```
- [ ] Resposta: 201 Created com dados do usuário (sem senha)
- [ ] Senha hasheada com bcrypt/argon2 antes de salvar no banco
- [ ] Validações server-side:
  - Email único
  - Formato de email válido
  - Força da senha (mínimo 8 caracteres, 1 número, 1 especial)
  - Nome completo não vazio
- [ ] Email de boas-vindas enviado via fila assíncrona (Celery)
- [ ] Transação de banco de dados: rollback se envio de email falhar (ou flag `email_sent: false`)
- [ ] Log de criação de usuário: `super_admin_id`, `created_user_id`, `timestamp`

**Validações de Senha:**
- [ ] Mínimo 8 caracteres
- [ ] Pelo menos 1 letra maiúscula
- [ ] Pelo menos 1 letra minúscula
- [ ] Pelo menos 1 número
- [ ] Pelo menos 1 caractere especial (!@#$%^&*...)
- [ ] Não pode ser senha comum (ex: "Password123!", "Admin@123")

**Email de Boas-Vindas:**
- [ ] Assunto: "Bem-vindo ao Sistema de Gestão de Documentos"
- [ ] Contém: Nome do usuário, credenciais (email), link para primeiro acesso, instruções de troca de senha
- [ ] Link de primeiro acesso expira em 48 horas
- [ ] Template HTML responsivo

**UX:**
- [ ] Loading indicator ao salvar
- [ ] Validações em tempo real (email já existe, força da senha)
- [ ] Indicador visual de força de senha (fraca/média/forte)
- [ ] Botão "Copiar Senha" se senha for gerada automaticamente
- [ ] Modal fecha automaticamente após sucesso
- [ ] Lista de usuários atualiza automaticamente

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-1.1.3

---

### US-1.2.2: Listar Usuários (Super Admin)

**Como** Super Admin,  
**Quero** visualizar lista de todos os usuários do sistema,  
**Para** gerenciar usuários cadastrados.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Gestão de Usuários" exibe tabela com todos os usuários
- [ ] Colunas da tabela:
  - Nome
  - Email
  - Status (Ativo/Inativo)
  - Grupos (quantidade de grupos aos quais pertence)
  - Data de criação
  - Último acesso
  - Ações (Editar, Desativar/Ativar, Ver Detalhes)
- [ ] Paginação: 25 usuários por página (configurável: 10, 25, 50, 100)
- [ ] Ordenação por coluna (clicável): Nome, Email, Data de criação, Último acesso
- [ ] Busca por: Nome ou Email (campo de busca no topo)
- [ ] Filtros:
  - Status (Ativo/Inativo/Todos)
  - Com/Sem Grupo atribuído
  - Por Grupo específico
- [ ] Total de usuários exibido: "Mostrando X-Y de Z usuários"
- [ ] Indicador visual de status: badge verde (Ativo), cinza (Inativo)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/users`
- [ ] Query params:
  ```
  ?page=1
  &per_page=25
  &sort_by=created_at
  &sort_order=desc
  &search=João
  &status=active
  &group_id=5
  ```
- [ ] Resposta:
  ```json
  {
    "users": [
      {
        "id": 1,
        "full_name": "string",
        "email": "string",
        "status": "active|inactive",
        "groups_count": 3,
        "created_at": "ISO8601",
        "last_login_at": "ISO8601|null"
      }
    ],
    "total": 150,
    "page": 1,
    "per_page": 25,
    "total_pages": 6
  }
  ```
- [ ] Query otimizada: JOIN com grupos para contar grupos por usuário
- [ ] Index em `users.email` e `users.full_name` para busca rápida
- [ ] Cache de resultados (Redis) por 5 minutos (invalidar ao criar/editar usuário)

**UX:**
- [ ] Loading skeleton durante carregamento
- [ ] Estado vazio: "Nenhum usuário encontrado" (quando lista vazia)
- [ ] Highlight de linha ao hover
- [ ] Ícones intuitivos para ações (lápis = editar, olho = ver, toggle = ativar/desativar)
- [ ] Tooltip em ícones de ação
- [ ] Busca com debounce (300ms)

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-1.2.1

---

### US-1.2.3: Editar Usuário (Super Admin)

**Como** Super Admin,  
**Quero** editar informações de um usuário,  
**Para** manter dados atualizados ou corrigir erros.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar" na linha do usuário abre modal de edição
- [ ] Modal pré-preenchido com dados atuais do usuário
- [ ] Campos editáveis:
  - Nome completo
  - Email
  - Telefone
  - Cargo/Função
  - Status (Ativo/Inativo)
- [ ] Campo "Email" valida formato e unicidade
- [ ] NÃO é possível editar senha nesta tela (há US específica para resetar senha)
- [ ] Botão "Salvar" atualiza dados
- [ ] Mensagem de sucesso: "Usuário [Nome] atualizado com sucesso"
- [ ] Se email for alterado, usuário recebe notificação no novo email

**Técnico:**
- [ ] Endpoint: `PUT /api/v1/users/{user_id}`
- [ ] Payload:
  ```json
  {
    "full_name": "string",
    "email": "string",
    "phone": "string|null",
    "job_title": "string|null",
    "status": "active|inactive"
  }
  ```
- [ ] Resposta: 200 OK com dados atualizados
- [ ] Validações server-side:
  - Email único (exceto o próprio)
  - Formato de email válido
  - Nome completo não vazio
- [ ] Se status mudar para "inactive", sistema registra timestamp de desativação
- [ ] Se email mudar, dispara email de confirmação de mudança
- [ ] Log de edição: `admin_id`, `edited_user_id`, `changed_fields`, `timestamp`
- [ ] Cache de usuários invalidado após edição

**Notificação de Mudança de Email:**
- [ ] Email enviado para **ambos** os endereços (antigo e novo)
- [ ] Assunto: "Seu email foi alterado no Sistema de Documentos"
- [ ] Contém: Antigo email, novo email, data da mudança, quem alterou (Super Admin)

**UX:**
- [ ] Loading indicator ao salvar
- [ ] Validações em tempo real
- [ ] Botão "Cancelar" fecha modal sem salvar
- [ ] Confirmação se houver mudanças não salvas ao fechar modal
- [ ] Modal fecha automaticamente após sucesso

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-1.2.2

---

### US-1.2.4: Desativar Usuário (Super Admin)

**Como** Super Admin,  
**Quero** desativar um usuário,  
**Para** impedir acesso ao sistema sem deletar dados históricos.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Desativar" visível apenas para usuários com status "Ativo"
- [ ] Ao clicar "Desativar", modal de confirmação aparece
- [ ] Modal contém:
  - Mensagem: "Tem certeza que deseja desativar [Nome do Usuário]?"
  - Aviso: "O usuário não poderá mais fazer login, mas seus documentos e histórico serão preservados."
  - Botões: "Cancelar" e "Confirmar Desativação"
- [ ] Ao confirmar, usuário é desativado (status → inactive)
- [ ] Mensagem de sucesso: "Usuário [Nome] desativado com sucesso"
- [ ] Lista de usuários atualiza automaticamente
- [ ] Badge de status muda para "Inativo" (cinza)

**Técnico:**
- [ ] Endpoint: `PATCH /api/v1/users/{user_id}/deactivate`
- [ ] Resposta: 200 OK
- [ ] Atualização no banco: `status = 'inactive'`, `deactivated_at = NOW()`
- [ ] Usuário desativado não pode fazer login (validação no endpoint de login)
- [ ] Tokens JWT existentes do usuário são invalidados (adicionados a blacklist)
- [ ] Sessões ativas do usuário são encerradas
- [ ] Documentos criados pelo usuário **não são afetados**
- [ ] Log de desativação: `admin_id`, `deactivated_user_id`, `reason`, `timestamp`
- [ ] Notificação enviada ao usuário por email informando desativação

**Efeitos da Desativação:**
- [ ] Usuário não pode fazer login
- [ ] Usuário removido de todas as atribuições de tarefas futuras
- [ ] Documentos em DRAFT do usuário ficam visíveis para Admin de Grupo
- [ ] Histórico de ações do usuário preservado (versionamento, comentários, etc.)
- [ ] Menções ao usuário em comentários permanecem

**UX:**
- [ ] Confirmação clara antes da ação
- [ ] Loading indicator durante desativação
- [ ] Feedback visual imediato (linha fica cinza, badge muda)

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-1.2.2

---

### US-1.2.5: Reativar Usuário (Super Admin)

**Como** Super Admin,  
**Quero** reativar um usuário desativado,  
**Para** permitir que ele volte a acessar o sistema.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Reativar" visível apenas para usuários com status "Inativo"
- [ ] Ao clicar "Reativar", modal de confirmação aparece
- [ ] Modal contém:
  - Mensagem: "Tem certeza que deseja reativar [Nome do Usuário]?"
  - Botões: "Cancelar" e "Confirmar Reativação"
- [ ] Ao confirmar, usuário é reativado (status → active)
- [ ] Mensagem de sucesso: "Usuário [Nome] reativado com sucesso"
- [ ] Lista de usuários atualiza automaticamente
- [ ] Badge de status muda para "Ativo" (verde)

**Técnico:**
- [ ] Endpoint: `PATCH /api/v1/users/{user_id}/activate`
- [ ] Resposta: 200 OK
- [ ] Atualização no banco: `status = 'active'`, `reactivated_at = NOW()`
- [ ] Usuário pode fazer login novamente
- [ ] Permissões e atribuições de grupo são restauradas
- [ ] Log de reativação: `admin_id`, `reactivated_user_id`, `timestamp`
- [ ] Notificação enviada ao usuário por email informando reativação

**Email de Reativação:**
- [ ] Assunto: "Sua conta foi reativada"
- [ ] Contém: Mensagem de reativação, link para login, instruções de troca de senha (se necessário)

**UX:**
- [ ] Confirmação clara antes da ação
- [ ] Loading indicator durante reativação
- [ ] Feedback visual imediato

**Prioridade:** Média  
**Estimativa:** 2 pontos  
**Dependências:** US-1.2.4

---

### US-1.2.6: Resetar Senha de Usuário (Super Admin)

**Como** Super Admin,  
**Quero** resetar a senha de um usuário,  
**Para** permitir que ele recupere acesso à conta.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Resetar Senha" disponível na página de detalhes do usuário
- [ ] Ao clicar, modal de confirmação aparece
- [ ] Modal contém:
  - Mensagem: "Enviar email de recuperação de senha para [Email do Usuário]?"
  - Botões: "Cancelar" e "Enviar Email"
- [ ] Ao confirmar, sistema gera token de reset de senha
- [ ] Email de reset enviado para o usuário
- [ ] Token de reset expira em 24 horas
- [ ] Mensagem de sucesso: "Email de recuperação enviado para [Email]"

**Técnico:**
- [ ] Endpoint: `POST /api/v1/users/{user_id}/reset-password`
- [ ] Resposta: 200 OK
- [ ] Token UUID gerado e armazenado com: `user_id`, `token`, `expires_at`
- [ ] Email enviado via fila assíncrona com link: `https://app.com/reset-password?token={token}`
- [ ] Endpoint de validação de token: `GET /api/v1/auth/validate-reset-token/{token}`
- [ ] Endpoint de definir nova senha: `POST /api/v1/auth/reset-password`
  ```json
  {
    "token": "uuid",
    "new_password": "string",
    "confirm_password": "string"
  }
  ```
- [ ] Após reset bem-sucedido, token é invalidado
- [ ] Todos os tokens JWT anteriores do usuário são invalidados (blacklist)
- [ ] Log de reset: `admin_id`, `target_user_id`, `timestamp`

**Email de Reset:**
- [ ] Assunto: "Solicitação de Redefinição de Senha"
- [ ] Contém: Link de reset, tempo de expiração (24h), aviso de segurança
- [ ] Template HTML responsivo

**Página de Reset (Frontend):**
- [ ] Validação de token ao carregar página
- [ ] Se token inválido/expirado: mensagem de erro + link para solicitar novo
- [ ] Formulário com:
  - Nova senha (com validação de força)
  - Confirmar nova senha
  - Indicador de força de senha
- [ ] Ao salvar: senha atualizada, redirecionado para login com mensagem de sucesso

**UX:**
- [ ] Loading indicator ao enviar email
- [ ] Mensagem clara de sucesso

**Prioridade:** Média  
**Estimativa:** 5 pontos  
**Dependências:** US-1.2.1

---

## 1.3 Gestão de Grupos

### US-1.3.1: Criar Novo Grupo (Super Admin)

**Como** Super Admin,  
**Quero** criar novos grupos (setores) na organização,  
**Para** organizar documentos e usuários por áreas/departamentos.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Gestão de Grupos" acessível apenas para Super Admin
- [ ] Botão "Novo Grupo" abre modal/formulário
- [ ] Formulário contém campos obrigatórios:
  - Nome do Grupo
  - Descrição
- [ ] Formulário contém campos opcionais:
  - Cor/Ícone do grupo (para identificação visual)
- [ ] Nome do grupo deve ser único no sistema
- [ ] Ao criar grupo, sistema cria estrutura de pastas raiz automaticamente
- [ ] Mensagem de sucesso: "Grupo [Nome] criado com sucesso"
- [ ] Grupo criado sem usuários inicialmente (atribuição em US separada)

**Técnico:**
- [ ] Endpoint: `POST /api/v1/groups`
- [ ] Payload:
  ```json
  {
    "name": "string",
    "description": "string",
    "color": "string|null",
    "icon": "string|null"
  }
  ```
- [ ] Resposta: 201 Created com dados do grupo
- [ ] Validações server-side:
  - Nome único
  - Nome não vazio (mínimo 3 caracteres)
  - Descrição não vazia
- [ ] Ao criar grupo, criar registro em `groups` table
- [ ] Log de criação: `super_admin_id`, `created_group_id`, `timestamp`
- [ ] Estrutura de pastas raiz criada automaticamente (ou permite pasta raiz vazia)

**Schema de Banco (groups):**
```sql
CREATE TABLE groups (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  description TEXT NOT NULL,
  color VARCHAR(7),  -- Hex color code
  icon VARCHAR(50),   -- Icon name (ex: "folder", "briefcase")
  created_at TIMESTAMP DEFAULT NOW(),
  created_by INTEGER REFERENCES users(id),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**UX:**
- [ ] Color picker para seleção de cor
- [ ] Icon picker com preview (biblioteca de ícones: Font Awesome, Material Icons)
- [ ] Preview do grupo (card com nome, cor, ícone)
- [ ] Validação em tempo real (nome único)
- [ ] Loading indicator ao salvar
- [ ] Modal fecha automaticamente após sucesso

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-1.1.3

---

### US-1.3.2: Listar Grupos (Super Admin e Usuários)

**Como** Super Admin ou usuário com acesso,  
**Quero** visualizar lista de grupos,  
**Para** navegar e gerenciar grupos disponíveis.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Grupos" exibe cards ou tabela com todos os grupos
- [ ] Para Super Admin: vê **todos** os grupos do sistema
- [ ] Para outros usuários: vê apenas grupos aos quais pertence
- [ ] Card/linha do grupo exibe:
  - Nome do grupo
  - Descrição (truncada, com tooltip)
  - Ícone e cor
  - Quantidade de usuários
  - Quantidade de documentos
  - Data de criação
  - Ações (se Super Admin: Editar, Ver Detalhes)
- [ ] Busca por nome de grupo (campo de busca no topo)
- [ ] Ordenação: Nome (A-Z), Data de criação, Quantidade de documentos
- [ ] Layout em cards (grid responsivo) ou tabela (toggle view)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/groups`
- [ ] Query params:
  ```
  ?search=RH
  &sort_by=name
  &sort_order=asc
  ```
- [ ] Resposta:
  ```json
  {
    "groups": [
      {
        "id": 1,
        "name": "string",
        "description": "string",
        "color": "#3B82F6",
        "icon": "folder",
        "users_count": 15,
        "documents_count": 230,
        "created_at": "ISO8601"
      }
    ],
    "total": 8
  }
  ```
- [ ] Para Super Admin: query retorna todos os grupos
- [ ] Para usuários: query filtra apenas grupos aos quais pertencem (JOIN com `user_groups`)
- [ ] Agregações de contagem:
  - `users_count`: COUNT de `user_groups` WHERE `group_id`
  - `documents_count`: COUNT de `documents` WHERE `group_id`
- [ ] Cache de resultados (Redis) por 5 minutos

**UX:**
- [ ] Loading skeleton durante carregamento
- [ ] Estado vazio: "Nenhum grupo encontrado"
- [ ] Cards com hover effect
- [ ] Cor do grupo aplicada em borda ou fundo do card
- [ ] Ícone exibido em tamanho apropriado
- [ ] Click no card abre página de detalhes do grupo

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-1.3.1

---

### US-1.3.3: Editar Grupo (Super Admin)

**Como** Super Admin,  
**Quero** editar informações de um grupo,  
**Para** manter dados atualizados ou corrigir erros.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar" na página de detalhes do grupo (ou na lista)
- [ ] Modal de edição pré-preenchido com dados atuais
- [ ] Campos editáveis:
  - Nome do grupo
  - Descrição
  - Cor
  - Ícone
- [ ] Nome do grupo deve ser único (validação)
- [ ] Botão "Salvar" atualiza dados
- [ ] Mensagem de sucesso: "Grupo [Nome] atualizado com sucesso"

**Técnico:**
- [ ] Endpoint: `PUT /api/v1/groups/{group_id}`
- [ ] Payload:
  ```json
  {
    "name": "string",
    "description": "string",
    "color": "string|null",
    "icon": "string|null"
  }
  ```
- [ ] Resposta: 200 OK com dados atualizados
- [ ] Validações server-side:
  - Nome único (exceto o próprio)
  - Nome não vazio (mínimo 3 caracteres)
- [ ] Log de edição: `admin_id`, `edited_group_id`, `changed_fields`, `timestamp`
- [ ] Cache de grupos invalidado

**UX:**
- [ ] Color picker e icon picker funcionais
- [ ] Preview do grupo atualizado em tempo real
- [ ] Loading indicator ao salvar
- [ ] Validações em tempo real
- [ ] Modal fecha automaticamente após sucesso

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-1.3.2

---

### US-1.3.4: Ver Detalhes do Grupo (Super Admin e Admin de Grupo)

**Como** Super Admin ou Admin de Grupo,  
**Quero** ver detalhes completos de um grupo,  
**Para** gerenciar usuários, pastas e documentos do grupo.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página de detalhes do grupo acessível ao clicar no card/nome do grupo
- [ ] Header da página exibe:
  - Nome do grupo (com ícone e cor)
  - Descrição completa
  - Breadcrumb: "Grupos > [Nome do Grupo]"
- [ ] Tabs/seções:
  - **Usuários:** Lista de usuários do grupo com seus papéis
  - **Pastas:** Estrutura de pastas do grupo
  - **Documentos:** Documentos recentes/principais
  - **Estatísticas:** Métricas do grupo (total docs, docs publicados, etc.)
- [ ] Seção "Usuários":
  - Tabela com: Nome, Email, Papéis, Data de adição
  - Botão "Adicionar Usuário" (Admin de Grupo e Super Admin)
  - Botão "Editar Papéis" em cada linha
  - Botão "Remover do Grupo"
- [ ] Seção "Pastas":
  - Árvore de pastas (hierarquia visual)
  - Botão "Nova Pasta"
  - Click na pasta navega para documentos da pasta
- [ ] Seção "Documentos":
  - Lista de documentos mais recentes (últimos 10)
  - Link "Ver Todos os Documentos"
- [ ] Seção "Estatísticas":
  - Total de documentos
  - Documentos publicados
  - Documentos em rascunho
  - Documentos pendentes de aprovação
  - Gráfico de documentos por status (pizza ou barras)

**Técnico:**
- [ ] Endpoint: `GET /api/v1/groups/{group_id}`
- [ ] Resposta:
  ```json
  {
    "id": 1,
    "name": "string",
    "description": "string",
    "color": "#3B82F6",
    "icon": "folder",
    "created_at": "ISO8601",
    "statistics": {
      "total_documents": 230,
      "published_documents": 180,
      "draft_documents": 30,
      "pending_approval_documents": 20
    },
    "users": [
      {
        "id": 1,
        "full_name": "string",
        "email": "string",
        "roles": ["editor", "revisor"],
        "added_at": "ISO8601"
      }
    ],
    "folders": [
      {
        "id": 1,
        "name": "Políticas",
        "parent_id": null,
        "documents_count": 15
      }
    ],
    "recent_documents": [...]
  }
  ```
- [ ] Autorização: Super Admin vê todos os grupos, Admin de Grupo vê apenas grupos que administra
- [ ] Agregações de estatísticas via query otimizada (COUNT com GROUP BY status)

**UX:**
- [ ] Loading skeleton durante carregamento
- [ ] Tabs com navegação clara
- [ ] Gráficos interativos (hover mostra valores)
- [ ] Actions buttons claramente visíveis
- [ ] Breadcrumb clicável

**Prioridade:** Alta  
**Estimativa:** 8 pontos  
**Dependências:** US-1.3.2, US-1.4.1

---

## 1.4 Atribuição de Papéis

### US-1.4.1: Atribuir Usuário a Grupo com Papéis (Super Admin e Admin de Grupo)

**Como** Super Admin ou Admin de Grupo,  
**Quero** adicionar usuários a um grupo com papéis específicos,  
**Para** dar acesso e permissões aos documentos do grupo.

#### Critérios de Aceitação

**Funcional:**
- [ ] Na página de detalhes do grupo, botão "Adicionar Usuário"
- [ ] Modal contém:
  - Dropdown/autocomplete para selecionar usuário (busca por nome ou email)
  - Checkboxes para selecionar papéis:
    - ☐ Admin de Grupo
    - ☐ Revisor
    - ☐ Editor
    - ☐ Reader
  - Usuário pode ter múltiplos papéis selecionados
  - Pelo menos 1 papel deve ser selecionado
- [ ] Dropdown mostra apenas usuários que NÃO estão no grupo
- [ ] Ao salvar, usuário é adicionado ao grupo com papéis selecionados
- [ ] Mensagem de sucesso: "Usuário [Nome] adicionado ao grupo [Grupo] com papéis: [Lista de Papéis]"
- [ ] Lista de usuários do grupo atualiza automaticamente
- [ ] Usuário recebe notificação por email informando adição ao grupo

**Técnico:**
- [ ] Endpoint: `POST /api/v1/groups/{group_id}/users`
- [ ] Payload:
  ```json
  {
    "user_id": 1,
    "roles": ["editor", "revisor"]
  }
  ```
- [ ] Resposta: 201 Created
- [ ] Validações server-side:
  - Usuário existe
  - Usuário NÃO está no grupo
  - Pelo menos 1 papel selecionado
  - Papéis válidos: ["super_admin", "admin", "revisor", "editor", "reader"]
  - Super Admin pode atribuir qualquer papel
  - Admin de Grupo NÃO pode atribuir papel "super_admin"
- [ ] Tabela `user_groups`:
  ```sql
  CREATE TABLE user_groups (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    roles JSONB NOT NULL,  -- ["editor", "revisor"]
    added_at TIMESTAMP DEFAULT NOW(),
    added_by INTEGER REFERENCES users(id),
    UNIQUE(user_id, group_id)
  );
  ```
- [ ] Log de atribuição: `admin_id`, `user_id`, `group_id`, `roles`, `timestamp`
- [ ] Email de notificação enviado ao usuário via fila assíncrona

**Email de Notificação:**
- [ ] Assunto: "Você foi adicionado ao grupo [Nome do Grupo]"
- [ ] Contém: Nome do grupo, papéis atribuídos, link para acessar grupo, instruções

**UX:**
- [ ] Autocomplete com debounce (300ms)
- [ ] Preview dos papéis selecionados
- [ ] Indicador visual de papéis (badges)
- [ ] Loading indicator ao salvar
- [ ] Modal fecha automaticamente após sucesso

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-1.3.4

---

### US-1.4.2: Editar Papéis de Usuário no Grupo (Super Admin e Admin de Grupo)

**Como** Super Admin ou Admin de Grupo,  
**Quero** editar os papéis de um usuário em um grupo,  
**Para** ajustar permissões conforme necessário.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar Papéis" na linha do usuário na lista de usuários do grupo
- [ ] Modal de edição exibe:
  - Nome e email do usuário (read-only)
  - Checkboxes com papéis atuais pré-selecionados
  - Pelo menos 1 papel deve permanecer selecionado
- [ ] Ao salvar, papéis são atualizados
- [ ] Mensagem de sucesso: "Papéis de [Nome] atualizados no grupo [Grupo]"
- [ ] Usuário recebe notificação por email informando mudança de papéis

**Técnico:**
- [ ] Endpoint: `PUT /api/v1/groups/{group_id}/users/{user_id}`
- [ ] Payload:
  ```json
  {
    "roles": ["editor", "revisor", "admin"]
  }
  ```
- [ ] Resposta: 200 OK
- [ ] Validações server-side:
  - Pelo menos 1 papel selecionado
  - Papéis válidos
  - Admin de Grupo NÃO pode remover/adicionar papel "super_admin"
- [ ] Atualização em `user_groups`: UPDATE `roles` WHERE `user_id` AND `group_id`
- [ ] Log de edição: `admin_id`, `user_id`, `group_id`, `old_roles`, `new_roles`, `timestamp`

**Email de Notificação:**
- [ ] Assunto: "Seus papéis foram atualizados no grupo [Nome do Grupo]"
- [ ] Contém: Papéis anteriores, papéis novos, data da mudança

**UX:**
- [ ] Preview dos papéis (badges)
- [ ] Loading indicator ao salvar
- [ ] Modal fecha automaticamente após sucesso

**Prioridade:** Alta  
**Estimativa:** 3 pontos  
**Dependências:** US-1.4.1

---

### US-1.4.3: Remover Usuário de Grupo (Super Admin e Admin de Grupo)

**Como** Super Admin ou Admin de Grupo,  
**Quero** remover um usuário de um grupo,  
**Para** revogar acesso aos documentos desse grupo.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Remover do Grupo" na linha do usuário
- [ ] Modal de confirmação:
  - Mensagem: "Tem certeza que deseja remover [Nome] do grupo [Grupo]?"
  - Aviso: "O usuário perderá acesso a todos os documentos deste grupo."
  - Botões: "Cancelar" e "Confirmar Remoção"
- [ ] Ao confirmar, usuário é removido do grupo
- [ ] Mensagem de sucesso: "Usuário [Nome] removido do grupo [Grupo]"
- [ ] Lista de usuários do grupo atualiza automaticamente
- [ ] Usuário recebe notificação por email informando remoção

**Técnico:**
- [ ] Endpoint: `DELETE /api/v1/groups/{group_id}/users/{user_id}`
- [ ] Resposta: 204 No Content
- [ ] Deleção em `user_groups`: DELETE WHERE `user_id` AND `group_id`
- [ ] Documentos criados pelo usuário no grupo **não são deletados**
- [ ] Documentos em DRAFT do usuário ficam acessíveis para Admins do grupo
- [ ] Comentários do usuário permanecem (autor preservado)
- [ ] Log de remoção: `admin_id`, `removed_user_id`, `group_id`, `timestamp`

**Email de Notificação:**
- [ ] Assunto: "Você foi removido do grupo [Nome do Grupo]"
- [ ] Contém: Nome do grupo, data da remoção, contato para dúvidas

**UX:**
- [ ] Confirmação clara antes da ação
- [ ] Loading indicator durante remoção
- [ ] Feedback visual imediato

**Prioridade:** Alta  
**Estimativa:** 3 pontos  
**Dependências:** US-1.4.1

---

## 1.5 Perfil do Usuário

### US-1.5.1: Ver Meu Perfil

**Como** usuário autenticado,  
**Quero** visualizar meu perfil,  
**Para** ver minhas informações e grupos aos quais pertenço.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Meu Perfil" acessível via menu do usuário (topbar)
- [ ] Exibe informações:
  - Nome completo
  - Email
  - Telefone
  - Cargo/Função
  - Data de criação da conta
  - Último login
- [ ] Seção "Meus Grupos":
  - Lista de grupos aos quais pertence
  - Para cada grupo: Nome, papéis, data de adição
  - Click no grupo navega para detalhes do grupo
- [ ] Botão "Editar Perfil"

**Técnico:**
- [ ] Endpoint: `GET /api/v1/users/me`
- [ ] Resposta:
  ```json
  {
    "id": 1,
    "full_name": "string",
    "email": "string",
    "phone": "string|null",
    "job_title": "string|null",
    "created_at": "ISO8601",
    "last_login_at": "ISO8601",
    "groups": [
      {
        "id": 1,
        "name": "RH",
        "roles": ["editor", "revisor"],
        "added_at": "ISO8601"
      }
    ]
  }
  ```
- [ ] Autenticação via JWT (usuário vê apenas próprio perfil)

**UX:**
- [ ] Layout limpo e organizado
- [ ] Avatar/foto do usuário (iniciais se não houver foto)
- [ ] Badges de papéis com cores distintas
- [ ] Ícones dos grupos exibidos

**Prioridade:** Média  
**Estimativa:** 3 pontos  
**Dependências:** US-1.1.1

---

### US-1.5.2: Editar Meu Perfil

**Como** usuário autenticado,  
**Quero** editar meu perfil,  
**Para** manter dados pessoais atualizados.

#### Critérios de Aceitação

**Funcional:**
- [ ] Botão "Editar Perfil" abre modal/formulário de edição
- [ ] Campos editáveis:
  - Nome completo
  - Telefone
  - Cargo/Função
- [ ] Email NÃO é editável pelo usuário (apenas Super Admin pode alterar)
- [ ] Botão "Salvar" atualiza dados
- [ ] Mensagem de sucesso: "Perfil atualizado com sucesso"

**Técnico:**
- [ ] Endpoint: `PUT /api/v1/users/me`
- [ ] Payload:
  ```json
  {
    "full_name": "string",
    "phone": "string|null",
    "job_title": "string|null"
  }
  ```
- [ ] Resposta: 200 OK com dados atualizados
- [ ] Validações server-side:
  - Nome completo não vazio
  - Telefone no formato válido (se fornecido)
- [ ] Log de edição: `user_id`, `changed_fields`, `timestamp`

**UX:**
- [ ] Validações em tempo real
- [ ] Loading indicator ao salvar
- [ ] Modal fecha automaticamente após sucesso

**Prioridade:** Baixa  
**Estimativa:** 2 pontos  
**Dependências:** US-1.5.1

---

### US-1.5.3: Alterar Minha Senha

**Como** usuário autenticado,  
**Quero** alterar minha senha,  
**Para** manter minha conta segura.

#### Critérios de Aceitação

**Funcional:**
- [ ] Página "Meu Perfil" contém seção "Segurança"
- [ ] Botão "Alterar Senha" abre modal
- [ ] Formulário contém:
  - Senha atual (obrigatória)
  - Nova senha (validação de força)
  - Confirmar nova senha (deve ser igual)
- [ ] Indicador de força de senha exibido em tempo real
- [ ] Botão "Salvar" altera senha
- [ ] Mensagem de sucesso: "Senha alterada com sucesso. Você será redirecionado para fazer login novamente."
- [ ] Após sucesso, usuário é deslogado e redirecionado para login

**Técnico:**
- [ ] Endpoint: `POST /api/v1/users/me/change-password`
- [ ] Payload:
  ```json
  {
    "current_password": "string",
    "new_password": "string",
    "confirm_password": "string"
  }
  ```
- [ ] Resposta: 200 OK
- [ ] Validações server-side:
  - Senha atual correta (hash verification)
  - Nova senha diferente da atual
  - Força da senha (mínimo 8 caracteres, 1 número, 1 especial)
  - Nova senha = Confirmar senha
- [ ] Após alteração:
  - Senha hasheada e atualizada no banco
  - Todos os tokens JWT do usuário invalidados (blacklist)
  - Log de alteração: `user_id`, `timestamp`, `ip_address`
- [ ] Email de notificação enviado: "Sua senha foi alterada"

**Email de Notificação:**
- [ ] Assunto: "Sua senha foi alterada"
- [ ] Contém: Data e hora da mudança, IP do dispositivo, link de segurança (se não foi você)

**UX:**
- [ ] Senha atual com toggle "mostrar/ocultar"
- [ ] Indicador de força de senha (barra colorida)
- [ ] Validações em tempo real
- [ ] Loading indicator ao salvar
- [ ] Confirmação antes de deslogar

**Prioridade:** Média  
**Estimativa:** 5 pontos  
**Dependências:** US-1.5.1

---

## 📊 Resumo do Épico 1

### Estatísticas

- **Total de User Stories:** 19
- **Estimativa Total:** 86 pontos
- **Prioridade:** Crítica (1)

### Distribuição de Prioridades

- **Crítica:** 4 histórias (21%)
- **Alta:** 9 histórias (47%)
- **Média:** 5 histórias (26%)
- **Baixa:** 1 história (6%)

### Dependências Principais

```
US-1.1.1 (Login)
  └── US-1.1.2 (Logout)
  └── US-1.1.3 (RBAC)
       └── US-1.2.1 (Criar Usuário)
            └── US-1.2.2 (Listar Usuários)
                 └── US-1.2.3 (Editar Usuário)
                 └── US-1.2.4 (Desativar)
                      └── US-1.2.5 (Reativar)
       └── US-1.3.1 (Criar Grupo)
            └── US-1.3.2 (Listar Grupos)
                 └── US-1.3.3 (Editar Grupo)
                 └── US-1.3.4 (Ver Detalhes)
                      └── US-1.4.1 (Atribuir Usuário)
                           └── US-1.4.2 (Editar Papéis)
                           └── US-1.4.3 (Remover Usuário)
```

### Checklist de Implementação

#### Fase 1 - Autenticação (Sprint 1)
- [ ] US-1.1.1: Login de Usuário
- [ ] US-1.1.2: Logout de Usuário
- [ ] US-1.1.3: Controle de Acesso (RBAC)

#### Fase 2 - Gestão de Usuários (Sprint 2)
- [ ] US-1.2.1: Criar Novo Usuário
- [ ] US-1.2.2: Listar Usuários
- [ ] US-1.2.3: Editar Usuário
- [ ] US-1.2.4: Desativar Usuário
- [ ] US-1.2.5: Reativar Usuário
- [ ] US-1.2.6: Resetar Senha

#### Fase 3 - Gestão de Grupos (Sprint 3)
- [ ] US-1.3.1: Criar Novo Grupo
- [ ] US-1.3.2: Listar Grupos
- [ ] US-1.3.3: Editar Grupo
- [ ] US-1.3.4: Ver Detalhes do Grupo

#### Fase 4 - Atribuição de Papéis (Sprint 4)
- [ ] US-1.4.1: Atribuir Usuário a Grupo
- [ ] US-1.4.2: Editar Papéis de Usuário
- [ ] US-1.4.3: Remover Usuário de Grupo

#### Fase 5 - Perfil do Usuário (Sprint 5)
- [ ] US-1.5.1: Ver Meu Perfil
- [ ] US-1.5.2: Editar Meu Perfil
- [ ] US-1.5.3: Alterar Minha Senha

---

## 🎯 Próximos Passos

1. **Validação:** Revisar histórias com stakeholders
2. **Refinamento:** Adicionar detalhes técnicos específicos do projeto
3. **Priorização:** Ajustar ordem de implementação se necessário
4. **Desenvolvimento:** Iniciar Sprint 1 com histórias de autenticação

---

**Épico preparado por:** Claude (Anthropic)  
**Revisão:** Pendente  
**Status:** Pronto para Desenvolvimento  
**Próximo Épico:** ÉPICO 2 - Gestão de Documentos (CRUD)

