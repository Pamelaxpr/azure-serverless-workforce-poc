# 1. Identidad Administrada dedicada para el Panel Web (solo necesita AcrPull)
resource "azurerm_user_assigned_identity" "panel_identity" {
  name                = "id-workforce-panel"
  resource_group_name = azurerm_resource_group.app_rg.name
  location            = azurerm_resource_group.app_rg.location
}

# 2. Permiso para descargar imágenes desde Azure Container Registry
resource "azurerm_role_assignment" "panel_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.panel_identity.principal_id
}

# 3. Container App pública para Streamlit (puerto 8501)
resource "azurerm_container_app" "panel" {
  name                         = "ca-workforce-panel"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.app_rg.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.panel_identity.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.panel_identity.id
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    container {
      name   = "web-panel"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "WORKFORCE_API_URL"
        value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
      }
    }

    min_replicas = 1
    max_replicas = 1
  }

  lifecycle {
    ignore_changes = [
      template[0].container[0].image
    ]
  }

  depends_on = [
    azurerm_role_assignment.panel_acr_pull
  ]
}

output "web_panel_url" {
  description = "URL pública del panel de control en Streamlit"
  value       = "https://${azurerm_container_app.panel.ingress[0].fqdn}"
}