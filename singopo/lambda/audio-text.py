import json
import boto3
import datetime
import uuid
import time
import urllib.parse

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    transcribe = boto3.client('transcribe')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('customer-call-analysis')
    
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    
    if not file_key.lower().endswith('.wav') or 'transcribed' in file_key:
        return {'statusCode': 200, 'body': 'Skipped file'}

    file_name = file_key.split('/')[-1]
    contact_id = file_name.split('_')[0]
    job_name = f"transcribe_{str(uuid.uuid4())[:8]}"
    
    try:
        # Update trạng thái processing
        table.update_item(
            Key={'ContactId': contact_id},
            UpdateExpression="set TranscriptionStatus = :s",
            ExpressionAttributeValues={
                ':s': 'PROCESSING'
            }
        )
        
        # Bắt đầu transcription
        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{bucket_name}/{file_key}'},
            MediaFormat='wav',
            LanguageCode='vi-VN',
            OutputBucketName=bucket_name,  # Thêm bucket đích
            OutputKey=f"transcribed/{job_name}.json",  # Thêm key đích
            Settings={'ShowSpeakerLabels': False}
        )
        
        # Chờ transcription hoàn thành
        max_attempts = 60
        attempts = 0
        
        while attempts < max_attempts:
            status = transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Đọc file kết quả từ S3
                output_key = f"transcribed/{job_name}.json"
                response = s3.get_object(Bucket=bucket_name, Key=output_key)
                transcript_data = json.loads(response['Body'].read().decode('utf-8'))
                transcript_text = transcript_data['results']['transcripts'][0]['transcript']
                
                # Cập nhật DynamoDB với kết quả transcription
                table.update_item(
                    Key={'ContactId': contact_id},
                    UpdateExpression="set TranscriptionText = :t, TranscriptionStatus = :s, TranscriptionTimestamp = :ts",
                    ExpressionAttributeValues={
                        ':t': transcript_text,
                        ':s': 'COMPLETED',
                        ':ts': datetime.datetime.now().isoformat()
                    }
                )
                
                return {
                    'statusCode': 200,
                    'body': 'Successfully processed recording',
                    'contactId': contact_id,
                    'transcriptionText': transcript_text
                }
                
            elif status == 'FAILED':
                raise Exception(f'Transcription job {job_name} failed')
            
            attempts += 1
            time.sleep(5)
            
        raise Exception(f'Transcription job {job_name} timed out')
            
    except Exception as e:
        # Cập nhật lỗi trong DynamoDB
        table.update_item(
            Key={'ContactId': contact_id},
            UpdateExpression="set TranscriptionStatus = :s, TranscriptionError = :e, LastUpdatedAt = :t",
            ExpressionAttributeValues={
                ':s': 'FAILED',
                ':e': str(e),
                ':t': datetime.datetime.now().isoformat()
            }
        )
        
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'contactId': contact_id,
                'jobName': job_name
            }
        }