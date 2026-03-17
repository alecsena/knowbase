# API REST - Especificação de Endpoints

**Sistema de Gestão de Documentos e Conhecimento**  
**Versão da API:** v1  
**Base URL:** `https://api.documentos.empresa.com/api/v1`  
**Protocolo:** HTTPS  
**Formato:** JSON  
**Autenticação:** JWT Bearer Token

---

## 📋 Índice

1. [Autenticação](#1-autenticação)
2. [Usuários](#2-usuários)
3. [Grupos](#3-grupos)
4. [Pastas](#4-pastas)
5. [Documentos](#5-documentos)
6. [Templates](#6-templates)
7. [Comentários](#7-comentários)
8. [Workflow de Aprovação](#8-workflow-de-aprovação)
9. [Conversão de Documentos](#9-conversão-de-documentos)
10. [Notificações](#10-notificações)
11. [Relatórios](#11-relatórios)
12. [Busca](#12-busca)
13. [Upload de Arquivos](#13-upload-de-arquivos)

---

## 🔐 Autenticação

Todos os endpoints (exceto `/auth/login`) requerem autenticação via JWT Bearer Token.

### Header de Autenticação
```http
Authorization: Bearer <token>
```

### Token JWT
- **Algoritmo:** HS256
- **Expiração:** 24 horas
- **Payload:**
  ```json
  {
    "user_id": 123,
    "email": "joao@empresa.com",
    "roles": ["editor", "revisor"],
    "groups": [1, 2, 3],
    "exp": 1705536000
  }
  ```

---

## 1. Autenticação

### 1.1 Login

```http
POST /auth/login
```

**Descrição:** Autentica usuário e retorna JWT token.

**Request Body:**
```json
{
  "email": "joao@empresa.com",
  "password": "SenhaForte123!"
}
```

**Response 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": 123,
    "name": "João Silva",
    "email": "joao@empresa.com",
    "groups": [
      {
        "id": 1,
        "name": "RH",
        "roles": ["editor", "revisor"]
      }
    ]
  }
}
```

**Response 401 Unauthorized:**
```json
{
  "error": "invalid_credentials",
  "message": "Email ou senha incorretos"
}
```

**Response 429 Too Many Requests:**
```json
{
  "error": "too_many_attempts",
  "message": "Muitas tentativas de login. Tente novamente em 15 minutos.",
  "retry_after": 900
}
```

**Rate Limit:** 10 tentativas por IP a cada 15 minutos

---

### 1.2 Logout

```http
POST /auth/logout
```

**Descrição:** Invalida token JWT atual (adiciona à blacklist).

**Headers:**
```http
Authorization: Bearer <token>
```

**Response 204 No Content**

---

### 1.3 Refresh Token

```http
POST /auth/refresh
```

**Descrição:** Renova token JWT antes da expiração.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

---

### 1.4 Solicitar Reset de Senha

```http
POST /auth/reset-password
```

**Descrição:** Envia email com link de reset de senha.

**Request Body:**
```json
{
  "email": "joao@empresa.com"
}
```

**Response 200 OK:**
```json
{
  "message": "Se o email existir, você receberá instruções para resetar sua senha."
}
```

**Nota:** Sempre retorna 200 por segurança (não revela se email existe)

---

### 1.5 Confirmar Reset de Senha

```http
POST /auth/reset-password/confirm
```

**Descrição:** Define nova senha usando token de reset.

**Request Body:**
```json
{
  "token": "550e8400-e29b-41d4-a716-446655440000",
  "new_password": "NovaSenhaForte123!"
}
```

**Response 200 OK:**
```json
{
  "message": "Senha alterada com sucesso"
}
```

**Response 400 Bad Request:**
```json
{
  "error": "invalid_token",
  "message": "Token inválido ou expirado"
}
```

---

## 2. Usuários

### 2.1 Criar Usuário

```http
POST /users
```

**Descrição:** Cria novo usuário (apenas Super Admin).

**Autorização:** `super_admin`

**Request Body:**
```json
{
  "full_name": "Maria Santos",
  "email": "maria@empresa.com",
  "password": "SenhaForte123!",
  "phone": "+55 11 98765-4321",
  "job_title": "Analista de RH"
}
```

**Response 201 Created:**
```json
{
  "id": 124,
  "full_name": "Maria Santos",
  "email": "maria@empresa.com",
  "phone": "+55 11 98765-4321",
  "job_title": "Analista de RH",
  "status": "active",
  "created_at": "2024-01-17T10:30:00Z"
}
```

**Response 400 Bad Request:**
```json
{
  "error": "validation_error",
  "message": "Dados inválidos",
  "details": {
    "email": ["Email já existe"],
    "password": ["Senha deve ter no mínimo 8 caracteres"]
  }
}
```

---

### 2.2 Listar Usuários

```http
GET /users
```

**Descrição:** Lista usuários com paginação e filtros.

**Autorização:** `super_admin`

**Query Parameters:**
- `page` (integer, default: 1) - Número da página
- `per_page` (integer, default: 25, max: 100) - Itens por página
- `search` (string) - Busca por nome ou email
- `status` (string: active|inactive) - Filtrar por status
- `group_id` (integer) - Filtrar por grupo
- `sort_by` (string: name|email|created_at, default: name) - Ordenação
- `sort_order` (string: asc|desc, default: asc) - Direção

**Exemplo:**
```http
GET /users?page=1&per_page=25&search=silva&status=active&sort_by=name&sort_order=asc
```

**Response 200 OK:**
```json
{
  "users": [
    {
      "id": 123,
      "full_name": "João Silva",
      "email": "joao@empresa.com",
      "phone": "+55 11 91234-5678",
      "job_title": "Gerente de Projetos",
      "status": "active",
      "groups": [
        {
          "id": 1,
          "name": "RH",
          "roles": ["editor"]
        }
      ],
      "created_at": "2024-01-01T10:00:00Z",
      "last_login_at": "2024-01-17T09:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 150,
    "total_pages": 6
  }
}
```

---

### 2.3 Obter Usuário por ID

```http
GET /users/{user_id}
```

**Descrição:** Retorna detalhes de um usuário.

**Autorização:** `super_admin` ou próprio usuário

**Response 200 OK:**
```json
{
  "id": 123,
  "full_name": "João Silva",
  "email": "joao@empresa.com",
  "phone": "+55 11 91234-5678",
  "job_title": "Gerente de Projetos",
  "status": "active",
  "groups": [
    {
      "id": 1,
      "name": "RH",
      "roles": ["editor", "revisor"]
    }
  ],
  "created_at": "2024-01-01T10:00:00Z",
  "last_login_at": "2024-01-17T09:15:00Z",
  "stats": {
    "documents_created": 45,
    "comments_added": 120,
    "documents_reviewed": 30
  }
}
```

---

### 2.4 Atualizar Usuário

```http
PUT /users/{user_id}
```

**Descrição:** Atualiza dados do usuário.

**Autorização:** `super_admin`

**Request Body:**
```json
{
  "full_name": "João Silva Santos",
  "phone": "+55 11 91234-5678",
  "job_title": "Gerente Sênior de Projetos"
}
```

**Response 200 OK:**
```json
{
  "id": 123,
  "full_name": "João Silva Santos",
  "email": "joao@empresa.com",
  "phone": "+55 11 91234-5678",
  "job_title": "Gerente Sênior de Projetos",
  "updated_at": "2024-01-17T10:30:00Z"
}
```

---

### 2.5 Desativar Usuário

```http
PATCH /users/{user_id}/deactivate
```

**Descrição:** Desativa usuário (soft delete).

**Autorização:** `super_admin`

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "inactive",
  "deactivated_at": "2024-01-17T10:30:00Z"
}
```

---

### 2.6 Reativar Usuário

```http
PATCH /users/{user_id}/activate
```

**Descrição:** Reativa usuário desativado.

**Autorização:** `super_admin`

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "active",
  "reactivated_at": "2024-01-17T10:30:00Z"
}
```

---

### 2.7 Obter Perfil Atual

```http
GET /users/me
```

**Descrição:** Retorna perfil do usuário autenticado.

**Response 200 OK:**
```json
{
  "id": 123,
  "full_name": "João Silva",
  "email": "joao@empresa.com",
  "phone": "+55 11 91234-5678",
  "job_title": "Gerente de Projetos",
  "groups": [
    {
      "id": 1,
      "name": "RH",
      "roles": ["editor", "revisor"]
    }
  ],
  "notification_preferences": {
    "email_enabled": true,
    "email_frequency": "immediate"
  }
}
```

---

### 2.8 Atualizar Perfil Atual

```http
PUT /users/me
```

**Descrição:** Atualiza perfil do usuário autenticado.

**Request Body:**
```json
{
  "full_name": "João Silva Santos",
  "phone": "+55 11 91234-5678",
  "job_title": "Gerente Sênior"
}
```

**Response 200 OK:** (mesmo formato de GET /users/me)

---

### 2.9 Alterar Senha

```http
POST /users/me/change-password
```

**Descrição:** Altera senha do usuário autenticado.

**Request Body:**
```json
{
  "current_password": "SenhaAtual123!",
  "new_password": "NovaSenhaForte456!"
}
```

**Response 200 OK:**
```json
{
  "message": "Senha alterada com sucesso"
}
```

**Response 400 Bad Request:**
```json
{
  "error": "invalid_password",
  "message": "Senha atual incorreta"
}
```

---

## 3. Grupos

### 3.1 Criar Grupo

```http
POST /groups
```

**Descrição:** Cria novo grupo.

**Autorização:** `super_admin`

**Request Body:**
```json
{
  "name": "Tecnologia",
  "description": "Departamento de TI e Desenvolvimento",
  "color": "#3B82F6",
  "icon": "laptop"
}
```

**Response 201 Created:**
```json
{
  "id": 5,
  "name": "Tecnologia",
  "description": "Departamento de TI e Desenvolvimento",
  "color": "#3B82F6",
  "icon": "laptop",
  "created_at": "2024-01-17T10:30:00Z",
  "created_by": {
    "id": 1,
    "name": "Admin Sistema"
  }
}
```

---

### 3.2 Listar Grupos

```http
GET /groups
```

**Descrição:** Lista grupos acessíveis ao usuário.

**Query Parameters:**
- `page` (integer, default: 1)
- `per_page` (integer, default: 25)
- `search` (string) - Busca por nome
- `include_stats` (boolean, default: false) - Incluir estatísticas

**Response 200 OK:**
```json
{
  "groups": [
    {
      "id": 1,
      "name": "RH",
      "description": "Recursos Humanos",
      "color": "#10B981",
      "icon": "users",
      "created_at": "2024-01-01T10:00:00Z",
      "my_roles": ["editor", "revisor"],
      "stats": {
        "members_count": 15,
        "documents_count": 120,
        "folders_count": 8
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 5,
    "total_pages": 1
  }
}
```

---

### 3.3 Obter Grupo por ID

```http
GET /groups/{group_id}
```

**Descrição:** Retorna detalhes completos do grupo.

**Autorização:** Membro do grupo

**Response 200 OK:**
```json
{
  "id": 1,
  "name": "RH",
  "description": "Recursos Humanos",
  "color": "#10B981",
  "icon": "users",
  "created_at": "2024-01-01T10:00:00Z",
  "created_by": {
    "id": 1,
    "name": "Admin Sistema"
  },
  "members": [
    {
      "user_id": 5,
      "name": "João Silva",
      "email": "joao@empresa.com",
      "roles": ["editor"],
      "added_at": "2024-01-05T10:00:00Z"
    }
  ],
  "stats": {
    "members_count": 15,
    "documents_count": 120,
    "published_count": 80,
    "pending_approval_count": 5,
    "folders_count": 8
  }
}
```

---

### 3.4 Atualizar Grupo

```http
PUT /groups/{group_id}
```

**Descrição:** Atualiza informações do grupo.

**Autorização:** `super_admin`

**Request Body:**
```json
{
  "name": "Recursos Humanos",
  "description": "Departamento de RH e People",
  "color": "#059669",
  "icon": "user-group"
}
```

**Response 200 OK:** (mesmo formato de GET /groups/{id})

---

### 3.5 Adicionar Usuário ao Grupo

```http
POST /groups/{group_id}/users
```

**Descrição:** Adiciona usuário ao grupo com papéis.

**Autorização:** `super_admin` ou `admin_grupo`

**Request Body:**
```json
{
  "user_id": 10,
  "roles": ["editor", "revisor"]
}
```

**Response 201 Created:**
```json
{
  "user_id": 10,
  "name": "Maria Santos",
  "email": "maria@empresa.com",
  "roles": ["editor", "revisor"],
  "added_at": "2024-01-17T10:30:00Z",
  "added_by": {
    "id": 1,
    "name": "Admin Sistema"
  }
}
```

---

### 3.6 Atualizar Papéis do Usuário

```http
PUT /groups/{group_id}/users/{user_id}
```

**Descrição:** Atualiza papéis do usuário no grupo.

**Autorização:** `super_admin` ou `admin_grupo`

**Request Body:**
```json
{
  "roles": ["editor", "revisor", "admin_grupo"]
}
```

**Response 200 OK:**
```json
{
  "user_id": 10,
  "name": "Maria Santos",
  "roles": ["editor", "revisor", "admin_grupo"],
  "updated_at": "2024-01-17T10:30:00Z"
}
```

---

### 3.7 Remover Usuário do Grupo

```http
DELETE /groups/{group_id}/users/{user_id}
```

**Descrição:** Remove usuário do grupo.

**Autorização:** `super_admin` ou `admin_grupo`

**Response 204 No Content**

---

## 4. Pastas

### 4.1 Criar Pasta

```http
POST /folders
```

**Descrição:** Cria nova pasta no grupo.

**Autorização:** `editor`, `admin_grupo`, `super_admin`

**Request Body:**
```json
{
  "name": "Políticas 2024",
  "description": "Políticas internas atualizadas",
  "group_id": 1,
  "parent_folder_id": null
}
```

**Response 201 Created:**
```json
{
  "id": 10,
  "name": "Políticas 2024",
  "description": "Políticas internas atualizadas",
  "group_id": 1,
  "parent_folder_id": null,
  "path": "/Políticas 2024",
  "level": 1,
  "created_at": "2024-01-17T10:30:00Z",
  "created_by": {
    "id": 5,
    "name": "João Silva"
  }
}
```

---

### 4.2 Listar Pastas em Árvore

```http
GET /groups/{group_id}/folders/tree
```

**Descrição:** Retorna estrutura hierárquica de pastas.

**Response 200 OK:**
```json
{
  "folders": [
    {
      "id": 1,
      "name": "Políticas",
      "description": "Políticas da empresa",
      "level": 1,
      "path": "/Políticas",
      "documents_count": 5,
      "children": [
        {
          "id": 2,
          "name": "RH",
          "description": "Políticas de RH",
          "level": 2,
          "path": "/Políticas/RH",
          "parent_folder_id": 1,
          "documents_count": 3,
          "children": []
        }
      ]
    }
  ]
}
```

---

### 4.3 Listar Pastas (Flat)

```http
GET /groups/{group_id}/folders
```

**Descrição:** Lista pastas sem hierarquia.

**Query Parameters:**
- `parent_folder_id` (integer) - Filtrar por pasta pai
- `search` (string) - Busca por nome
- `page`, `per_page` - Paginação

**Response 200 OK:**
```json
{
  "folders": [
    {
      "id": 1,
      "name": "Políticas",
      "description": "Políticas da empresa",
      "group_id": 1,
      "parent_folder_id": null,
      "level": 1,
      "path": "/Políticas",
      "documents_count": 5,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 8,
    "total_pages": 1
  }
}
```

---

### 4.4 Obter Pasta por ID

```http
GET /folders/{folder_id}
```

**Descrição:** Retorna detalhes da pasta.

**Response 200 OK:**
```json
{
  "id": 1,
  "name": "Políticas",
  "description": "Políticas da empresa",
  "group_id": 1,
  "parent_folder_id": null,
  "level": 1,
  "path": "/Políticas",
  "breadcrumb": [
    {"id": 1, "name": "Políticas"}
  ],
  "documents_count": 5,
  "subfolders_count": 3,
  "created_at": "2024-01-01T10:00:00Z",
  "created_by": {
    "id": 1,
    "name": "Admin Sistema"
  }
}
```

---

### 4.5 Atualizar Pasta

```http
PUT /folders/{folder_id}
```

**Descrição:** Atualiza nome e descrição da pasta.

**Autorização:** `admin_grupo`, `super_admin`

**Request Body:**
```json
{
  "name": "Políticas Corporativas",
  "description": "Políticas atualizadas 2024"
}
```

**Response 200 OK:** (mesmo formato de GET /folders/{id})

---

### 4.6 Deletar Pasta

```http
DELETE /folders/{folder_id}
```

**Descrição:** Deleta pasta vazia.

**Autorização:** `admin_grupo`, `super_admin`

**Response 204 No Content**

**Response 400 Bad Request:**
```json
{
  "error": "folder_not_empty",
  "message": "Pasta contém documentos ou subpastas"
}
```

---

## 5. Documentos

### 5.1 Criar Documento

```http
POST /documents
```

**Descrição:** Cria novo documento em branco.

**Autorização:** `editor`, `admin_grupo`, `super_admin`

**Request Body:**
```json
{
  "title": "Política de Férias 2024",
  "group_id": 1,
  "folder_id": 5,
  "category_id": 3,
  "tags": ["férias", "benefícios", "rh"],
  "content": "# Política de Férias\n\n..."
}
```

**Response 201 Created:**
```json
{
  "id": 123,
  "title": "Política de Férias 2024",
  "status": "draft",
  "group_id": 1,
  "folder_id": 5,
  "category_id": 3,
  "tags": ["férias", "benefícios", "rh"],
  "content": "# Política de Férias\n\n...",
  "version": 1,
  "created_at": "2024-01-17T10:30:00Z",
  "created_by": {
    "id": 5,
    "name": "João Silva"
  }
}
```

---

### 5.2 Criar Documento a partir de Template

```http
POST /documents/from-template
```

**Descrição:** Cria documento baseado em template.

**Request Body:**
```json
{
  "template_id": 10,
  "title": "Política de Home Office 2024",
  "group_id": 1,
  "folder_id": 5
}
```

**Response 201 Created:** (mesmo formato de POST /documents)

---

### 5.3 Listar Documentos

```http
GET /documents
```

**Descrição:** Lista documentos com filtros e paginação.

**Query Parameters:**
- `page` (integer, default: 1)
- `per_page` (integer, default: 25, max: 100)
- `group_id` (integer) - Filtrar por grupo
- `folder_id` (integer) - Filtrar por pasta
- `status` (string: draft|pending_approval|approved|published|changes_requested|archived)
- `category_id` (integer)
- `tags` (array) - Filtrar por tags (ex: `tags[]=férias&tags[]=rh`)
- `created_by` (integer) - Filtrar por autor
- `search` (string) - Busca em título e conteúdo
- `sort_by` (string: title|created_at|updated_at|published_at)
- `sort_order` (string: asc|desc)

**Exemplo:**
```http
GET /documents?group_id=1&status=published&tags[]=rh&search=férias&sort_by=updated_at&sort_order=desc
```

**Response 200 OK:**
```json
{
  "documents": [
    {
      "id": 123,
      "title": "Política de Férias 2024",
      "status": "published",
      "group": {
        "id": 1,
        "name": "RH"
      },
      "folder": {
        "id": 5,
        "name": "Políticas",
        "path": "/Políticas/RH"
      },
      "category": {
        "id": 3,
        "name": "Benefícios"
      },
      "tags": ["férias", "benefícios"],
      "version": 2,
      "created_by": {
        "id": 5,
        "name": "João Silva"
      },
      "created_at": "2024-01-10T10:00:00Z",
      "updated_at": "2024-01-15T14:30:00Z",
      "published_at": "2024-01-15T15:00:00Z",
      "unresolved_comments_count": 0
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 150,
    "total_pages": 6
  }
}
```

---

### 5.4 Obter Documento por ID

```http
GET /documents/{document_id}
```

**Descrição:** Retorna documento completo.

**Query Parameters:**
- `include_comments` (boolean, default: false)
- `include_versions` (boolean, default: false)

**Response 200 OK:**
```json
{
  "id": 123,
  "title": "Política de Férias 2024",
  "content": "# Política de Férias\n\nTodos os colaboradores...",
  "status": "published",
  "group": {
    "id": 1,
    "name": "RH",
    "color": "#10B981"
  },
  "folder": {
    "id": 5,
    "name": "Políticas",
    "path": "/Políticas/RH"
  },
  "category": {
    "id": 3,
    "name": "Benefícios"
  },
  "tags": ["férias", "benefícios", "rh"],
  "version": 2,
  "related_documents": [
    {
      "id": 124,
      "title": "Política de Licenças"
    }
  ],
  "created_by": {
    "id": 5,
    "name": "João Silva",
    "email": "joao@empresa.com"
  },
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z",
  "updated_by": {
    "id": 5,
    "name": "João Silva"
  },
  "published_at": "2024-01-15T15:00:00Z",
  "locked_by": null,
  "locked_at": null,
  "stats": {
    "views_count": 250,
    "comments_count": 12,
    "unresolved_comments_count": 0
  }
}
```

---

### 5.5 Atualizar Documento

```http
PATCH /documents/{document_id}
```

**Descrição:** Atualiza documento (auto-save ou edição completa).

**Autorização:** `editor` (criador), `admin_grupo`, `super_admin`

**Request Body:**
```json
{
  "title": "Política de Férias 2024 - Atualizada",
  "content": "# Política de Férias\n\nTodos os colaboradores...",
  "tags": ["férias", "benefícios", "rh", "atualizado"],
  "category_id": 3
}
```

**Response 200 OK:**
```json
{
  "id": 123,
  "title": "Política de Férias 2024 - Atualizada",
  "content": "...",
  "updated_at": "2024-01-17T10:35:00Z",
  "auto_saved": false
}
```

---

### 5.6 Adquirir Lock de Edição

```http
POST /documents/{document_id}/lock
```

**Descrição:** Adquire lock para edição (evita edições concorrentes).

**Response 200 OK:**
```json
{
  "locked": true,
  "locked_by": {
    "id": 5,
    "name": "João Silva"
  },
  "locked_at": "2024-01-17T10:30:00Z",
  "lock_expires_at": "2024-01-17T11:00:00Z"
}
```

**Response 409 Conflict:**
```json
{
  "error": "document_locked",
  "message": "Documento está sendo editado por outro usuário",
  "locked_by": {
    "id": 10,
    "name": "Maria Santos"
  },
  "locked_at": "2024-01-17T10:25:00Z"
}
```

---

### 5.7 Renovar Lock (Heartbeat)

```http
PUT /documents/{document_id}/lock
```

**Descrição:** Renova lock de edição (heartbeat a cada 30s).

**Response 200 OK:**
```json
{
  "locked": true,
  "lock_expires_at": "2024-01-17T11:05:00Z"
}
```

---

### 5.8 Liberar Lock

```http
DELETE /documents/{document_id}/lock
```

**Descrição:** Libera lock de edição manualmente.

**Response 204 No Content**

---

### 5.9 Deletar Documento

```http
DELETE /documents/{document_id}
```

**Descrição:** Deleta documento em DRAFT.

**Autorização:** Criador, `admin_grupo`, `super_admin`

**Response 204 No Content**

**Response 400 Bad Request:**
```json
{
  "error": "cannot_delete",
  "message": "Apenas documentos em DRAFT podem ser deletados"
}
```

---

### 5.10 Arquivar Documento

```http
POST /documents/{document_id}/archive
```

**Descrição:** Arquiva documento PUBLISHED.

**Autorização:** `admin_grupo`, `super_admin`

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "archived",
  "archived_at": "2024-01-17T10:30:00Z",
  "archived_by": {
    "id": 1,
    "name": "Admin Sistema"
  }
}
```

---

### 5.11 Despublicar Documento

```http
POST /documents/{document_id}/unpublish
```

**Descrição:** Volta documento PUBLISHED para DRAFT.

**Autorização:** `admin_grupo`, `super_admin`

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "draft",
  "unpublished_at": "2024-01-17T10:30:00Z"
}
```

---

### 5.12 Marcar como DEPRECATED

```http
POST /documents/{document_id}/deprecate
```

**Descrição:** Marca documento como obsoleto.

**Autorização:** `revisor`, `admin_grupo`, `super_admin`

**Request Body:**
```json
{
  "reason": "Substituído por nova política",
  "replacement_document_id": 150
}
```

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "deprecated",
  "deprecated_at": "2024-01-17T10:30:00Z",
  "deprecated_by": {
    "id": 10,
    "name": "Maria Santos"
  },
  "deprecation_reason": "Substituído por nova política",
  "replacement_document": {
    "id": 150,
    "title": "Política de Férias 2025"
  }
}
```

---

## 6. Templates

### 6.1 Criar Template

```http
POST /templates
```

**Descrição:** Cria template global.

**Autorização:** `admin_grupo`, `super_admin`

**Request Body:**
```json
{
  "name": "Template de Política",
  "description": "Template padrão para políticas internas",
  "content": "# [Título da Política]\n\n## Objetivo\n\n...",
  "default_tags": ["política"],
  "default_category_id": 3
}
```

**Response 201 Created:**
```json
{
  "id": 10,
  "name": "Template de Política",
  "description": "Template padrão para políticas internas",
  "content": "# [Título da Política]\n\n## Objetivo\n\n...",
  "default_tags": ["política"],
  "default_category_id": 3,
  "created_at": "2024-01-17T10:30:00Z",
  "created_by": {
    "id": 5,
    "name": "João Silva"
  }
}
```

---

### 6.2 Listar Templates

```http
GET /templates
```

**Descrição:** Lista templates disponíveis.

**Query Parameters:**
- `search` (string)
- `sort_by` (string: name|created_at)
- `page`, `per_page`

**Response 200 OK:**
```json
{
  "templates": [
    {
      "id": 10,
      "name": "Template de Política",
      "description": "Template padrão para políticas internas",
      "preview": "# [Título da Política]\n\n## Objetivo...",
      "usage_count": 25,
      "created_at": "2024-01-01T10:00:00Z",
      "created_by": {
        "id": 1,
        "name": "Admin Sistema"
      }
    }
  ],
  "pagination": {...}
}
```

---

### 6.3 Obter Template por ID

```http
GET /templates/{template_id}
```

**Response 200 OK:**
```json
{
  "id": 10,
  "name": "Template de Política",
  "description": "Template padrão para políticas internas",
  "content": "# [Título da Política]\n\n## Objetivo\n\n...",
  "default_tags": ["política"],
  "default_category_id": 3,
  "usage_count": 25,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-10T15:00:00Z"
}
```

---

### 6.4 Atualizar Template

```http
PUT /templates/{template_id}
```

**Autorização:** Criador, `super_admin`

**Request Body:** (mesmo de POST)

**Response 200 OK:** (mesmo de GET)

---

### 6.5 Deletar Template

```http
DELETE /templates/{template_id}
```

**Autorização:** `super_admin`

**Response 204 No Content**

---

## 7. Comentários

### 7.1 Adicionar Comentário

```http
POST /documents/{document_id}/comments
```

**Descrição:** Adiciona comentário em trecho ou geral.

**Autorização:** `revisor`, `admin_grupo`, `super_admin`

**Request Body (Comentário em trecho):**
```json
{
  "text": "Esta informação está desatualizada. @[João Silva](5), você pode verificar?",
  "start_offset": 1250,
  "end_offset": 1320,
  "selected_text": "benefícios incluem vale-transporte",
  "context_before": "...todos os funcionários. Os ",
  "context_after": " e vale-refeição no valor...",
  "is_critical": true,
  "mentioned_user_ids": [5]
}
```

**Request Body (Comentário geral):**
```json
{
  "text": "Documento bem estruturado, mas sugiro adicionar exemplos práticos.",
  "is_general": true,
  "is_critical": false
}
```

**Response 201 Created:**
```json
{
  "id": 100,
  "document_id": 123,
  "text": "Esta informação está desatualizada...",
  "start_offset": 1250,
  "end_offset": 1320,
  "selected_text": "benefícios incluem vale-transporte",
  "is_critical": true,
  "is_general": false,
  "resolved": false,
  "created_by": {
    "id": 10,
    "name": "Maria Santos",
    "avatar_url": "..."
  },
  "created_at": "2024-01-17T10:30:00Z",
  "mentions": [
    {
      "id": 5,
      "name": "João Silva"
    }
  ]
}
```

---

### 7.2 Listar Comentários do Documento

```http
GET /documents/{document_id}/comments
```

**Descrição:** Lista todos os comentários do documento.

**Query Parameters:**
- `include_resolved` (boolean, default: false)
- `include_deleted` (boolean, default: false)
- `critical_only` (boolean, default: false)

**Response 200 OK:**
```json
{
  "comments": [
    {
      "id": 100,
      "text": "Esta informação está desatualizada...",
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
      "mentions": [...]
    }
  ],
  "general_comments": [
    {
      "id": 101,
      "text": "Documento bem estruturado",
      "is_critical": false,
      "resolved": false,
      "created_by": {...},
      "created_at": "2024-01-17T10:35:00Z"
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

---

### 7.3 Obter Comentário por ID

```http
GET /comments/{comment_id}
```

**Response 200 OK:**
```json
{
  "id": 100,
  "document_id": 123,
  "document_title": "Política de Férias 2024",
  "text": "Esta informação está desatualizada...",
  "start_offset": 1250,
  "end_offset": 1320,
  "selected_text": "benefícios incluem vale-transporte",
  "context_before": "...",
  "context_after": "...",
  "is_critical": true,
  "resolved": false,
  "created_by": {...},
  "created_at": "2024-01-17T10:30:00Z",
  "mentions": [...]
}
```

---

### 7.4 Resolver Comentário

```http
PUT /comments/{comment_id}/resolve
```

**Descrição:** Marca comentário como resolvido/não resolvido.

**Autorização:** Editor do doc, criador do comentário, Admin

**Request Body:**
```json
{
  "resolved": true
}
```

**Response 200 OK:**
```json
{
  "id": 100,
  "resolved": true,
  "resolved_at": "2024-01-17T11:00:00Z",
  "resolved_by": {
    "id": 5,
    "name": "João Silva"
  }
}
```

---

### 7.5 Resolver Todos os Comentários

```http
POST /documents/{document_id}/comments/resolve-all
```

**Descrição:** Marca todos os comentários não resolvidos como resolvidos.

**Autorização:** Editor do doc, Admin

**Response 200 OK:**
```json
{
  "resolved_count": 10,
  "message": "10 comentários foram marcados como resolvidos"
}
```

---

### 7.6 Deletar Comentário

```http
DELETE /comments/{comment_id}
```

**Descrição:** Soft delete de comentário.

**Autorização:** Criador, Admin

**Response 204 No Content**

---

### 7.7 Estatísticas de Comentários

```http
GET /documents/{document_id}/comments/stats
```

**Response 200 OK:**
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

---

### 7.8 Exportar Comentários

```http
POST /documents/{document_id}/comments/export
```

**Descrição:** Exporta comentários para PDF ou CSV.

**Autorização:** Admin

**Request Body:**
```json
{
  "format": "pdf",
  "include_resolved": true,
  "critical_only": false,
  "sort_by": "position"
}
```

**Response 202 Accepted:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Exportação iniciada. Você receberá uma notificação quando estiver pronto."
}
```

---

## 8. Workflow de Aprovação

### 8.1 Enviar para Aprovação

```http
POST /documents/{document_id}/submit-for-approval
```

**Descrição:** Envia documento DRAFT para aprovação.

**Autorização:** Editor (criador), Admin

**Request Body:**
```json
{
  "reviewer_message": "Por favor, revisar seção de benefícios atualizada"
}
```

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "pending_approval",
  "submitted_for_approval_at": "2024-01-17T10:30:00Z",
  "submitted_by": {
    "id": 5,
    "name": "João Silva"
  },
  "reviewer_message": "Por favor, revisar seção de benefícios atualizada",
  "reviewers_notified": [
    {
      "id": 10,
      "name": "Maria Santos"
    }
  ]
}
```

**Response 400 Bad Request:**
```json
{
  "error": "unresolved_comments",
  "message": "Há 3 comentários não resolvidos",
  "unresolved_comments_count": 3
}
```

---

### 8.2 Cancelar Envio

```http
POST /documents/{document_id}/cancel-submission
```

**Descrição:** Cancela envio para aprovação (volta para DRAFT).

**Autorização:** Editor que enviou, Admin

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "draft",
  "message": "Envio cancelado com sucesso"
}
```

---

### 8.3 Listar Documentos Pendentes de Aprovação

```http
GET /documents/pending-approval
```

**Descrição:** Lista documentos PENDING_APPROVAL dos grupos do revisor.

**Autorização:** Revisor

**Query Parameters:**
- `group_id` (integer)
- `author_id` (integer)
- `sort_by` (string: submitted_at|title)
- `sort_order` (string: asc|desc, default: asc)
- `page`, `per_page`

**Response 200 OK:**
```json
{
  "documents": [
    {
      "id": 123,
      "title": "Política de Férias 2024",
      "author": {
        "id": 5,
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
        "id": 5,
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

---

### 8.4 Obter Documento em Modo Revisão

```http
GET /documents/{document_id}/review
```

**Descrição:** Retorna documento com informações de revisão.

**Autorização:** Revisor do grupo

**Response 200 OK:**
```json
{
  "document": {
    "id": 123,
    "title": "Política de Férias 2024",
    "content": "...",
    "status": "pending_approval",
    ...
  },
  "submission": {
    "submitted_by": {
      "id": 5,
      "name": "João Silva"
    },
    "submitted_at": "2024-01-15T10:30:00Z",
    "reviewer_message": "Por favor revisar seção de benefícios",
    "previous_rejections_count": 1
  },
  "comments": [...],
  "previous_submissions": [
    {
      "id": 1,
      "submitted_at": "2024-01-10T10:00:00Z",
      "reviewed_at": "2024-01-11T14:30:00Z",
      "reviewed_by": {
        "id": 10,
        "name": "Maria Santos"
      },
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

---

### 8.5 Aprovar Documento

```http
POST /documents/{document_id}/approve
```

**Descrição:** Aprova documento para publicação.

**Autorização:** Revisor do grupo

**Request Body:**
```json
{
  "review_notes": "Documento bem estruturado, aprovado para publicação"
}
```

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "approved",
  "reviewed_at": "2024-01-17T11:00:00Z",
  "reviewed_by": {
    "id": 10,
    "name": "Maria Santos"
  },
  "review_decision": "approved",
  "review_notes": "Documento bem estruturado, aprovado para publicação",
  "message": "Documento aprovado e será publicado em breve"
}
```

---

### 8.6 Solicitar Mudanças

```http
POST /documents/{document_id}/request-changes
```

**Descrição:** Rejeita documento e solicita correções.

**Autorização:** Revisor do grupo

**Request Body:**
```json
{
  "review_notes": "Por favor, ajustar seção de benefícios conforme comentários. Adicionar exemplos práticos.",
  "notify_immediately": true
}
```

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "changes_requested",
  "reviewed_at": "2024-01-17T11:00:00Z",
  "reviewed_by": {
    "id": 10,
    "name": "Maria Santos"
  },
  "review_decision": "changes_requested",
  "review_notes": "Por favor, ajustar seção de benefícios...",
  "message": "Mudanças solicitadas. O editor foi notificado."
}
```

---

### 8.7 Visualizar Mudanças Solicitadas

```http
GET /documents/{document_id}/changes-requested
```

**Descrição:** Retorna detalhes de mudanças solicitadas.

**Autorização:** Editor (criador), Admin

**Response 200 OK:**
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
  "comments": [...],
  "previous_reviews": [...]
}
```

---

### 8.8 Histórico de Aprovações

```http
GET /documents/{document_id}/approval-history
```

**Descrição:** Retorna histórico completo de aprovações.

**Response 200 OK:**
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
    }
  ]
}
```

---

## 9. Conversão de Documentos

### 9.1 Upload de Arquivo para Conversão

```http
POST /documents/upload
```

**Descrição:** Faz upload de arquivo para conversão.

**Autorização:** Editor, Admin

**Request:** `multipart/form-data`

**Form Data:**
```
file: <arquivo.pdf>
title: "Política de Férias 2024"
group_id: 1
folder_id: 5
category_id: 3
tags[]: "férias"
tags[]: "rh"
```

**Response 201 Created:**
```json
{
  "id": 123,
  "title": "Política de Férias 2024",
  "status": "new",
  "original_file_name": "politica-ferias-2024.pdf",
  "original_file_size": 2048000,
  "original_mime_type": "application/pdf",
  "original_file_url": "https://s3.../documents-originals/1/123/original.pdf",
  "celery_task_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-17T10:30:00Z"
}
```

**Response 400 Bad Request:**
```json
{
  "error": "invalid_file",
  "message": "Tipo de arquivo não suportado",
  "supported_types": [".pdf", ".docx", ".html", ".txt", ".md", ".pptx", ".xlsx"]
}
```

**Response 413 Payload Too Large:**
```json
{
  "error": "file_too_large",
  "message": "Arquivo excede o tamanho máximo de 100 MB",
  "max_size_bytes": 104857600
}
```

---

### 9.2 Status Stream de Conversão (SSE)

```http
GET /documents/{document_id}/status-stream
```

**Descrição:** Stream de eventos de conversão em tempo real.

**Autorização:** Editor (criador), Admin

**Headers:**
```http
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Eventos SSE:**

```
event: status_update
data: {"status": "processing", "progress": 0, "message": "Iniciando conversão..."}

event: status_update
data: {"status": "processing", "progress": 50, "message": "Convertendo páginas..."}

event: status_update
data: {"status": "draft", "progress": 100, "message": "Conversão concluída!"}

event: heartbeat
data: {"timestamp": "2024-01-17T10:31:00Z"}

event: error
data: {"status": "error", "error": "Arquivo corrompido", "can_retry": true}
```

---

### 9.3 Re-upload Após Falha

```http
POST /documents/{document_id}/retry-conversion
```

**Descrição:** Reinicia conversão com novo arquivo após falha.

**Request:** `multipart/form-data`

**Form Data:**
```
file: <novo-arquivo.pdf>
```

**Response 200 OK:**
```json
{
  "id": 123,
  "status": "processing",
  "celery_task_id": "650e8400-e29b-41d4-a716-446655440001",
  "conversion_attempts": 1,
  "message": "Nova tentativa de conversão iniciada"
}
```

---

### 9.4 Logs de Conversão

```http
GET /documents/{document_id}/conversion-logs
```

**Descrição:** Retorna logs de tentativas de conversão.

**Autorização:** Editor (criador), Admin

**Response 200 OK:**
```json
{
  "logs": [
    {
      "id": 1,
      "attempt": 1,
      "status": "failed",
      "error_message": "Arquivo PDF protegido por senha",
      "started_at": "2024-01-17T10:30:00Z",
      "completed_at": "2024-01-17T10:30:15Z",
      "duration_seconds": 15
    },
    {
      "id": 2,
      "attempt": 2,
      "status": "success",
      "error_message": null,
      "started_at": "2024-01-17T10:35:00Z",
      "completed_at": "2024-01-17T10:35:45Z",
      "duration_seconds": 45
    }
  ]
}
```

---

## 10. Notificações

### 10.1 Listar Notificações

```http
GET /notifications
```

**Descrição:** Lista notificações do usuário.

**Query Parameters:**
- `unread` (boolean) - Filtrar não lidas
- `type` (string) - Filtrar por tipo
- `limit` (integer, default: 10, max: 50)
- `offset` (integer)

**Response 200 OK:**
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

---

### 10.2 Marcar Notificação como Lida

```http
PUT /notifications/{notification_id}/read
```

**Response 200 OK:**
```json
{
  "id": 1,
  "read": true,
  "read_at": "2024-01-17T12:30:00Z"
}
```

---

### 10.3 Marcar Todas como Lidas

```http
PUT /notifications/mark-all-read
```

**Response 200 OK:**
```json
{
  "marked_count": 15,
  "message": "15 notificações marcadas como lidas"
}
```

---

### 10.4 Preferências de Notificação

```http
GET /users/me/notification-preferences
```

**Response 200 OK:**
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

---

### 10.5 Atualizar Preferências

```http
PUT /users/me/notification-preferences
```

**Request Body:**
```json
{
  "email_enabled": true,
  "email_frequency": "daily",
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

**Response 200 OK:** (mesmo de GET)

---

### 10.6 Listar Menções

```http
GET /users/me/mentions
```

**Descrição:** Lista comentários onde usuário foi mencionado.

**Query Parameters:**
- `unread` (boolean)
- `document_id` (integer)
- `limit`, `offset`

**Response 200 OK:**
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

---

## 11. Relatórios

### 11.1 Relatório de Workflow de Aprovação

```http
GET /reports/approval-workflow
```

**Descrição:** Métricas de aprovações e rejeições.

**Autorização:** Admin

**Query Parameters:**
- `group_id` (integer)
- `start_date` (date, ISO 8601)
- `end_date` (date, ISO 8601)

**Response 200 OK:**
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

---

### 11.2 Relatório de Documentos

```http
GET /reports/documents
```

**Autorização:** Admin

**Query Parameters:**
- `group_id` (integer)
- `start_date`, `end_date`

**Response 200 OK:**
```json
{
  "metrics": {
    "total_documents": 500,
    "published": 350,
    "draft": 100,
    "pending_approval": 30,
    "archived": 20,
    "avg_documents_per_month": 25,
    "most_active_authors": [
      {
        "user_id": 5,
        "name": "João Silva",
        "documents_created": 45
      }
    ]
  },
  "by_category": [
    {
      "category_id": 1,
      "category_name": "Políticas",
      "count": 150
    }
  ],
  "timeline": [...]
}
```

---

## 12. Busca

### 12.1 Busca Global

```http
GET /search
```

**Descrição:** Busca em documentos, respeitando permissões.

**Query Parameters:**
- `q` (string, required) - Termo de busca
- `group_id` (integer) - Filtrar por grupo
- `status` (string) - Filtrar por status
- `category_id` (integer)
- `tags[]` (array)
- `created_after` (date)
- `created_before` (date)
- `page`, `per_page`

**Response 200 OK:**
```json
{
  "results": [
    {
      "id": 123,
      "title": "Política de Férias 2024",
      "snippet": "...todos os colaboradores têm direito a <mark>férias</mark> anuais...",
      "status": "published",
      "group": {
        "id": 1,
        "name": "RH"
      },
      "score": 0.95,
      "published_at": "2024-01-15T15:00:00Z"
    }
  ],
  "facets": {
    "by_group": [
      {"group_id": 1, "group_name": "RH", "count": 25}
    ],
    "by_status": [
      {"status": "published", "count": 80}
    ],
    "by_category": [...]
  },
  "pagination": {...}
}
```

---

## 13. Upload de Arquivos

### 13.1 Upload de Imagem (para Editor)

```http
POST /upload/image
```

**Descrição:** Upload de imagem para uso em documentos.

**Request:** `multipart/form-data`

**Form Data:**
```
file: <imagem.png>
document_id: 123
```

**Response 201 Created:**
```json
{
  "url": "https://cdn.empresa.com/images/123/550e8400.png",
  "filename": "imagem.png",
  "size": 512000,
  "mime_type": "image/png",
  "width": 1200,
  "height": 800
}
```

---

## 📊 Códigos de Status HTTP

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Requisição bem-sucedida |
| 201 | Created | Recurso criado com sucesso |
| 204 | No Content | Ação bem-sucedida sem conteúdo de resposta |
| 400 | Bad Request | Dados inválidos ou incompletos |
| 401 | Unauthorized | Token JWT ausente ou inválido |
| 403 | Forbidden | Usuário autenticado mas sem permissão |
| 404 | Not Found | Recurso não encontrado |
| 409 | Conflict | Conflito (ex: documento sendo editado) |
| 413 | Payload Too Large | Arquivo muito grande |
| 422 | Unprocessable Entity | Validação de negócio falhou |
| 429 | Too Many Requests | Rate limit excedido |
| 500 | Internal Server Error | Erro do servidor |
| 503 | Service Unavailable | Serviço temporariamente indisponível |

---

## ⚠️ Tratamento de Erros

### Formato Padrão de Erro

```json
{
  "error": "validation_error",
  "message": "Dados inválidos",
  "details": {
    "email": ["Email já existe"],
    "password": ["Senha deve ter no mínimo 8 caracteres"]
  },
  "timestamp": "2024-01-17T10:30:00Z",
  "path": "/api/v1/users",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Códigos de Erro Comuns

| Código | Descrição |
|--------|-----------|
| `invalid_credentials` | Email ou senha incorretos |
| `token_expired` | Token JWT expirado |
| `token_invalid` | Token JWT inválido |
| `insufficient_permissions` | Sem permissão para ação |
| `resource_not_found` | Recurso não encontrado |
| `validation_error` | Erro de validação de dados |
| `duplicate_entry` | Recurso já existe |
| `document_locked` | Documento sendo editado por outro usuário |
| `invalid_status_transition` | Transição de status inválida |
| `rate_limit_exceeded` | Muitas requisições |

---

## 🔒 Rate Limiting

### Limites por Endpoint

| Endpoint | Limite | Janela |
|----------|--------|--------|
| `POST /auth/login` | 10 req | 15 min |
| `POST /documents/upload` | 20 req | 1 hora |
| `GET /documents` | 100 req | 1 min |
| Outros endpoints | 60 req | 1 min |

### Headers de Rate Limit

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705536000
```

---

## 🔐 Autorização (RBAC)

### Matriz de Permissões

| Ação | Super Admin | Admin Grupo | Revisor | Editor | Reader |
|------|-------------|-------------|---------|--------|--------|
| Criar usuário | ✅ | ❌ | ❌ | ❌ | ❌ |
| Criar grupo | ✅ | ❌ | ❌ | ❌ | ❌ |
| Adicionar usuário ao grupo | ✅ | ✅ | ❌ | ❌ | ❌ |
| Criar documento | ✅ | ✅ | ✅ | ✅ | ❌ |
| Editar documento | ✅ | ✅ | ❌ | ✅ (próprio) | ❌ |
| Aprovar documento | ✅ | ✅ | ✅ | ❌ | ❌ |
| Adicionar comentário | ✅ | ✅ | ✅ | ❌ | ❌ |
| Visualizar documento | ✅ | ✅ | ✅ | ✅ | ✅ |
| Marcar como DEPRECATED | ✅ | ✅ | ✅ | ❌ | ❌ |
| Arquivar documento | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 📝 Versionamento da API

**Versão Atual:** v1

**Estratégia:** Versionamento via URL (`/api/v1/...`)

**Depreciação:** Versões antigas mantidas por 12 meses após nova versão

---

## 🚀 Resumo da Especificação

### Endpoints por Módulo

1. **Autenticação:** 5 endpoints
2. **Usuários:** 9 endpoints
3. **Grupos:** 7 endpoints
4. **Pastas:** 6 endpoints
5. **Documentos:** 12 endpoints
6. **Templates:** 5 endpoints
7. **Comentários:** 8 endpoints
8. **Workflow:** 8 endpoints
9. **Conversão:** 4 endpoints
10. **Notificações:** 6 endpoints
11. **Relatórios:** 2 endpoints
12. **Busca:** 1 endpoint
13. **Upload:** 1 endpoint

**Total: 74 endpoints** 🎉

---

**Especificação preparada por:** Claude (Anthropic)  
**Versão:** 1.0  
**Data:** Janeiro 2026  
**Status:** Completa e Pronta para Implementação

