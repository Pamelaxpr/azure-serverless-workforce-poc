# 1. Tabla NoSQL en Azure Table Storage para persistir los fichajes
resource "azurerm_storage_table" "attendance_table" {
  name                 = "tblworkforceattendance"
  storage_account_name = azurerm_storage_account.storage.name
}

# 2. Identidad Administrada dedicada para el futuro microservicio consumidor (Worker)
resource "azurerm_user_assigned_identity" "worker_identity" {
  name                = "id-workforce-worker"
  resource_group_name = azurerm_resource_group.app_rg.name
  location            = azurerm_resource_group.app_rg.location
}

# 3. Permiso RBAC en la Cola para el Worker (Principio de mínimo privilegio:
# solo permite leer, procesar y borrar mensajes ya procesados, no administrar la cola)
resource "azurerm_role_assignment" "worker_queue_processor" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Queue Data Message Processor"
  principal_id         = azurerm_user_assigned_identity.worker_identity.principal_id
}

# 4. Permiso RBAC en Table Storage para que el Worker inserte/consulte registros
resource "azurerm_role_assignment" "worker_table_contributor" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = azurerm_user_assigned_identity.worker_identity.principal_id
}

# 5. Permiso RBAC en Table Storage para tu usuario local (pruebas en WSL con az login)
resource "azurerm_role_assignment" "local_dev_table_contributor" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}