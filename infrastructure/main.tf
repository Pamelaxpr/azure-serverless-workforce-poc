# 1. Grupo de Recursos para la Aplicación (Separado de la caja fuerte)
resource "azurerm_resource_group" "app_rg" {
  name     = "rg-workforce-app"
  location = "spaincentral"
}

# 2. Log Analytics Workspace (Requisito obligatorio de Azure para ver los logs del contenedor)
resource "azurerm_log_analytics_workspace" "law" {
  name                = "law-workforce-app"
  location            = azurerm_resource_group.app_rg.location
  resource_group_name = azurerm_resource_group.app_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# 3. Azure Container Registry (El almacén de contenedores)
resource "azurerm_container_registry" "acr" {
  name                = "acrworkforcepoc" # NOTA: Azure exige que este nombre sea ÚNICO EN EL MUNDO. Si falla al aplicar, añádele un número al final (ej. acrworkforcepoc99)
  resource_group_name = azurerm_resource_group.app_rg.name
  location            = azurerm_resource_group.app_rg.location
  sku                 = "Basic" # El más barato, ideal para PoC y estudiantes
  admin_enabled       = true    # Necesario para que GitHub Actions se pueda autenticar fácilmente
}

# 4. Azure Container App Environment (El ecosistema Serverless)
resource "azurerm_container_app_environment" "env" {
  name                       = "cae-workforce-app"
  location                   = azurerm_resource_group.app_rg.location
  resource_group_name        = azurerm_resource_group.app_rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
}

# 5. Identidad Gestionada específica para la Container App (Resuelve la restricción Express)
resource "azurerm_user_assigned_identity" "ca_api_identity" {
  name                = "id-ca-workforce-api"
  location            = azurerm_resource_group.app_rg.location
  resource_group_name = azurerm_resource_group.app_rg.name
}

# 5.1 Permiso explícito para que la App descargue del Registro
resource "azurerm_role_assignment" "acr_pull" {
  scope                            = azurerm_container_registry.acr.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_user_assigned_identity.ca_api_identity.principal_id
  skip_service_principal_aad_check = true
}

# 5.2 Azure Container App (La API)
resource "azurerm_container_app" "api" {
  name                         = "ca-workforce-api"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.app_rg.name
  revision_mode                = "Single"

  # A. Asignamos la identidad de usuario creada previamente
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.ca_api_identity.id]
  }

  # B. Enlazamos el ACR usando la ID exacta de la Identidad Gestionada
  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.ca_api_identity.id
  }

  template {
    container {
      name = "api-ingestion"
      # IMAGEN FANTASMA: Desplegamos un Hola Mundo genérico. 
      # GitHub Actions sobreescribirá esto después con nuestra verdadera API.
      image  = "${azurerm_container_registry.acr.login_server}/api-ingestion:latest"
      cpu    = 0.25
      memory = "0.5Gi"
      # Variables de entorno para la integración con Azure SDK en FastAPI
      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = azurerm_storage_account.storage.name
      }

      env {
        name  = "AZURE_STORAGE_QUEUE_NAME"
        value = azurerm_storage_queue.time_tracking_queue.name
      }

      env {
        name  = "AZURE_STORAGE_TABLE_NAME"
        value = azurerm_storage_table.attendance_table.name
      }

      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.ca_api_identity.client_id
      }
    }
    # Restricciones de Negocio de nuestro PMO:
    min_replicas = 1
    max_replicas = 3
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8000 # El puerto del Hello World fantasma. Lo cambiaremos a 8000 en el pipeline.
    transport                  = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  # Evita que Terraform sobrescriba la imagen real y el puerto 8000 cuando GitHub Actions actualice la app
  lifecycle {
    ignore_changes = [
      template[0].container[0].image
    ]
  }

  depends_on = [
    azurerm_role_assignment.acr_pull
  ]
}

# 7. Identidad Gestionada para GitHub Actions (Gestionada 100% por Terraform)
resource "azurerm_user_assigned_identity" "github_actions" {
  name                = "id-github-actions"
  location            = azurerm_resource_group.app_rg.location
  resource_group_name = azurerm_resource_group.app_rg.name
}

# 8. Asignación de Rol Contributor 
resource "azurerm_role_assignment" "github_contributor" {
  scope                = azurerm_resource_group.app_rg.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.github_actions.principal_id
}

# 9. Credencial Federada OIDC
resource "azurerm_federated_identity_credential" "github_oidc" {
  name                = "cred-github-actions"
  resource_group_name = azurerm_resource_group.app_rg.name
  parent_id           = azurerm_user_assigned_identity.github_actions.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  subject             = "repo:Pamelaxpr@188255722/azure-serverless-workforce-poc@1448476566:ref:refs/heads/main"
}