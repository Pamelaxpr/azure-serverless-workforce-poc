# 1. Cuenta de Almacenamiento para colas y persistencia
resource "azurerm_storage_account" "storage" {
  name                     = "stworkforcepoc" # Debe ser único globalmente, solo letras minúsculas y números
  resource_group_name      = azurerm_resource_group.app_rg.name
  location                 = azurerm_resource_group.app_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  tags = {
    environment = "poc"
    project     = "azure-serverless-workforce-poc"
  }
}

# 2. Cola de almacenamiento para registros de fichaje / eventos
resource "azurerm_storage_queue" "time_tracking_queue" {
  name                 = "queue-workforce-events"
  storage_account_name = azurerm_storage_account.storage.name
}

# 3. Rol RBAC: Asignar 'Storage Queue Data Contributor' a la Identidad Gestionada de la API
# Permite enviar, leer y eliminar mensajes de la cola mediante Managed Identity
resource "azurerm_role_assignment" "queue_contributor" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = azurerm_user_assigned_identity.ca_api_identity.principal_id
}