import requests
import json

def test_chatbot_api():
    """Test the CarHub chatbot API endpoint"""
    url = "http://127.0.0.1:5000/api/chat"
    
    test_messages = [
        "Hello! Can you tell me about CarHub?",
        "What cars do you sell?",
        "Do you have any sports cars?",
        "Can I schedule a test drive?",
        "What financing options do you offer?"
    ]
    
    print("🚗 Testing CarHub Chatbot API")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: {message}")
        print("-" * 30)
        
        try:
            response = requests.post(url, 
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and data.get('success', False):
                    print(f"✅ Success: {data['message'][:200]}...")
                    if 'metadata' in data:
                        print(f"📊 Intent: {data['metadata'].get('intent', 'unknown')}")
                        if data['metadata'].get('mentioned_cars'):
                            print(f"🚗 Cars mentioned: {', '.join(data['metadata']['mentioned_cars'][:3])}")
                elif 'response' in data:
                    print(f"✅ Success: {data['response'][:200]}...")
                else:
                    print(f"❌ Error in response: {data}")
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 API Testing Complete!")

if __name__ == "__main__":
    test_chatbot_api()
