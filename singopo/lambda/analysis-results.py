import json
import requests
import re
from urllib.parse import urlencode
import boto3
from datetime import datetime
from decimal import Decimal
import logging

# Cấu hình logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    API_ENDPOINT = "https://dkk8q33lo5.execute-api.us-west-2.amazonaws.com/dev/"
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Xử lý DynamoDB Stream event
        for record in event['Records']:
            logger.info(f"Processing record: {json.dumps(record)}")
            
            # Chỉ xử lý các records mới được insert
            if record['eventName'] == 'INSERT':
                # Lấy thông tin từ new image
                new_image = record['dynamodb']['NewImage']
                contactId = new_image['ContactId']['S']
                call_date = new_image['CallDate']['S']
                phone_number = new_image['PhoneNumber']['S']
                prompt = new_image['TranscriptionText']['S']
                
                logger.info(f"ContactId: {contactId}")
                logger.info(f"Transcription text: {prompt}")
                
                if not prompt:
                    logger.error("Empty transcription text received")
                    raise ValueError("Empty transcription text")
                
                headers = {
                    'Content-Type': 'application/json'
                }
                payload = {
                    "prompt": prompt
                }
                
                logger.info(f"Sending request to API: {API_ENDPOINT}")
                logger.debug(f"Request payload: {json.dumps(payload)}")
                
                response = requests.post(
                    API_ENDPOINT,
                    headers=headers,
                    json=payload
                )
                
                logger.info(f"API Response status code: {response.status_code}")
                logger.info(f"API Response content: {response.text}")
                
                if response.status_code == 200:
                    try:
                        analysis_result = process_response(response.text)
                        logger.info(f"Analysis result: {json.dumps(analysis_result)}")
                        
                        save_result = save_analysis_result(
                            contactId=contactId,
                            call_date=call_date,
                            phone_number=phone_number,
                            analysis=analysis_result,
                            raw_response=response.text
                        )
                        return {
                            'statusCode': 200,
                            'body': json.dumps({
                                'message': 'Analysis completed and saved successfully',
                                'analysis': analysis_result,
                                'contactId': contactId
                            })
                        }
                    except Exception as e:
                        logger.error(f"Error processing response: {str(e)}", exc_info=True)
                        return error_response(500, str(e))
                else:
                    logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    return error_response(response.status_code, f"API request failed: {response.text}")
                    
 
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}", exc_info=True)
        return error_response(500, str(e))

def process_response(response_text):
    try:
        # Parse JSON response 
        response_text = fix_json_string(response_text)
        logger.info(f"Fixed JSON string: {response_text}")
        response_data = json.loads(response_text)
        
        # Lấy và xử lý nội dung result
        result_content = response_data.get('result', '')
        
        # Tìm vị trí bắt đầu của JSON object
        start_idx = result_content.find('{')
        
        if start_idx != -1:
            # Lấy phần JSON và sửa nếu cần
            inner_json = result_content[start_idx:]
            inner_json = fix_inner_json(inner_json)
            
            logger.info(f"Inner JSON after fixing: {inner_json}")
            analysis_data = json.loads(inner_json)
            
            # Extract thông tin
            analysis_result = {
                'summary': result_content[:start_idx].strip(),
                'compliance_score': analysis_data.get('compliance_score', 0),
                'violations': analysis_data.get('violations', []),
                'recommendations': analysis_data.get('recommendations', []),
                'detailed_analysis': analysis_data.get('detailed_analysis', ''),
                "customer_emotion": analysis_data.get('customer_emotion', 'trung tính'),
                "emotion_details": analysis_data.get('emotion_details', ''),
            }
            
            return analysis_result
        else:
            raise Exception("Could not find valid JSON data in response")
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.error(f"Problematic text: {response_text}")
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        raise

def fix_inner_json(json_str):
    """Sửa JSON string bên trong"""
    try:
        # Nếu JSON đã hợp lệ, return luôn
        if is_valid_json(json_str):
            return json_str
            
        # Đếm số dấu { và }
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        
        # Nếu thiếu dấu đóng
        if open_braces > close_braces:
            # Kiểm tra xem có phải thiếu .\"\n}" không
            if json_str.rstrip().endswith('"'):
                json_str = json_str.rstrip() + '.\"\n}'
                logger.info("Added .\"\\n} to the end")
            else:
                # Thêm số lượng } còn thiếu
                json_str = json_str + ('}' * (open_braces - close_braces))
                logger.info(f"Added {open_braces - close_braces} closing braces")
                
        # Thử sửa một số trường hợp cụ thể
        if not is_valid_json(json_str):
            # Nếu kết thúc bằng dấu " mà chưa có }
            if json_str.rstrip().endswith('"'):
                json_str = json_str.rstrip() + '}'
                logger.info("Added closing brace after quote")
                
            # Nếu thiếu dấu " trước }
            elif json_str.rstrip().endswith('}'):
                json_str = json_str.rstrip()[:-1] + '"}'
                logger.info("Added quote before closing brace")
        
        return json_str
        
    except Exception as e:
        logger.error(f"Error fixing inner JSON: {str(e)}")
        return json_str

def fix_json_string(json_str):
    """Sửa JSON string không hợp lệ"""
    try:
        # Nếu JSON đã hợp lệ, return luôn
        if is_valid_json(json_str):
            return json_str
            
        # Đếm số dấu { và }
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        
        # Nếu thiếu dấu }, thêm vào
        if open_braces > close_braces:
            missing_braces = open_braces - close_braces
            json_str = json_str + ('"}' * missing_braces)
            logger.warning(f"Fixed JSON by adding {missing_braces} closing quote and brace(s)")
        
        # Loại bỏ các ký tự không hợp lệ ở cuối
        json_str = json_str.strip()
        
        # Nếu vẫn không hợp lệ, thử thêm "} vào cuối
        if not is_valid_json(json_str):
            test_str = json_str + '"}'
            if is_valid_json(test_str):
                json_str = test_str
                logger.warning("Fixed JSON by adding closing quote and brace at the end")
                
        return json_str
        
    except Exception as e:
        logger.error(f"Error fixing JSON string: {str(e)}")
        return json_str

def is_valid_json(json_str):
    """Kiểm tra JSON có hợp lệ không"""
    try:
        json.loads(json_str)
        return True
    except:
        return False


def save_analysis_result(contactId, call_date, phone_number, analysis, raw_response=None):
    """Lưu kết quả phân tích vào DynamoDB"""
    logger.info(f"Starting save_analysis_result for contactId: {contactId}")
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('analysis-results-it-got-talent')
        
        # Chuẩn bị item để lưu
        item = {
            'ContactId': contactId,
            'CallDate': call_date,
            'PhoneNumber': phone_number,
            'Analysis': {
                'compliance_score': str(analysis.get('compliance_score', 0)),
                'violations': analysis.get('violations', []),
                'recommendations': analysis.get('recommendations', []),
                'detailed_analysis': analysis.get('detailed_analysis', ''),
                "customer_emotion": analysis.get('customer_emotion', 'trung tính'),
                "emotion_details": analysis.get('emotion_details', ''),
            },
            'AnalysisTimestamp': datetime.now().isoformat()
        }
        
        if raw_response:
            item['RawResponse'] = raw_response
            
        logger.info(f"Prepared DynamoDB item: {json.dumps(item)}")
        
        # Lưu vào DynamoDB
        response = table.put_item(Item=item)
        
        logger.info(f"DynamoDB put_item response: {json.dumps(response)}")
        return response
        
    except Exception as e:
        logger.error(f"Error in save_analysis_result: {str(e)}", exc_info=True)
        raise

def error_response(status_code, message):
    """Tạo response lỗi theo format chuẩn"""
    error_body = {
        'error': message
    }
    logger.error(f"Returning error response: {json.dumps(error_body)}")
    return {
        'statusCode': status_code,
        'body': json.dumps(error_body),
        'headers': {
            'Content-Type': 'application/json'
        }
    }