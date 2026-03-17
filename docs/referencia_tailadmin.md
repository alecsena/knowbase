# Referência do TailAdmin (Agente & Desenvolvedor)

Este documento serve como um guia completo para o template **TailAdmin** implementado neste projeto Next.js. Ele foi desenhado para acelerar o aprendizado sobre estrutura, componentes e padrões utilizados.

## 1. Visão Geral

O projeto utiliza **Last.js** (App Router) com **Tailwind CSS**. A estrutura de diretórios e componentes segue o padrão do template TailAdmin, adaptado para este sistema.

- **Framework**: Next.js 15+ (App Router)
- **Estilização**: Tailwind CSS
- **Iconografia**: SVG Icons (grupados em componentes ou arquivos individuais)
- **Estado Global**: React Context (SidebarContext, ThemeContext)

## 2. Instalação e Execução

Para rodar o frontend localmente:

### Pré-requisitos
- Node.js (versão 18+ recomendada)
- NPM ou Yarn

### Comandos
1.  **Instalar dependências**:
    ```bash
    cd frontend
    npm install
    ```
2.  **Rodar servidor de desenvolvimento**:
    ```bash
    npm run dev
    ```
    O sistema estará acessível em `http://localhost:3000`.

## 3. Estrutura de Diretórios

A estrutura principal dentro de `frontend/src` é organizada da seguinte forma:

```
src/
├── app/                 # Next.js App Router
│   ├── (admin)/         # Rotas autenticadas/administrativas (com Sidebar)
│   ├── (auth)/          # Rotas de autenticação (Login, Registro)
│   ├── layout.tsx       # Root Layout (Providers globais)
│   └── globals.css      # Estilos globais Tailwind
├── components/          # Componentes de UI Reutilizáveis
│   ├── common/          # Componentes genéricos (Loaders, etc.)
│   ├── ui/              # Componentes base (Buttons, Cards, Inputs)
│   ├── form/            # Elementos de formulário (Selects, Checkboxes)
│   ├── tables/          # Componentes de Tabela
│   └── ...              # Outros módulos de domínio
├── layout/              # Componentes Estruturais do Dashboard
│   ├── AppSidebar.tsx   # Barra lateral de navegação
│   ├── AppHeader.tsx    # Cabeçalho superior (User dropdown, Notificações)
│   └── Backdrop.tsx     # Fundo escuro para mobile
├── context/             # React Contexts
│   ├── SidebarContext.tsx # Controle de estado da Sidebar
│   └── ThemeContext.tsx   # Controle de Tema (Dark/Light)
└── icons/               # Ícones SVG
```

## 4. Layout e Navegação

O layout principal do painel administrativo está definido em `src/app/(admin)/layout.tsx`. Ele envolve o conteúdo das páginas com a Sidebar e o Header.

### AppSidebar (`src/layout/AppSidebar.tsx`)
Responsável pela navegação principal.
- **Como adicionar item**: Edite este arquivo para incluir novos links no menu. O estado `isExpanded` e `isHovered` controla a exibição (expandida/colapsada).
- **Estrutura**: Utiliza `SidebarProvider` para saber se deve estar aberto ou fechado.

### AppHeader (`src/layout/AppHeader.tsx`)
Barra superior contendo:
- Botão de Toggle da Sidebar (Hamburger menu).
- Dropdown de Notificações.
- Dropdown de Usuário (Perfil, Logout).
- Toggle de Dark/Light Mode.

## 5. Componentes Principais

Os componentes estão em `src/components`. Reutilize-os para manter a consistência visual.

### UI Base (`src/components/ui`)
- **Card**: Container padrão com sombra e borda.
  ```tsx
  <div className="rounded-sm border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
    {children}
  </div>
  ```
- **Button**: Botões estilizados. Verifique se existe um componente `Button` ou utilize as classes utilitárias do Tailwind (`bg-primary text-white ...`).

### Tabelas (`src/components/tables`)
Utilize para listagem de dados. O padrão TailAdmin geralmente inclui tabelas responsivas.
- Estrutura comum:
  ```tsx
  <div className="rounded-sm border border-stroke bg-white px-5 pt-6 pb-2.5 shadow-default sm:px-7.5 xl:pb-1">
    <h4 className="mb-6 text-xl font-semibold text-black dark:text-white">Título</h4>
    {/* Cabeçalho */}
    <div className="grid grid-cols-3 rounded-sm bg-gray-2 dark:bg-meta-4 sm:grid-cols-5">...</div>
    {/* Linhas */}
    <div className="grid grid-cols-3 border-b border-stroke dark:border-strokedark sm:grid-cols-5">...</div>
  </div>
  ```

### Formulários (`src/components/form`)
- **Input de Texto**: Campo de entrada padrão.
- **Select**: Dropdown de seleção.
- **Checkbox/Switcher**: Switches de alternância.

### Alertas e Notificações
Componentes visuais para feedback do usuário (Sucesso, Erro, Aviso). Geralmente encontrados em exemplos ou componentes dedicados.

## 6. Criando Novas Páginas

Para adicionar uma nova rota no sistema (ex: `/usuarios`):

1.  **Crie a pasta**: `src/app/(admin)/usuarios`
2.  **Crie o arquivo**: `page.tsx` dentro da pasta.
    ```tsx
    import Breadcrumb from "@/components/Breadcrumbs/Breadcrumb";
    import DefaultLayout from "@/layout/DefaultLayout"; // Se necessário, ou use o layout automático do (admin)

    const UsuariosPage = () => {
      return (
        <>
          <Breadcrumb pageName="Gestão de Usuários" />
          <div className="flex flex-col gap-10">
            {/* Conteúdo da Página */}
          </div>
        </>
      );
    };

    export default UsuariosPage;
    ```
3.  **Adicione ao Menu**: Abra `src/layout/AppSidebar.tsx` e adicione o `Link` para `/usuarios`.

## 7. Personalização e Configuração

### Tailwind CSS (`tailwind.config.ts`)
Aqui estão definidas as cores personalizadas, fontes e breakpoints.
- **Cores principais**: `primary`, `secondary`, `stroke`, `boxdark`, etc.
- **Fontes**: A fonte padrão é `Outfit` (definida em `layout.tsx` e `tailwind.config.ts`).

### Dark Mode
O suporte a Dark Mode é nativo via classe `dark` no elemento `html` ou `body`, controlado pelo `ThemeContext`. Utilize as classes `dark:` do Tailwind (ex: `bg-white dark:bg-boxdark`) para garantir compatibilidade.

## 8. Dicas Rápidas para Agentes

- **Sempre verifique `src/components`** antes de criar um novo componente de UI.
- **Respeite o Layout**: Use `src/app/(admin)` para páginas do sistema interno. Use `src/app/(auth)` para Login/Cadastro.
- **Ícones**: Verifique a pasta `src/icons` ou use bibliotecas SVG inline se necessário, seguindo o padrão existente.
- **Responsividade**: O TailAdmin é Mobile-First. Teste componentes em larguras menores.
