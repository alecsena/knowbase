# Exemplos de Código

Este documento serve como índice para os exemplos de código disponíveis em `docs/examples`. Estes arquivos podem ser copiados e adaptados para o diretório `frontend/src` conforme a necessidade do projeto.

## Estrutura de Exemplos

Os exemplos estão organizados refletindo a estrutura do Next.js App Router:

### 1. Componentes (`docs/examples/components`)

Componentes reutilizáveis de UI, formulários e visualização de dados.

- **UI Base** (`ui/`): Botões, Badges, Modais, Tooltips.
- **Formulários** (`form/`): Inputs, Checkboxes, Switches, Datepickers.
- **Tabelas** (`tables/`): Tabelas simples e complexas.
- **Gráficos** (`charts/`): Exemplos de integração de gráficos (ApexCharts ou similar).
- **Autenticação** (`auth/`): Formulários de login e registro.
- **Comum** (`common/`): Loaders, paginação.

### 2. Layout (`docs/examples/layout`)

Os blocos de construção principais do layout do painel administrativo.

- `AppSidebar.tsx`: Barra lateral com navegação.
- `AppHeader.tsx`: Cabeçalho com perfil e notificações.
- `Backdrop.tsx`: Fundo escuro para menus mobile.

### 3. Páginas da Aplicação (`docs/examples/app`)

Exemplos de páginas completas.

- **Admin** (`(admin)/`): Dashboard, Perfil, Tabelas, Calendar.
- **Páginas completas** (`(full-width-pages)/`): Páginas de erro (404), Manutenção.

## Como Utilizar

1.  **Identifique o componente**: Navegue pelas pastas em `docs/examples` para encontrar o que precisa.
2.  **Copie o código**: Copie o arquivo desejado para o seu diretório `frontend/src/components` ou `frontend/src/app`.
3.  **Ajuste os imports**: Verifique se os caminhos de importação (como `@/components/...`) estão corretos para a sua estrutura.
4.  **Personalize**: Adapte o código (cores, classes Tailwind, lógica) para os requisitos específicos do KMS.

> **Dica**: Sempre verifique o arquivo `README.md` dentro de `docs/examples` (se existir) para instruções específicas de dependências.
