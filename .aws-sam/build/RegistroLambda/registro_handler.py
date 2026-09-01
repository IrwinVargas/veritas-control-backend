import json
import os
import boto3

# Inicializamos el cliente de Cognito fuera del handler para reutilizar conexiones
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*', # Cambiar por tu URL de producción en el futuro
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS Preflight exitoso'})
        }
        
    try:
        # =========================================================================
        # CAPA DE SEGURIDAD MULTI-TENANT & RBAC (Validación del Token del Socio)
        # =========================================================================
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        if not authorizer:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': 'No autorizado. Token de Cognito ausente.'})
            }
        
        # Extraemos los datos del Socio firmante de forma inviolable desde la nube
        socio_tenant_id = authorizer.get('custom:tenant_id')
        socio_role = authorizer.get('custom:role')

        # REGLA DE NEGOCIO ESTRICTA: Solo los Socios administran el personal
        if socio_role != 'Socio':
            print(f"INTENTO DE INTRUSIÓN: Usuario con rol [{socio_role}] intentó registrar personal.")
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({'error': 'Acceso denegado. Solo los Socios Administradores pueden dar de alta usuarios.'})
            }

        # =========================================================================
        # 2. CAPTURA DE DATOS DEL NUEVO USUARIO (Desde el Frontend en React)
        # =========================================================================
        body = json.loads(event.get('body', '{}'))
        nuevo_email = body.get('email')
        nuevo_name = body.get('name')
        nuevo_role = body.get('role') # Asociado, Pasante o Contador

        # Validaciones de entrada básicas
        if not nuevo_email or not nuevo_name or not nuevo_role:
            return {
                'statusCode': 400,
                'headers': headers, 
                'body': json.dumps({'error': 'Faltan campos obligatorios (email, name, role).'})
            }

        # Validar que el Socio no intente crear un rol inexistente o corrupto
        if nuevo_role not in ['Socio', 'Asociado', 'Pasante', 'Contador']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'El rol seleccionado no es válido en el sistema.'})
            }

        # =========================================================================
        # 3. CONEXIÓN CON COGNITO PARA ALTA ADMINISTRATIVA
        # =========================================================================
        user_pool_id = os.environ.get('USER_POOL_ID')
        
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=nuevo_email, # El correo actúa como identificador único
            UserAttributes=[
                { 'Name': 'email', 'Value': nuevo_email },
                { 'Name': 'email_verified', 'Value': 'true' },
                { 'Name': 'name', 'Value': nuevo_name },
                # INYECCIÓN INVIOLABLE: Le heredamos el tenant_id exacto del Socio
                { 'Name': 'custom:tenant_id', 'Value': socio_tenant_id },
                { 'Name': 'custom:role', 'Value': nuevo_role }
            ],
            DesiredDeliveryMediums=['EMAIL'] # AWS le enviará su contraseña temporal por correo
        )

        print(f"Usuario [{nuevo_email}] creado con éxito bajo el Tenant [{socio_tenant_id}] por orden del Socio.")

        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Abogado registrado con éxito. Se ha enviado un correo con sus accesos temporales.'
            })
        }

    except cognito_client.exceptions.UsernameExistsException:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'El correo electrónico ya se encuentra registrado en la plataforma.'})
        }
    except Exception as e:
        print(f"Error crítico en el registro: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Error interno en los servidores de AWS al procesar el alta.'})
        }   
