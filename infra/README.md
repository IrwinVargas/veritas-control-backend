<p align="center">
  <a href="#">
    <img width="100%" src="veritas-headbar.jpg" alt="veritas-control">
  </a>
  <br>
  <img alt="build:passing" src="https://img.shields.io/badge/VERSION-1.0.0-brightgreen">
  <br>
</p>

## **Acerca de este proyecto**

En esta carpeta de Infra encontraras todos los CloudFormation necesarios para la infraestructura de Veritas Control. Para evitar errores al desplegar en un ambiente nuevo, sigue los despliegues en el orden de este documento.

## **1. Cognito UserPool**
Para desplegar e integrar Amazon Cognito de forma automatizada y replicable en tu cuenta de AWS, la mejor práctica de ingeniería es utilizar un archivo de AWS CloudFormation en formato YAML. Este código creará el User Pool, configurará el Client App que se conecta con el Frontend en React e inyectará de forma nativa los Custom Attributes (tenant_id y role) indispensables para la arquitectura multi-tenant.

El archivo se llama `cognito-infra.yaml`

### **1.1 Como desplegarlo desde tu terminal con la AWS CLI**

```bash
aws cloudformation create-stack \
  --stack-name veritas-control-cognito-dev \
  --template-body file://cognito-infra.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev \
  --profile tu-profile

```
**Nota:** `ParameterValue` debe tener el valor con base a al ambiente donde se pretende desplegar `[dev, qa, prod]`.

Una vez que termine el despliegue, la terminal o la consola de AWS te arrojará los valores exactos de `UserPoolId` y `AppClientId` listos para inyectarlos en tu archivo `.env` de React.