# Permiso de lectura/escritura en la cola para la identidad que ejecuta Terraform (pruebas locales)
resource "azurerm_role_assignment" "local_dev_queue_contributor" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}