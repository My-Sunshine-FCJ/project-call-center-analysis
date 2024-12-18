import json
import boto3
import re

def truncate_text(text, max_length=4000):
    """Cắt ngắn văn bản nếu quá dài"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

def clean_conversation(text):
    """Làm sạch và rút gọn cuộc hội thoại"""
    # Loại bỏ các ký tự đặc biệt và khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text)
    # Chỉ giữ lại các đoạn hội thoại chính
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def get_compliance_rules():
    """Trả về quy định giao tiếp với khách hàng"""
    return """
    Quy định giao tiếp với khách hàng ngân hàng:
    1. Chào hỏi và xưng danh
       - Chào đúng thời điểm + xưng tên/vị trí
       - Thái độ lịch sự, tôn trọng
    2. Thái độ phục vụ
       - Giọng nói thân thiện, kiên nhẫn
       - Lắng nghe, không cáu gắt
    3. Quy trình xử lý
       - Xác thực khách hàng
       - Tuân thủ quy trình bảo mật
       - Không yêu cầu thông tin nhạy cảm
    4. Giải quyết vấn đề  
       - Nắm bắt nhu cầu chính xác
       - Đưa giải pháp phù hợp
       - Cam kết thời gian xử lý   
    5. Kết thúc cuộc gọi
       - Tóm tắt nội dung chính
       - Hỏi nhu cầu hỗ trợ thêm
       - Cảm ơn và chào tạm biệt
    6. Bảo mật thông tin
       - Không tiết lộ thông tin nội bộ
       - Bảo vệ thông tin khách hàng
    """

def create_analysis_prompt(conversation):
    """Tạo prompt cho việc phân tích cuộc hội thoại"""
    rules = get_compliance_rules()
    return f"""
    Analyze the following conversation based on these banking customer service guidelines:

    Conversation:
    {conversation}
    
    Provide analysis in the following JSON format ONLY:
    {{
        "compliance_score": <score from 1-10>,
        "violations": [<list of specific violations>],
        "recommendations": [<list of specific improvements>],
        "detailed_analysis": "<brief analysis>",
        "customer_emotion": "<Tích cực/Trung tính/Tiêu cực>",
        "emotion_details": "<brief emotion analysis>"
    }}
    
    Requirements:
    - compliance_score must be a number between 1 and 10
    - All fields must be present
    - Response must be valid JSON, chú ý'{{', '}}'
    - Keep analysis concise and specific
    - Focus on compliance with banking regulations
    """

def fix_json_response(response_text):
    """
    Kiểm tra và thêm dấu } nếu thiếu ở cuối JSON response
    """
    # Loại bỏ khoảng trắng ở đầu và cuối
    response_text = response_text.strip()
    
    # Đếm số dấu { và }
    open_braces = response_text.count('{')
    close_braces = response_text.count('}')
    
    # Nếu thiếu dấu }, thêm vào
    if open_braces > close_braces:
        missing_braces = open_braces - close_braces
        response_text += '}' * missing_braces
    
    return response_text

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    client_bedrock_knowledgebase = boto3.client(
        'bedrock-agent-runtime',
        region_name='us-west-2'
    )
    
    try:
        # Xử lý input
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        user_prompt = body.get('prompt')
        
        if not user_prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No prompt provided in request body'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }

        # Log input để debug
        print(f"Original prompt: {user_prompt}")

        # Làm sạch và rút gọn input
        cleaned_prompt = clean_conversation(user_prompt)
        truncated_prompt = truncate_text(cleaned_prompt)
        
        # Tạo prompt phân tích
        analysis_prompt = create_analysis_prompt(truncated_prompt)
        
        # Log prompt đã xử lý để debug
        print(f"Processed prompt: {analysis_prompt}")

        # Gọi Bedrock API
        response = client_bedrock_knowledgebase.retrieve_and_generate(
            input={
                'text': analysis_prompt
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': 'XB9EB0ZA2G',
                    'modelArn': 'arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
                }
            }
        )
        
        # Lấy và log response để debug
        response_text = response['output']['text']
        # Fix JSON response nếu thiếu dấu }
        response_text = fix_json_response(response_text)
        print(f"Fixed API response: {response_text}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'result': response_text
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except ValueError as ve:
        print("Validation error:", str(ve))  # Debug log
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': str(ve)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    except Exception as e:
        print("Error:", str(e))  # Debug log
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
