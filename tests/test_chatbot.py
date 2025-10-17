#!/usr/bin/env python3
"""
CarHub Chatbot Demo Script
Test the chatbot functionality without running the full Flask app
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_connection():
    """Test basic OpenAI API connection"""
    print("🔑 Testing OpenAI API connection...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your-openai-api-key-here':
        print("❌ OpenAI API key not configured in .env file")
        return False
    
    try:
        import openai
        
        # Configure client based on API key type
        if api_key.startswith('sk-or-'):
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "CarHub Chatbot"
                }
            )
            model_name = "openai/gpt-3.5-turbo"
        else:
            client = openai.OpenAI(api_key=api_key)
            model_name = "gpt-3.5-turbo"
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Hello, just testing the connection."}],
            max_tokens=10
        )
        
        print("✅ OpenAI API connection successful!")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        return False

def test_chatbot_knowledge():
    """Test the chatbot's knowledge base"""
    print("\n🧠 Testing CarHub knowledge base...")
    
    try:
        # Import without Flask context
        sys.path.insert(0, '.')
        from chatbot import CarHubChatbot
        
        # Create mock objects for the test
        class MockDB:
            pass
        
        class MockUser:
            pass
        
        class MockCar:
            pass
        
        class MockOrder:
            pass
        
        # Initialize chatbot
        chatbot = CarHubChatbot(MockDB(), MockUser, MockCar, MockOrder)
        
        print("✅ Chatbot initialized successfully")
        print(f"   Company: {chatbot.knowledge_base['company_info']['name']}")
        print(f"   Tagline: {chatbot.knowledge_base['company_info']['tagline']}")
        print(f"   Services: {len(chatbot.knowledge_base['services'])} available")
        print(f"   Inventory: {len(chatbot.knowledge_base['current_inventory'])} cars")
        
        # Test a few knowledge queries
        test_queries = [
            "Tell me about CarHub",
            "What cars do you have?",
            "I want to buy a luxury car"
        ]
        
        print("\n🤖 Testing sample conversations...")
        for query in test_queries:
            print(f"\n   User: {query}")
            response = chatbot.get_chat_response(query)
            if response['success']:
                print(f"   Bot: {response['message'][:100]}...")
            else:
                print(f"   Error: {response.get('message', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge base test failed: {e}")
        return False

def test_car_recommendations():
    """Test personalized car recommendations"""
    print("\n🎯 Testing car recommendation system...")
    
    try:
        from chatbot import CarHubChatbot
        
        class MockDB:
            pass
        
        class MockUser:
            pass
        
        class MockCar:
            pass
        
        class MockOrder:
            pass
        
        chatbot = CarHubChatbot(MockDB(), MockUser, MockCar, MockOrder)
        
        # Test recommendations
        preferences = {
            'budget': '100000',
            'category': 'luxury',
            'usage': 'weekend'
        }
        
        recommendations = chatbot.get_personalized_recommendations(preferences)
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec['car']['name']} - {rec['car']['price']} ({rec['car']['category']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Recommendation test failed: {e}")
        return False

def simulate_conversation():
    """Simulate a full conversation with the chatbot"""
    print("\n💬 Starting interactive demo...")
    print("   Type 'quit' to exit the demo")
    print("   Note: This requires a valid OpenAI API key")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your-openai-api-key-here':
        print("   ⚠️  Skipping interactive demo - OpenAI API key not configured")
        return
    
    try:
        from chatbot import CarHubChatbot
        
        class MockDB:
            pass
        
        class MockUser:
            pass
        
        class MockCar:
            pass
        
        class MockOrder:
            pass
        
        chatbot = CarHubChatbot(MockDB(), MockUser, MockCar, MockOrder)
        conversation_history = []
        
        print("\n🤖 CarHub AI: Hello! I'm your CarHub assistant. How can I help you today?")
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("🤖 CarHub AI: Thank you for chatting with CarHub! Have a great day! 🚗")
                    break
                
                if not user_input:
                    continue
                
                response = chatbot.get_chat_response(user_input, None, conversation_history)
                
                if response['success']:
                    print(f"🤖 CarHub AI: {response['message']}")
                    
                    # Update conversation history
                    conversation_history.extend([
                        {"role": "user", "content": user_input},
                        {"role": "assistant", "content": response['message']}
                    ])
                    
                    # Keep only last 10 messages
                    conversation_history = conversation_history[-10:]
                    
                else:
                    print(f"❌ Error: {response.get('message', 'Unknown error occurred')}")
                
            except KeyboardInterrupt:
                print("\n\n🤖 CarHub AI: Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Chat error: {e}")
                
    except Exception as e:
        print(f"❌ Demo failed to start: {e}")

def main():
    """Main demo function"""
    print("🚗 CarHub AI Chatbot Demo")
    print("=" * 50)
    
    # Test 1: OpenAI Connection
    openai_works = test_openai_connection()
    
    # Test 2: Knowledge Base
    knowledge_works = test_chatbot_knowledge()
    
    # Test 3: Recommendations
    recommendations_work = test_car_recommendations()
    
    # Test 4: Interactive Demo (if OpenAI works)
    if openai_works and knowledge_works:
        simulate_conversation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Demo Results Summary:")
    print(f"   OpenAI Connection: {'✅ Working' if openai_works else '❌ Failed'}")
    print(f"   Knowledge Base: {'✅ Working' if knowledge_works else '❌ Failed'}")
    print(f"   Recommendations: {'✅ Working' if recommendations_work else '❌ Failed'}")
    
    if openai_works and knowledge_works and recommendations_work:
        print("\n🎉 All systems are working! Your chatbot is ready!")
        print("\n📋 Next Steps:")
        print("   1. Start your Flask app: python app.py")
        print("   2. Visit http://localhost:5000")
        print("   3. Look for the chat widget in the bottom-right corner")
        print("   4. Start chatting with your AI assistant!")
    else:
        print("\n⚠️  Some components need attention:")
        if not openai_works:
            print("   • Configure your OpenAI API key in .env file")
        if not knowledge_works:
            print("   • Check chatbot.py for any import errors")
        if not recommendations_work:
            print("   • Verify recommendation system is working")
    
    print("\n💡 Remember:")
    print("   • The chatbot will appear on all pages of your CarHub website")
    print("   • It has comprehensive knowledge about your car inventory")
    print("   • It can help with buying, selling, and service inquiries")
    print("   • Responses are powered by OpenAI's GPT models")

if __name__ == "__main__":
    main()
