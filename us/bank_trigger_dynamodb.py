import json
import boto3
import re

def lambda_handler(event, context):
    client_bedrock_knowledgebase = boto3.client(
        'bedrock-agent-runtime',
        region_name='us-west-2'
    )
    
    try:
        print("Input event:", event)
        
        # Kiểm tra và lấy prompt từ event
        if 'prompt' not in event:
            raise ValueError("No prompt found in event")

        user_prompt = event.get('prompt')
        if not user_prompt:
            raise ValueError("No prompt provided in request body")

        print("User prompt:", user_prompt)  # Debug log

        compliance_context = """

        Quy định giao tiếp với khách hàng của ngân hàng:
        1. Chào hỏi và xưng danh:
           - Chào khách hàng đúng thời điểm (sáng/chiều)
           - Xưng danh rõ ràng tên và vị trí công tác
           
        2. Thái độ phục vụ:
           - Giọng nói niềm nở, thân thiện
           - Kiên nhẫn lắng nghe khách hàng
           - Không được cáu gắt hoặc tỏ thái độ thiếu chuyên nghiệp
        
        3. Quy trình xử lý:
           - Xác thực thông tin khách hàng theo quy định
           - Tuân thủ quy trình bảo mật thông tin
           - Không được yêu cầu thông tin nhạy cảm qua điện thoại
        
        4. Giải quyết vấn đề:
           - Nắm bắt chính xác nhu cầu khách hàng
           - Đưa ra giải pháp phù hợp và đầy đủ
           - Cam kết thời gian xử lý rõ ràng
        
        5. Kết thúc cuộc gọi:
           - Tóm tắt lại các nội dung đã trao đổi
           - Hỏi khách hàng có cần hỗ trợ gì thêm không
           - Cảm ơn và chào tạm biệt

        6. Quy định về bảo mật:
           - Không được tiết lộ thông tin nội bộ
           - Tuân thủ quy trình xác thực khách hàng
           - Bảo vệ thông tin cá nhân của khách hàng
        """

        rule = f"""
        Hãy phân tích ra cho tôi
        Dựa trên các quy định sau:
        {compliance_context}
        Hãy phân tích cuộc hội thoại dưới đây và trả về kết quả theo format JSON:
        {{
            "compliance_score": <điểm đánh giá 1-10>,
            "violations": [<danh sách các vi phạm>],
            "recommendations": [<danh sách đề xuất cải thiện>],
            "detailed_analysis": "<phân tích chi tiết>"
        }}
        Chú ý định dạng theo format JSON bên trên chính xác
        """

        # Combine prompt with rule
        full_prompt = f"{user_prompt}\n{rule}"
        print("Full prompt:", full_prompt)  # Debug log

        response = client_bedrock_knowledgebase.retrieve_and_generate(
            input={
                'text': full_prompt
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': 'WFMYLBQZWL',
                    'modelArn': 'arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
                }
            }
        )
        
        response_text = response['output']['text']
        print("Response text:", response_text)  # Debug log
        
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