import json
import requests
import re
from urllib.parse import urlencode
import boto3
from datetime import datetime
from decimal import Decimal

def lambda_handler(event, context):
    API_ENDPOINT = "https://6vrrtorln4.execute-api.us-west-2.amazonaws.com/dev/"
    
    try:
        # Xử lý DynamoDB Stream event
        for record in event['Records']:
            # Chỉ xử lý các records mới được insert
            if record['eventName'] == 'INSERT':
                # Lấy thông tin từ new image
                new_image = record['dynamodb']['NewImage']
                prompt = new_image['TranscriptionText']['S']
                file_name = new_image['FileName']['S']
                timestamp = new_image['Timestamp']['S']
                
                if not prompt:
                    raise ValueError("Empty transcription text")
                
                # Log để debug
                print(f"Processing new transcription: {prompt}")
                
                # Gọi API với prompt
                params = {'prompt': prompt}
                url = f"{API_ENDPOINT}?{urlencode(params)}"

                response = requests.post(url, headers={'Content-Type': 'application/json'})

                if response.status_code == 200:
                    api_response = json.loads(response.text)
                    if 'body' in api_response:
                        body_content = json.loads(api_response['body']) if isinstance(api_response['body'], str) else api_response['body']
                        if 'result' in body_content:
                            # Phân tích kết quả
                            analysis_result = process_response(body_content['result'])
                            
                            try:
                                # Lưu kết quả phân tích
                                save_analysis_result(
                                    file_name=file_name,
                                    timestamp=timestamp,
                                    analysis=analysis_result,
                                    raw_response=body_content['result']
                                )
                                
                                return {
                                    'statusCode': 200,
                                    'body': json.dumps({
                                        'message': 'Analysis completed and saved successfully',
                                        'raw_response': body_content['result'],
                                        'analysis': analysis_result,
                                        'source': {
                                            'fileName': file_name,
                                            'timestamp': timestamp
                                        }
                                    }),
                                    'headers': {
                                        'Content-Type': 'application/json'
                                    }
                                }
                            except Exception as save_error:
                                print(f"Error saving analysis: {str(save_error)}")
                                return error_response(500, f"Analysis completed but failed to save: {str(save_error)}")
                else:
                    raise Exception(f"API returned status code {response.status_code}")
                    
    except Exception as e:
        print(f"Error processing record: {str(e)}")
        return error_response(500, str(e))

def save_analysis_result(file_name, timestamp, analysis, raw_response=None):
    """Lưu kết quả phân tích vào DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('analysis-results')
        
        # Chuẩn bị item để lưu
        item = {
            'FileName': file_name,
            'Timestamp': timestamp,
            'Analysis': {
                'compliance_score': str(analysis.get('compliance_score', 0)),
                'violations': analysis.get('violations', []),
                'recommendations': analysis.get('recommendations', []),
                'detailed_analysis': analysis.get('detailed_analysis', '')
            },
            'AnalysisTimestamp': datetime.now().isoformat()
        }
        
        # Thêm raw response nếu có
        if raw_response:
            item['RawResponse'] = raw_response
            
        # Lưu vào DynamoDB
        response = table.put_item(Item=item)
        
        print(f"Successfully saved analysis result for {file_name}")
        return response
        
    except Exception as e:
        print(f"Error saving analysis result: {str(e)}")
        raise e


def process_response(response_text):
    """Xử lý response text và trích xuất thông tin"""
    try:
        # Tìm và parse phần JSON trong response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            evaluation = json.loads(json_match.group())
            return {
                'compliance_score': str(evaluation.get('compliance_score', 0)),
                'violations': evaluation.get('violations', []),
                'recommendations': evaluation.get('recommendations', []),
                'detailed_analysis': evaluation.get('detailed_analysis', '')
            }
        else:
            # Nếu không tìm thấy JSON, xử lý text
            return {
                'compliance_score': str(extract_score(response_text)),
                'violations': extract_violations(response_text),
                'recommendations': extract_recommendations(response_text),
                'detailed_analysis': extract_analysis(response_text)
            }
    except json.JSONDecodeError:
        return process_text_response(response_text)

def process_text_response(text):
    """Xử lý response dạng text thuần"""
    return {
        'compliance_score': str(extract_score(text)),
        'violations': extract_violations(text),
        'recommendations': extract_recommendations(text),
        'detailed_analysis': extract_analysis(text)
    }


def extract_score(response):
    score_pattern = r'(?i)(?:điểm|score).*?(\d+(?:\.\d+)?)'
    match = re.search(score_pattern, response)
    if match:
        score = Decimal(match.group(1))  # Chuyển trực tiếp sang Decimal
        return str(min(max(score, Decimal('0')), Decimal('10')))  # Giới hạn điểm từ 0-10
    return '0'

def extract_violations(response):
    """Trích xuất các vi phạm"""
    violations = []
    # Tìm đoạn văn bản chứa vi phạm
    violation_section = re.search(r'(?i)vi phạm:(.*?)(?=\n\n|$)', response, re.DOTALL)
    if violation_section:
        # Tách các vi phạm riêng lẻ
        items = re.findall(r'[-•]\s*(.*?)(?=[-•]|\n|$)', violation_section.group(1))
        violations.extend([item.strip() for item in items if item.strip()])
    return violations

def extract_recommendations(response):
    """Trích xuất các đề xuất"""
    recommendations = []
    # Tìm đoạn văn bản chứa đề xuất
    recommendation_section = re.search(r'(?i)đề xuất:(.*?)(?=\n\n|$)', response, re.DOTALL)
    if recommendation_section:
        # Tách các đề xuất riêng lẻ
        items = re.findall(r'[-•]\s*(.*?)(?=[-•]|\n|$)', recommendation_section.group(1))
        recommendations.extend([item.strip() for item in items if item.strip()])
    return recommendations

def extract_analysis(response):
    """Trích xuất phân tích chi tiết"""
    analysis_pattern = r'(?i)phân tích chi tiết:(.*?)(?=\n\n|$)'
    match = re.search(analysis_pattern, response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "Không có phân tích chi tiết"

def error_response(status_code, message):
    """Tạo response lỗi theo format chuẩn"""
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'error': message
        }),
        'headers': {
            'Content-Type': 'application/json'
        }
    }