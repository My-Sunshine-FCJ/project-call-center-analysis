import json
import boto3
import datetime
import uuid
import time
import re
import urllib.parse

def lambda_handler(event, context):
    print(json.dumps(event))
    
    # Khởi tạo client S3, Transcribe và DynamoDB
    s3 = boto3.client('s3')
    transcribe = boto3.client('transcribe')
    dynamodb = boto3.resource('dynamodb')
    
    table = dynamodb.Table('data-transribe')  # Tên bảng DynamoDB
    
    # Lấy thông tin từ sự kiện S3
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']
    file_key = urllib.parse.unquote_plus(file_key)


    # Lấy thời gian từ tên file hoặc hiện tại
    today = datetime.datetime.now()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    day = today.strftime('%d')
    
    # Tạo đường dẫn S3 cho file âm thanh
    media_uri = f's3://{bucket_name}/{file_key}'
    
    # Tạo tên job cho Transcribe (xử lý ký tự không hợp lệ)
    file_name = file_key.split('/')[-1]  # Lấy tên file từ đường dẫn
    sanitized_file_name = file_name.replace('.', '_').replace(':', '_').replace('%', '_')  # Thay thế ký tự không hợp lệ
    
    job_name = f"{sanitized_file_name}_{uuid.uuid4()}"
    
    # Tạo outputKey (xử lý ký tự không hợp lệ)
    output_key = f"connect/ai-call-analysis/CallRecordings/{year}/{month}/{day}/transcribed/{job_name}.json"
    
    try:
        # Gọi Amazon Transcribe
        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_uri},
            MediaFormat='wav',  # Thay đổi nếu định dạng khác
            LanguageCode='vi-VN',  # Thay đổi nếu cần
            OutputBucketName=bucket_name,
            OutputKey=output_key
        )
        
        print(json.dumps(response, default=str))
        
        # Lấy TranscriptionJobName để theo dõi tiến trình
        transcription_job_name = response['TranscriptionJob']['TranscriptionJobName']
        
        # Chờ job hoàn tất và lấy kết quả
        status = "IN_PROGRESS"
        while status == "IN_PROGRESS":
            time.sleep(5)  # Đợi 5 giây trước khi kiểm tra lại
            result = transcribe.get_transcription_job(TranscriptionJobName=transcription_job_name)
            status = result['TranscriptionJob']['TranscriptionJobStatus']
            if status == "FAILED":
                raise Exception(f"Transcription job failed: {result}")
        
        if status == "COMPLETED":
            transcription_url = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
            
            # Tải nội dung JSON từ Transcribe URL
            transcribed_response = boto3.client('s3').get_object(
                Bucket=bucket_name,
                Key=output_key
            )['Body'].read().decode('utf-8')
            transcript_text = json.loads(transcribed_response)['results']['transcripts'][0]['transcript']
            
            # Lưu nội dung vào DynamoDB
            table.put_item(
                Item={
                    'FileName': file_name,  # Partition Key
                    'JobName': job_name,
                    'TranscriptionText': transcript_text,
                    'Timestamp': today.isoformat()
                }
            )
        
        return {
            'TranscriptionJobName': transcription_job_name,
            'TranscriptionURL': transcription_url
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'error': str(e)
        }
