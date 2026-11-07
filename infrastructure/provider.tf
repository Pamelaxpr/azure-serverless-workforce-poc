terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0" # Usamos una versión estable 3.x
    }
  }

  # Aquí le decimos a Terraform dónde está su cerebro (Backend)
  # Nota: NO ponemos la Access Key aquí. Terraform la leerá del entorno.
  backend "azurerm" {
    resource_group_name  = "rg-terraform-workforce"
    storage_account_name = "sttfstateworkforce9625"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate" # El nombre del archivo que se creará
  }
}

# Configuramos el proveedor de Azure
provider "azurerm" {
  features {}
}