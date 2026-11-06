# Veritas Control Backend

## Estructura del proyecto

```text
veritas-control-backend/
├── README.md
├── buildspec.yml
├── estructura.md
├── output.json
├── prompt_test.json
├── samconfig.toml
├── template.yaml
├── infra/
│   ├── README.md
│   ├── cognito-infra.yaml
│   ├── database-infra.yaml
│   ├── network-infra.yaml
│   ├── pipeline-infra.yaml
│   ├── samconfig.toml
│   ├── storage-infra.yaml
│   └── veritas-headbar.jpg
├── lambdas/
│   ├── admin/
│   │   ├── create_tenant_handler.py
│   │   ├── get_analytics_handler.py
│   │   └── stripe_webhook_handler.py
│   ├── archivo_lista_negra_sat/
│   │   ├── descargar_csv_lista_negra_handler.py
│   │   └── requirements.txt
│   ├── calcular_kpis/
│   │   ├── Untitled-5.json
│   │   ├── calcular_kpis_nosql_handler.py
│   │   └── requirements.txt
│   ├── cargar_excel/
│   │   ├── carga_excel_handler.py
│   │   └── requirements.txt
│   ├── finanzas_dashboard copy/
│   │   ├── finanzas_handler.py
│   │   └── requirements.txt
│   ├── insertar_lista_negra_sat/
│   │   ├── insertar_lista_negra_handler.py
│   │   └── requirements.txt
│   ├── lista_clientes/
│   │   ├── lista_clientes_handler.py
│   │   └── requirements.txt
│   ├── materialidad/
│   │   ├── auditoria_69b_handler.py
│   │   ├── comunicacion_handler.py
│   │   ├── consolidador_handler.py
│   │   ├── contrato_handler.py
│   │   ├── core_zip_packer_handler.py
│   │   ├── crear_cliente_manual_handler.py
│   │   ├── detonar_handler.py
│   │   ├── disparador_handler.py
│   │   ├── evidencia_handler.py
│   │   ├── guardar_producto_nosql_handler.py
│   │   ├── listar_archivos_handler.py
│   │   ├── orquestador_materialidad.py
│   │   ├── planeacion_handler.py
│   │   ├── preventivo_bimestral_handler.py
│   │   ├── preventivo_comunicacion_handler.py
│   │   ├── preventivo_contrato_handler.py
│   │   ├── preventivo_evidencia_handler.py
│   │   ├── preventivo_planeacion_handler.py
│   │   ├── requirements.txt
│   │   ├── seed_prompts_robustos.py
│   │   ├── step1_extractor_handler.py
│   │   ├── step2_redactor_handler.py
│   │   └── step3_escultor_handler.py
│   ├── metricas/
│   │   ├── metricas_handler.py
│   │   └── requirements.txt
│   ├── notificaciones/
│   │   ├── historial_handler.py
│   │   └── leer_handler.py
│   ├── parser_s3/
│   │   ├── parser_s3_handler.py
│   │   └── requirements.txt
│   ├── registro/
│   │   ├── registro_handler.py
│   │   └── requirements.txt
│   ├── sincronizador_sat/
│   │   ├── requirements.txt
│   │   └── sat_sync_handler.py
│   └── url_firmada/
│       ├── requirements.txt
│       └── url_firmada_handler.py
└── scripts/
```

> El árbol corresponde al contenido presente en la raíz del repositorio al generar este documento. Se omite `.git`.
