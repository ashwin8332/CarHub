# CarHub - Developer Documentation
## Project Architecture
### Core Components
1. **Flask Web Application (`app.py`)**
   - Main application entry point
   - Route definitions and handlers
   - User authentication logic
   - Database models
   - Form validation
2. **AI Chatbot (`chatbot.py`)**
   - OpenAI integration
   - Knowledge base management
   - Conversational logic
   - Car recommendation engine

3. **Authentication (`google_auth.py`)**
   - Google OAuth integration
   - User account management

4. **Database (`instance/carhub.db`)**
   - SQLite database with SQLAlchemy ORM
   - User, Car, Order, and other models

5. **Templates (`templates/`)**
   - HTML templates with Jinja2 templating
   - Modular components

6. **Static Assets (`static/`)**
   - CSS styling
   - JavaScript functionality
   - Media files (videos, 3D models)

## Database Schema

### User Model
- id (Primary Key)
- username
- email (Unique)
- password_hash
- google_id (Optional)
- profile_picture (Optional)
- is_verified (Boolean)
- role (admin/user)
- Other profile fields

### Car Model
- id (Primary Key)
- name
- brand
- model
- year
- price
- category
- description
- image_path
- model_path (3D model)
- video_path

### Order Model
- id (Primary Key)
- user_id (Foreign Key)
- car_id (Foreign Key)
- status (pending/completed/cancelled)
- price
- payment_method
- created_at
- cancellation_fee (Optional)

### Other Models
- FinanceApplication
- UserActivity
- Parts
- Reviews

## Route Structure

### Main Pages
- `/` - Homepage
- `/cars` - Car listing
- `/about` - About page
- `/services` - Services page
- `/contact` - Contact page
- `/inventory` - Inventory page

### Authentication
- `/login` - User login
- `/sign_up` - User registration
- `/logout` - User logout
- `/forgot_password` - Password recovery
- `/reset_password/<token>` - Password reset
- `/auth/google` - Google OAuth

### Car Details
- `/car-details/<car_name>` - Detailed car view
- `/part-details/<part_id>` - Detailed part view
- `/product-details/<product_id>` - Product details

### User Dashboard
- `/profile` - User profile
- `/dashboard` - User dashboard
- `/edit_profile` - Edit user profile
- `/my_orders` - User orders

### Payment & Checkout
- `/buy/<car_name>` - Initiate purchase
- `/payment` - Payment processing
- `/payment-success/<int:order_id>` - Payment confirmation
- `/finance` - Financing application
- `/finance-success/<int:application_id>` - Finance approval
- `/download-invoice/<int:order_id>` - Invoice PDF generation

### Admin Routes
- `/admin_panel` - Admin dashboard
- `/admin_users` - User management
- `/admin_orders` - Order management
- `/admin_activities` - Activity logs

### API Endpoints
- `/api/chat` - Chatbot conversation
- `/api/chat/recommendations` - Car recommendations
- `/api/chat/car-details/<car_name>` - Car information

## Implementation Details

### Authentication System
- Password hashing with Werkzeug
- Login session management with Flask-Login
- Password reset via secure tokens
- Google OAuth integration with google-auth

### Email System
- Flask-Mail integration
- HTML email templates
- Token-based verification
- Error handling

### Order Processing
- Multi-step checkout flow
- Status tracking
- Cancellation logic with fee calculation
- PDF invoice generation with ReportLab

### AI Chatbot
- OpenAI API integration
- Context-aware conversations
- Fallback responses when API unavailable
- User-specific personalization

### 3D Model Rendering
- Three.js integration
- GLB model format
- Camera controls and lighting
- Mobile optimization

## Security Measures

### Authentication Security
- Password hashing
- CSRF protection
- Secure session cookies
- OAuth token validation

### Data Protection
- Input validation and sanitization
- SQL injection prevention via ORM
- XSS protection
- Sensitive data encryption

### Access Control
- Role-based permissions
- Route protection with login_required
- User ownership validation

## Frontend Architecture

### CSS Structure
- Base styling (`style.css`)
- Theme components (`theme.css`)
- Responsive design
- Dark mode support

### JavaScript Components
- Form validation
- 3D model viewer
- Chatbot interface
- Theme toggling

### Media Management
- Video backgrounds
- 3D models
- Responsive images
- Lazy loading

## Deployment Considerations

### Environment Variables
- Secret key generation
- API keys management
- Email configuration
- Database connection strings

### Database Management
- Initial schema creation
- Migration strategy
- Backup procedures

### Performance Optimization
- Static asset caching
- Database query optimization
- Video compression
- 3D model optimization

### Scaling Considerations
- Potential migration to PostgreSQL
- Static content CDN
- API rate limiting

## Development Workflow

### Local Setup
1. Clone repository
2. Install dependencies
3. Configure environment variables
4. Initialize database
5. Start development server

### Code Style
- PEP 8 Python conventions
- Consistent indentation (4 spaces)
- Descriptive variable names
- Function/class documentation

### Testing
- Unit tests for core functionality
- Form validation testing
- API endpoint testing
- Authentication flow testing

---

## Future Development Roadmap

### Planned Features
- Payment gateway integration
- Multi-language support
- Enhanced admin analytics
- Mobile app integration

### Technical Improvements
- Migration to PostgreSQL
- API rate limiting
- Front-end framework integration
- Containerization with Docker

### Performance Enhancements
- Image optimization pipeline
- Server-side rendering
- Database indexing
- Query optimization

---
*Created for CarHub development team *