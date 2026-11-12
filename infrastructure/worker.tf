# 1. Permiso para que la identidad del Worker descargue imágenes desde Azure Container Registry
resource "azurerm_role_assignment" "worker_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.worker_identity.principal_id
}

# 2. Container App del Worker (100% Zero-Secrets, sin exposición HTTP)
resource "azurerm_container_app" "worker" {
  name                         = "ca-workforce-worker"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.app_rg.name
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.worker_identity.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.worker_identity.id
  }

  template {
    container {
      name   = "async-worker"
      image  = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
      cpu    = 0.25
      memory = "0.5Gi"

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
        value = azurerm_user_assigned_identity.worker_identity.client_id
      }
    }

    # En entornos Express ejecutamos 1 réplica continua escuchando la cola cada 5s
    min_replicas = 1
    max_replicas = 1
  }

  lifecycle {
    ignore_changes = [
      template[0].container[0].image
    ]
  }

  depends_on = [
    azurerm_role_assignment.worker_acr_pull,
    azurerm_role_assignment.worker_queue_processor,
    azurerm_role_assignment.worker_table_contributor
  ]
}