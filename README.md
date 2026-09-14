O Aura APM é uma solução de inteligência artificial agêntica e engenharia de dados desenvolvida para otimizar a triagem, investigação de causas-raiz e acompanhamento de SLAs de infraestrutura na Locaweb.

Integrado nativamente ao n8n e utilizando os modelos Google Gemini, o sistema processa planilhas de logs operacionais (XLSX/CSV) enviadas diretamente via chat corporativo, gerando diagnósticos analíticos acompanhados de gráficos executivos em tempo real.

Como Executar o Projeto Localmente
Pré-requisitos
Docker e Docker Compose instalados.

Uma chave de API gratuita do Google AI Studio (Gemini).

Um token de bot do Telegram criado via @BotFather.

- Passo 1: Clonar o Repositório
git clone https://github.com/seu-usuario/aura-apm.git
cd aura-apm

- Passo 2: Subir a Instância do n8n via Docker
Crie o container do n8n com o comando abaixo:
docker compose up -d

- Acesse o painel web em seu navegador: http://localhost:5678.

- Passo 3: Importar o Workflow
No n8n, crie uma conta local de administrador caso seja o primeiro acesso.
No menu lateral, acesse Workflows e clique no botão Add Workflow (ou utilize o atalho Ctrl + O / Cmd + O).
Clique nos três pontinhos (...) no canto superior direito da tela e selecione Import from File.
Selecione o arquivo workflows/aura_apm_workflow.json deste repositório.

- Passo 4: Configurar as Credenciais
O fluxo depende de duas credenciais para operar:
Google Gemini API:
Clique em qualquer nó marcado como Google Gemini Model.
Em Credential for Google Gemini, selecione Create New Credential.
Cole sua API Key gerada no Google AI Studio e salve.
Telegram Bot API:
Abra o nó Telegram Trigger (ou Send Telegram Reply).
Em Credential for Telegram, selecione Create New Credential.
Insira o token do bot fornecido pelo BotFather e salve.

- Passo 5: Testar o Fluxo
Clique no botão Save e, em seguida, em Test step / Listen for test event no nó Telegram Trigger.
Abra a conversa com o seu bot no Telegram.
Teste 1 (Conversação): Envie "Olá, meu nome é Danilo e atuo no time de SRE. Qual é o seu papel?". Verifique se o bot responde mantendo o contexto.
Teste 2 (Análise + Dashboard): Envie a planilha de teste samples/logs_exemplo.xlsx preenchendo a legenda com "Quantos incidentes de prioridade alta constam no arquivo e quais os maiores impactos?".
O bot retornará o gráfico gerado dinamicamente com o sumário executivo em tópicos.
