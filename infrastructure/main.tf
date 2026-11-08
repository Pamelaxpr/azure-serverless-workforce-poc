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

# 5. Azure Container App (La API en sí misma)
resource "azurerm_container_app" "api" {
  name                         = "ca-workforce-api"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.app_rg.name
  revision_mode                = "Single"

  template {
    container {
      name = "api-ingestion"
      # IMAGEN FANTASMA: Desplegamos un Hola Mundo genérico. 
      # GitHub Actions sobreescribirá esto después con nuestra verdadera API.
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
    # Restricciones de Negocio de nuestro PMO:
    min_replicas = 1
    max_replicas = 3
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 80 # El puerto del Hello World fantasma. Lo cambiaremos a 8000 en el pipeline.

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}