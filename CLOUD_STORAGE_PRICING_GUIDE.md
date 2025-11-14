# Cloud Storage Pricing Guide

## Where to Find Pricing

### 1. AWS S3
**Official Pricing Page:** https://aws.amazon.com/s3/pricing/
- **Storage:** Per GB/month (varies by storage class)
- **Requests:** PUT/COPY/POST/LIST vs GET/HEAD
- **Data Transfer:** Out to internet

**Key Pricing (US East - as of 2024):**
- Standard Storage: $0.023 per GB/month
- PUT/COPY/POST/LIST: $0.005 per 1,000 requests
- GET/HEAD: $0.0004 per 1,000 requests
- Data Transfer Out: $0.09 per GB (first 10 TB)

### 2. Google Cloud Storage
**Official Pricing Page:** https://cloud.google.com/storage/pricing
- **Storage:** Per GB/month (varies by storage class)
- **Operations:** Class A (writes) vs Class B (reads)
- **Network Egress:** Out to internet

**Key Pricing (US East - as of 2024):**
- Standard Storage: $0.020 per GB/month
- Class A Operations: $0.005 per 1,000 operations
- Class B Operations: $0.0004 per 1,000 operations
- Network Egress: $0.12 per GB (first 1 TB)

### 3. Azure Blob Storage
**Official Pricing Page:** https://azure.microsoft.com/en-us/pricing/details/storage/blobs/
- **Storage:** Per GB/month (varies by access tier)
- **Transactions:** Write vs Read
- **Data Transfer:** Outbound data

**Key Pricing (US East - as of 2024):**
- Hot Tier Storage: $0.018 per GB/month
- Write Transactions: $0.005 per 10,000 transactions
- Read Transactions: $0.0004 per 10,000 transactions
- Data Transfer Out: $0.087 per GB (first 5 GB free)

### 4. Cloudflare R2
**Official Pricing Page:** https://developers.cloudflare.com/r2/pricing/
- **Storage:** Per GB/month
- **Class A Operations:** Writes
- **Class B Operations:** Reads
- **Egress:** Free (no egress fees!)

**Key Pricing (as of 2024):**
- Storage: $0.015 per GB/month
- Class A Operations: $4.50 per million operations
- Class B Operations: $0.36 per million operations
- Egress: FREE (unlimited)

### 5. Backblaze B2
**Official Pricing Page:** https://www.backblaze.com/b2/cloud-storage-pricing.html
- **Storage:** Per GB/month
- **Downloads:** Per GB downloaded
- **Operations:** Per 10,000 operations

**Key Pricing (as of 2024):**
- Storage: $0.005 per GB/month
- Downloads: $0.01 per GB
- Class C Operations: $0.004 per 10,000 operations

## Registry Format

For cloud storage, we need to track:
1. **Storage costs** (per GB/month) - usually tracked separately
2. **API operation costs** (per request/operation)
3. **Data transfer costs** (per GB transferred)

### Format Structure

```json
{
  "aws_s3:put": {
    "per_1k_requests": 0.005
  },
  "aws_s3:get": {
    "per_1k_requests": 0.0004
  },
  "aws_s3:storage": {
    "per_gb_month": 0.023
  },
  "aws_s3:transfer_out": {
    "per_gb": 0.09
  }
}
```

### How to Add to Registry

1. Open `collector/pricing/registry.json`
2. Add entries using the format above
3. Use provider:operation format (e.g., `aws_s3:put`)
4. Use appropriate pricing fields:
   - `per_1k_requests` for request-based pricing
   - `per_gb_month` for storage pricing
   - `per_gb` for data transfer pricing

## Notes

- **Storage costs** are typically monthly, so you'd need to calculate daily costs if tracking daily
- **Request costs** are per-operation (PUT, GET, etc.)
- **Data transfer** is usually per GB outbound
- Prices vary by region - use US East as default unless you track regions
- Some providers have free tiers (e.g., first 5 GB free)



