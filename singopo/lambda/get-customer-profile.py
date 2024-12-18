import json
import boto3
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('customer-call-analysis')

def format_phone_number(phone):
    """
    Chuẩn hóa số điện thoại về format +84
    """
    # Loại bỏ tất cả các ký tự không phải số
    phone = ''.join(filter(str.isdigit, phone))
    
    # Nếu số điện thoại bắt đầu bằng 0, thay thế bằng +84
    if phone.startswith('0'):
        phone = '+84' + phone[1:]
    # Nếu số điện thoại chưa có +84 và không bắt đầu bằng 84
    elif not phone.startswith('84'):
        phone = '+84' + phone
    # Nếu số điện thoại bắt đầu bằng 84 nhưng không có dấu +
    elif phone.startswith('84'):
        phone = '+' + phone
    
    return phone

def lambda_handler(event, context):
    logger.info(f"Incoming event: {json.dumps(event, indent=2)}")
    
    try:
        # Lấy và chuẩn hóa số điện thoại
        raw_phone = event['Details']['ContactData']['CustomerEndpoint']['Address']
        phone_number = format_phone_number(raw_phone)
        
        contact_id = event['Details']['ContactData']['ContactId']
        timestamp = int(datetime.now().timestamp() * 1000)
        call_date = datetime.now().isoformat()
        
        # Log số điện thoại trước và sau khi format
        logger.info(f"Original phone number: {raw_phone}")
        logger.info(f"Formatted phone number: {phone_number}")
        
        # Tạo item để lưu vào DynamoDB
        item = {
            'ContactId': contact_id,
            'PhoneNumber': phone_number,  # Số điện thoại đã được chuẩn hóa
            'OriginalPhoneNumber': raw_phone,  # Lưu cả số gốc để tham khảo
            'Timestamp': timestamp,
            'CallDate': call_date,
            'Channel': 'voice',
            'QueueInfo': event['Details']['ContactData'].get('Queue', 'No Queue'),
            'TranscriptionStatus': 'PENDING',
            'ProcessingStatus': 'INITIATED'
        }
        
        # Lưu vào DynamoDB
        table.put_item(Item=item)
        logger.info(f"Successfully saved to DynamoDB with formatted phone: {phone_number}")
        
        return {
            'phoneNumber': phone_number,
            'contactId': contact_id,
            'timestamp': str(timestamp)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'error': str(e)
        }