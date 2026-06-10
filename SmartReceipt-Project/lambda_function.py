import json
import boto3
import base64
import uuid
from datetime import datetime

# אתחול שירותי AWS
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition') # עכשיו אנחנו בפרנקפורט אז אין צורך לציין אזור
dynamodb = boto3.resource('dynamodb')

# שימו לב: הכניסו כאן את שם הבאקט של התמונות שיצרתם בשלב 2!
BUCKET_NAME = 'smartreceipt-uploads-final-2026'
TABLE_NAME = 'Receipts'

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        image_data = base64.b64decode(body['image'])
        
        receipt_id = str(uuid.uuid4())
        file_name = f"{receipt_id}.jpg"
        
        # שמירת התמונה ב-S3
        s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=image_data, ContentType='image/jpeg')
        
        # ניתוח התמונה מתוך הזיכרון (כדי למנוע בעיות אבטחה בין שירותים)
        rekognition_response = rekognition.detect_text(
            Image={'Bytes': image_data}
        )
        
        detected_text = " ".join([text['DetectedText'] for text in rekognition_response['TextDetections'] if text['Type'] == 'LINE'])
        
        # שמירת הנתונים ב-DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                'ReceiptId': receipt_id,
                'UploadDate': datetime.now().isoformat(),
                'ExtractedText': detected_text,
                'S3ImageUrl': f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_name}"
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Success!', 'receiptId': receipt_id, 'text': detected_text})
        }
        
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}