"""
CarHub AI Chatbot
Powered by OpenAI GPT with comprehensive CarHub business knowledge
"""

import openai
import os
import json
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CarHubChatbot:
    def __init__(self, db, User, Car, Order):
        """Initialize the ChatBot with OpenAI API key and CarHub knowledge base"""
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        print(f"🔑 API Key found: {api_key[:20] + '...' if api_key and len(api_key) > 20 else 'None'}")
        
        if api_key and api_key != 'your-openai-api-key-here' and len(api_key) > 20:
            try:
                # Set the API key as environment variable
                os.environ['OPENAI_API_KEY'] = api_key
                
                # Check if this is an OpenRouter API key
                if api_key.startswith('sk-or-'):
                    print("🔗 Detected OpenRouter API key - configuring for OpenRouter")
                    self.client = openai.OpenAI(
                        api_key=api_key,
                        base_url="https://openrouter.ai/api/v1",
                        default_headers={
                            "HTTP-Referer": "http://localhost:5000",  # Your site URL
                            "X-Title": "CarHub Chatbot"  # Your app name
                        }
                    )
                else:
                    print("🔗 Detected OpenAI API key - configuring for OpenAI")
                    self.client = openai.OpenAI()
                
                self.openai_available = True
                print("✅ OpenAI client initialized successfully!")
            except Exception as e:
                print(f"❌ Error initializing OpenAI client: {e}")
                self.client = None
                self.openai_available = False
        else:
            self.client = None
            self.openai_available = False
            print("⚠️  OpenAI API key not configured - chatbot will use fallback responses")
        
        self.db = db
        self.User = User
        self.Car = Car
        self.Order = Order
        
        # CarHub Knowledge Base
        self.knowledge_base = {
            "company_info": {
                "name": "CarHub",
                "tagline": "Where Every Journey Begins - Discover, Acquire, Excel",
                "description": "Your premium automotive destination offering curated selection of new and pre-owned vehicles",
                "founded": "2024",
                "mission": "To provide exceptional automotive experiences with unbeatable prices and unmatched quality",
                "vision": "To be the future of automotive retail with innovative technology and customer-first approach"
            },
            
            "services": {
                "car_buying": {
                    "description": "Premium selection of new and pre-owned vehicles",
                    "features": ["3D Model Viewing", "Virtual Car Tours", "Expert Consultation", "Financing Options"],
                    "process": ["Browse Inventory", "Virtual/Physical Inspection", "Test Drive", "Financing", "Purchase"]
                },
                "car_selling": {
                    "description": "Seamless selling with maximized value and best market prices",
                    "features": ["Free Valuation", "Quick Process", "Best Market Prices", "Smooth Transactions"],
                    "process": ["Get Quote", "Vehicle Inspection", "Price Negotiation", "Documentation", "Payment"]
                },
                "car_servicing": {
                    "description": "Precision service for peak performance with certified technicians",
                    "features": ["Certified Technicians", "State-of-art Equipment", "Maintenance", "Repairs"],
                    "services": ["Oil Changes", "Brake Service", "Engine Diagnostics", "Tire Service", "General Maintenance"]
                },
                "vintage_cars": {
                    "description": "Exquisite collection of vintage automobiles - timeless beauty and rare finds",
                    "features": ["Museum-grade Restoration", "Historical Documentation", "Expert Authentication"],
                    "specialties": ["Classic Cars", "Vintage Restoration", "Rare Collectibles", "Historical Vehicles"]
                }
            },
            
            "car_categories": {
                "luxury": ["Lamborghini", "Ferrari", "Rolls Royce", "Bentley", "Aston Martin", "McLaren"],
                "sports": ["Porsche", "BMW M Series", "Mercedes AMG", "Bugatti"],  
                "electric": ["Tesla", "Hyundai Ioniq", "Mercedes EQS"],
                "classic": ["Vintage Rolls Royce", "Classic Ferrari", "Vintage Lamborghini"],
                "family": ["BMW", "Mercedes", "Hyundai", "Maruti Suzuki"],
                "off_road": ["Jeep Wrangler", "Mahindra Scorpio"]
            },
            
            "current_inventory": [
                {"name": "Lamborghini Revuelto", "price": "$600,000", "category": "luxury", "status": "available"},
                {"name": "Tesla Model 3", "price": "$45,000", "category": "electric", "status": "available"},
                {"name": "BMW M2 G87", "price": "$65,000", "category": "sports", "status": "available"},
                {"name": "Rolls Royce Ghost", "price": "$400,000", "category": "luxury", "status": "available"},
                {"name": "Ferrari 296 GTB", "price": "$320,000", "category": "sports", "status": "available"},
                {"name": "Porsche 718 Cayman GTS", "price": "$85,000", "category": "sports", "status": "available"},
                {"name": "Bugatti Centodieci", "price": "$9,000,000", "category": "luxury", "status": "limited"},
                {"name": "Hyundai Ioniq 5N", "price": "$55,000", "category": "electric", "status": "available"},
                {"name": "Bentley Mulliner Batur", "price": "$2,000,000", "category": "luxury", "status": "limited"},
                {"name": "Aston Martin V8 Vantage", "price": "$150,000", "category": "luxury", "status": "available"}
            ],
            
            "features": {
                "technology": [
                    "3D Model Viewing - Examine every detail before visiting",
                    "Virtual Car Tours - Immersive vehicle exploration",
                    "AI-Powered Search - Find your perfect match",
                    "Digital Documentation - Paperless transactions",
                    "Online Financing - Quick approval process"
                ],
                "customer_service": [
                    "24/7 Customer Support",
                    "Expert Consultation",
                    "Personalized Service",
                    "Flexible Payment Options",
                    "After-sales Support"
                ],
                "quality_assurance": [
                    "Rigorous Inspection Process",
                    "Certified Pre-owned Program",
                    "Warranty Coverage",
                    "Quality Guarantee",
                    "Transparent History Reports"
                ]
            },
            
            "customer_reviews": {
                "rating": "4.9/5",
                "total_customers": "2,500+",
                "satisfaction_rate": "98%",
                "testimonials": [
                    {"customer": "Sarah Johnson", "car": "Tesla Model 3", "review": "Exceptional service and quality vehicles. Seamless experience!"},
                    {"customer": "Michael Chen", "car": "Lamborghini Revuelto", "review": "3D model viewing is incredible! Outstanding customer service."},
                    {"customer": "Emily Rodriguez", "car": "BMW M2", "review": "Professional, transparent, and trustworthy. Smooth process."}
                ]
            },
            
            "contact_info": {
                "website": "localhost:5000",
                "support": "Available through website chat",
                "hours": "24/7 Online Support, Showroom: 9 AM - 8 PM",
                "locations": "Premium showroom locations (contact for details)"
            },
            
            "pricing_financing": {
                "financing_options": ["Auto Loans", "Lease Options", "Trade-in Programs", "Flexible Payment Plans"],
                "payment_methods": ["Credit Card", "Bank Transfer", "Financing", "Cash"],
                "trade_in": "Best market value for your current vehicle",
                "warranty": "Comprehensive warranty coverage available"
            }
        }
        
        # System prompt for the chatbot
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self):
        """Create a comprehensive system prompt with CarHub knowledge"""
        return f"""
You are CarHub's AI Assistant, a knowledgeable and professional automotive expert representing CarHub - "Where Every Journey Begins."

COMPANY INFORMATION:
{json.dumps(self.knowledge_base['company_info'], indent=2)}

SERVICES OFFERED:
{json.dumps(self.knowledge_base['services'], indent=2)}

CURRENT INVENTORY:
{json.dumps(self.knowledge_base['current_inventory'], indent=2)}

FEATURES & TECHNOLOGY:
{json.dumps(self.knowledge_base['features'], indent=2)}

CUSTOMER SATISFACTION:
{json.dumps(self.knowledge_base['customer_reviews'], indent=2)}

PERSONALITY & GUIDELINES:
- Be professional, friendly, and knowledgeable about automotive topics
- Show enthusiasm for cars and the automotive industry
- Provide detailed information about CarHub's services and inventory
- Help customers find the perfect vehicle for their needs
- Explain technical features in an accessible way
- Always prioritize customer satisfaction and service excellence
- If asked about specific prices or availability, reference the current inventory
- For complex technical questions, offer to connect them with a specialist
- Maintain CarHub's premium brand image in all interactions
- Use automotive terminology appropriately
- Be helpful with both buying and selling inquiries

RESPONSE STYLE:
- Professional yet approachable
- Enthusiastic about cars and automotive technology
- Detailed when discussing vehicles or services
- Concise for simple questions
- Always end with an offer to help further

IMPORTANT: 
- Only provide information about CarHub and automotive topics
- If asked about unrelated topics, politely redirect to automotive assistance
- Always maintain a helpful and professional tone
- Reference specific CarHub services and features when relevant
"""

    def get_chat_response(self, user_message, user_context=None, conversation_history=None):
        """
        Generate a response using OpenAI GPT with CarHub knowledge
        
        Args:
            user_message (str): The user's message
            user_context (dict): User information for personalization
            conversation_history (list): Previous conversation messages
        
        Returns:
            dict: Response with message and metadata
        """
        try:
            # If OpenAI is not available, use fallback responses
            if not self.openai_available:
                return self._get_fallback_response(user_message, user_context)
            
            # Prepare conversation history
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Keep last 10 messages for context
            
            # Add user context if available
            context_message = ""
            if user_context:
                context_message = f"\nUser Context: {json.dumps(user_context)}\n"
            
            # Add current user message
            messages.append({
                "role": "user", 
                "content": context_message + user_message
            })
            
            # Get response from OpenAI/OpenRouter
            model_name = "gpt-3.5-turbo"
            if hasattr(self, 'client') and self.client and hasattr(self.client, '_base_url'):
                if "openrouter.ai" in str(self.client._base_url):
                    model_name = "openai/gpt-3.5-turbo"  # OpenRouter format
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            assistant_message = response.choices[0].message.content
            
            # Check if the response contains specific CarHub information
            response_metadata = self._analyze_response(assistant_message, user_message)
            
            return {
                "success": True,
                "message": assistant_message,
                "metadata": response_metadata,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Handle specific OpenAI errors
            error_message = str(e)
            print(f"OpenAI Error: {error_message}")
            
            if "insufficient_quota" in error_message or "exceeded your current quota" in error_message:
                print("⚠️  OpenAI quota exceeded - falling back to knowledge base")
                # Fall back to knowledge base responses
                return self._get_fallback_response(user_message, user_context)
            elif "rate_limit" in error_message:
                print("⚠️  OpenAI rate limit - falling back to knowledge base")
                return self._get_fallback_response(user_message, user_context)
            else:
                print("⚠️  OpenAI API error - falling back to knowledge base")
                return self._get_fallback_response(user_message, user_context)
    
    def _get_fallback_response(self, user_message, user_context=None):
        """
        Generate fallback responses when OpenAI is not available
        """
        message_lower = user_message.lower()
        
        # Detect intent and provide relevant responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            response = f"Welcome to CarHub! 🚗 I'm your automotive assistant. How can I help you today?"
            
        elif any(word in message_lower for word in ['buy', 'purchase', 'looking for', 'want to buy']):
            response = f"""I'd be happy to help you find the perfect car! 

Here are some of our featured vehicles:
• Lamborghini Revuelto - $600,000 (Luxury)
• Tesla Model 3 - $45,000 (Electric)  
• BMW M2 G87 - $65,000 (Sports)
• Rolls Royce Ghost - $400,000 (Luxury)

What type of car are you interested in? Luxury, sports, electric, or family vehicles?"""

        elif any(word in message_lower for word in ['sell', 'selling', 'trade']):
            response = f"""Great! CarHub offers seamless car selling with maximized value.

Our selling process:
1. Free vehicle valuation
2. Quick inspection process  
3. Best market price guarantee
4. Smooth paperwork handling
5. Fast payment processing

Would you like to get a quote for your vehicle? I can help you get started!"""

        elif any(word in message_lower for word in ['service', 'maintenance', 'repair']):
            response = f"""CarHub provides precision service for peak performance!

Our services include:
• Oil changes and fluid checks
• Brake service and inspection
• Engine diagnostics
• Tire service and rotation
• General maintenance

Our certified technicians use state-of-the-art equipment. Would you like to schedule a service appointment?"""

        elif any(word in message_lower for word in ['luxury', 'expensive', 'premium']):
            response = f"""Our luxury collection features the finest automobiles:

Premium Vehicles Available:
• Bugatti Centodieci - $9,000,000 (Limited Edition)
• Bentley Mulliner Batur - $2,000,000 (Exclusive)
• Rolls Royce Ghost - $400,000
• Ferrari 296 GTB - $320,000
• Aston Martin V8 Vantage - $150,000

All vehicles come with comprehensive warranties and white-glove service."""

        elif any(word in message_lower for word in ['electric', 'ev', 'tesla', 'eco']):
            response = f"""Discover our electric vehicle collection:

Electric Cars Available:
• Tesla Model 3 - $45,000 (Premium electric sedan)
• Hyundai Ioniq 5N - $55,000 (High-performance electric SUV)

Benefits of going electric:
• Zero emissions
• Lower operating costs
• Advanced technology features
• Government incentives available

Would you like more details about any of these electric vehicles?"""

        elif any(word in message_lower for word in ['financing', 'loan', 'payment', 'credit']):
            response = f"""CarHub offers flexible financing options:

Available Options:
• Auto loans with competitive rates
• Lease programs with low monthly payments
• Trade-in programs for your current vehicle
• Flexible payment plans
• Quick approval process

We work with multiple lenders to get you the best rates. What's your budget range?"""

        elif any(word in message_lower for word in ['vintage', 'classic', 'old', 'antique']):
            response = f"""Explore our exquisite vintage collection - timeless beauty and rare finds!

Our vintage cars feature:
• Museum-grade restoration quality
• Historical documentation
• Expert authentication
• Comprehensive maintenance records

Each classic car is a piece of history, meticulously inspected and ready for a new legacy. Are you looking for a specific vintage model?"""

        elif any(word in message_lower for word in ['price', 'cost', 'how much', 'expensive']):
            response = f"""CarHub offers vehicles across all price ranges:

Price Categories:
• Family Cars: $25,000 - $50,000
• Sports Cars: $50,000 - $150,000  
• Luxury Cars: $150,000 - $500,000
• Ultra-Luxury: $500,000+
• Vintage Classics: Varies by rarity

We also offer financing to make your dream car affordable. What's your budget range?"""

        elif any(word in message_lower for word in ['contact', 'phone', 'call', 'reach']):
            response = f"""You can reach CarHub through:

• Website: Visit us at localhost:5000
• Online Chat: Right here with me! 
• Showroom: Premium locations (contact for details)
• Support Hours: 24/7 online, Showroom 9 AM - 8 PM

I'm here to help with any questions about our vehicles, services, or processes!"""

        else:
            response = f"""I'm here to help with all your automotive needs at CarHub!

I can assist you with:
🚗 Car Buying - Find your perfect vehicle
💰 Car Selling - Get the best value for your car  
🔧 Service - Schedule maintenance and repairs
✨ Luxury Cars - Explore premium vehicles
💳 Financing - Flexible payment options

What would you like to know more about?"""

        return {
            "success": True,
            "message": response,
            "metadata": self._analyze_response(response, user_message),
            "timestamp": datetime.now().isoformat(),
            "fallback": True
        }
    
    def _analyze_response(self, response, user_message):
        """Analyze the response to provide metadata"""
        metadata = {
            "intent": self._detect_intent(user_message),
            "mentioned_cars": self._extract_car_mentions(response),
            "mentioned_services": self._extract_service_mentions(response),
            "requires_followup": self._requires_followup(response)
        }
        return metadata
    
    def _detect_intent(self, message):
        """Detect user intent from the message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['buy', 'purchase', 'looking for', 'want to buy']):
            return 'buying_intent'
        elif any(word in message_lower for word in ['sell', 'selling', 'trade', 'trade-in']):
            return 'selling_intent'
        elif any(word in message_lower for word in ['service', 'maintenance', 'repair', 'fix']):
            return 'service_intent'
        elif any(word in message_lower for word in ['price', 'cost', 'how much', 'pricing']):
            return 'pricing_inquiry'
        elif any(word in message_lower for word in ['financing', 'loan', 'payment', 'finance']):
            return 'financing_inquiry'
        else:
            return 'general_inquiry'
    
    def _extract_car_mentions(self, response):
        """Extract mentioned car models from the response"""
        mentioned_cars = []
        for car in self.knowledge_base['current_inventory']:
            if car['name'].lower() in response.lower():
                mentioned_cars.append(car['name'])
        return mentioned_cars
    
    def _extract_service_mentions(self, response):
        """Extract mentioned services from the response"""
        mentioned_services = []
        for service in self.knowledge_base['services'].keys():
            if service.replace('_', ' ') in response.lower():
                mentioned_services.append(service)
        return mentioned_services
    
    def _requires_followup(self, response):
        """Determine if the response requires follow-up action"""
        followup_indicators = [
            'contact', 'schedule', 'visit', 'appointment', 
            'specialist', 'call', 'more information'
        ]
        return any(indicator in response.lower() for indicator in followup_indicators)
    
    def get_personalized_recommendations(self, user_preferences):
        """
        Get personalized car recommendations based on user preferences
        
        Args:
            user_preferences (dict): User preferences like budget, category, etc.
        
        Returns:
            list: Recommended cars with reasons
        """
        recommendations = []
        
        budget = user_preferences.get('budget', 'any')
        category = user_preferences.get('category', 'any')
        usage = user_preferences.get('usage', 'any')
        
        for car in self.knowledge_base['current_inventory']:
            score = 0
            reasons = []
            
            # Budget matching (simplified)
            if budget != 'any':
                # Add budget logic here
                pass
            
            # Category matching
            if category != 'any' and car['category'] == category:
                score += 2
                reasons.append(f"Matches your preferred {category} category")
            
            # Usage matching
            if usage != 'any':
                # Add usage logic here
                pass
            
            if score > 0:
                recommendations.append({
                    "car": car,
                    "score": score,
                    "reasons": reasons
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:5]  # Return top 5 recommendations
    
    def get_car_details(self, car_name):
        """Get detailed information about a specific car"""
        for car in self.knowledge_base['current_inventory']:
            if car_name.lower() in car['name'].lower():
                return {
                    "found": True,
                    "details": car,
                    "additional_info": self._get_additional_car_info(car['name'])
                }
        return {"found": False, "message": f"Sorry, I couldn't find information about {car_name}"}
    
    def _get_additional_car_info(self, car_name):
        """Get additional information about a car (could be from database)"""
        # This could query your Car model for more details
        return {
            "features": "Contact us for detailed specifications",
            "warranty": "Comprehensive warranty available",
            "financing": "Flexible financing options available"
        }

# Flask routes for chatbot integration
def create_chatbot_routes(app, db, User, Car, Order):
    """Create Flask routes for the chatbot"""
    
    # Initialize chatbot
    chatbot = CarHubChatbot(db, User, Car, Order)
    
    @app.route('/api/chat', methods=['POST'])
    def chat_endpoint():
        """Main chat endpoint"""
        try:
            print("📨 Chat endpoint called")
            data = request.get_json()
            print(f"📊 Request data: {data}")
            
            if not data or 'message' not in data:
                print("❌ No message in request")
                return jsonify({
                    "success": False,
                    "error": "Message is required"
                }), 400
            
            user_message = data['message']
            conversation_history = data.get('history', [])
            print(f"💬 Processing message: {user_message}")
            
            # Get user context if logged in
            user_context = None
            try:
                if hasattr(session, 'user_id') and session.get('user_id'):
                    user = User.query.get(session['user_id'])
                    if user:
                        user_context = {
                            "username": user.username,
                            "email": user.email,
                            "is_returning_customer": True
                        }
                        print(f"👤 User context: {user_context}")
            except Exception as ctx_error:
                print(f"⚠️ User context error: {ctx_error}")
                pass
            
            # Get response from chatbot
            print("🤖 Getting chatbot response...")
            response = chatbot.get_chat_response(
                user_message, 
                user_context, 
                conversation_history
            )
            
            print(f"✅ Chatbot response: {response}")
            return jsonify(response)
            
        except Exception as e:
            print(f"❌ Chat endpoint error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": "An error occurred processing your request",
                "details": str(e)
            }), 500
    
    @app.route('/api/chat/recommendations', methods=['POST'])
    def get_recommendations():
        """Get personalized car recommendations"""
        try:
            data = request.get_json()
            preferences = data.get('preferences', {})
            
            recommendations = chatbot.get_personalized_recommendations(preferences)
            
            return jsonify({
                "success": True,
                "recommendations": recommendations
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/api/chat/car-details/<car_name>')
    def get_car_details(car_name):
        """Get details about a specific car"""
        try:
            details = chatbot.get_car_details(car_name)
            return jsonify({
                "success": True,
                "data": details
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    return chatbot
