# User Stories - ÉPICO 3: Conversão de Documentos

**Versão:** 1.0 MVP  
**Data:** Janeiro 2026  
**Prioridade:** 1 (Crítico para MVP)  
**Status:** Planejamento

---

## 📋 Índice do Épico

- [3.1 Infraestrutura de Conversão](#31-infraestrutura-de-conversão)
- [3.2 Upload e Validação de Arquivos](#32-upload-e-validação-de-arquivos)
- [3.3 Processamento e Conversão](#33-processamento-e-conversão)
- [3.4 Notificações em Tempo Real (SSE)](#34-notificações-em-tempo-real-sse)
- [3.5 Tratamento de Erros e Retry](#35-tratamento-de-erros-e-retry)
- [3.6 Monitoramento e Logs](#36-monitoramento-e-logs)

---

## 3.1 Infraestrutura de Conversão

### US-3.1.1: Configurar Sistema de Queue (Celery + RabbitMQ)

**Como** desenvolvedor,  
**Quero** configurar sistema de filas para processamento assíncrono,  
**Para** converter documentos em background sem bloquear requisições HTTP.

#### Critérios de Aceitação

**Funcional:**
- [ ] Sistema de queue configurado e operacional
- [ ] Filas separadas por tipo de job:
  - `documents.conversion` - Conversão de documentos
  - `documents.embedding` - Geração de embeddings (futuro)
  - `notifications.email` - Envio de emails
- [ ] Workers executando em background
- [ ] Dead Letter Queue (DLQ) para jobs falhados
- [ ] Retry automático configurado (até 3 tentativas)
- [ ] Exponential backoff entre retries (1min, 5min, 15min)

**Técnico:**
- [ ] RabbitMQ instalado e configurado:
  - Porta: 5672 (AMQP)
  - Management UI: 15672
  - Usuário/senha configurados
  - Virtual host: `/documents`
- [ ] Celery configurado no backend:
  ```python
  # celery_config.py
  broker_url = 'amqp://user:pass@rabbitmq:5672/documents'
  result_backend = 'redis://redis:6379/1'
  task_serializer = 'json'
  accept_content = ['json']
  result_serializer = 'json'
  timezone = 'UTC'
  enable_utc = True
  
  task_routes = {
      'documents.tasks.convert_document': {'queue': 'documents.conversion'},
      'documents.tasks.generate_embeddings': {'queue': 'documents.embedding'},
      'notifications.tasks.send_email': {'queue': 'notifications.email'}
  }
  task_routes = {
      'documents.tasks.convert_document': {'queue': 'celery'},
      'documents.tasks.generate_embeddings': {'queue': 'documents.embedding'},
      'notifications.tasks.send_email': {'queue': 'notifications.email'}
  }
  
  task_annotations = {
      'documents.tasks.convert_document': {
          'rate_limit': '10/m',  # Max 10 conversões por minuto
          'time_limit': 600,      # Timeout 10 minutos
          'soft_time_limit': 540  # Soft timeout 9 minutos
      }
  }
  ```
- [ ] Workers iniciados:
  ```bash
  celery -A app.celery worker --loglevel=info --queues=documents.conversion -c 4
  celery -A app.celery worker --loglevel=info --queues=notifications.email -c 2
  ```
- [ ] Celery Beat para tarefas agendadas (limpeza de locks expirados, etc.)
- [ ] Dead Letter Exchange configurado:
  ```python
  task_reject_on_worker_lost = True
  task_acks_late = True
  ```

**Monitoramento:**
- [ ] Flower instalado para monitorar workers:
  ```bash
  celery -A app.celery flower --port=5555
  ```
- [ ] Dashboard mostra:
  - Workers ativos
  - Jobs em processamento
  - Jobs na fila
  - Taxa de sucesso/falha
  - Tempo médio de processamento

**Docker Compose:**
```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: documents_user
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
      RABBITMQ_DEFAULT_VHOST: /documents
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  celery_worker:
    build: .
    command: celery -A app.celery worker --loglevel=info --queues=documents.conversion -c 4
    environment:
      CELERY_BROKER_URL: amqp://documents_user:${RABBITMQ_PASSWORD}@rabbitmq:5672/documents
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    depends_on:
      - rabbitmq
      - redis

  flower:
    build: .
    command: celery -A app.celery flower --port=5555
    ports:
      - "5555:5555"
    environment:
      CELERY_BROKER_URL: amqp://documents_user:${RABBITMQ_PASSWORD}@rabbitmq:5672/documents
    depends_on:
      - rabbitmq
```

**Health Checks:**
- [ ] Endpoint: `GET /api/v1/health/queue`
- [ ] Resposta:
  ```json
  {
    "rabbitmq": {
      "status": "healthy",
      "connection": "ok"
    },
    "celery": {
      "status": "healthy",
      "active_workers": 6,
      "queues": {
        "documents.conversion": {
          "pending": 3,
          "active": 2
        }
      }
    }
  }
  ```

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** Nenhuma (infra base)

---

### US-3.1.2: Configurar Armazenamento de Arquivos (S3/MinIO)

**Como** desenvolvedor,  
**Quero** configurar armazenamento de objetos,  
**Para** salvar arquivos originais e imagens dos documentos.

#### Critérios de Aceitação

**Funcional:**
- [ ] Object storage configurado (S3 AWS ou MinIO local)
- [ ] Buckets organizados:
  - `documents-originals` - Arquivos originais enviados
  - `documents-images` - Imagens extraídas/uploaded dos documentos
  - `documents-exports` - Exports gerados (PDF, DOCX - futuro)
- [ ] URLs assinadas (presigned URLs) para acesso temporário
- [ ] Política de expiração configurada (opcionais para originais, 90 dias para exports)
- [ ] Versionamento habilitado em bucket de originais (backup)

**Técnico:**
- [ ] SDK configurado (boto3 para S3 ou MinIO client):
  ```python
  # storage.py
  import boto3
  from botocore.config import Config
  
  s3_client = boto3.client(
      's3',
      endpoint_url=settings.S3_ENDPOINT,  # None para AWS, URL para MinIO
      aws_access_key_id=settings.S3_ACCESS_KEY,
      aws_secret_access_key=settings.S3_SECRET_KEY,
      config=Config(signature_version='s3v4'),
      region_name=settings.S3_REGION
  )
  
  def upload_file(file_path: str, bucket: str, key: str) -> str:
      """Upload file and return public URL"""
      s3_client.upload_file(file_path, bucket, key)
      return f"{settings.S3_ENDPOINT}/{bucket}/{key}"
  
  def generate_presigned_url(bucket: str, key: str, expiration: int = 3600) -> str:
      """Generate presigned URL for temporary access"""
      return s3_client.generate_presigned_url(
          'get_object',
          Params={'Bucket': bucket, 'Key': key},
          ExpiresIn=expiration
      )
  
  def delete_file(bucket: str, key: str):
      """Delete file from storage"""
      s3_client.delete_object(Bucket=bucket, Key=key)
  ```

**Estrutura de Chaves (Keys):**
```
documents-originals/
  ├── {group_id}/
  │   ├── {document_id}/
  │   │   ├── original.pdf
  │   │   └── original.docx

documents-images/
  ├── {group_id}/
  │   ├── {document_id}/
  │   │   ├── image-001.png
  │   │   ├── image-002.jpg
  │   │   └── ...

documents-exports/
  ├── {group_id}/
  │   ├── {document_id}/
  │   │   ├── v1.0.pdf
  │   │   └── v2.1.docx
```

**Configuração MinIO (Docker):**
```yaml
services:
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  createbuckets:
    image: minio/mc
    depends_on:
      - minio
    entrypoint: >
      /bin/sh -c "
      /usr/bin/mc alias set myminio http://minio:9000 minioadmin ${MINIO_PASSWORD};
      /usr/bin/mc mb myminio/documents-originals --ignore-existing;
      /usr/bin/mc mb myminio/documents-images --ignore-existing;
      /usr/bin/mc mb myminio/documents-exports --ignore-existing;
      /usr/bin/mc anonymous set download myminio/documents-images;
      "
```

**Políticas de Lifecycle:**
- [ ] Arquivos originais: retenção indefinida (ou conforme compliance)
- [ ] Exports temporários: deletar após 90 dias
- [ ] Versionamento: manter últimas 5 versões de originais

**Segurança:**
- [ ] Buckets privados por padrão (exceto images com presigned URLs)
- [ ] CORS configurado para upload direto do frontend (se necessário)
- [ ] Encryption at rest habilitada (S3 SSE ou MinIO encryption)

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** Nenhuma

---

### US-3.1.3: Instalar e Configurar Docling

**Como** desenvolvedor,  
**Quero** instalar e configurar Docling,  
**Para** converter documentos para Markdown.

#### Critérios de Aceitação

**Funcional:**
- [ ] Docling instalado no ambiente de workers
- [ ] Formatos suportados validados:
  - PDF (incluindo PDFs escaneados com OCR)
  - DOCX (Microsoft Word)
  - HTML
  - TXT
  - MD (Markdown - conversão direta)
  - PPTX (PowerPoint - opcional)
  - XLSX (Excel - opcional, apenas texto)
- [ ] Conversão preserva:
  - Estrutura de headers (H1-H6)
  - Listas (ordered, unordered)
  - Tabelas
  - Links
  - Imagens (extraídas e salvas separadamente)
  - Formatação básica (bold, italic)
- [ ] Configurações otimizadas para qualidade e velocidade

**Técnico:**
- [ ] Instalação Docling:
  ```bash
  pip install docling --break-system-packages
  # Ou via requirements.txt
  docling==x.x.x
  ```
- [ ] Wrapper Python para Docling:
  ```python
  # docling_converter.py
  from docling.document_converter import DocumentConverter
  from pathlib import Path
  import logging
  
  logger = logging.getLogger(__name__)
  
  class DoclingConverter:
      def __init__(self):
          self.converter = DocumentConverter()
      
      def convert_to_markdown(
          self, 
          input_path: str, 
          output_path: str,
          extract_images: bool = True
      ) -> dict:
          """
          Convert document to Markdown
          
          Returns:
              {
                  'markdown': str,
                  'images': [{'path': str, 'original_name': str}],
                  'metadata': {...}
              }
          """
          try:
              result = self.converter.convert(
                  input_path,
                  output_format='markdown'
              )
              
              markdown_content = result.document.export_to_markdown()
              
              # Salvar Markdown
              Path(output_path).write_text(markdown_content, encoding='utf-8')
              
              # Extrair imagens se houver
              images = []
              if extract_images and result.document.pictures:
                  images = self._extract_images(result.document.pictures, output_path)
              
              metadata = {
                  'pages': result.document.num_pages if hasattr(result.document, 'num_pages') else None,
                  'title': result.document.title if hasattr(result.document, 'title') else None,
                  'author': result.document.author if hasattr(result.document, 'author') else None,
              }
              
              return {
                  'markdown': markdown_content,
                  'images': images,
                  'metadata': metadata
              }
          
          except Exception as e:
              logger.error(f"Docling conversion failed: {str(e)}")
              raise
      
      def _extract_images(self, pictures, base_path):
          """Extract and save images"""
          images = []
          for idx, picture in enumerate(pictures):
              image_path = f"{base_path}/image-{idx:03d}.{picture.format}"
              picture.save(image_path)
              images.append({
                  'path': image_path,
                  'original_name': f"image-{idx:03d}.{picture.format}"
              })
          return images
      
      def is_supported_format(self, file_extension: str) -> bool:
          """Check if file format is supported"""
          supported = ['.pdf', '.docx', '.html', '.txt', '.md', '.pptx', '.xlsx']
          return file_extension.lower() in supported
  ```

**Configuração de Conversão:**
```python
# Docling config
DOCLING_CONFIG = {
    'ocr_enabled': True,  # OCR para PDFs escaneados
    'table_detection': True,  # Detectar tabelas
    'image_extraction': True,  # Extrair imagens
    'max_image_size': 5 * 1024 * 1024,  # 5 MB por imagem
    'timeout': 300,  # 5 minutos timeout por documento
}
```

**Validação de Funcionamento:**
- [ ] Teste unitário de conversão para cada formato suportado
- [ ] Teste de conversão de PDF com imagens
- [ ] Teste de conversão de DOCX com tabelas
- [ ] Teste de conversão de PDF escaneado (OCR)

**Dependências do Sistema:**
- [ ] Dependências de OCR instaladas (se necessário):
  ```bash
  apt-get install tesseract-ocr tesseract-ocr-por
  ```

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-3.1.1

---

## 3.2 Upload e Validação de Arquivos

### US-3.2.1: Upload de Arquivo com Validação (Frontend + Backend)

**Como** Editor,  
**Quero** fazer upload de documentos com validação em tempo real,  
**Para** garantir que apenas arquivos válidos sejam enviados.

#### Critérios de Aceitação

**Funcional:**
- [ ] Interface de upload (drag & drop + botão)
- [ ] Validações client-side (frontend):
  - Formato do arquivo (extensão)
  - Tamanho máximo (100 MB - configurável)
  - Nome do arquivo (caracteres válidos)
- [ ] Preview do arquivo selecionado:
  - Nome
  - Tamanho (formatado: KB, MB)
  - Tipo (ícone baseado em extensão)
  - Miniatura (se imagem)
- [ ] Barra de progresso durante upload
- [ ] Feedback visual de validação:
  - ✅ Arquivo válido (borda verde)
  - ❌ Arquivo inválido (borda vermelha + mensagem de erro)
- [ ] Mensagens de erro claras:
  - "Formato não suportado. Use: PDF, DOCX, HTML, TXT, MD"
  - "Arquivo muito grande. Tamanho máximo: 100 MB"
  - "Nome do arquivo contém caracteres inválidos"

**Técnico - Frontend:**
```javascript
// FileUpload.jsx
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB
const SUPPORTED_FORMATS = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/html',
  'text/plain',
  'text/markdown'
];

function validateFile(file) {
  const errors = [];
  
  // Validar tamanho
  if (file.size > MAX_FILE_SIZE) {
    errors.push('Arquivo muito grande. Tamanho máximo: 100 MB');
  }
  
  // Validar formato
  if (!SUPPORTED_FORMATS.includes(file.type)) {
    errors.push('Formato não suportado. Use: PDF, DOCX, HTML, TXT, MD');
  }
  
  // Validar nome
  const invalidChars = /[<>:"/\\|?*]/;
  if (invalidChars.test(file.name)) {
    errors.push('Nome do arquivo contém caracteres inválidos');
  }
  
  return errors;
}

async function uploadFile(file, metadata) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', metadata.title);
  formData.append('group_id', metadata.group_id);
  formData.append('folder_id', metadata.folder_id);
  formData.append('tags', JSON.stringify(metadata.tags));
  formData.append('category_id', metadata.category_id);
  
  const response = await fetch('/api/v1/documents/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData,
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      setUploadProgress(percentCompleted);
    }
  });
  
  if (!response.ok) {
    throw new Error(await response.text());
  }
  
  return response.json();
}
```

**Técnico - Backend:**
- [ ] Endpoint: `POST /api/v1/documents/upload`
- [ ] Content-Type: `multipart/form-data`
- [ ] Validações server-side (NUNCA confiar apenas no frontend):
  ```python
  # validators.py
  import magic
  from pathlib import Path
  
  SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.html', '.txt', '.md', '.pptx', '.xlsx']
  SUPPORTED_MIME_TYPES = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/html',
      'text/plain',
      'text/markdown'
  ]
  MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
  
  def validate_upload(file) -> tuple[bool, list[str]]:
      errors = []
      
      # Validar tamanho
      file.seek(0, 2)  # Seek to end
      size = file.tell()
      file.seek(0)  # Reset
      
      if size > MAX_FILE_SIZE:
          errors.append(f'File too large: {size} bytes (max {MAX_FILE_SIZE})')
      
      # Validar extensão
      ext = Path(file.filename).suffix.lower()
      if ext not in SUPPORTED_EXTENSIONS:
          errors.append(f'Unsupported extension: {ext}')
      
      # Validar MIME type (magic numbers)
      mime = magic.from_buffer(file.read(2048), mime=True)
      file.seek(0)
      
      if mime not in SUPPORTED_MIME_TYPES:
          errors.append(f'Invalid file type: {mime}')
      
      # Validar nome do arquivo
      invalid_chars = set('<>:"/\\|?*')
      if any(c in file.filename for c in invalid_chars):
          errors.append('Filename contains invalid characters')
      
      return len(errors) == 0, errors
  ```

**Sanitização:**
- [ ] Nome do arquivo sanitizado (remover caracteres perigosos)
- [ ] Path traversal prevention (não permitir ../, etc.)
- [ ] Arquivo salvo temporariamente com UUID único

**Rate Limiting:**
- [ ] Máximo 10 uploads por minuto por usuário
- [ ] Máximo 100 MB por upload
- [ ] Máximo 500 MB por hora por usuário

**UX:**
- [ ] Drag & drop visual com destaque ao arrastar arquivo
- [ ] Múltiplos arquivos? (MVP: apenas 1 por vez)
- [ ] Loading spinner durante upload
- [ ] Progresso em % e MB/s
- [ ] Possibilidade de cancelar upload (AbortController)
- [ ] Mensagens de erro inline, não apenas toast

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-2.2.3, US-3.1.2

---

### US-3.2.2: Salvar Arquivo Original no Storage

**Como** sistema,  
**Quero** salvar arquivo original enviado no object storage,  
**Para** manter backup e permitir re-conversão futura.

#### Critérios de Aceitação

**Funcional:**
- [ ] Arquivo original salvo após upload bem-sucedido
- [ ] Arquivo salvo antes de adicionar job na fila (garantir que existe)
- [ ] Path/URL do arquivo salvo em `documents.original_file_url`
- [ ] Metadados do arquivo salvos:
  - Nome original
  - Tamanho em bytes
  - MIME type
  - Checksum (MD5 ou SHA256)
- [ ] Se upload falhar, arquivo temporário é deletado

**Técnico:**
- [ ] Fluxo de salvamento:
  ```python
  # upload_handler.py
  import hashlib
  from pathlib import Path
  
  async def handle_upload(file, document_id: int, group_id: int):
      # 1. Salvar temporariamente
      temp_path = f"/tmp/{document_id}_{file.filename}"
      with open(temp_path, 'wb') as f:
          f.write(file.read())
      
      # 2. Calcular checksum
      checksum = calculate_checksum(temp_path)
      
      # 3. Upload para S3
      s3_key = f"{group_id}/{document_id}/original{Path(file.filename).suffix}"
      s3_url = upload_to_s3(
          temp_path, 
          bucket='documents-originals', 
          key=s3_key
      )
      
      # 4. Salvar metadados no banco
      await db.execute(
          """
          UPDATE documents 
          SET 
              original_file_url = $1,
              original_file_name = $2,
              original_file_size = $3,
              original_file_checksum = $4,
              original_mime_type = $5
          WHERE id = $6
          """,
          s3_url, file.filename, file.size, checksum, file.content_type, document_id
      )
      
      # 5. Deletar arquivo temporário
      os.remove(temp_path)
      
      return s3_url
  
  def calculate_checksum(file_path: str) -> str:
      sha256 = hashlib.sha256()
      with open(file_path, 'rb') as f:
          for chunk in iter(lambda: f.read(4096), b''):
              sha256.update(chunk)
      return sha256.hexdigest()
  ```

**Schema Adicional:**
```sql
ALTER TABLE documents 
ADD COLUMN original_file_url VARCHAR(500),
ADD COLUMN original_file_name VARCHAR(255),
ADD COLUMN original_file_size BIGINT,
ADD COLUMN original_file_checksum VARCHAR(64),
ADD COLUMN original_mime_type VARCHAR(100);
```

**Tratamento de Erro:**
- [ ] Se upload para S3 falhar: reverter criação do documento (transação)
- [ ] Log de erro detalhado
- [ ] Retornar 500 com mensagem clara ao usuário

**Segurança:**
- [ ] Verificar checksum antes de processar (detectar corrupção)
- [ ] Verificar que arquivo não foi modificado após upload

**Prioridade:** Crítica  
**Estimativa:** 5 pontos  
**Dependências:** US-3.2.1, US-3.1.2

---

## 3.3 Processamento e Conversão

### US-3.3.1: Adicionar Job de Conversão na Fila

**Como** sistema,  
**Quero** adicionar job de conversão na fila após upload,  
**Para** processar conversão de forma assíncrona.

#### Critérios de Aceitação

**Funcional:**
- [ ] Após salvar arquivo original, job é adicionado à fila `documents.conversion`
- [ ] Job contém dados necessários para conversão:
  - document_id
  - original_file_url
  - file_type (extensão)
  - group_id (para organizar outputs)
- [ ] Status do documento atualizado: NEW → PROCESSING
- [ ] Resposta HTTP retornada imediatamente (não espera conversão)
- [ ] Job ID retornado para tracking (opcional)

**Técnico:**
- [ ] Task Celery para conversão:
  ```python
  # tasks.py
  from celery import Task
  from app import celery
  
  @celery.task(
      bind=True,
      name='documents.tasks.convert_document',
      max_retries=3,
      default_retry_delay=60  # 1 minuto entre retries
  )
  def convert_document(self, document_id: int):
      """
      Convert document to Markdown using Docling
      
      Args:
          document_id: ID do documento a converter
      
      Raises:
          Retry: Se conversão falhar (até 3x)
      """
      try:
          # 1. Buscar documento no banco
          document = get_document(document_id)
          
          if not document:
              raise ValueError(f"Document {document_id} not found")
          
          # 2. Atualizar status para PROCESSING
          update_document_status(document_id, 'processing')
          
          # 3. Download arquivo do S3
          local_path = download_from_s3(document.original_file_url)
          
          # 4. Converter com Docling
          converter = DoclingConverter()
          result = converter.convert_to_markdown(
              input_path=local_path,
              output_path=f"/tmp/{document_id}/",
              extract_images=True
          )
          
          # 5. Upload de imagens para S3
          image_urls = []
          for img in result['images']:
              s3_url = upload_to_s3(
                  img['path'],
                  bucket='documents-images',
                  key=f"{document.group_id}/{document_id}/{img['original_name']}"
              )
              image_urls.append(s3_url)
          
          # 6. Substituir referências de imagens no Markdown
          markdown = replace_image_urls(result['markdown'], image_urls)
          
          # 7. Salvar Markdown no banco
          update_document_content(document_id, markdown, result['metadata'])
          
          # 8. Atualizar status para DRAFT
          update_document_status(document_id, 'draft')
          
          # 9. Limpar arquivos temporários
          cleanup_temp_files(f"/tmp/{document_id}/")
          
          # 10. Emitir evento SSE
          emit_sse_event(document_id, 'status_change', {'status': 'draft'})
          
          logger.info(f"Document {document_id} converted successfully")
          
      except Exception as exc:
          logger.error(f"Conversion failed for document {document_id}: {str(exc)}")
          
          # Incrementar contador de tentativas
          increment_conversion_attempts(document_id)
          
          # Retry se ainda há tentativas
          if self.request.retries < self.max_retries:
              raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
          else:
              # Falhou após 3 tentativas
              update_document_status(document_id, 'error')
              update_document_error(document_id, str(exc))
              emit_sse_event(document_id, 'status_change', {
                  'status': 'error',
                  'error': str(exc)
              })
              raise
  ```

**Adicionar Job:**
```python
# upload_handler.py
from tasks import convert_document

async def after_upload(document_id: int):
    # Adicionar job na fila
    task = convert_document.apply_async(
        args=[document_id],
        queue='documents.conversion',
        routing_key='documents.conversion'
    )
    
    logger.info(f"Conversion job queued for document {document_id}, task_id: {task.id}")
    
    return task.id
```

**Schema Adicional:**
```sql
ALTER TABLE documents 
ADD COLUMN conversion_attempts INTEGER DEFAULT 0,
ADD COLUMN conversion_error TEXT,
ADD COLUMN conversion_started_at TIMESTAMP,
ADD COLUMN conversion_completed_at TIMESTAMP,
ADD COLUMN celery_task_id VARCHAR(255);
```

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-3.1.1, US-3.1.3, US-3.2.2

---

### US-3.3.2: Worker Processa Conversão com Docling

**Como** worker Celery,  
**Quero** processar job de conversão usando Docling,  
**Para** converter documento em Markdown.

#### Critérios de Aceitação

**Funcional:**
- [ ] Worker recebe job da fila
- [ ] Worker baixa arquivo original do S3
- [ ] Worker converte arquivo usando Docling
- [ ] Worker extrai imagens (se houver)
- [ ] Worker faz upload de imagens para S3
- [ ] Worker atualiza conteúdo Markdown no banco
- [ ] Worker atualiza status do documento (PROCESSING → DRAFT)
- [ ] Worker limpa arquivos temporários
- [ ] Worker emite evento SSE de sucesso

**Técnico:**
- [ ] Implementação detalhada em US-3.3.1 (task `convert_document`)
- [ ] Funções auxiliares:
  ```python
  def download_from_s3(s3_url: str) -> str:
      """Download file from S3 to temp location"""
      parsed = urlparse(s3_url)
      bucket = parsed.netloc.split('.')[0]
      key = parsed.path.lstrip('/')
      
      temp_path = f"/tmp/{uuid.uuid4()}.tmp"
      s3_client.download_file(bucket, key, temp_path)
      
      return temp_path
  
  def replace_image_urls(markdown: str, image_urls: list) -> str:
      """Replace local image paths with S3 URLs in markdown"""
      for idx, url in enumerate(image_urls):
          markdown = markdown.replace(
              f"image-{idx:03d}",
              url
          )
      return markdown
  
  def update_document_content(document_id: int, content: str, metadata: dict):
      """Update document with converted content"""
      db.execute(
          """
          UPDATE documents 
          SET 
              content = $1,
              conversion_completed_at = NOW(),
              updated_at = NOW()
          WHERE id = $2
          """,
          content, document_id
      )
      
      # Salvar metadata se houver
      if metadata:
          db.execute(
              """
              UPDATE documents 
              SET metadata = $1
              WHERE id = $2
              """,
              json.dumps(metadata), document_id
          )
  
  def cleanup_temp_files(path: str):
      """Remove temporary files and directories"""
      import shutil
      if os.path.exists(path):
          shutil.rmtree(path)
  ```

**Timeout e Limites:**
- [ ] Timeout total: 10 minutos (hard limit)
- [ ] Soft timeout: 9 minutos (aviso)
- [ ] Tamanho máximo de arquivo: 100 MB
- [ ] Tamanho máximo de imagem extraída: 5 MB

**Logs:**
- [ ] Log de início de conversão: `conversion_started_at`
- [ ] Log de cada etapa (download, conversão, upload)
- [ ] Log de conclusão: `conversion_completed_at`
- [ ] Log de erro detalhado se falhar

**Prioridade:** Crítica  
**Estimativa:** 8 pontos  
**Dependências:** US-3.3.1

---

### US-3.3.3: Atualizar Status do Documento Durante Conversão

**Como** worker,  
**Quero** atualizar status do documento em cada etapa,  
**Para** usuário acompanhar progresso.

#### Critérios de Aceitação

**Funcional:**
- [ ] Status atualizado em cada etapa:
  - **NEW** → Documento criado, aguardando processamento
  - **PROCESSING** → Conversão em andamento
  - **DRAFT** → Conversão concluída com sucesso
  - **ERROR** → Conversão falhou após 3 tentativas
- [ ] Timestamps registrados:
  - `conversion_started_at` - Quando iniciou
  - `conversion_completed_at` - Quando terminou
- [ ] Contador de tentativas incrementado: `conversion_attempts`
- [ ] Erro salvo se falhar: `conversion_error`

**Técnico:**
- [ ] Funções de atualização de status:
  ```python
  def update_document_status(document_id: int, status: str):
      """Update document status and timestamp"""
      db.execute(
          """
          UPDATE documents 
          SET 
              status = $1,
              updated_at = NOW()
          WHERE id = $2
          """,
          status, document_id
      )
      
      logger.info(f"Document {document_id} status updated to {status}")
  
  def increment_conversion_attempts(document_id: int):
      """Increment conversion attempts counter"""
      db.execute(
          """
          UPDATE documents 
          SET conversion_attempts = conversion_attempts + 1
          WHERE id = $1
          """,
          document_id
      )
  
  def update_document_error(document_id: int, error: str):
      """Save conversion error message"""
      db.execute(
          """
          UPDATE documents 
          SET 
              conversion_error = $1,
              updated_at = NOW()
          WHERE id = $2
          """,
          error, document_id
      )
  ```

**Estados Válidos:**
```python
class DocumentStatus(str, Enum):
    NEW = 'new'
    PROCESSING = 'processing'
    DRAFT = 'draft'
    PENDING_APPROVAL = 'pending_approval'
    CHANGES_REQUESTED = 'changes_requested'
    APPROVED = 'approved'
    PUBLISHED = 'published'
    DEPRECATED = 'deprecated'
    ARCHIVED = 'archived'
    ERROR = 'error'
```

**Transições de Status Permitidas (Conversão):**
```
NEW → PROCESSING → DRAFT (sucesso)
NEW → PROCESSING → ERROR (falha)
ERROR → PROCESSING → DRAFT (retry bem-sucedido)
```

**Prioridade:** Alta  
**Estimativa:** 3 pontos  
**Dependências:** US-3.3.2

---

## 3.4 Notificações em Tempo Real (SSE)

### US-3.4.1: Implementar Endpoint SSE para Streaming de Eventos

**Como** desenvolvedor,  
**Quero** implementar endpoint SSE,  
**Para** enviar notificações em tempo real ao frontend.

#### Critérios de Aceitação

**Funcional:**
- [ ] Endpoint SSE disponível: `GET /api/v1/documents/{document_id}/status-stream`
- [ ] Conexão mantida aberta (long-lived HTTP connection)
- [ ] Eventos enviados quando status do documento muda
- [ ] Conexão fechada automaticamente após documento entrar em DRAFT ou ERROR
- [ ] Heartbeat enviado a cada 30 segundos para manter conexão viva
- [ ] Suporte a múltiplos clientes conectados ao mesmo documento

**Técnico - Backend (FastAPI):**
```python
# sse.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

router = APIRouter()

# In-memory storage para canais SSE (produção: usar Redis Pub/Sub)
sse_channels = {}

@router.get("/documents/{document_id}/status-stream")
async def document_status_stream(document_id: int):
    """
    SSE endpoint para streaming de eventos de status do documento
    """
    async def event_generator():
        # Criar canal para este documento se não existir
        if document_id not in sse_channels:
            sse_channels[document_id] = asyncio.Queue()
        
        queue = sse_channels[document_id]
        
        try:
            # Enviar status atual imediatamente
            document = await get_document(document_id)
            yield {
                "event": "status",
                "data": json.dumps({
                    "status": document.status,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
            
            # Loop de eventos
            while True:
                # Heartbeat a cada 30 segundos
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event["type"],
                        "data": json.dumps(event["data"])
                    }
                    
                    # Fechar conexão se status final
                    if event["data"]["status"] in ["draft", "error"]:
                        break
                
                except asyncio.TimeoutError:
                    # Enviar heartbeat
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})
                    }
        
        finally:
            # Cleanup ao fechar conexão
            if document_id in sse_channels:
                del sse_channels[document_id]
    
    return EventSourceResponse(event_generator())


async def emit_sse_event(document_id: int, event_type: str, data: dict):
    """
    Emitir evento SSE para todos os clientes conectados a este documento
    """
    if document_id in sse_channels:
        await sse_channels[document_id].put({
            "type": event_type,
            "data": {
                **data,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
```

**Alternativa: Redis Pub/Sub (Produção):**
```python
# sse_redis.py
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379")

@router.get("/documents/{document_id}/status-stream")
async def document_status_stream(document_id: int):
    async def event_generator():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"document:{document_id}:status")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield {
                        "event": data["event"],
                        "data": json.dumps(data["data"])
                    }
                    
                    if data["data"]["status"] in ["draft", "error"]:
                        break
        finally:
            await pubsub.unsubscribe(f"document:{document_id}:status")
            await pubsub.close()
    
    return EventSourceResponse(event_generator())

async def emit_sse_event(document_id: int, event_type: str, data: dict):
    """Publicar evento via Redis Pub/Sub"""
    await redis_client.publish(
        f"document:{document_id}:status",
        json.dumps({
            "event": event_type,
            "data": {
                **data,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    )
```

**Eventos SSE:**
```
event: status
data: {"status": "processing", "timestamp": "2024-01-17T10:30:00Z"}

event: status_change
data: {"status": "draft", "timestamp": "2024-01-17T10:35:00Z"}

event: status_change
data: {"status": "error", "error": "Unsupported format", "timestamp": "2024-01-17T10:40:00Z"}

event: heartbeat
data: {"timestamp": "2024-01-17T10:30:30Z"}
```

**Dependências:**
```bash
pip install sse-starlette
pip install redis
```

**Prioridade:** Alta  
**Estimativa:** 8 pontos  
**Dependências:** US-3.3.3

---

### US-3.4.2: Conectar Frontend ao SSE e Exibir Progresso

**Como** usuário,  
**Quero** ver progresso da conversão em tempo real,  
**Para** saber quando documento estará pronto.

#### Critérios de Aceitação

**Funcional:**
- [ ] Após upload, modal/página de "Conversão em andamento" é exibido
- [ ] Loading indicator animado (spinner ou barra de progresso indeterminada)
- [ ] Mensagem de status atualizada em tempo real:
  - "Enviando arquivo..." (durante upload)
  - "Convertendo documento..." (status PROCESSING)
  - "Conversão concluída!" (status DRAFT)
  - "Erro na conversão" (status ERROR)
- [ ] Tempo decorrido exibido: "Convertendo há 1m 30s..."
- [ ] Ao concluir com sucesso: redirecionado para editor automaticamente
- [ ] Ao falhar: exibir mensagem de erro com opções:
  - "Tentar novamente" (re-upload)
  - "Deletar documento"

**Técnico - Frontend:**
```javascript
// useSSE.js - React Hook para SSE
import { useEffect, useState } from 'react';

function useDocumentStatus(documentId) {
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const [startTime] = useState(Date.now());
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    const eventSource = new EventSource(
      `/api/v1/documents/${documentId}/status-stream`,
      {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      }
    );

    eventSource.addEventListener('status', (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status);
    });

    eventSource.addEventListener('status_change', (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status);
      
      if (data.status === 'error') {
        setError(data.error);
      }
      
      if (data.status === 'draft' || data.status === 'error') {
        eventSource.close();
      }
    });

    eventSource.addEventListener('heartbeat', (event) => {
      // Apenas para manter conexão viva
      console.log('SSE heartbeat received');
    });

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
      setError('Conexão perdida. Atualize a página para verificar status.');
    };

    // Timer para tempo decorrido
    const timer = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => {
      eventSource.close();
      clearInterval(timer);
    };
  }, [documentId]);

  return { status, error, elapsedTime };
}

// ConversionProgress.jsx
function ConversionProgress({ documentId }) {
  const { status, error, elapsedTime } = useDocumentStatus(documentId);
  const navigate = useNavigate();

  useEffect(() => {
    if (status === 'draft') {
      // Redirecionar para editor após 2 segundos
      setTimeout(() => {
        navigate(`/documents/${documentId}/edit`);
      }, 2000);
    }
  }, [status, documentId, navigate]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="conversion-progress">
      {status === 'processing' && (
        <>
          <Spinner />
          <h3>Convertendo documento...</h3>
          <p>Tempo decorrido: {formatTime(elapsedTime)}</p>
          <p className="text-muted">
            Isso pode levar alguns minutos dependendo do tamanho do arquivo.
          </p>
        </>
      )}

      {status === 'draft' && (
        <>
          <SuccessIcon />
          <h3>Conversão concluída!</h3>
          <p>Redirecionando para o editor...</p>
        </>
      )}

      {status === 'error' && (
        <>
          <ErrorIcon />
          <h3>Erro na conversão</h3>
          <p className="error-message">{error}</p>
          <div className="actions">
            <button onClick={() => handleRetry()}>Tentar novamente</button>
            <button onClick={() => handleDelete()}>Deletar documento</button>
          </div>
        </>
      )}
    </div>
  );
}
```

**UX:**
- [ ] Modal não pode ser fechado durante conversão (ou confirmar se fechar)
- [ ] Loading indicator com animação suave
- [ ] Mensagens de status claras e amigáveis
- [ ] Tempo decorrido atualizado a cada segundo
- [ ] Feedback visual de sucesso (ícone verde, animação)
- [ ] Feedback visual de erro (ícone vermelho, mensagem destacada)
- [ ] Botões de ação claramente visíveis em caso de erro

**Fallback (sem SSE):**
- [ ] Se SSE não for suportado, fazer polling a cada 5 segundos:
  ```javascript
  useEffect(() => {
    const interval = setInterval(async () => {
      const response = await fetch(`/api/v1/documents/${documentId}`);
      const data = await response.json();
      setStatus(data.status);
      
      if (data.status === 'draft' || data.status === 'error') {
        clearInterval(interval);
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [documentId]);
  ```

**Prioridade:** Alta  
**Estimativa:** 8 pontos  
**Dependências:** US-3.4.1

---

## 3.5 Tratamento de Erros e Retry

### US-3.5.1: Implementar Retry Logic com Exponential Backoff

**Como** worker,  
**Quero** tentar reconverter documento automaticamente em caso de falha,  
**Para** aumentar taxa de sucesso de conversões.

#### Critérios de Aceitação

**Funcional:**
- [ ] Worker tenta converter até 3 vezes em caso de falha
- [ ] Intervalo entre tentativas aumenta exponencialmente:
  - Tentativa 1 → 2: espera 1 minuto
  - Tentativa 2 → 3: espera 5 minutos
  - Após tentativa 3: falha definitiva (status ERROR)
- [ ] Cada tentativa é logada com timestamp e erro
- [ ] Contador de tentativas incrementado: `conversion_attempts`
- [ ] Após 3 falhas, documento vai para status ERROR
- [ ] Usuário recebe notificação de erro final

**Técnico:**
- [ ] Retry já implementado em `convert_document` task (US-3.3.1)
- [ ] Configuração de retry:
  ```python
  @celery.task(
      bind=True,
      max_retries=3,
      default_retry_delay=60,  # 1 minuto base
      autoretry_for=(Exception,),
      retry_backoff=True,
      retry_backoff_max=900,  # 15 minutos máximo
      retry_jitter=True  # Adicionar jitter aleatório
  )
  def convert_document(self, document_id: int):
      try:
          # Conversão...
          pass
      except Exception as exc:
          # Calcular delay com exponential backoff
          retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
          
          # Log de retry
          logger.warning(
              f"Conversion failed for document {document_id}, "
              f"retry {self.request.retries + 1}/{self.max_retries} "
              f"in {retry_delay}s"
          )
          
          # Incrementar contador
          increment_conversion_attempts(document_id)
          
          # Retry se ainda há tentativas
          if self.request.retries < self.max_retries:
              raise self.retry(exc=exc, countdown=retry_delay)
          else:
              # Falha final
              logger.error(f"Conversion permanently failed for document {document_id}")
              update_document_status(document_id, 'error')
              update_document_error(document_id, str(exc))
              emit_sse_event(document_id, 'status_change', {
                  'status': 'error',
                  'error': str(exc),
                  'attempts': self.max_retries + 1
              })
              
              # Enviar notificação ao usuário
              notify_conversion_failed(document_id)
              
              raise
  ```

**Logs de Retry:**
```sql
CREATE TABLE conversion_logs (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  attempt INTEGER NOT NULL,
  status VARCHAR(50) NOT NULL,  -- 'started', 'success', 'failed'
  error_message TEXT,
  started_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP,
  duration_seconds INTEGER
);

CREATE INDEX idx_conversion_logs_document ON conversion_logs(document_id);
```

**Função de Log:**
```python
def log_conversion_attempt(
    document_id: int, 
    attempt: int, 
    status: str, 
    error: str = None
):
    """Log conversion attempt"""
    db.execute(
        """
        INSERT INTO conversion_logs 
        (document_id, attempt, status, error_message)
        VALUES ($1, $2, $3, $4)
        """,
        document_id, attempt, status, error
    )
```

**Tipos de Erros e Retry:**
- [ ] Erros temporários (RETRY):
  - Network error ao baixar de S3
  - Docling timeout
  - Memória insuficiente temporária
- [ ] Erros permanentes (NÃO RETRY):
  - Arquivo corrompido (checksum mismatch)
  - Formato realmente não suportado
  - Arquivo protegido por senha
  - Documento vazio

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-3.3.2

---

### US-3.5.2: Tratar Erros Comuns de Conversão

**Como** worker,  
**Quero** identificar e tratar erros comuns,  
**Para** fornecer mensagens claras ao usuário.

#### Critérios de Aceitação

**Funcional:**
- [ ] Erros categorizados por tipo:
  - **Formato não suportado:** "O formato deste arquivo não é suportado"
  - **Arquivo corrompido:** "O arquivo está corrompido ou incompleto"
  - **Arquivo protegido:** "Este arquivo está protegido por senha"
  - **Arquivo muito complexo:** "Este arquivo é muito complexo para converter automaticamente"
  - **Timeout:** "A conversão demorou muito tempo (timeout)"
  - **Erro genérico:** "Erro inesperado durante conversão"
- [ ] Mensagens de erro salvas em `documents.conversion_error`
- [ ] Mensagens traduzidas e amigáveis (não stack traces)
- [ ] Sugestões de ação quando aplicável:
  - "Tente converter o arquivo manualmente para PDF primeiro"
  - "Remova a proteção por senha e tente novamente"

**Técnico:**
```python
# error_handler.py
class ConversionError(Exception):
    """Base class for conversion errors"""
    pass

class UnsupportedFormatError(ConversionError):
    message = "O formato deste arquivo não é suportado. Formatos aceitos: PDF, DOCX, HTML, TXT, MD"

class CorruptedFileError(ConversionError):
    message = "O arquivo está corrompido ou incompleto. Por favor, envie novamente."

class PasswordProtectedError(ConversionError):
    message = "Este arquivo está protegido por senha. Remova a proteção e tente novamente."

class ConversionTimeoutError(ConversionError):
    message = "A conversão demorou muito tempo. Tente com um arquivo menor ou mais simples."

class ComplexDocumentError(ConversionError):
    message = "Este documento é muito complexo para converter automaticamente. Considere criar o documento manualmente."

def handle_conversion_error(exc: Exception) -> str:
    """
    Convert exception to user-friendly error message
    
    Returns:
        User-friendly error message
    """
    error_map = {
        'unsupported': UnsupportedFormatError.message,
        'corrupted': CorruptedFileError.message,
        'password': PasswordProtectedError.message,
        'timeout': ConversionTimeoutError.message,
        'complex': ComplexDocumentError.message,
    }
    
    # Detectar tipo de erro baseado em keywords
    error_str = str(exc).lower()
    
    if 'unsupported' in error_str or 'format' in error_str:
        return error_map['unsupported']
    elif 'corrupt' in error_str or 'invalid' in error_str:
        return error_map['corrupted']
    elif 'password' in error_str or 'encrypted' in error_str:
        return error_map['password']
    elif 'timeout' in error_str:
        return error_map['timeout']
    elif 'complex' in error_str or 'memory' in error_str:
        return error_map['complex']
    else:
        return f"Erro inesperado durante conversão: {str(exc)[:200]}"

# Uso no worker
try:
    result = converter.convert_to_markdown(...)
except Exception as exc:
    user_error = handle_conversion_error(exc)
    update_document_error(document_id, user_error)
    logger.error(f"Conversion error: {str(exc)}")  # Log completo
    raise ConversionError(user_error)
```

**Testes de Erro:**
- [ ] Teste com PDF corrompido
- [ ] Teste com DOCX protegido por senha
- [ ] Teste com arquivo .exe (formato inválido)
- [ ] Teste com PDF de 500 páginas (timeout)
- [ ] Teste com arquivo vazio

**Prioridade:** Média  
**Estimativa:** 5 pontos  
**Dependências:** US-3.5.1

---

### US-3.5.3: Permitir Re-upload Após Falha

**Como** usuário,  
**Quero** poder fazer re-upload do documento após falha,  
**Para** corrigir problema e tentar novamente.

#### Critérios de Aceitação

**Funcional:**
- [ ] Quando documento está em status ERROR, botão "Tentar novamente" disponível
- [ ] Botão abre interface de upload novamente
- [ ] Usuário pode enviar mesmo arquivo (corrigido) ou arquivo diferente
- [ ] Ao fazer re-upload:
  - Documento volta para status NEW
  - Contador de tentativas resetado: `conversion_attempts = 0`
  - Erro anterior limpo: `conversion_error = NULL`
  - Arquivo original substituído no S3
  - Novo job adicionado à fila
- [ ] SSE reconectado automaticamente
- [ ] Interface de progresso exibida novamente

**Técnico:**
- [ ] Endpoint: `POST /api/v1/documents/{document_id}/re-upload`
- [ ] Fluxo:
  ```python
  async def re_upload_document(document_id: int, file: UploadFile):
      # 1. Validar que documento está em ERROR
      document = await get_document(document_id)
      if document.status != 'error':
          raise HTTPException(400, "Apenas documentos com erro podem ser re-enviados")
      
      # 2. Validar arquivo
      valid, errors = validate_upload(file)
      if not valid:
          raise HTTPException(400, errors)
      
      # 3. Deletar arquivo antigo do S3
      if document.original_file_url:
          delete_file_from_s3(document.original_file_url)
      
      # 4. Upload novo arquivo
      s3_url = await upload_file_to_s3(file, document.group_id, document_id)
      
      # 5. Resetar status e erros
      await db.execute(
          """
          UPDATE documents 
          SET 
              status = 'new',
              original_file_url = $1,
              original_file_name = $2,
              original_file_size = $3,
              conversion_attempts = 0,
              conversion_error = NULL,
              conversion_started_at = NULL,
              conversion_completed_at = NULL,
              updated_at = NOW()
          WHERE id = $4
          """,
          s3_url, file.filename, file.size, document_id
      )
      
      # 6. Adicionar novo job na fila
      task_id = convert_document.apply_async(args=[document_id])
      
      # 7. Atualizar para PROCESSING
      await update_document_status(document_id, 'processing')
      
      return {"document_id": document_id, "task_id": task_id}
  ```

**UX:**
- [ ] Botão "Tentar novamente" destacado na tela de erro
- [ ] Texto explicativo: "Você pode enviar o mesmo arquivo após corrigi-lo ou um arquivo diferente"
- [ ] Histórico de tentativas visível (opcional): "Tentativa 1: Erro X, Tentativa 2: ..."
- [ ] Confirmação antes de substituir arquivo: "Isto irá substituir o arquivo anterior. Continuar?"

**Prioridade:** Alta  
**Estimativa:** 5 pontos  
**Dependências:** US-3.5.2

---

## 3.6 Monitoramento e Logs

### US-3.6.1: Dashboard de Monitoramento (Flower)

**Como** admin ou desenvolvedor,  
**Quero** visualizar dashboard de jobs,  
**Para** monitorar conversões e identificar problemas.

#### Critérios de Aceitação

**Funcional:**
- [ ] Flower UI acessível em `http://localhost:5555` (ou porta configurada)
- [ ] Dashboard mostra:
  - Workers ativos
  - Jobs em processamento (por queue)
  - Jobs completados com sucesso
  - Jobs falhados
  - Taxa de sucesso/falha
  - Tempo médio de processamento
  - Gráficos de tendência
- [ ] Possibilidade de:
  - Ver detalhes de job específico
  - Ver logs de job
  - Retrigger job falhado manualmente
  - Ver stack trace de erros
- [ ] Filtros por queue, status, período

**Técnico:**
- [ ] Flower instalado e configurado (já em US-3.1.1)
- [ ] Autenticação habilitada (opcional mas recomendado):
  ```python
  # celery_config.py
  flower_basic_auth = ['admin:password']
  ```
- [ ] Integração com Celery:
  ```bash
  celery -A app.celery flower --port=5555 --basic_auth=admin:${FLOWER_PASSWORD}
  ```

**Métricas Importantes:**
- [ ] Taxa de sucesso de conversão (%)
- [ ] Tempo médio de conversão por formato
- [ ] Jobs na fila (backlog)
- [ ] Workers ociosos vs ocupados
- [ ] Erros mais comuns

**Alertas (Opcional):**
- [ ] Alerta se taxa de falha > 20%
- [ ] Alerta se fila > 50 jobs
- [ ] Alerta se nenhum worker ativo

**Prioridade:** Baixa  
**Estimativa:** 2 pontos (já configurado em US-3.1.1)  
**Dependências:** US-3.1.1

---

### US-3.6.2: Logs Estruturados de Conversão

**Como** desenvolvedor,  
**Quero** logs estruturados de conversões,  
**Para** debugar problemas e analisar performance.

#### Critérios de Aceitação

**Funcional:**
- [ ] Todos os eventos de conversão logados:
  - Início da conversão
  - Download de arquivo do S3
  - Início da conversão Docling
  - Extração de imagens
  - Upload de imagens
  - Salvamento de Markdown
  - Conclusão com sucesso
  - Falha (com stack trace)
- [ ] Logs incluem:
  - Timestamp
  - document_id
  - user_id
  - Etapa (stage)
  - Duração (se aplicável)
  - Tamanho do arquivo
  - Formato do arquivo
  - Número de tentativa
  - Erro (se houver)

**Técnico:**
```python
# logging_config.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_conversion_event(
        self,
        event: str,
        document_id: int,
        user_id: int = None,
        duration: float = None,
        error: str = None,
        **extra
    ):
        """Log conversion event with structured data"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event,
            'document_id': document_id,
            'user_id': user_id,
            'duration_seconds': duration,
            'error': error,
            **extra
        }
        
        if error:
            self.logger.error(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))

# Uso
logger = StructuredLogger('conversion')

# No worker
logger.log_conversion_event(
    'conversion_started',
    document_id=123,
    user_id=45,
    file_size=5242880,
    file_format='pdf'
)

logger.log_conversion_event(
    'conversion_completed',
    document_id=123,
    user_id=45,
    duration=45.3,
    num_images=5,
    markdown_length=15000
)

logger.log_conversion_event(
    'conversion_failed',
    document_id=123,
    user_id=45,
    duration=30.1,
    error='Timeout after 300s',
    attempt=3
)
```

**Formato de Log (JSON):**
```json
{
  "timestamp": "2024-01-17T10:30:00.123Z",
  "event": "conversion_started",
  "document_id": 123,
  "user_id": 45,
  "file_size": 5242880,
  "file_format": "pdf"
}

{
  "timestamp": "2024-01-17T10:30:45.456Z",
  "event": "conversion_completed",
  "document_id": 123,
  "user_id": 45,
  "duration_seconds": 45.3,
  "num_images": 5,
  "markdown_length": 15000
}
```

**Agregação de Logs (ELK Stack - Opcional):**
- [ ] Enviar logs para Elasticsearch
- [ ] Criar dashboards no Kibana:
  - Taxa de sucesso por formato
  - Tempo médio de conversão
  - Erros mais comuns
  - Volume de conversões por hora/dia

**Prioridade:** Baixa  
**Estimativa:** 3 pontos  
**Dependências:** US-3.3.2

---

## 📊 Resumo do Épico 3

### Estatísticas

- **Total de User Stories:** 15
- **Estimativa Total:** 88 pontos
- **Prioridade:** 1 (Crítico para MVP)

### Distribuição de Prioridades

- **Crítica:** 8 histórias (53%)
- **Alta:** 5 histórias (33%)
- **Média:** 1 história (7%)
- **Baixa:** 1 história (7%)

### Distribuição por Seção

1. **Infraestrutura de Conversão:** 3 histórias (18 pontos)
2. **Upload e Validação:** 2 histórias (13 pontos)
3. **Processamento e Conversão:** 3 histórias (19 pontos)
4. **Notificações SSE:** 2 histórias (16 pontos)
5. **Tratamento de Erros:** 3 histórias (15 pontos)
6. **Monitoramento:** 2 histórias (5 pontos)

### Stack Tecnológico

- **Queue:** Celery + RabbitMQ
- **Storage:** S3 / MinIO
- **Conversão:** Docling
- **SSE:** sse-starlette (FastAPI)
- **Cache/Pub-Sub:** Redis
- **Monitoramento:** Flower
- **Logs:** Structured JSON (ELK opcional)

### Dependências Principais

```
US-3.1.1 (Queue)
  └── US-3.1.3 (Docling)
       └── US-3.3.1 (Adicionar Job)
            └── US-3.3.2 (Worker Processa)
                 └── US-3.3.3 (Atualizar Status)
                      └── US-3.4.1 (Endpoint SSE)
                           └── US-3.4.2 (Frontend SSE)

US-3.1.2 (Storage S3)
  └── US-3.2.1 (Upload)
       └── US-3.2.2 (Salvar Original)

US-3.5.1 (Retry Logic)
  └── US-3.5.2 (Tratamento Erros)
       └── US-3.5.3 (Re-upload)
```

### Checklist de Implementação

#### Sprint 11 - Infraestrutura
- [ ] US-3.1.1: Configurar Queue (Celery + RabbitMQ)
- [ ] US-3.1.2: Configurar Storage (S3/MinIO)
- [ ] US-3.1.3: Instalar Docling

#### Sprint 12 - Upload e Conversão Básica
- [ ] US-3.2.1: Upload com Validação
- [ ] US-3.2.2: Salvar Original no S3
- [ ] US-3.3.1: Adicionar Job na Fila
- [ ] US-3.3.2: Worker Processa Conversão

#### Sprint 13 - SSE e Status
- [ ] US-3.3.3: Atualizar Status
- [ ] US-3.4.1: Endpoint SSE
- [ ] US-3.4.2: Frontend conectar SSE

#### Sprint 14 - Retry e Erros
- [ ] US-3.5.1: Retry Logic
- [ ] US-3.5.2: Tratamento de Erros
- [ ] US-3.5.3: Re-upload

#### Sprint 15 - Monitoramento
- [ ] US-3.6.1: Dashboard Flower
- [ ] US-3.6.2: Logs Estruturados

---

## 🎯 Próximos Passos

1. **Validação:** Revisar histórias com time de infra/DevOps
2. **Setup de Ambiente:** Preparar Docker Compose com RabbitMQ, MinIO, Redis
3. **Testes de Docling:** Validar conversão com documentos reais
4. **Desenvolvimento:** Iniciar Sprint 11 com infraestrutura

---

## ⚠️ Considerações Importantes

### Performance
- [ ] Workers escaláveis horizontalmente (adicionar mais containers)
- [ ] Monitorar memória (Docling pode usar bastante RAM)
- [ ] Cache de resultados de conversão (se mesmo arquivo for enviado novamente)

### Segurança
- [ ] Validação rigorosa de formatos (magic numbers, não apenas extensão)
- [ ] Scanning de malware antes de processar (ClamAV?)
- [ ] Rate limiting em uploads
- [ ] Isolamento de workers (containers separados)

### Escalabilidade
- [ ] Fila separada por tipo de arquivo (PDF queue, DOCX queue)
- [ ] Workers especializados por formato
- [ ] Auto-scaling de workers baseado em tamanho da fila

---

**Épico preparado por:** Claude (Anthropic)  
**Revisão:** Pendente  
**Status:** Pronto para Desenvolvimento  
**Próximo Épico:** ÉPICO 4 - Workflow de Aprovação

