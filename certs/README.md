# Certificate Setup for Notification Service

## Option 1: Skip mTLS (Recommended for development)

Set in `.env`:

```
SKIP_MTLS=true
NODE_ENV=development
```

## Option 2: Test mTLS locally

1. Generate certificates using the main script:
   ```bash
   cd ../certs
   ./generate-certificates.sh
   ```

2. Copy certificate files to this directory:
   ```bash
   cp ../certs/server-cert.pem ./certs/
   cp ../certs/server-key.pem ./certs/
   cp ../certs/ca-cert.pem ./certs/
   ```

3. Start service with mTLS enabled:
   ```bash
   SKIP_MTLS=false python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --ssl-keyfile certs/server-key.pem --ssl-certfile certs/server-cert.pem
   ```

4. Test with client certificate:
   ```bash
   curl -k --cert ../certs/apim-client-cert.pem --key ../certs/apim-client-key.pem https://localhost:8001/health
   ```

## Production Configuration

For Azure deployment, certificates are handled by Azure App Service. The service will automatically use certificates uploaded to the App Service.

### Required Environment Variables:
- `SKIP_MTLS=false`
- `NODE_ENV=production`

### Azure Configuration:
1. Upload `server-keystore.p12` to App Service TLS/SSL settings
2. Set `WEBSITE_LOAD_CERTIFICATES=*` in Application settings
3. APIM backend configuration with client certificate validation
