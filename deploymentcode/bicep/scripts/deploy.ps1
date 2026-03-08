param(
    [Parameter()]
    [ValidateSet('dev', 'test')]
    [string]$Environment = 'dev',

    [Parameter()]
    [string]$Location = 'eastus2'
)

$ErrorActionPreference = 'Stop'

# Configuration
$ProjectName = 'claudebricks'
$ResourceGroup = "rg-$ProjectName-$Environment"
$TemplateFile = Join-Path $PSScriptRoot '..\main.bicep'
$ParamsFile = Join-Path $PSScriptRoot "..\parameters\$Environment.bicepparam"

Write-Host "=== Claude.Bricks Infrastructure Deployment ===" -ForegroundColor Cyan
Write-Host "Environment: $Environment"
Write-Host "Location:    $Location"
Write-Host "RG:          $ResourceGroup"
Write-Host ""

# Verify login
try { az account show | Out-Null } catch {
    Write-Error "Not logged in. Run 'az login' first."
    exit 1
}

$Subscription = az account show --query name -o tsv
Write-Host "Subscription: $Subscription"

# Create resource group
Write-Host "`n--- Creating resource group ---" -ForegroundColor Yellow
az group create `
    --name $ResourceGroup `
    --location $Location `
    --tags project=claude-bricks environment=$Environment managedBy=bicep

# What-if
Write-Host "`n--- What-If Preview ---" -ForegroundColor Yellow
az deployment group what-if `
    --resource-group $ResourceGroup `
    --template-file $TemplateFile `
    --parameters $ParamsFile `
    --parameters location=$Location

# Confirm
$Confirm = Read-Host "`nProceed with deployment? (y/N)"
if ($Confirm -ne 'y') {
    Write-Host "Deployment cancelled."
    exit 0
}

# Deploy
$DeploymentName = "deploy-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "`n--- Deploying ---" -ForegroundColor Yellow
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file $TemplateFile `
    --parameters $ParamsFile `
    --parameters location=$Location `
    --name $DeploymentName `
    --verbose

Write-Host "`n=== Deployment complete ===" -ForegroundColor Green
