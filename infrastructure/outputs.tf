output "azure_client_id" {
  description = "ID del Cliente OIDC de GitHub Actions (AZURE_CLIENT_ID)"
  value       = azurerm_user_assigned_identity.github_actions.client_id
}

output "azure_tenant_id" {
  description = "ID del Inquilino de Azure (AZURE_TENANT_ID)"
  value       = data.azurerm_client_config.current.tenant_id
}

output "azure_subscription_id" {
  description = "ID de la Suscripción de Azure (AZURE_SUBSCRIPTION_ID)"
  value       = data.azurerm_client_config.current.subscription_id
}

output "acr_login_server" {
  description = "Servidor de inicio de sesión de ACR (ACR_LOGIN_SERVER)"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_username" {
  description = "Usuario Administrador del ACR (ACR_USERNAME)"
  value       = azurerm_container_registry.acr.admin_username
}

output "acr_password" {
  description = "Contraseña Administradora del ACR (ACR_PASSWORD)"
  value       = azurerm_container_registry.acr.admin_password
  sensitive   = true
}

output "container_app_url" {
  description = "URL pública de acceso a la Container App"
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "ca_identity_client_id" {
  description = "Client ID de la Identidad Gestionada de la Container App"
  value       = azurerm_user_assigned_identity.ca_api_identity.client_id
}