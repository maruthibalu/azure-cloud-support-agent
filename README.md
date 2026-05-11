# Customer Support Ticket Agent

An intelligent Azure Foundry agent that triages customer support tickets, searches a knowledge base for solutions, and routes complex issues to human specialists.

## Features

- **Ticket Analysis**: Automatically categorize tickets, determine severity, and identify key issues
- **Knowledge Base Search**: Find relevant solutions from a knowledge base with relevance scoring
- **Intelligent Routing**: Route tickets to appropriate specialists or resolve with KB solutions
- **Sentiment Analysis**: Understand customer sentiment for priority handling
- **Comprehensive Logging**: Track all agent decisions with detailed logging
- **Modular Design**: Easy to test, extend, and integrate

## Project Structure

```
src/
├── agent.py                    # Main agent orchestration
├── models/
│   ├── ticket.py              # Ticket data model
│   └── solution.py            # Solution data model
├── tools/
│   ├── ticket_analyzer.py     # Analysis tool
│   ├── kb_searcher.py         # Knowledge base search
│   └── router.py              # Routing logic
└── utils/
    └── logger.py              # Logging setup

config/
├── agent_config.json          # Agent configuration
└── kb_data.json               # Knowledge base data

examples/
├── sample_tickets.json        # Sample test tickets
└── run_agent.py              # Example usage script

tests/
└── test_agent_flow.py        # Test scenarios
```

## Installation

1. **Clone or navigate to project directory**
   ```bash
   cd AgenticWorkflow
   ```

2. **Create virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure Foundry credentials
   ```

## Usage

### Azure AI Configuration

Set these environment variables to enable Azure OpenAI-powered semantic analysis:

```bash
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

If these are not set, the system automatically falls back to deterministic rule-based analysis.

### Process Sample Tickets

```bash
python examples/run_agent.py --mode sample
```

This will process the predefined sample tickets from `examples/sample_tickets.json` and display the routing decisions.

### Interactive Mode

```bash
python examples/run_agent.py --mode interactive
```

Manually enter ticket details and see how the agent processes them.

### Web UI (Browser Access)

```bash
python examples/run_web.py
```

Open http://localhost:8000 in your browser.

Available web endpoints:
- `GET /` - Web UI
- `GET /health` - Health check
- `POST /api/tickets/process` - Process ticket JSON payload

## Azure Hosting (Web UI)

This project is now ready for Azure hosting using either Azure Container Apps (recommended) or Azure App Service for Containers.

### Option A: Azure Container Apps with AZD

Prerequisites:
- Azure CLI installed
- Azure Developer CLI (`azd`) installed
- Docker Desktop running

Commands:

```bash
az login
azd auth login
azd init -t .
azd up
```

`azure.yaml` is included and points to the `Dockerfile` for building and deploying the web service.

### Option B: Azure App Service (Container)

1. Build and push container image to Azure Container Registry (ACR)
2. Create Linux Web App configured for container image
3. Set required app settings

Example commands:

```bash
az login
az group create --name rg-cloud-agent --location eastus
az acr create --resource-group rg-cloud-agent --name <acrName> --sku Basic
az acr build --registry <acrName> --image cloud-agent-ui:latest .

az appservice plan create --name plan-cloud-agent --resource-group rg-cloud-agent --is-linux --sku B1
az webapp create --resource-group rg-cloud-agent --plan plan-cloud-agent --name <webAppName> --deployment-container-image-name <acrName>.azurecr.io/cloud-agent-ui:latest
az webapp config appsettings set --resource-group rg-cloud-agent --name <webAppName> --settings WEBSITES_PORT=8000
```

Set AI environment variables in Azure (App Settings):

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION` (optional)

If these are not set, the app still runs using rule-based fallback analysis.

## CI/CD for Infra and App Deployment

This repository now includes a GitHub Actions pipeline for both infrastructure provisioning and application deployment:

- Workflow file: `.github/workflows/azure-cicd.yml`
- Infrastructure template: `infra/main.bicep`

### Azure Resources Provisioned by Pipeline

The infra stage deploys:

1. Resource Group (existing or created by workflow)
2. Azure Container Registry (ACR)
3. Log Analytics Workspace
4. Azure Container Apps Environment
5. Azure Container App (public ingress on port 8000)

The app stage:

1. Builds and pushes container image to ACR
2. Updates Container App image to new SHA tag
3. Sets Azure OpenAI runtime environment variables

### GitHub Secrets Required

Create these repository secrets before running pipeline:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `AZURE_LOCATION` (example: `eastus`)
- `ENVIRONMENT_NAME` (example: `dev`)
- `ACR_NAME` (globally unique, lowercase)
- `CONTAINER_APPS_ENV_NAME`
- `CONTAINER_APP_NAME`
- `LOG_ANALYTICS_NAME`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION` (example: `2024-08-01-preview`)

### One-Time Azure Setup for OIDC Login

Create an Azure AD app/service principal with federated credential for GitHub Actions and grant it at least `Contributor` role on target resource group.

After this, every push to `main` triggers:

1. Python test run
2. Infra deployment/update (Bicep)
3. Container build and app deployment

### Run Test Suite

```bash
python tests/test_agent_flow.py
```

Runs comprehensive test scenarios to verify agent behavior.

### Use as a Library

```python
from src.agent import SupportAgent

agent = SupportAgent()

result = agent.process_raw_ticket(
    ticket_id="TK001",
    customer_name="John Doe",
    customer_email="john@example.com",
    subject="Password reset issue",
    message="I can't reset my password..."
)

print(result['routing']['action'])  # resolve_with_kb, escalate_to_specialist, or send_followup
```

## How It Works

### Ticket Processing Flow

1. **Analyze Ticket**: Extract category, severity, key issues, and sentiment
2. **Search KB**: Find matching knowledge base articles
3. **Route Decision**: Determine action based on analysis and KB match quality
4. **Generate Response**: Create appropriate response for customer

### Routing Logic

- **Critical/High Severity**: Escalate to specialist
- **Good KB Match (score > 0.8)**: Resolve with knowledge base solution
- **Moderate Match (0.5-0.8)**: Send follow-up with KB solution
- **Low Match**: Escalate to specialist

### Categories

- `billing` - Billing and payment issues
- `technical` - Technical problems and errors
- `security` - Account security and authentication
- `account` - Account management
- `urgent` - Time-critical issues
- `general` - General inquiries

### Severity Levels

- `critical` - Service down, data loss, security issues
- `high` - Major functionality broken
- `medium` - Partial functionality issues
- `low` - General questions, minor issues

## Customization

### Add Knowledge Base Articles

Edit `config/kb_data.json`:

```json
{
  "articles": [
    {
      "article_id": "KB009",
      "title": "Your Solution Title",
      "category": "billing",
      "keywords": ["payment", "issue", "solution"],
      "solution_summary": "Brief summary",
      "steps": ["Step 1", "Step 2"],
      "prerequisites": ["Requirement 1"]
    }
  ]
}
```

### Modify Agent Behavior

Edit `config/agent_config.json` to change:
- System prompt and agent instructions
- Tool schemas
- Model configuration
- Temperature and iteration settings

### Update Tool Logic

Modify tool implementations in `src/tools/`:
- `ticket_analyzer.py`: Adjust categorization and sentiment analysis
- `kb_searcher.py`: Modify search algorithm and relevance scoring
- `router.py`: Change routing decision logic

## Logging

Logs are written to `logs/agent_YYYYMMDD.log` with both console and file output.

Set log level in `.env`:
```
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Testing

The test suite includes:

- **Simple Billing Issue**: Tests KB resolution for straightforward questions
- **Critical Technical Issue**: Tests escalation for urgent problems
- **Account Security Question**: Tests security category handling
- **Password Reset Failure**: Tests escalation for authentication issues
- **Integration Help**: Tests technical category and KB search
- **Subscription Upgrade**: Tests routing with multiple KB matches

## Next Steps

### Future Enhancements

1. **Azure Foundry Integration**: Connect web/API layer to full multi-agent orchestrations
2. **ML-based Analysis**: Use NLP/ML for more accurate categorization and sentiment
3. **Multi-language Support**: Handle tickets in multiple languages
4. **Feedback Loop**: Learn from specialist decisions to improve routing
5. **Analytics Dashboard**: Track ticket patterns and agent performance
6. **Real Database**: Replace JSON with Azure Cosmos DB or SQL

### Integration with Azure Services

To integrate with real Azure services:
1. Set up Azure AI Foundry project
2. Configure authentication via `.env`
3. Connect to real databases/APIs via tool implementations
4. Add monitoring and diagnostics via Application Insights

## Contributing

To extend the agent:
1. Add new tools in `src/tools/`
2. Update `config/agent_config.json` with tool schemas
3. Add tests in `tests/`
4. Document changes in code and README

## License

This project is part of the Azure Foundry Automaton Builder initiative.
