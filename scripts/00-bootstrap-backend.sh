#!/bin/bash
# ==============================================================================
# PROYECTO: Azure Serverless Workforce PoC
# FASE 0: Bootstrapping de Infraestructura Base
# DESCRIPCIÓN: Crea el Storage Account inmutable para guardar el estado de Terraform.
# ==============================================================================

RESOURCE_GROUP="rg-terraform-workforce"
STORAGE_ACCOUNT="sttfstateworkforce$RANDOM"
# Usamos spaincentral para cumplimiento GDPR y baja latencia
REGION="spaincentral"

echo "1. Creando Resource Group: $RESOURCE_GROUP en $REGION..."
az group create --name $RESOURCE_GROUP --location $REGION -o none

echo "2. Creando Storage Account seguro: $STORAGE_ACCOUNT..."
az storage account create --resource-group $RESOURCE_GROUP --name $STORAGE_ACCOUNT --sku Standard_LRS --encryption-services blob -o none

echo "3. Creando Contenedor para el tfstate..."
az storage container create --name tfstate --account-name $STORAGE_ACCOUNT --auth-mode login -o none

echo "=========================================================="
echo "🎯 BOOTSTRAP COMPLETADO"
echo "Storage Account Name: $STORAGE_ACCOUNT"
echo "Obtén tu Access Key ejecutando:"
echo "az storage account keys list -g $RESOURCE_GROUP -n $STORAGE_ACCOUNT --query '[0].value' -o tsv"
echo "=========================================================="