# Upload USER_DATA.csv to AWS Athena

## Prerequisites

- AWS CLI configured with credentials
- S3 bucket for data storage
- Athena workgroup configured

## Steps

### 1. Upload CSV to S3

```bash
# Create S3 bucket (if not exists)
aws s3 mb s3://sentra-user-data-bucket --region ap-south-1

# Upload USER_DATA.csv
aws s3 cp BackendAPI/USER_DATA.csv s3://sentra-user-data-bucket/user_data/ --region ap-south-1
```

### 2. Create Database in Athena

```sql
CREATE DATABASE IF NOT EXISTS user_data;
```

### 3. Create Table in Athena

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS user_data.user_data (
    self_email STRING,
    reportee_email STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://sentra-user-data-bucket/user_data/'
TBLPROPERTIES (
    'skip.header.line.count'='1',
    'serialization.null.format'=''
);
```

### 4. Verify Table

```sql
-- Check table structure
DESCRIBE user_data.user_data;

-- View all data
SELECT * FROM user_data.user_data;

-- Test hierarchy query
SELECT reportee_email 
FROM user_data.user_data 
WHERE self_email = 'super.admin@sentra.com';
```

Expected output:
```
reportee_email
--------------------------
super.admin@sentra.com
kamaljeet.singh@sentra.com
vishal.saxena@sentra.com
harsh.kumar@sentra.com
```

### 5. Test Security Filter

```sql
-- Test query that will be used by security filter
SELECT email
FROM insurance_db.insurance_data
WHERE email IN (
    SELECT reportee_email
    FROM user_data.user_data
    WHERE self_email = 'harsh.kumar@sentra.com'
);
```

## Alternative: Using AWS Console

### Step 1: Upload to S3
1. Go to S3 Console
2. Create bucket: `sentra-user-data-bucket`
3. Create folder: `user_data/`
4. Upload `USER_DATA.csv`

### Step 2: Create Table in Athena
1. Go to Athena Console
2. Select Query Editor
3. Run the CREATE DATABASE and CREATE TABLE queries above

### Step 3: Verify
1. Run `SELECT * FROM user_data.user_data`
2. Verify 10 rows returned
3. Check hierarchy relationships

## Troubleshooting

### Issue: Table shows no data
**Solution**: Check S3 path in LOCATION matches upload location

### Issue: Headers appear as data row
**Solution**: Verify `'skip.header.line.count'='1'` in TBLPROPERTIES

### Issue: Columns not parsed correctly
**Solution**: Verify CSV uses comma delimiter (not semicolon or tab)

### Issue: Permission denied
**Solution**: Ensure IAM role has S3 read permissions for the bucket

## Verification Queries

```sql
-- Count total rows (should be 10)
SELECT COUNT(*) FROM user_data.user_data;

-- Count unique users (should be 4)
SELECT COUNT(DISTINCT self_email) FROM user_data.user_data;

-- Show hierarchy for each user
SELECT 
    self_email,
    COUNT(reportee_email) as reportee_count
FROM user_data.user_data
GROUP BY self_email
ORDER BY reportee_count DESC;
```

Expected output:
```
self_email                    reportee_count
--------------------------------------------
super.admin@sentra.com        4
kamaljeet.singh@sentra.com    3
vishal.saxena@sentra.com      2
harsh.kumar@sentra.com        1
```

## Update User Hierarchy

To add/modify users:

1. Edit `BackendAPI/USER_DATA.csv`
2. Re-upload to S3 (overwrites existing)
3. Athena automatically picks up changes (no table recreation needed)

Example: Add new manager
```csv
self_email,reportee_email
new.manager@sentra.com,new.manager@sentra.com
new.manager@sentra.com,agent1@sentra.com
new.manager@sentra.com,agent2@sentra.com
```

## Security Notes

- ✅ Table is read-only (EXTERNAL TABLE)
- ✅ Data stored in S3 with encryption
- ✅ Access controlled via IAM policies
- ✅ Athena queries logged in CloudTrail
- ⚠️ Ensure S3 bucket is not public

## Cost Estimation

- **S3 Storage**: ~$0.023/GB/month (USER_DATA.csv is <1KB)
- **Athena Queries**: $5/TB scanned (each security subquery scans <1KB)
- **Total Monthly Cost**: <$0.01 for typical usage

## Next Steps

After table creation:
1. Test security filter with different users
2. Verify insurance_data has email column populated
3. Update frontend to send user_email
4. Monitor query logs for security filter application
